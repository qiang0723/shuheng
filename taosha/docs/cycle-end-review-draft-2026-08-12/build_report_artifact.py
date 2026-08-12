import csv
import json
import math
from pathlib import Path


BASE = Path(__file__).resolve().parent
GENERATED_AT = "2026-08-12T08:32:43+08:00"
RESULT_SNAPSHOT = "2026-08-09 22:14:05.537694+08"
STATUS_SNAPSHOT = "2026-08-12 08:32:43+08 read-only ledger + STATE entry 155"


def load_csv(name):
    with (BASE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value, integer=False):
    if value in (None, ""):
        return None
    return int(value) if integer else float(value)


def wilson(successes, total, z=1.959963984540054):
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius


calibration = load_csv("calibration_results.csv")
ledger = load_csv("ledger_snapshot.csv")
gates = load_csv("evidence_bottlenecks.csv")
chain = load_csv("exp22_failure_chain.csv")

for row in calibration:
    for field in ("calibration_order", "exp_id", "family_trial", "n_events", "n_valid", "main_n"):
        row[field] = number(row[field], integer=True)
    for field in ("confidence", "caar", "adj_bmp", "rho_bar", "kish_n_eff", "kp_n_eff", "reject_ratio", "industry_unknown_pct"):
        row[field] = number(row[field])
    actual = "positive" if row["caar"] > 0 else "negative" if row["caar"] < 0 else "zero"
    row["derived_hit"] = actual == row["predicted_direction"]
    row["experiment"] = f'exp{row["exp_id"]} · {row["label"]}'
    row["outcome"] = "命中" if row["derived_hit"] else "未命中"

for row in gates:
    row["exp_id"] = number(row["exp_id"], integer=True)
    row["numerator"] = number(row["numerator"], integer=True)
    row["denominator"] = number(row["denominator"], integer=True)
    row["experiment"] = f'exp{row["exp_id"]} · {row["family"]}'
    row["state_label"] = "失败后停止" if row["gate_state"] == "FAIL" else "跨期暂停"

status_counts = {}
for row in ledger:
    status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
real_done = [row for row in ledger if row["status"] == "done" and row["family"] != "synthetic_smoke"]
real_sig = [row for row in real_done if row["verdict"] == "SIG"]
full_done = [row for row in real_done if row["verdict_power"] == "full"]
full_sig = [row for row in full_done if row["verdict"] == "SIG"]
hits = sum(row["derived_hit"] for row in calibration)
low, high = wilson(hits, len(calibration))

headline = [{
    "formal_real_done": len(real_done),
    "calibrated_count": len(calibration),
    "direction_hit_rate": hits / len(calibration),
    "real_sig_count": len(real_sig),
    "full_sig_rate": len(full_sig) / len(full_done),
    "hard_stops": len(gates),
}]

source = {
    "id": "cycle-end-review-snapshot",
    "label": "阿里云台账与闭卷校准只读快照，连同权威数据闭合与暂停档",
    "path": "taosha/docs/cycle-end-review-draft-2026-08-12/calibration_results.csv",
    "query": {
        "engine": "PostgreSQL + repository evidence",
        "language": "SQL",
        "executed_at": RESULT_SNAPSHOT,
        "sql": (BASE / "extract.sql").read_text(encoding="utf-8"),
        "description": "只读抽取正式结果与台账；停点来自权威数据闭合和暂停档。结果与研发状态分列。",
        "tables_used": ["taosha.experiment"],
        "filters": ["default_transaction_read_only=on", f"result snapshot={RESULT_SNAPSHOT}", f"status snapshot={STATUS_SNAPSHOT}"],
        "metric_definitions": [
            "正式真实done=done且family不等于synthetic_smoke",
            "方向命中=密封方向与主窗CAAR符号一致",
            "四条证据停点各按自身证据合同解释，不横向比较通过率",
        ],
    },
}

card_specs = [
    ("formal-done", "正式真实 done", "formal_real_done", "number", "台账done剔除exp7合成冒烟。"),
    ("calibrated", "方向校准", "calibrated_count", "number", "有密封方向且已开封入册。"),
    ("hit-rate", "方向命中率", "direction_hit_rate", "percent", f"5/12；Wilson 95%={low:.1%}–{high:.1%}。"),
    ("real-sig", "真实 SIG", "real_sig_count", "number", "唯一为exp568，效力仍是llm/prescreen。"),
    ("full-sig", "full SIG率", "full_sig_rate", "percent", "4条真实full研究全部NOT_SIG。"),
    ("hard-stops", "证据停点", "hard_stops", "number", "exp18/21/23失败，exp22跨期暂停。"),
]
cards = [{
    "id": item[0], "description": item[4], "dataset": "headline_metrics", "sourceId": source["id"],
    "metrics": [{"label": item[1], "field": item[2], "format": item[3]}],
} for item in card_specs]

