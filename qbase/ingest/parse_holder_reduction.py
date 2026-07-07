"""L3 · 减持预披露公告 PDF 解析件(已批范围钉死,2026-07-07)。

承 `cninfo.py`(只抓公告列表元数据、不解析正文)下游接一刀:定位**减持预披露**公告 →
下载 PDF → 抽**三字段**。范围钉死(人批,不得扩):
  ①仅**减持预披露**类(排除 期限届满/实施情况/进展/结果/增持);
  ②仅抽三字段 = 拟减持股东名 / 拟减持比例上限(%) / 减持期间(起-止);
  ③抽取失败**如实标注**(字段留 None + 记 fail 原因),不猜不填默认;
  ④**不做通用框架**——只认这一类公告的固定文书结构,别的公告不碰。

L4 实采结论(2026-07-07 侦察 002230 等):巨潮 announcement_type/category **码不稳**
  (同为「减持预披露公告」,type 一次带 012399 一次不带)→ 靠 type/category 筛不可靠;
  **title 才是稳定判别**(减持+预披露,排除 期限届满/实施情况/进展)。故本件用 title 筛。

红线(承 cninfo):只忠实解析公开披露事实,不解读、不打标签、不做投资判断。本刀**不入库**
  (落库对接 #3 事件另说);产出结构化记录供上层。PIT:valid_time=公告披露时点(cninfo 已转 UTC)。

依赖:cninfo(同目录,stdlib 采集)+ pypdf(纯 Python PDF 文本抽取)。
用法:python parse_holder_reduction.py --code 002230 --start 2023-01-01 --end 2023-12-31
      python parse_holder_reduction.py --sample     # 抽验固定几只票,验 title 筛 + 三字段抽取
"""
import argparse
import datetime as dt
import io
import re
import sys
import urllib.request

import cninfo  # 同目录采集件(借入,只抓不入库)

# ── title 判别(L4:靠 title 不靠 type 码)────────────────────────────────────
# 预披露 = 减持"计划"的事前披露;排除事后/进展/届满/增持。
_RE_REDUCE_PRE = re.compile(r"减持")
_RE_PREDISCLOSE = re.compile(r"预披露")
_RE_EXCLUDE = re.compile(r"期限届满|实施情况|实施进展|进展公告|减持结果|完成情况|届满暨|增持")


def is_reduction_predisclosure(title: str) -> bool:
    """减持预披露公告判别:title 含 减持+预披露 且不含 事后/进展/增持 词。"""
    t = title or ""
    return bool(_RE_REDUCE_PRE.search(t) and _RE_PREDISCLOSE.search(t)
                and not _RE_EXCLUDE.search(t))


