"""淘沙 · compute · #2b 策略版单事件持有路径模拟(附录 B B1 + P1-P5;exp_id 3)。

附录 B B1(冻结):#2 策略版 = **单事件持有路径模拟**——每个进场事件独立模拟一条持仓路径,
按冻结离场规则(**成本价−20% 强平 或 收盘破 20 日线,先到先出**)逐日推进至离场,记路径净收益
(成本全额扣减);各事件路径相互独立(无组合/无资金约束/无仓位重叠/无再平衡),输出=事件级净收益分布。

离场操作化 5 空白点(人 2026-07-10 裁定,原文即口径,STATE〈#2b 步③施工令〉):
  · P1 收盘确认:当日后复权 close ≤ 成本×0.8 才触发强平;破 20 日线亦"收盘破"(close<ma20);
    逐 present-bar 收盘检两条件(与信号侧 ma20 同口径,MA_LONG 单一来源)。
  · P2 同日 tie-break:某收盘日两条离场同时满足 → **−20% 强平优先**(硬止损更早锁定)。
  · P3 顺延:离场信号日跌停(卖不掉)/停牌(缺行→天然不在 present 序列)→ 顺延解禁后首个可成交
    present-bar 的 **open** 成交,登记顺延 bar 数诊断。
  · P4 右删失:样本末端仍未离场 → 按末端后复权 close 强制平仓,单列删失诊断(**不设最大持有上限**)。
  · P5 触发日收盘成交(否决"次日开盘"):正常触发日以后复权 **close** 成交。
    ⚠已知口径特征(报告须登记,不藏):P1 收盘确认 + P5 收盘成交 = 同刻口径含轻微前视/乐观
    (用当日收盘信息确认又当日收盘价成交),且与 #4/#2b 进场"后复权 open"不对称。

分层红线:本件在 compute 层,**不 import engine**(净收益用成本乘式由 engine/execution 算);本件只产
路径几何(进/出场 bar 索引·价·原因·顺延·删失)+ 进出场价,成本净收益留 engine 单一来源。
PIT:ma20 仅用评估日及之前 present-bar;进场价/离场价均事实价,无未来信息(除 P1+P5 同刻特征,已登记)。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# 破 20 日线口径 = 信号侧同一冻结常量(单一来源,骗不了人:离场"20 日线"= 信号"MA_LONG")
from taosha.compute.drawdown_signal import MA_LONG

# 附录 B B1 冻结:成本价 −20% 强平 → 强平线 = 成本 × STOP_FRAC
STOP_DROP = 0.20
STOP_FRAC = 1.0 - STOP_DROP  # 0.8


@dataclass(frozen=True)
class HoldingPath:
    """一条单事件持仓路径(几何 + 进出场价;净收益由 engine 用 execution.net_return 算)。

    exit_reason:
      · 'stop_loss'     = 成本×0.8 强平(收盘确认;P2 同日优先)
      · 'break_ma20'    = 收盘破 20 日线
      · 'right_censored'= 全程未触发离场,末端 close 强平(P4)
    right_censored=True 亦可伴 stop_loss/break_ma20:已触发但顺延卖不掉直到末端 → 末端 close 截断(P3→P4)。
    exit_on_close:True=触发日/末端后复权 close 成交(P5/P4);False=顺延后 open 成交(P3)。
    holding_bars=exit_idx−entry_idx(present-bar 口径,与 D2 同轴);postpone_bars=触发→成交 present-bar 数(P3)。
    """
    entry_idx: int
    entry_price: float
    exit_idx: int
    exit_price: float
    exit_reason: str
    exit_on_close: bool
    holding_bars: int
    postpone_bars: int
    right_censored: bool


def _sma(closes: list, i: int, w: int) -> Optional[float]:
    """trailing-w present-bar 均值(含 i);满窗前 None。与信号侧 drawdown_signal._sma 同式(PIT)。"""
    if i < w - 1:
        return None
    return sum(closes[i - w + 1:i + 1]) / w


def _sellable(limit_status: str, close: float, prev_close: Optional[float]) -> bool:
    """某 present-bar 卖出是否可成交。

    · limit_down            → 卖不掉(跌停无买盘)。
    · one_word(一字,方向未分)→ 方向自决(P3 小口径工程裁定,登记):后复权 close < 前一 present-bar close
      = 一字跌停 → 卖不掉;否则(涨向/平)→ 可卖。首 bar 无前值时保守判可卖(无据不阻)。
    · none / limit_up       → 可卖(涨停可卖出,只是买不进)。
    """
    if limit_status == "limit_down":
        return False
    if limit_status == "one_word":
        if prev_close is not None and close < prev_close:
            return False  # 一字跌停:卖不掉
        return True
    return True  # none / limit_up


def simulate_holding_path(
    closes: list,
    opens: list,
    limit_status: list,
    entry_idx: int,
    ma_long: int = MA_LONG,
    stop_frac: float = STOP_FRAC,
) -> Optional[HoldingPath]:
    """给定建仓 bar(τ=0,事件版同源进场已定位的可成交进场日),模拟离场路径。纯函数、PIT。

    closes/opens/limit_status: present-bar 序列(交易日轴升序,close 已过滤 None;与信号侧同轴)。
    entry_idx: 建仓 present-bar 索引(τ=0);进场价 = opens[entry_idx](后复权;事件版进场口径)。
    返回 None:建仓越界 / 建仓价缺(open None/≤0 = 不可建仓,engine 记同源差集)。
    """
    n = len(closes)
    if not (0 <= entry_idx < n):
        return None
    entry_price = opens[entry_idx]
    if entry_price is None or entry_price <= 0:
        return None
    stop_line = entry_price * stop_frac

    # 逐 present-bar 收盘检两条件(自建仓当日收盘起;P1 收盘确认)
    for j in range(entry_idx, n):
        c = closes[j]
        ma20 = _sma(closes, j, ma_long)
        stop = c <= stop_line
        brk = (ma20 is not None) and (c < ma20)
        if not (stop or brk):
            continue
        reason = "stop_loss" if stop else "break_ma20"   # P2:同日两满足 → 强平优先
        # 触发日 j:P5 收盘成交(若可卖);否则 P3 顺延解禁后首个可成交 open
        prev_c = closes[j - 1] if j > 0 else None
        if _sellable(limit_status[j], c, prev_c):
            return HoldingPath(entry_idx, entry_price, j, c, reason,
                               True, j - entry_idx, 0, False)
        # P3 顺延:向后找首个可成交 present-bar,以其 open 成交
        for k in range(j + 1, n):
            ok = opens[k]
            if ok is not None and ok > 0 and _sellable(limit_status[k], closes[k], closes[k - 1]):
                return HoldingPath(entry_idx, entry_price, k, ok, reason,
                                   False, k - entry_idx, k - j, False)
        # 顺延至末端仍卖不掉 → P4 末端 close 截断(触发因保留 + 标删失)
        last = n - 1
        return HoldingPath(entry_idx, entry_price, last, closes[last], reason,
                           True, last - entry_idx, last - j, True)

    # 全程未触发离场 → P4 右删失,末端后复权 close 强制平仓
    last = n - 1
    return HoldingPath(entry_idx, entry_price, last, closes[last], "right_censored",
                       True, last - entry_idx, 0, True)


if __name__ == "__main__":
    NS = ["none"] * 400  # 默认全可成交

    # ── P1/P5 break_ma20:建仓后价缓跌破 20 日线,触发日收盘成交 ──────────────────────
    #   前 30 日横盘 100(ma20=100),建仓于 idx=30(open=100),之后跌到 <ma20 触发破线。
    closes = [100.0] * 30 + [99.0, 98.0, 97.0, 96.0]
    opens = [100.0] * 34
    p = simulate_holding_path(closes, opens, NS[:34], entry_idx=30)
    assert p is not None and p.exit_reason == "break_ma20", p
    assert p.exit_on_close and p.postpone_bars == 0 and not p.right_censored
    assert p.entry_price == 100.0 and p.exit_idx == 30  # 建仓当日收盘 99<ma20≈100 即破
    # 净收益乘式手算对照(engine 用 execution.net_return,同式)
    bf, sf = 0.00125, 0.00225
    exp_net = p.exit_price * (1 - sf) / (p.entry_price * (1 + bf)) - 1.0
    assert exp_net < 0  # 破线离场亏损

    # ── P2 tie-break:同日 close 既≤成本×0.8 又<ma20 → 强平优先 ────────────────────
    #   横盘 100 至 idx=29,建仓 idx=30(open=100,强平线=80),当日暴跌到 79(<80 且 <ma20)。
    c2 = [100.0] * 30 + [79.0]
    o2 = [100.0] * 31
    p2 = simulate_holding_path(c2, o2, NS[:31], entry_idx=30)
    assert p2 is not None and p2.exit_reason == "stop_loss", p2  # 两满足取强平(P2)
    assert p2.exit_price == 79.0 and p2.exit_on_close

    # ── P3 顺延:触发日一字跌停卖不掉 → 顺延次日 open 成交,登记顺延 bar ─────────────
    #   建仓 idx=30(open100);idx=31 收盘 79 触发强平但一字跌停(close<prev)卖不掉;idx=32 可成交。
    c3 = [100.0] * 31 + [79.0, 78.0]
    o3 = [100.0] * 31 + [79.0, 77.5]
    ls3 = ["none"] * 31 + ["one_word", "none"]   # idx31 一字(79<80 跌向→卖不掉)
    p3 = simulate_holding_path(c3, o3, ls3, entry_idx=30)
    assert p3 is not None and p3.exit_reason == "stop_loss", p3
    assert not p3.exit_on_close and p3.postpone_bars == 1, p3
    assert p3.exit_idx == 32 and p3.exit_price == 77.5  # 顺延日 open 成交

    # ── P3 顺延卖不掉到末端 → P4 截断(触发因保留 + right_censored) ───────────────
    c4 = [100.0] * 31 + [79.0, 78.0]
    o4 = [100.0] * 31 + [79.0, 77.5]
    ls4 = ["none"] * 31 + ["limit_down", "limit_down"]  # 触发后连续跌停到末端
    p4 = simulate_holding_path(c4, o4, ls4, entry_idx=30)
    assert p4 is not None and p4.exit_reason == "stop_loss" and p4.right_censored, p4
    assert p4.exit_on_close and p4.exit_idx == 32 and p4.exit_price == 78.0  # 末端 close 截断

    # ── P4 右删失:全程未触发离场,末端 close 平仓 ─────────────────────────────────
    #   建仓后价一直在 ma20 上、不破 80% → 持有到末端。
    c5 = [100.0] * 30 + [100.0, 101.0, 102.0, 103.0]
    o5 = [100.0] * 34
    p5 = simulate_holding_path(c5, o5, NS[:34], entry_idx=30)
    assert p5 is not None and p5.exit_reason == "right_censored" and p5.right_censored, p5
    assert p5.exit_idx == 33 and p5.exit_price == 103.0 and p5.holding_bars == 3

    # ── one_word 方向自决:一字涨停(close>prev)可卖 ───────────────────────────────
    #   触发日破线但一字涨停 → 视为可卖,当日收盘成交(P5)。
    c6 = [100.0] * 30 + [96.0]   # 建仓 open100,idx30 收盘 96<ma20≈99.87 破线
    o6 = [100.0] * 31
    ls6 = ["none"] * 30 + ["one_word"]  # 一字但 96<100(跌向)→ 卖不掉 → 顺延无 bar → 末端截断
    p6 = simulate_holding_path(c6, o6, ls6, entry_idx=30)
    assert p6 is not None and p6.exit_reason == "break_ma20" and p6.right_censored, p6

    # ── 建仓越界 / 建仓价缺 → None ───────────────────────────────────────────────
    assert simulate_holding_path([100.0], [100.0], ["none"], entry_idx=5) is None
    assert simulate_holding_path([100.0, 100.0], [100.0, None], ["none", "none"], entry_idx=1) is None
    assert simulate_holding_path([100.0, 100.0], [100.0, 0.0], ["none", "none"], entry_idx=1) is None

    # ── 建仓即末 bar(holding_bars=0):当日收盘检查 ──────────────────────────────
    c7 = [100.0] * 30 + [70.0]  # 建仓 idx30 当日收盘 70≤80 强平
    o7 = [100.0] * 31
    p7 = simulate_holding_path(c7, o7, NS[:31], entry_idx=30)
    assert p7.exit_reason == "stop_loss" and p7.holding_bars == 0 and p7.exit_idx == 30

    print("holding_path.py 自检 OK:P1收盘确认/P2强平优先/P3顺延open/P3→P4截断/P4右删失/"
          "one_word方向自决/越界价缺→None/建仓即末bar;STOP_FRAC=%.2f MA_LONG=%d" % (STOP_FRAC, MA_LONG))
