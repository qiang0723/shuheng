import csv
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
GENERATED_AT = "2026-07-31T10:57:18+08:00"


def load_csv(name):
    with (BASE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value, integer=False):
    if value in (None, ""):
        return None
    return int(value) if integer else float(value)


calibration = load_csv("calibration_results.csv")
ledger = load_csv("ledger_snapshot.csv")

for row in calibration:
    row["calibration_order"] = number(row["calibration_order"], integer=True)
    row["exp_id"] = number(row["exp_id"], integer=True)
    row["family_trial"] = number(row["family_trial"], integer=True)
    row["confidence"] = number(row["confidence"])
    row["direction_hit"] = row["direction_hit"] == "true"
    for field in ("n_events", "n_valid", "main_n"):
        row[field] = number(row[field], integer=True)
    for field in (
        "caar",
        "adj_bmp",
        "rho_bar",
        "kish_n_eff",
        "kp_n_eff",
        "reject_ratio",
        "industry_unknown_pct",
    ):
        row[field] = number(row[field])
    row["experiment"] = f'exp{row["exp_id"]} · {row["label"]}'
    row["outcome"] = "命中" if row["direction_hit"] else "未命中"
    row["caar_pct"] = row["caar"]

status_counts = {}
for row in ledger:
    status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

real_done = [row for row in ledger if row["status"] == "done" and row["family"] != "synthetic_smoke"]
real_sig = [row for row in real_done if row["verdict"] == "SIG"]
full_done = [row for row in real_done if row["verdict_power"] == "full"]
full_sig = [row for row in full_done if row["verdict"] == "SIG"]

headline = [{
    "calibrated_count": len(calibration),
    "direction_hit_rate": sum(row["direction_hit"] for row in calibration) / len(calibration),
    "real_sig_rate": len(real_sig) / len(real_done),
    "full_sig_rate": len(full_sig) / len(full_done),
    "registered_count": status_counts["registered"],
}]

source = {
    "id": "stage-review-snapshot",
    "label": "阿里云 experiment 台账与十条闭卷校准档（只读快照）",
    "path": "taosha/docs/stage-review-10-experiments-2026-07-31/calibration_results.csv",
    "query": {
        "engine": "PostgreSQL",
        "language": "SQL",
        "executed_at": GENERATED_AT,
        "sql": (BASE / "result_extract.sql").read_text(encoding="utf-8"),
        "description": "读取十条校准实验的正式 result_json 统计量，并核对 experiment 状态分布。方向命中来自各 persist/闭卷档。",
        "tables_used": ["taosha.experiment"],
        "filters": [
            "exp_id IN (8,10,11,12,13,16,17,20,24,568)",
            "数据库会话 default_transaction_read_only=on",
            "as of 2026-07-31 UTC+8",
        ],
        "metric_definitions": [
            "方向命中率=预判方向与主窗CAAR符号一致的实验数/10",
            "真实研究SIG率=剔除synthetic_smoke后的done且SIG实验数/真实done实验数",
            "full SIG率=真实done且verdict_power=full且SIG实验数/full真实done实验数",
        ],
    },
}

cards = [
    {
        "id": "calibrated-count",
        "description": "进入密封开封校准册的正式实验数。",
        "dataset": "headline_metrics",
        "sourceId": source["id"],
        "metrics": [{"label": "校准读数", "field": "calibrated_count", "format": "number"}],
    },
    {
        "id": "direction-hit-rate",
        "description": "只看方向符号，不代表显著或可交易。",
        "dataset": "headline_metrics",
        "sourceId": source["id"],
        "metrics": [{"label": "方向命中率", "field": "direction_hit_rate", "format": "percent"}],
    },
    {
        "id": "real-sig-rate",
        "description": "13条真实done研究中仅exp568为SIG。",
        "dataset": "headline_metrics",
        "sourceId": source["id"],
        "metrics": [{"label": "真实研究SIG率", "field": "real_sig_rate", "format": "percent"}],
    },
    {
        "id": "full-sig-rate",
        "description": "4条真实full效力研究全部NOT_SIG。",
        "dataset": "headline_metrics",
        "sourceId": source["id"],
        "metrics": [{"label": "full研究SIG率", "field": "full_sig_rate", "format": "percent"}],
    },
    {
        "id": "registered-count",
        "description": "当前台账registered数量；其中7条llm/prescreen、1条human/full。",
        "dataset": "headline_metrics",
        "sourceId": source["id"],
        "metrics": [{"label": "待排产", "field": "registered_count", "format": "number"}],
    },
]