chart = {
    "id": "adj-bmp-by-experiment", "title": "十二条校准实验的主窗 ADJ-BMP",
    "subtitle": "零线与名义±1.96供视觉参考；exp568 trial 2实际临界值为±2.241。",
    "intent": "comparison", "question": "哪条实验越过自身预注册判决门槛？",
    "rationale": "只比较主判决统计量是否越过预注册阈值，不跨实验排名CAAR。",
    "comparisonContext": {"grain": "每个校准实验一行", "unit": "ADJ-BMP", "denominator": "各实验主窗完整样本", "semanticFamily": "预注册主判决统计量"},
    "type": "horizontalBar", "dataset": "calibration_table", "sourceId": source["id"],
    "encodings": {
        "x": {"field": "experiment", "type": "nominal", "aggregate": "none", "label": "实验"},
        "y": {"field": "adj_bmp", "type": "quantitative", "aggregate": "none", "label": "ADJ-BMP"},
        "tooltip": [
            {"field": "outcome", "type": "text", "label": "方向"}, {"field": "verdict", "type": "text", "label": "判决"},
            {"field": "caar", "type": "quantitative", "format": "percent", "label": "CAAR"},
            {"field": "main_n", "type": "quantitative", "format": "number", "label": "主窗N"},
        ],
    },
    "layout": "full", "palette": {"kind": "diverging", "midpoint": 0},
    "referenceLines": [
        {"axis": "y", "value": 0, "label": "0", "color": "neutral", "lineStyle": "solid"},
        {"axis": "y", "value": 1.96, "label": "+1.96", "color": "neutral", "lineStyle": "dashed"},
        {"axis": "y", "value": -1.96, "label": "−1.96", "color": "neutral", "lineStyle": "dashed"},
    ],
    "settings": {"showValues": True, "sort": "none", "categoryLabelPolicy": "wrap"},
    "surface": {"surface": "card", "showControls": False, "viewMode": "both"},
}

tables = [
    {
        "id": "calibration-detail", "title": "十二条方向校准明细", "subtitle": "方向命中由CAAR符号独立重导。",
        "dataset": "calibration_table", "defaultSort": {"field": "calibration_order", "direction": "asc"},
        "density": "dense", "sourceId": source["id"], "layout": "full",
        "columns": [
            {"field": "calibration_order", "label": "序号", "type": "number"}, {"field": "experiment", "label": "实验", "type": "text"},
            {"field": "outcome", "label": "方向", "type": "text"}, {"field": "confidence", "label": "把握度", "format": "percent"},
            {"field": "verdict", "label": "判决", "type": "text"}, {"field": "verdict_power", "label": "效力", "type": "text"},
            {"field": "caar", "label": "主窗CAAR", "format": "percent"}, {"field": "adj_bmp", "label": "ADJ-BMP", "format": "number"},
            {"field": "main_n", "label": "主窗N", "format": "number"},
        ],
    },
    {
        "id": "evidence-gates", "title": "四条公告证据停点", "subtitle": "exp22是路由进度，严禁与三条抽核比率横比。",
        "dataset": "evidence_gates", "density": "dense", "sourceId": source["id"], "layout": "full",
        "columns": [
            {"field": "experiment", "label": "实验", "type": "text"}, {"field": "state_label", "label": "状态", "type": "text"},
            {"field": "display_value", "label": "证据读数", "type": "text"}, {"field": "blocking_fact", "label": "阻塞事实", "type": "text"},
        ],
    },
]