# ── PDF 正文抽取 ─────────────────────────────────────────────────────────────
def fetch_pdf_text(url: str, timeout: float = 30) -> str:
    """下载 PDF → pypdf 抽全文文本。失败抛异常(上层记 fail)。"""
    from pypdf import PdfReader
    req = urllib.request.Request(url, headers={"User-Agent": cninfo.UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


# ── 三字段抽取(只认减持预披露文书固定结构;失败留 None)───────────────────────
_DATE = r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日"
# 减持期间(绝对式):"减持期间：起-止" 或 "计划在 起-止 …方式减持"(特别提示句)。
_RE_PERIOD_LABELED = re.compile(r"减持期间[：:]\s*(" + _DATE + r")\s*[-—~至]+\s*(" + _DATE + r")")
_RE_PERIOD_PLAN = re.compile(r"计划在\s*(" + _DATE + r")\s*[-—~至]+\s*(" + _DATE + r")")
# 减持期间(相对式):"…本(减持计划)?公告(披露)之日起 N…个月内"(无绝对日,如实捕获原文)。
# 覆盖 "本公告之日起" / "本减持计划公告之日起" / "本公告披露之日起" 三种起算措辞。
_RE_PERIOD_REL = re.compile(
    r"(本(?:次)?(?:减持计划)?公告(?:披露)?之日起[^，。；]{0,50}?(?:个月内|日内|之内))")
# 股东名(精度优先:宁可失败也不出垃圾。三锚 + 噪声词拒绝过滤)。
_RE_HOLDER_LABELED = re.compile(r"股东的?名称[：:]\s*([^，。；、（(]{2,40})")
# 机构名:实体后缀收尾 + 右界须紧跟 (以下简称|计划|拟|，|将等,防吞正文);左界 股东-标志紧邻(≤6字修饰)。
_ENT_SUFFIX = (r"(?:股份有限公司|有限责任公司|有限公司|合伙企业|投资中心|管理中心|"
               r"资产管理|基金|集团|银行|证券|保险|信托)")
_RE_HOLDER_ENTITY = re.compile(
    r"(?:持股[^，。；、]{0,10}?股东|公司股东|控股股东|第[一二三四五六]大股东|、股东|的股东|^股东|。股东)"
    r"([一-龥]{2,26}?" + _ENT_SUFFIX + r")(?:（[^）]{0,25}）)?\s*(?:计划|拟|将|，|、|（以下)")
# 个人(董监高/一致行动人):姓名紧邻 先生/女士 前 2-4 字;前缀非捕获、限≤10 字防跨句。
_RE_HOLDER_PERSON = re.compile(
    r"(?:高级管理人员|监事|董事|控股股东|一致行动人)[^，。；]{0,10}?([一-龥]{2,4})(?:先生|女士)")
# 噪声词:干净公司/人名不含这些标题/正文词;含即判垃圾(横跨标题吞进的误匹配)→拒绝、判失败。
_RE_HOLDER_NOISE = re.compile(r"减持|预披露|公告|计划|情况|披露|本公司|证券交易所")
# 个人名前的角色/关系前缀:剥离(如"董事李杰"→"李杰"、"及其一致行动人林林"→"林林")。
_RE_ROLE_PREFIX = re.compile(
    r"^(?:独立董事|董事会秘书|副总经理|财务总监|高级管理人员|总经理|副总裁|董事|监事|董秘|"
    r"及其一致行动人|一致行动人|之一)+")


def _valid_holder(name):
    """精度过滤:去边缘符 + 剥角色前缀、拒噪声词污染名、拒过短/过长。返回干净名或 None(判失败)。"""
    if not name:
        return None
    name = name.strip("的。、，（(“\" ")
    name = _RE_ROLE_PREFIX.sub("", name).strip("的、 ")
    if not (2 <= len(name) <= 40) or _RE_HOLDER_NOISE.search(name):
        return None
    return name
# 拟减持比例上限:**必须锚在减持句"不超过…总股本…X%"**。陷阱:同段并列**股东持股比例**
#   ("持有…股份 N 股(占…总股本…8.08%)"),不含"不超过"→若只匹配"总股本…X%"会误抓持股比例。
#   故强制"不超过 … 总股本 … X%"(覆盖 占总股本比例为X% / 公司总股本比例的X% 两种措辞)。
_RE_RATIO = re.compile(r"不超过[^%]{0,110}?总股本[^%]{0,20}?([\d.]+)\s*%")
# 退路:比例不带"总股本"字样时,"减持…不超过…X%"(仍要求"减持"锚定,避开无关百分数)。
_RE_RATIO_FALLBACK = re.compile(r"减持[^%]{0,60}?不超过[^%]{0,60}?([\d.]+)\s*%")


def _norm_date(s: str) -> str:
    """'2023 年 8 月 22 日' → '2023-08-22'(纯归一格式,不改语义)。"""
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if not m:
        return s.strip()
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def extract_fields(text: str) -> dict:
    """抽三字段。每字段独立成败,失败留 None 并记 fail 列表(如实标注,不猜)。
    减持期间两态:绝对式→start/end 日期 + kind=absolute;相对式(披露之日起…)→原文 text + kind=relative
    (相对期间无绝对日,如实存原文非失败——绝对日需交易日历换算,留下游 #3 按 valid_time 折算)。"""
    # CJK PDF 换行/空格是排版噪声(会把"6 个\n月内"、被拆断的数字截断)→抽取前统一去空白。
    text = re.sub(r"\s+", "", text)
    fails = []
    # 减持期间:先试绝对式,再试相对式
    p_start = p_end = p_text = p_kind = None
    m = _RE_PERIOD_LABELED.search(text) or _RE_PERIOD_PLAN.search(text)
    if m:
        p_start, p_end = _norm_date(m.group(1)), _norm_date(m.group(2))
        p_text, p_kind = f"{p_start}~{p_end}", "absolute"
    else:
        mr = _RE_PERIOD_REL.search(text)
        if mr:
            p_text = re.sub(r"\s+", "", mr.group(1))
            p_kind = "relative"
        else:
            fails.append("reduce_period")
    # 拟减持股东名:标注字段 → 机构实体名 → 个人姓名(由准到宽);逐锚过噪声过滤,首个干净即用。
    holder = None
    for rx in (_RE_HOLDER_LABELED, _RE_HOLDER_ENTITY, _RE_HOLDER_PERSON):
        m = rx.search(text)
        if m:
            holder = _valid_holder(m.group(1))
            if holder:
                break
    if not holder:
        fails.append("holder_name")  # 精度优先:多主体/异构表述宁判失败也不出垃圾
    # 拟减持比例上限(%)
    m = _RE_RATIO.search(text) or _RE_RATIO_FALLBACK.search(text)
    ratio_pct = float(m.group(1)) if m else None
    if ratio_pct is None:
        fails.append("reduce_ratio_max_pct")
    return {
        "holder_name": holder,
        "reduce_ratio_max_pct": ratio_pct,
        "reduce_period_start": p_start,   # 绝对式起日(相对式为 None)
        "reduce_period_end": p_end,       # 绝对式止日
        "reduce_period_text": p_text,     # 期间原文(绝对式=起~止;相对式=披露之日起…原文)
        "reduce_period_kind": p_kind,     # absolute | relative | None
        "parse_fail": fails,              # 空=三字段全中;非空=如实标注哪几项没抽到
    }


def parse_code(code: str, start: dt.date, end: dt.date) -> list[dict]:
    """抓某票某期减持预披露公告 → 逐份下载解析 → 结构化记录(含 provenance + 成败标注)。"""
    anns = cninfo.fetch_announcements(code, start, end)
    hits = [a for a in anns if is_reduction_predisclosure(a["title"])]
    out = []
    for a in hits:
        rec = {
            "stock_code": a["stock_code"], "title": a["title"],
            "valid_time": a["valid_time"], "source_url": a["source_url"],
            "holder_name": None, "reduce_ratio_max_pct": None,
            "reduce_period_start": None, "reduce_period_end": None,
            "reduce_period_text": None, "reduce_period_kind": None,
            "parse_fail": ["pdf_fetch_or_parse"],
        }
        try:
            text = fetch_pdf_text(a["source_url"])
            rec.update(extract_fields(text))
        except Exception as e:  # noqa: BLE001 —— PDF 下载/解析失败:如实标注,不静默
            rec["parse_fail"] = [f"pdf_error:{type(e).__name__}"]
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code")
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2023-12-31")
    ap.add_argument("--sample", action="store_true",
                    help="抽验固定几只票(验 title 筛 + 三字段抽取 + 失败标注)")
    args = ap.parse_args()

    codes = ["002230", "002415", "300308"] if args.sample else [args.code]
    if not args.sample and not args.code:
        sys.exit("需 --code 或 --sample")
    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)

    total = ok = 0
    for code in codes:
        recs = parse_code(code, start, end)
        print(f"═══ {code} [{start}~{end}] 减持预披露命中 {len(recs)} 份 ═══", flush=True)
        for r in recs:
            total += 1
            status = "✅全中" if not r["parse_fail"] else f"⚠缺{r['parse_fail']}"
            ok += 0 if r["parse_fail"] else 1
            print(f"  {status}", flush=True)
            print(f"    title : {r['title']}", flush=True)
            print(f"    股东  : {r['holder_name']}", flush=True)
            print(f"    比例上限: {r['reduce_ratio_max_pct']}%  期间({r['reduce_period_kind']}): "
                  f"{r['reduce_period_text']}", flush=True)
            print(f"    url   : {r['source_url']}", flush=True)
    print(f"\n合计 {total} 份,三字段全中 {ok},失败/部分 {total - ok}(失败如实标注,不猜不填)。",
          flush=True)


if __name__ == "__main__":
    main()
