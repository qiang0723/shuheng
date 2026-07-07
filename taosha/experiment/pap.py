"""淘沙 · PAP 构造与校验(切片1)。

红线(spec §2⑤ / CLAUDE.md):LLM 只做"想法→PAP 草稿翻译",不发明事件定义、不选参数终值。
本模块只**结构化承载人冻结的 PAP 原文**并做完整性校验;所有数值/定义均转录自
spec v0.2 冻结版 §6,一个数不改。pap_json 一旦经 ledger 冻结即不可变(触发器焊死)。

pap_json 必备键(spec §4 注:事件定义/窗口/池/基准/成本/holdout/清洗/数据快照批次要求):
  event_def, window, pool, benchmark, cost, holdout, cleaning, snapshot_batch_req
"""
from __future__ import annotations

# ── §6 通用(冻结,人批 2026-07-05)── 转录,不改 ────────────────────────────────
FROZEN_COST = {
    "commission": 0.00025,          # 佣金 万2.5
    "stamp_tax_sell": 0.001,        # 卖出印花税 千1
    "slippage_oneway": 0.001,       # 滑点 单边千1
    "limit_up_board_untradeable": True,   # 一字板日不可成交
}
FROZEN_BENCHMARK = {
    "pool_hypothesis": "雷达股池等权",      # 池内假设
    "market_hypothesis": "全市场等权",      # 全市场假设
}
HOLDOUT_START = "2024-07-01"       # 动用须人批,每假设一次
SAMPLE_GATE = 30                    # 样本量闸;<30 → INSUFFICIENT(合法终态)

REQUIRED_KEYS = (
    "event_def", "window", "pool", "benchmark",
    "cost", "holdout", "cleaning", "snapshot_batch_req",
)

VALID_SOURCE_TYPES = ("human", "platform", "literature", "llm")
VALID_VERDICT_POWER = ("full", "prescreen")


def build_pap(*, event_def, window, pool, cleaning, snapshot_batch_req,
              benchmark=None, cost=None, holdout=None, extra=None) -> dict:
    """组装 pap_json:通用件(成本/基准/holdout/闸)默认取 §6 冻结常量,
    调用方只传假设特有的 event_def/window/pool/cleaning/snapshot_batch_req。
    extra=假设特有附加键(如 layers/exit_rule),原样并入。"""
    pap = {
        "event_def": event_def,
        "window": window,
        "pool": pool,
        "benchmark": benchmark if benchmark is not None else dict(FROZEN_BENCHMARK),
        "cost": cost if cost is not None else dict(FROZEN_COST),
        "holdout": holdout if holdout is not None else {"holdout_start": HOLDOUT_START,
                                                        "use_requires_human_approval": True,
                                                        "once_per_hypothesis": True},
        "cleaning": cleaning,
        "snapshot_batch_req": snapshot_batch_req,
        "sample_gate": SAMPLE_GATE,
    }
    if extra:
        pap.update(extra)
    validate_pap(pap)
    return pap


def validate_pap(pap: dict) -> None:
    """完整性校验:必备键齐全、非空。不校验语义(语义是人冻结的,不由代码评判)。"""
    if not isinstance(pap, dict):
        raise ValueError("pap 必须是 dict")
    missing = [k for k in REQUIRED_KEYS if k not in pap or pap[k] in (None, "", {})]
    if missing:
        raise ValueError(f"pap_json 缺必备键或为空: {missing}")