title = "枢衡六周期期末复盘底稿 v1"
blocks = [
    {"id": "title", "type": "markdown", "body": f"# {title}\n\n**DRAFT / NOT-FINAL · 2026-08-12 · UTC+8**"},
    {"id": "executive-summary", "type": "markdown", "sourceId": source["id"], "body": f"""## Executive Summary

- **复盘已经开工，8月25日只做定版。** 当前底稿先完成重算、外审和修订；最终签字前再做一次只读增量核对。
- **研究流水线成熟，alpha证据仍弱。** 15条正式真实done中仅exp568为SIG且仍是`llm/prescreen`；4条真实`full`研究全部NOT_SIG。
- **方向校准尚无稳定优势。** 十二条为5命中/7未命中，命中率{hits/len(calibration):.1%}，Wilson 95%区间{low:.1%}–{high:.1%}。
- **主要瓶颈已转向官方公告证据链。** exp18/21/23在不同联合硬门停止，exp22在v1–v8官方分页集合漂移后跨期暂停；不能靠代理或放宽首次披露规则救样本。
"""},
    {"id": "headline", "type": "metric-strip", "cardIds": [card["id"] for card in cards]},
    {"id": "count-reconciliation", "type": "markdown", "sourceId": source["id"], "body": """## 先把计数口径钉死

旧 STATE 的“判决闭卷14条”是 exp14 完成后未同步递增的滚动叙述，不是第二个研究总体。已外审台账快照可重导为：`done=16`；剔除 exp7 合成冒烟后是**15条正式真实done**；其中12条进入方向校准，exp3/4/5三条早期full研究不在当前校准序列。本稿从此分列三种口径，不再混称。
"""},
    {"id": "portfolio", "type": "markdown", "sourceId": source["id"], "body": """## 组合证据：唯一SIG仍不能升级为荐股

exp568 是唯一真实 `SIG`，但效力是 `llm/prescreen`，且闭卷边界禁止把统计显著升级为可交易结论。其 family trial 2 双侧临界值是 **±2.241**；下图的 ±1.96 只作多数 trial 1 的名义视觉参考。方向命中与统计显著必须分开，`NOT_SIG` 也不能反向改写成“证明没有效应”。
"""},
    {"id": "chart", "type": "chart", "chartId": chart["id"], "layout": "full"},
    {"id": "calibration", "type": "table", "tableId": "calibration-detail", "layout": "full"},
    {"id": "bottleneck", "type": "markdown", "sourceId": source["id"], "body": """## 公司公告类四连停点：fail-closed在不利证据前成立

exp18、exp21、exp23的抽核标准不同，不能仅按比率排优先级；exp22更不是抽核通过率，而是官方分页证据链的合法路由进度。共同结论是：统计内核没有先成为瓶颈，首次披露、金额分离、方案身份、用途分类和官方集合稳定性先撞墙。v1–v8失败件继续保全，不建立v9，除非另有人令改判来源工程。
"""},
    {"id": "gates", "type": "table", "tableId": "evidence-gates", "layout": "full"},
    {"id": "recommendations", "type": "markdown", "body": """## 到8月25日前怎么做

1. 现在完成底稿、可执行notebook、便携HTML和外审，不新增正式研究运行。
2. 8月19–21日消化外审；8月22–24日只修证据、定义和呈现，不事后改实验判决。
3. 8月25日重新做连接级只读增量核对，确认台账、校准和停点没有漂移后签字。
4. 下一周期排产只在签字时裁：优先比较公告证据工程与human/full复验的信息增量，不按施工最省事排序。
"""},
    {"id": "questions", "type": "markdown", "body": """## Further Questions

- 下一周期是否减少相似`llm/prescreen`扩张，转投官方证据合同或human/full复验？
- 四条公告停点中，哪些值得恢复，哪些继续封存？
- 是否把“台账done / 正式真实done / 方向校准”写成永久三层计数规范？
"""},
    {"id": "caveats", "type": "markdown", "sourceId": source["id"], "body": f"""## Caveats and Assumptions

- 结果快照时点：`{RESULT_SNAPSHOT}`；研发状态时点：`{STATUS_SNAPSHOT}`。两者独立，未冒充同一最新时点。
- exp22的51/646是route progress，不是抽核pass rate，严禁与12/22、1/23、15/28横比。
- 本稿不输出个股候选，不恢复任何冻结、运行或persist授权。
- 本稿是DRAFT / NOT-FINAL；2026-08-25最终签字前必须刷新只读快照。
"""},
]

artifact = {
    "surface": "report",
    "manifest": {"version": 1, "surface": "report", "title": title, "description": "六周期研究组合、校准与证据瓶颈期末复盘底稿。", "generatedAt": GENERATED_AT, "cards": cards, "charts": [chart], "tables": tables, "sources": [source], "blocks": blocks},
    "snapshot": {"version": 1, "generatedAt": GENERATED_AT, "status": "partial", "datasets": {"headline_metrics": headline, "calibration_table": calibration, "ledger_snapshot": ledger, "evidence_gates": gates, "exp22_failure_chain": chain}},
    "sources": [source],
}

(BASE / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(BASE / "artifact.json")
