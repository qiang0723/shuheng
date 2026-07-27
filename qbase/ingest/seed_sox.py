#!/usr/bin/env python3
"""exp24 数据前置 · SOX 单指数最小采集件(阿里云执行;人令 2026-07-27 二,裁定 A4)。

主锚=Nasdaq GIW 站点内部端点 POST https://indexes.nasdaq.com/Index/HistoryData
(人裁 A4;**不得称"官方授权API"**——站点内部 AJAX,非承诺接口;原始响应与 SHA256
仅存内部证据包 --evidence 目录,不入库不入仓)。Yahoo ^SOX 交叉校验=另件
sox_cross_check.py(AWS 出口执行)。

采集范围(人令,不因 A 股估计窗扩大):
  自「首个研究事件前一个 SOX 交易日」起,至「能完整判定 event_date<2024-07-01」止。
  推定(交付档留痕):研究范围=PAP 草案 2011-01-01≤event_date<2024-07-01;映射=美国交易日 T
  收盘→北京历日 T+1 起首个 A 股交易日(窄闸§2.3)。以 qbase trade_cal_snap(SSE,最新批)推定:
  T0=最小 T 使 map(T)≥首个 2011 年 A 股交易日;载入起点=T0 的前一个实际 SOX 交易行;
  T_end=最大 T 使 map(T)≤holdout 前最后一个 A 股交易日。拉取窗带少量日历缓冲以定边界实际行,
  **缓冲行只留证据包不落库**(载入=[起点,T_end] 精确裁剪)。

范式承 seed_marketdata.py:fact_batch(source='nasdaq_giw:sox_daily')+append-only COPY+
整行去重+双时戳(valid_time=美东交易日 16:00 America/New_York 收盘之 UTC;observed_time=
本批 pull_time,不冒充实时)。范围红线:单指数 SOX,不建通用美股腿。

用法:python seed_sox.py --evidence /root/s24dataclose/nasdaq_raw          # 采集+落库
      python seed_sox.py --dry --evidence /tmp/sox_dry                     # 单窗连通验证,不落库
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import psycopg

ENDPOINT = "https://indexes.nasdaq.com/Index/HistoryData"
UA = "Mozilla/5.0 (X11; Linux x86_64)"
RESEARCH_START = date(2011, 1, 1)      # PAP 草案研究范围下界(确认清单#5 已批)
HOLDOUT_START = date(2024, 7, 1)       # holdout(视图焊死同值)
FETCH_BUFFER_START = date(2010, 12, 20)  # 日历缓冲(仅为定边界实际行;缓冲行不落库)
ET = ZoneInfo("America/New_York")


def load_env(path="/opt/quant/.env"):
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def fetch_window(start: date, end: date, evidence_dir: str, sleep_s: float, log):
    """单窗 POST;原始响应字节仅写证据包并记 SHA256;返回 (rows, sha, raw_path)。"""
    data = urllib.parse.urlencode({
        "id": "SOX", "startDate": start.isoformat(), "endDate": end.isoformat(),
        "timeOfDay": "EOD"}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA})
    last = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            break
        except Exception as e:                      # 节流容错:退避重试,3 次仍败即停报
            last = e
            log(f"  窗 {start}..{end} 第{attempt}次失败: {type(e).__name__} {e}; 退避重试")
            time.sleep(5 * attempt)
    else:
        raise RuntimeError(f"Nasdaq 端点三次失败,停报(人裁A4 无自动改源): {last}")
    sha = hashlib.sha256(raw).hexdigest()
    raw_path = os.path.join(evidence_dir, f"nasdaq_SOX_{start}_{end}.json")
    with open(raw_path, "wb") as f:
        f.write(raw)
    doc = json.loads(raw)
    rows = []
    for r in doc.get("aaData", []):
        ms = int(re.search(r"-?\d+", r["TimeStamp"]).group())
        d = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()
        rows.append({
            "trade_date": d,
            "close": None if r.get("Value") is None else str(r["Value"]),
            "high": None if r.get("High") is None else str(r["High"]),
            "low": None if r.get("Low") is None else str(r["Low"]),
            "net_change": None if r.get("NetChange") is None else str(r["NetChange"]),
            "currency": r.get("Currency"),
        })
    log(f"  窗 {start}..{end}: {len(rows)} 行, sha256={sha[:16]}…")
    time.sleep(sleep_s)
    return rows, sha, os.path.basename(raw_path)


def year_windows(start: date, end: date):
    cur = start
    while cur <= end:
        stop = min(date(cur.year, 12, 31), end)
        yield cur, stop
        cur = stop + timedelta(days=1)


def load_open_days(cur):
    """A 股开市日(SSE,最新批;只读)。"""
    cur.execute(
        "SELECT cal_date FROM public.trade_cal_snap WHERE exchange='SSE' AND is_open=1 "
        "AND batch_id=(SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:trade_cal') "
        "ORDER BY cal_date")
    return [r[0] for r in cur.fetchall()]


def map_ashare(t: date, open_days: list) -> date | None:
    """美国交易日 T → 北京历日 T+1 起首个 A 股交易日(窄闸§2.3;日期级,无前视)。"""
    i = bisect_left(open_days, t + timedelta(days=1))
    return open_days[i] if i < len(open_days) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--evidence", required=True, help="内部证据包目录(原始响应+SHA;不入库不入仓)")
    ap.add_argument("--sleep", type=float, default=1.2)
    a = ap.parse_args()
    os.makedirs(a.evidence, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg, flush=True)
        log_lines.append(msg)

    env = load_env()
    pull_time = datetime.now(timezone.utc)

    if a.dry:
        rows, sha, _ = fetch_window(date(2026, 7, 20), date(2026, 7, 24), a.evidence, 0, log)
        log(f"--dry: 样本 {rows[:2]}")
        return 0

    with psycopg.connect(env["QBASE_APP_DSN"]) as conn, conn.cursor() as cur:
        open_days = load_open_days(cur)
        first_open_2011 = open_days[bisect_left(open_days, RESEARCH_START)]
        last_open_pre_holdout = open_days[bisect_left(open_days, HOLDOUT_START) - 1]
        log(f"A股界(trade_cal 最新批): 首个2011交易日={first_open_2011}, holdout 前最后交易日={last_open_pre_holdout}")

        # ── 拉取(含日历缓冲;T 上界=map(T)≤last_open 的日历必要条件 T≤last_open-1)──────
        fetch_end = last_open_pre_holdout - timedelta(days=1)
        windows, all_rows = [], []
        for ws, we in year_windows(FETCH_BUFFER_START, fetch_end):
            rows, sha, fname = fetch_window(ws, we, a.evidence, a.sleep, log)
            windows.append({"start": str(ws), "end": str(we), "rows": len(rows), "sha256": sha,
                            "file": fname})
            all_rows.extend(rows)

        # ── 整行去重+排序+完整性 ────────────────────────────────────────────────
        seen, rows = set(), []
        for r in all_rows:
            key = tuple(sorted(r.items(), key=lambda kv: kv[0]))
            if key not in seen:
                seen.add(key)
                rows.append(r)
        rows.sort(key=lambda r: r["trade_date"])
        dates = [r["trade_date"] for r in rows]
        assert len(dates) == len(set(dates)), "同日多行:源数据异常,停报"
        assert all(r["close"] is not None for r in rows), "存在空 close:停报"

        # ── 精确裁剪(人令范围;缓冲行只留证据包)───────────────────────────────
        t0 = next(d for d in dates if map_ashare(d, open_days) >= first_open_2011)
        i0 = dates.index(t0)
        assert i0 >= 1, "T0 前无前一 SOX 交易行(缓冲不足),停报"
        start_keep = dates[i0 - 1]                       # 首个研究事件前一个 SOX 交易日
        t_end = max(d for d in dates if map_ashare(d, open_days) is not None
                    and map_ashare(d, open_days) <= last_open_pre_holdout)
        kept = [r for r in rows if start_keep <= r["trade_date"] <= t_end]
        log(f"范围推定: T0={t0}(map→{map_ashare(t0, open_days)}), 载入起点={start_keep}, "
            f"T_end={t_end}(map→{map_ashare(t_end, open_days)}); 拉取 {len(rows)} 行→载入 {len(kept)} 行"
            f"(缓冲弃 {len(rows) - len(kept)} 行,仅存证据包)")

        # ── fact_batch + COPY(append-only)────────────────────────────────────
        note = (f"exp24 数据前置(人令2026-07-27二,裁定A4):Nasdaq GIW 站点内部端点(主锚,非官方授权API)"
                f"SOX 日线 EOD;载入范围 {start_keep}..{t_end}(=首个研究事件前一 SOX 交易日起,至完整判定 "
                f"event_date<{HOLDOUT_START} 止;T0={t0});原始响应+SHA 仅存内部证据包;"
                f"Yahoo ^SOX 交叉校验另件另录。")
        cur.execute("INSERT INTO public.fact_batch(source,asof_date,pull_time,note) "
                    "VALUES (%s,%s,%s,%s) RETURNING batch_id",
                    ("nasdaq_giw:sox_daily", t_end, pull_time, note))
        bid = cur.fetchone()[0]
        cols = "batch_id,trade_date,close,high,low,net_change,currency,valid_time,observed_time"
        with cur.copy(f"COPY public.sox_daily_snap ({cols}) FROM STDIN") as cp:
            for r in kept:
                vt = datetime.combine(r["trade_date"], datetime.min.time().replace(hour=16),
                                      tzinfo=ET).astimezone(timezone.utc)
                cp.write_row((bid, r["trade_date"], r["close"], r["high"], r["low"],
                              r["net_change"], r["currency"], vt, pull_time))
        conn.commit()
        cur.execute("SELECT count(*), min(trade_date), max(trade_date) "
                    "FROM public.sox_daily_snap WHERE batch_id=%s", (bid,))
        n, dmin, dmax = cur.fetchone()
        log(f"落库: batch_id={bid} rows={n} range={dmin}..{dmax}")
        assert n == len(kept), "落库行数≠载入行数,停报"

    manifest = {"pull_time": pull_time.isoformat(), "endpoint": ENDPOINT,
                "batch_id": bid, "loaded_rows": n, "loaded_range": [str(dmin), str(dmax)],
                "t0": str(t0), "t_end": str(t_end),
                "first_open_2011": str(first_open_2011),
                "last_open_pre_holdout": str(last_open_pre_holdout),
                "windows": windows, "note": note}
    with open(os.path.join(a.evidence, "nasdaq_fetch_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.evidence, "fetch_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    log("证据包写毕: nasdaq_fetch_manifest.json + 原始响应 + fetch_log.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
