"""#3 生产采集:全市场减持预披露(cninfo 列表 → title 放宽判据 → L3 三字段)→ JSONL staging。
可续跑(done.txt 跳过已采)、逐股错误隔离、附新判据召回重估统计(人裁③)。**不入库**(loader 另跑)。
"""
import datetime as dt
import json
import os
import re
import sys
import time
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 同目录:parse_holder_reduction 裸 import cninfo
import cninfo
import parse_holder_reduction as P
import psycopg

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # 仓根(.env 在此)

STAGE = "/tmp/s3prod"
HITS = STAGE + "/hits.jsonl"
DONE = STAGE + "/done.txt"
ERRS = STAGE + "/errors.jsonl"
STATS = STAGE + "/stats.json"
START, END = dt.date(2010, 1, 1), dt.date(2024, 6, 30)   # 尽可能长史;END<holdout 2024-07-01

# 召回重估用"很宽网"(新判据的上界候选):含"减持" 且 非明显增持/回购/要约。gap=新判据潜在残漏。
_VBROAD = re.compile(r"减持")
_VBROAD_EXCL = re.compile(r"增持|回购|要约")


def suffix(code):
    return code + (".SH" if code.startswith("6") else ".SZ")


def load_done():
    if not os.path.exists(DONE):
        return set()
    with open(DONE) as f:
        return set(x.strip() for x in f if x.strip())


def codes_from_db():
    env = {}
    for line in open(os.path.join(_ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
    c = psycopg.connect(env.get("QBASE_APP_DSN"))
    cur = c.cursor()
    cur.execute("""SELECT ts_code FROM entity_master
                   WHERE batch_id=(SELECT max(batch_id) FROM entity_batch WHERE source='tushare:stock_basic')
                     AND ts_code !~ '\\.BJ$' ORDER BY ts_code""")
    out = [r[0][:6] for r in cur.fetchall()]   # 无后缀(cninfo 口径)
    c.close()
    return out


def run():
    os.makedirs(STAGE, exist_ok=True)
    done = load_done()
    _test = os.environ.get("TEST_CODES")
    all_codes = _test.split(",") if _test else codes_from_db()
    todo = [c for c in all_codes if c not in done]
    print(f"全市场 {len(all_codes)} 只,已采 {len(done)},待采 {len(todo)}", flush=True)
    st = {"total_ann": 0, "vbroad": 0, "new_strict": 0, "hits_written": 0,
          "field_ok": {"holder": 0, "ratio": 0, "period": 0, "all3": 0},
          "by_year": {},                # {year: {strict, all3_ok, ratio_ge1, ratio_known}}
          "exclude_reasons": {}, "codes_done": len(done), "started": None,
          "_note_vbroad": "vbroad=title含减持 减 增持/回购/要约(超宽上界);vbroad∖new_strict 多为事后件"
                          "(进展/结果/实施/届满),真召回须人核 remaining_sample,非 new_strict/vbroad"}
    if os.path.exists(STATS):
        try:
            st = json.load(open(STATS))
        except Exception:
            pass
    hits_f = open(HITS, "a"); done_f = open(DONE, "a"); err_f = open(ERRS, "a")
    remaining_sample = []
    for n, code in enumerate(todo, 1):
        try:
            anns = cninfo.fetch_announcements(code, START, END, category="")
        except Exception as e:
            err_f.write(json.dumps({"code": code, "err": repr(e)}, ensure_ascii=False) + "\n"); err_f.flush()
            print(f"[{code}] 拉取失败 {e!r}", flush=True)
            continue
        seen = set()
        c_hits = 0
        for a in anns:
            aid = a.get("announcement_id")
            if aid in seen:
                continue
            seen.add(aid)
            st["total_ann"] += 1
            title = a.get("title", "")
            is_hit, reason = P.classify_title(title)
            vb = bool(_VBROAD.search(title) and not _VBROAD_EXCL.search(title))
            if vb:
                st["vbroad"] += 1
            if not is_hit:
                if reason.startswith("排除:"):
                    st["exclude_reasons"][reason] = st["exclude_reasons"].get(reason, 0) + 1
                if vb and len(remaining_sample) < 200:
                    remaining_sample.append({"code": code, "title": title, "reason": reason})
                continue
            st["new_strict"] += 1
            # 三字段解析
            url = a.get("source_url")
            try:
                text = P.fetch_pdf_text(url) if url else ""
                fields = P.extract_fields(text)
            except Exception as e:
                fields = {"holder_name": None, "reduce_ratio_max_pct": None,
                          "reduce_period_start": None, "reduce_period_end": None,
                          "reduce_period_text": None, "reduce_period_kind": None,
                          "parse_fail": ["pdf_error:" + type(e).__name__]}
            rec = {"stock_code": code, "ts_code": suffix(code),
                   "announcement_id": aid, "title": title,
                   "announcement_type": a.get("announcement_type"),
                   "source_url": url, "title_reason": reason,
                   "valid_time": a.get("valid_time").isoformat() if a.get("valid_time") else None,
                   **{k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in fields.items()
                      if k != "parse_fail"},
                   "parse_fail": fields.get("parse_fail") or []}
            hits_f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            c_hits += 1; st["hits_written"] += 1
            # 字段级解析率(人裁③×年份)+ 比例≥1%(#3 门槛)
            fails = fields.get("parse_fail") or []
            yr = a.get("valid_time").year if a.get("valid_time") else None
            d = st["by_year"].setdefault(str(yr), {"strict": 0, "all3_ok": 0, "ratio_ge1": 0, "ratio_known": 0})
            d["strict"] += 1
            if fields.get("holder_name"): st["field_ok"]["holder"] += 1
            if fields.get("reduce_ratio_max_pct") is not None: st["field_ok"]["ratio"] += 1
            if fields.get("reduce_period_text") or fields.get("reduce_period_start"): st["field_ok"]["period"] += 1
            if not fails:
                st["field_ok"]["all3"] += 1; d["all3_ok"] += 1
            r = fields.get("reduce_ratio_max_pct")
            if r is not None:
                d["ratio_known"] += 1
                if r >= 1.0: d["ratio_ge1"] += 1
        hits_f.flush()
        done_f.write(code + "\n"); done_f.flush()
        st["codes_done"] += 1
        if c_hits or n % 50 == 0:
            print(f"[{n}/{len(todo)}] {code} 公告{len(seen)} 命中{c_hits} | 累计命中{st['hits_written']}", flush=True)
        if n % 50 == 0:
            st["remaining_sample_n"] = len(remaining_sample)
            json.dump(st, open(STATS, "w"), ensure_ascii=False, indent=1)
    st["strict_over_vbroad"] = (st["new_strict"] / st["vbroad"]) if st["vbroad"] else None  # 非召回!见 _note_vbroad
    st["parse_rate_all3"] = (st["field_ok"]["all3"] / st["new_strict"]) if st["new_strict"] else None
    st["remaining_sample"] = remaining_sample   # vbroad∖new_strict:人核以定真召回(旧40%作废)
    st["by_year"] = dict(sorted(st["by_year"].items()))
    json.dump(st, open(STATS, "w"), ensure_ascii=False, indent=1)
    hits_f.close(); done_f.close(); err_f.close()
    print("=== 采集完成 ===", flush=True)
    print(json.dumps({k: v for k, v in st.items() if k not in ("remaining_sample",)},
                     ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