charts = [
    {
        "id": "adj-bmp-by-experiment",
        "title": "十条校准实验的主窗 ADJ-BMP",
        "subtitle": "多数trial 1以±1.96为参考；exp568使用family trial 2阈值±2.241，仍为唯一SIG。",
        "intent": "comparison",
        "question": "十条实验中，哪一条越过预注册显著性门槛？",
        "rationale": "标准化判决统计量可在不同事件定义间比较是否越过各自门槛；CAAR绝对值不作跨实验排名。",
        "comparisonContext": {
            "grain": "每个校准实验一行",
            "unit": "ADJ-BMP z统计量",
            "denominator": "各实验主窗完整样本",
            "semanticFamily": "预注册主判决统计量",
        },
        "type": "horizontalBar",
        "dataset": "calibration_table",
        "sourceId": source["id"],
        "encodings": {
            "x": {"field": "experiment", "type": "nominal", "aggregate": "none", "label": "实验"},
            "y": {"field": "adj_bmp", "type": "quantitative", "aggregate": "none", "label": "ADJ-BMP"},
            "tooltip": [
                {"field": "outcome", "type": "text", "label": "方向"},
                {"field": "verdict", "type": "text", "label": "判决"},
                {"field": "caar", "type": "quantitative", "format": "percent", "label": "主窗CAAR"},
                {"field": "main_n", "type": "quantitative", "format": "number", "label": "主窗N"},
                {"field": "verdict_power", "type": "text", "label": "效力"},
            ],
        },
        "layout": "full",
        "palette": {"kind": "diverging", "midpoint": 0},
        "referenceLines": [
            {"axis": "y", "value": 0, "label": "0", "color": "neutral", "lineStyle": "solid"},
            {"axis": "y", "value": 1.96, "label": "+1.96", "color": "neutral", "lineStyle": "dashed"},
            {"axis": "y", "value": -1.96, "label": "−1.96", "color": "neutral", "lineStyle": "dashed"},
        ],
        "settings": {"showValues": True, "sort": "none", "categoryLabelPolicy": "wrap"},
        "surface": {"surface": "card", "showControls": False, "viewMode": "both"},
    }
]

tables = [
    {
        "id": "calibration-detail",
        "title": "十条校准明细",
        "subtitle": "精确值来自库内正式result；方向命中来自闭卷校准册。",
        "dataset": "calibration_table",
        "defaultSort": {"field": "calibration_order", "direction": "asc"},
        "density": "dense",
        "sourceId": source["id"],
        "layout": "full",
        "columns": [
            {"field": "calibration_order", "label": "序号", "type": "number"},
            {"field": "experiment", "label": "实验", "type": "text"},
            {"field": "outcome", "label": "方向", "type": "text"},
            {"field": "confidence", "label": "把握度", "format": "percent"},
            {"field": "verdict", "label": "判决", "type": "text"},
            {"field": "verdict_power", "label": "效力", "type": "text"},
            {"field": "caar", "label": "主窗CAAR", "format": "percent"},
            {"field": "adj_bmp", "label": "ADJ-BMP", "format": "number"},
            {"field": "main_n", "label": "主窗N", "format": "number"},
            {"field": "kish_n_eff", "label": "Kish N_eff", "format": "number"},
            {"field": "reject_ratio", "label": "剔除率", "format": "percent"},
        ],
    }
]

