"""淘沙 · PAP 构造与校验(切片1)。

红线(spec §2⑤ / CLAUDE.md):LLM 只做"想法→PAP 草稿翻译",不发明事件定义、不选参数终值。
本模块只**结构化承载人冻结的 PAP 原文**并做完整性校验;所有数值/定义均转录自
spec v0.2 冻结版 §6,一个数不改。pap_json 一旦经 ledger 冻结即不可变(触发器焊死)。

pap_json 必备键(spec §4 注:事件定义/窗口/池/基准/成本/holdout/清洗/数据快照批次要求):
  event_def, window, pool, benchmark, cost, holdout, cleaning, snapshot_batch_req
"""
from __future__ import annotations

import re

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


def parse_test_windows(pap: dict) -> tuple[int, ...]:
    """从 pap['window'] 文本读**检验窗**日数(事件窗属事件定义,台账为唯一事实源;
    人裁 2026-07-07:检验窗从 pap 读、不在 frozen_ashare 复制)。

    window 文本形如 'T+1起,后20/60日' → 返回检验窗日数元组 (20, 60);
    语义: 后 N 日 = T+1..T+N = τ=0..N-1 = **N 个 τ 点**(τ=0:=T+1,S2-DEC3 锚对所有窗有效)。
    多窗按文本顺序、须升序(短→长,如 #4=20/60、#3=5/20/60)。runner 取首=主检验窗、末=稳健检验窗。
    锚词 '后' 或 '事件版'(两种冻结文本格式,忠实读原文非改口径,人裁 2026-07-09):
      #4='…后20/60日'、#2b(exp3)='事件版20/60日;策略版按离场'——两者 '20/60日' 语义同
      (τ=0..19/τ=0..59),仅表述不同;'事件版' 锚只取事件版窗数、不吞后续 '策略版按离场'
      (无数字不匹配)。#4/合成的 '后X/Y日' 逐字节照旧解析(约束③不破)。
    红线:解析失败即 raise(不静默默认,骗不了人)——检验窗错则全部统计错。"""
    w = pap.get("window", "")
    m = re.search(r"(?:后|事件版)\s*([\d/]+)\s*日", w)
    if not m:
        raise ValueError(f"pap.window 无法解析检验窗(期望含 '后X/Y日' 或 '事件版X/Y日'): {w!r}")
    days = tuple(int(x) for x in m.group(1).split("/") if x)
    if len(days) < 2:
        raise ValueError(f"pap.window 检验窗须≥2(主+稳健): {w!r} → {days}")
    if list(days) != sorted(days) or days[0] <= 0:
        raise ValueError(f"pap.window 检验窗须正、升序(短→长): {days}")
    return days


if __name__ == "__main__":
    # 检验窗解析固定回归(人裁 2026-07-09 要件③④):两种冻结文本格式同 τ 轴,#4/合成 '后' 零回归。
    # ② '策略版按离场' 半句不被吃(无数字不匹配)、不 raise → 策略版检验窗归附录B路径模拟域(步③消费)。
    assert parse_test_windows({"window": "事件版20/60日;策略版按离场"}) == (20, 60), "exp3(#2b)原文串"
    assert parse_test_windows({"window": "T+1起,后20/60日"}) == (20, 60), "#4 '后' 格式零回归"
    assert parse_test_windows({"window": "T+1起,后3/6日"}) == (3, 6), "合成 '后3/6日' 零回归"
    assert parse_test_windows({"window": "后5/20/60日"}) == (5, 20, 60), "三窗 '后' 格式"
    # 解析失败即 raise(不静默):无锚词 / 单窗 / 非升序
    for bad in ("20/60日", "事件版20日", "事件版60/20日"):
        try:
            parse_test_windows({"window": bad})
            raise SystemExit(f"应 raise 未 raise: {bad!r}")
        except ValueError:
            pass
    print("pap.parse_test_windows 自检 OK:事件版20/60→(20,60) / #4后格式零回归 / 策略版半句不吞 / "
          "无锚·单窗·非升序均 raise(要件③④)")
