"""淘沙 · A股市场微结构冻结常量(切片2 item 7/8/10)。

与 frozen_config(四统计口径)分家:那是**统计判断口径**,这是**A股市场制度事实**
(涨跌停限幅、创业板 regime 日期、事件窗几何、停牌告警阈值)。二者均为冻结配置、
运行时不可覆写(item 10),各自带 audit_digest;引擎只读取。

事件窗 τ 轴(S2-DEC3,人拍 2026-07-07):τ=0 := 首个可交易日 = T+1(事件日 T 盘后
披露→前视规避→观测自 T+1)。主窗 [0,+2]=T+1..T+3、稳健窗 [0,+5]=T+1..T+6。

涨跌停 regime(市场制度事实):
  - 主板(main):±10%(始终)。
  - 创业板(chinext):2020-08-24 前 ±10%,当日起 ±20%(注册制改革)。
  - 科创板(star):±20%(2019-07-22 开板起;上市前5日不设限,此简化不建模,合成域无关)。
  - ST/*ST:±5%。
一字板(one_word)= 开盘即封死于涨/跌停价、全日无有效成交 → 不可成交、事件窗顺延(spec §5)。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from types import MappingProxyType

# 样本量闸单一真源(不复制):见 experiment.gates.SAMPLE_GATE / pap.SAMPLE_GATE
from taosha.experiment.gates import SAMPLE_GATE

# ── 创业板涨跌幅 regime 边界(item 8)───────────────────────────────────────────
CHINEXT_REGIME_DATE = dt.date(2020, 8, 24)   # 当日起创业板 ±10%→±20%

# ── 各板/态涨跌停限幅(小数)──────────────────────────────────────────────────
LIMIT_MAIN = 0.10
LIMIT_CHINEXT_PRE = 0.10          # 2020-08-24 前
LIMIT_CHINEXT_POST = 0.20         # 2020-08-24 起
LIMIT_STAR = 0.20
LIMIT_ST = 0.05

# ── 事件窗几何(τ 轴,S2-DEC3;τ=0=T+1)────────────────────────────────────────
#   (start_tau, end_tau) 含端点;逐日 AR 覆盖 τ=start..end。
EVENT_WINDOW_MAIN = (0, 2)        # [0,+2] 主窗 = T+1..T+3
EVENT_WINDOW_ROBUST = (0, 5)      # [0,+5] 稳健窗 = T+1..T+6

# ── 停牌剔除告警阈值(item 7)──────────────────────────────────────────────────
SUSPENSION_ALERT_RATIO = 0.05     # 事件落停牌期剔除率 >5% → 告警

# 板块值域(与 reader.contract.BOARDS 对齐,单列此以供限幅查表)
_BOARDS = ("main", "chinext", "star", "bse")


def price_limit(board: str, trade_date: dt.date, is_st: bool) -> float:
    """按板块 + 交易日 + ST 态取涨跌停限幅(小数)。含 2020-08-24 创业板 regime 边界。

    ST 优先(ST 股无论主板/创业板一律 ±5%)。北交所(bse)按 ±30%,合成域少见,给值兜底。
    """
    if board not in _BOARDS:
        raise ValueError(f"board 非法: {board!r}")
    if is_st:
        return LIMIT_ST
    if board == "main":
        return LIMIT_MAIN
    if board == "chinext":
        return LIMIT_CHINEXT_PRE if trade_date < CHINEXT_REGIME_DATE else LIMIT_CHINEXT_POST
    if board == "star":
        return LIMIT_STAR
    return 0.30  # bse 北交所


def regime_segment(trade_date: dt.date) -> str:
    """创业板 regime 分段归属(item 8 边界处理):'pre_10pct'(前 ±10%)/'post_20pct'(后 ±20%)。"""
    return "pre_10pct" if trade_date < CHINEXT_REGIME_DATE else "post_20pct"


# ── 冻结只读视图(item 10:运行时不可覆写)─────────────────────────────────────
FROZEN = MappingProxyType({
    "chinext_regime_date": CHINEXT_REGIME_DATE.isoformat(),
    "price_limits": MappingProxyType({
        "main": LIMIT_MAIN,
        "chinext_pre_2020_08_24": LIMIT_CHINEXT_PRE,
        "chinext_post_2020_08_24": LIMIT_CHINEXT_POST,
        "star": LIMIT_STAR,
        "st": LIMIT_ST,
    }),
    "event_windows": MappingProxyType({
        "main": EVENT_WINDOW_MAIN,
        "robust": EVENT_WINDOW_ROBUST,
        "tau_axis": "τ=0:=首个可交易日=T+1(S2-DEC3);主窗T+1..T+3,稳健窗T+1..T+6",
    }),
    "suspension_alert_ratio": SUSPENSION_ALERT_RATIO,
    "sample_gate": SAMPLE_GATE,
    "sealed_by": "A股市场制度事实;冻结配置·运行时不可覆写(item 10)",
})


def _canonical(obj):
    if isinstance(obj, (MappingProxyType, dict)):
        return {k: _canonical(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonical(v) for v in obj]
    return obj


def audit_digest() -> str:
    """A股微结构冻结常量的稳定 sha256(item 10:参数变更走审计留痕)。"""
    payload = json.dumps(_canonical(FROZEN), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(_canonical(FROZEN), ensure_ascii=False, indent=2))
    print("audit_digest =", audit_digest())
    # 自检:regime 边界
    assert price_limit("chinext", dt.date(2020, 8, 23), False) == 0.10
    assert price_limit("chinext", dt.date(2020, 8, 24), False) == 0.20
    assert price_limit("main", dt.date(2021, 1, 1), False) == 0.10
    assert price_limit("chinext", dt.date(2021, 1, 1), True) == 0.05   # ST 优先
    assert regime_segment(dt.date(2020, 8, 24)) == "post_20pct"
    assert regime_segment(dt.date(2020, 8, 23)) == "pre_10pct"
    # 只读校验
    try:
        FROZEN["suspension_alert_ratio"] = 0.1
    except TypeError as e:
        print("只读校验 OK:", e)
    print("frozen_ashare.py 自检 OK:regime 边界 / ST 优先 / 只读")