title = "枢衡十条实验阶段复盘"
blocks = [
    {"id": "title", "type": "markdown", "body": f"# {title}"},
    {
        "id": "executive-summary",
        "type": "markdown",
        "sourceId": source["id"],
        "body": """## Executive Summary

- **先不启动第11条实验。** 十条校准方向正好5命中/5未命中；50%命中率的95% Wilson区间约为23.7%–76.3%，样本仍小，不能证明方向判断优于随机。
- **工程流水线已成熟，alpha证据尚未建立。** 台账已有14条done，但剔除synthetic smoke后13条真实研究仅1条SIG；该SIG是exp568 `llm/prescreen`，4条真实`full`研究全部NOT_SIG。
- **下一瓶颈在上游假设供给。** 今天完成复盘并停排产；8月3日先核“分析师预期”时间戳语义并重排候选池，8月4日检查点再决定是否给exp18开只读窄闸。
""",
    },
    {
        "id": "headline-metrics",
        "type": "metric-strip",
        "cardIds": [card["id"] for card in cards],
    },
    {
        "id": "finding-alpha",
        "type": "markdown",
        "sourceId": source["id"],
        "body": """## 研究生产率已达标，alpha生产率未达标

过去两周完成了十条带密封方向的正式校准，已明显超过六周期3–5条的吞吐目标。问题不再是“能不能跑”，而是“跑出的题是否值得跑”。

唯一真实SIG来自exp568实施ST风险警示：主窗CAAR为−15.93%，ADJ-BMP为−5.523；但它仍是`llm/prescreen`，并含一字跌停不可成交边界。正确动作是把它作为未来human/full复验候选，不能升级解释为已发现可交易alpha。
""",
    },
    {"id": "adj-bmp-chart-block", "type": "chart", "chartId": "adj-bmp-by-experiment", "layout": "full"},
    {
        "id": "finding-calibration",
        "type": "markdown",
        "sourceId": source["id"],
        "body": """## 方向校准停在五五开，高把握度也未形成证据

十条方向命中5条、未命中5条。把握度只是密封前主观概率，不是研究判决；当前样本不足以做细分校准，也不支持根据某一两条命中提高后续置信度。

更重要的是，方向命中与统计成立必须分开：命中的exp8、exp12、exp24、exp17均为NOT_SIG，只有exp568同时命中方向且SIG。
""",
    },
    {"id": "calibration-table-block", "type": "table", "tableId": "calibration-detail", "layout": "full"},
    {
        "id": "recommendations",
        "type": "markdown",
        "body": """## 现在应停一拍，不是停项目

1. **暂停连续排产一个工作日。** 不对第11条假设做PAP、冻结或正式运行。
2. **先修上游，不动统计内核。** 完成分析师预期类的时间戳口径核查；口径不明就不登记新题。
3. **重排剩余8条registered。** 优先级按“信息增量、数据现成度、判决形态现成度、是否full”排序，不按施工最省事排序。
4. **下一条只开窄闸。** 若上游核查通过，建议先对exp18 `audit_qualified`做只读准确性窄闸；不直接冻结。
5. **exp25继续封存。** 既有行业PIT/行业收益基准与组间差能力缺口不在本轮建设；除非8月4日排序会明确提升其优先级。
""",
    },
    {
        "id": "schedule",
        "type": "markdown",
        "body": """## 下一步排期（UTC+8）

- **7月31日（周五）**：完成本阶段复盘、冻结排产队列；不启动新研究。
- **8月1–2日（周末）**：研究主线休息；Web侧线保持独立，不与枢衡混线。
- **8月3日（周一）**：半天完成分析师预期时间戳窄闸，半天完成8条registered排序。
- **8月4日（周二，第21天检查点）**：人拍下一条；默认候选是exp18只读窄闸，不是正式运行。
""",
    },
    {
        "id": "further-questions",
        "type": "markdown",
        "body": """## Further Questions

- 下一阶段的首要目标，是增加`human/full`证据，还是继续用`llm/prescreen`扩展机制覆盖？
- exp568是否值得另立一条human/full复验，且把可成交性作为新假设边界，而不是事后改写原实验？
- 若分析师预期时间戳不能证明为研报真实发布时点，是否暂停该类轮巡而转向公司公告类题源？
""",
    },
    {
        "id": "caveats",
        "type": "markdown",
        "sourceId": source["id"],
        "body": """## Caveats and Assumptions

- 十条校准样本很小，方向命中率区间很宽；本报告不做能力显著性检验或事后分组。
- 各实验事件定义、signed语义、样本与执行限制不同；只比较预注册判决与方向，不跨实验排名CAAR。
- `SIG`不等于可交易；exp568尤其受一字跌停锁死bar与`prescreen`效力约束。
- Fable尚未对exp568 persist与exp16 v2 persist做独立终签复核；本报告的数值来自阿里云库内正式result与闭卷档直接只读，现阶段可用于排产，但该复核欠账应在8月4日检查点前清掉。
""",
    },
]

artifact = {
    "surface": "report",
    "manifest": {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": "截至2026-07-31 UTC+8的十条校准实验阶段复盘与下一阶段排产建议。",
        "generatedAt": GENERATED_AT,
        "cards": cards,
        "charts": charts,
        "tables": tables,
        "sources": [source],
        "blocks": blocks,
    },
    "snapshot": {
        "version": 1,
        "generatedAt": GENERATED_AT,
        "status": "ready",
        "datasets": {
            "headline_metrics": headline,
            "calibration_table": calibration,
            "ledger_snapshot": ledger,
        },
    },
    "sources": [source],
}

(BASE / "artifact.json").write_text(
    json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(BASE / "artifact.json")
