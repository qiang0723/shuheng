"""淘沙 · compute · #2b 策略版单事件持有路径模拟(附录 B B1 + 附录 G;exp_id 3)。

附录 B B1(冻结):#2 策略版 = **单事件持有路径模拟**——每个进场事件独立模拟一条持仓路径,
按冻结离场规则(**成本价−20% 强平 或 收盘破 20 日线,先到先出**)逐日推进至离场,记路径净收益
(成本全额扣减);各事件路径相互独立(无组合/无资金约束/无仓位重叠/无再平衡),输出=事件级净收益分布。

离场操作化 = **附录 G(人批冻结 2026-07-10,taosha/docs/taosha-spec-appendix-G.md,原文即口径)**:
  · G1(P1) 收盘确认:当日后复权 close ≤ 成本×0.8 才触发强平;破 20 日线亦"收盘破"(close<ma20);
    逐 present-bar 收盘检两条件(与信号侧 ma20 同口径,MA_LONG 单一来源)。登记:盘中硬止损频率被低估,
    对策略版收益方向保守。
  · G2(P2) 同日双触发 tie-break:离场日与成交价相同,**双 flag 均记账**(trigger_stop/trigger_ma20),
    主因(exit_reason)归强平;仅归因标签,不影响数值。
  · G4(P3) 顺延:离场信号日跌停(卖不掉)/停牌(缺行→天然不在 present 序列)→ 顺延至下一可成交
    present-bar,按该**顺延日收盘价**出(收盘,非 open——顺延日跳空为真实成本,如实吃进);顺延期间
    亏损如实计入。**上限条款**:顺延 >20 **交易日**仍不可卖 → 按可卖首日收盘出 + 极端案例单列标注
    (postpone_extreme),不静默。⚠交易日口径实现注记:停牌=缺行,present-bar 差会低估停牌顺延天数,
    故顺延天数按 `trade_day_idx`(各 bar 的日历交易日序号,engine 从 calendar 传入)计;未提供时退化
    为 present-bar 差(仅无缺行时等价)。
  · G5(P4) 右删失:样本末端仍未离场 → 末端后复权 close 标记平仓(mark-to-market),right_censored
    单列(open_position 计数/占比/未实现收益注记在 engine 报告层),**不剔除**(剔除=幸存偏差);
    不设最大持有上限。
  · G3(P5) 触发日收盘成交:正常触发日以后复权 **close** 成交。进出场不对称正当性(附录 G3 原文):
    进场信号为"连 3 日收盘确认"之第 3 日,盘后方知、次日才可行动;离场信号触发日收盘即当日可执行
    口径——两者各为其信息可得时点的**最早可执行价**。
  · G6 one_word 方向判定:按 close 对前收判向(追认入档)。
  ~~旧 P3 口径"顺延首个可成交日 open 成交"~~ 作废(附录 G4 改判,2026-07-11 落地)。

分层红线:本件在 compute 层,**不 import engine**(净收益用成本乘式由 engine/execution 算);本件只产
路径几何(进/出场 bar 索引·价·双触发 flag·主因·顺延·极端标注·删失)+ 进出场价,成本净收益留 engine 单一来源。
PIT:ma20 仅用评估日及之前 present-bar;进场价/离场价均事实价,无未来信息(除 P1+P5 同刻特征,附录 G3 登记)。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# 破 20 日线口径 = 信号侧同一冻结常量(单一来源,骗不了人:离场"20 日线"= 信号"MA_LONG")
from taosha.compute.drawdown_signal import MA_LONG

# 附录 B B1 冻结:成本价 −20% 强平 → 强平线 = 成本 × STOP_FRAC
STOP_DROP = 0.20
STOP_FRAC = 1.0 - STOP_DROP  # 0.8
# 附录 G4 上限条款:顺延 >20 交易日仍不可卖 → 极端案例单列标注(不静默)
POSTPONE_EXTREME_DAYS = 20


@dataclass(frozen=True)
class HoldingPath:
    """一条单事件持仓路径(几何 + 进出场价;净收益由 engine 用 execution.net_return 算)。

    exit_reason(主因,G2:双触发归强平):
      · 'stop_loss'     = 成本×0.8 强平(收盘确认)
      · 'break_ma20'    = 收盘破 20 日线
      · 'right_censored'= 全程未触发离场,末端 close 标记平仓(G5 mark-to-market)
    trigger_stop/trigger_ma20 = 触发日两条件各自命中(G2 双 flag 均记账;right_censored 路径双 False)。
    right_censored=True 亦可伴 stop_loss/break_ma20 主因:已触发但顺延卖不掉直到末端 → 末端 close 截断(G4→G5)。
    holding_bars=exit_idx−entry_idx(present-bar 口径,与 D2 同轴);postpone_bars=触发→成交 present-bar 数;
    postpone_days=同段**交易日**数(trade_day_idx 提供时;否则=postpone_bars);
    postpone_extreme=postpone_days>20(G4 上限条款,单列标注不静默)。
    所有成交价均为后复权 close(G3 触发日 / G4 顺延日 / G5 末端)。
    """
    entry_idx: int
    entry_price: float
    exit_idx: int
    exit_price: float
    exit_reason: str
    trigger_stop: bool
    trigger_ma20: bool
    holding_bars: int
    postpone_bars: int
    postpone_days: int
    postpone_extreme: bool
    right_censored: bool


def _sma(closes: list, i: int, w: int) -> Optional[float]:
    """trailing-w present-bar 均值(含 i);满窗前 None。与信号侧 drawdown_signal._sma 同式(PIT)。"""
    if i < w - 1:
        return None
    return sum(closes[i - w + 1:i + 1]) / w


def _sellable(limit_status: str, close: float, prev_close: Optional[float]) -> bool:
    """某 present-bar 卖出是否可成交。

    · limit_down            → 卖不掉(跌停无买盘)。
    · one_word(一字,方向未分)→ G6(追认入档):后复权 close < 前一 present-bar close
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


def _postpone_days(trade_day_idx: Optional[list], k: int, j: int) -> int:
    """触发 bar j → 成交/截断 bar k 的顺延**交易日**数(G4 上限条款口径)。

    trade_day_idx[i] = present-bar i 对应的日历交易日序号(engine 从 calendar 算好传入,单调递增);
    未提供时退化为 present-bar 差(仅无缺行/无停牌时与交易日差等价——G4 主场景含停牌,engine 必传)。
    """
    if trade_day_idx is not None:
        return trade_day_idx[k] - trade_day_idx[j]
    return k - j


def simulate_holding_path(
    closes: list,
    opens: list,
    limit_status: list,
    entry_idx: int,
    ma_long: int = MA_LONG,
    stop_frac: float = STOP_FRAC,
    trade_day_idx: Optional[list] = None,
) -> Optional[HoldingPath]:
    """给定建仓 bar(τ=0,事件版同源进场已定位的可成交进场日),模拟离场路径。纯函数、PIT。

    closes/opens/limit_status: present-bar 序列(交易日轴升序,close 已过滤 None;与信号侧同轴)。
    entry_idx: 建仓 present-bar 索引(τ=0);进场价 = opens[entry_idx](后复权;事件版进场口径)。
    trade_day_idx: 各 present-bar 的日历交易日序号(G4 顺延天数口径;None→退化 bar 差)。
    返回 None:建仓越界 / 建仓价缺(open None/≤0 = 不可建仓,engine 记同源差集)。
    """
    n = len(closes)
    if not (0 <= entry_idx < n):
        return None
    entry_price = opens[entry_idx]
    if entry_price is None or entry_price <= 0:
        return None
    stop_line = entry_price * stop_frac

    # 逐 present-bar 收盘检两条件(自建仓当日收盘起;G1 收盘确认)
    for j in range(entry_idx, n):
        c = closes[j]
        ma20 = _sma(closes, j, ma_long)
        stop = c <= stop_line
        brk = (ma20 is not None) and (c < ma20)
        if not (stop or brk):
            continue
        reason = "stop_loss" if stop else "break_ma20"   # G2:同日双触发 → 主因归强平
        # 触发日 j:G3 收盘成交(若可卖);否则 G4 顺延至下一可成交 bar 按其 close 成交
        prev_c = closes[j - 1] if j > 0 else None
        if _sellable(limit_status[j], c, prev_c):
            return HoldingPath(entry_idx, entry_price, j, c, reason, stop, brk,
                               j - entry_idx, 0, 0, False, False)
        # G4 顺延:向后找首个可成交 present-bar,按该顺延日**收盘价**成交(非 open);
        # >20 交易日仍不可卖 → 仍按可卖首日收盘出,极端案例标注(postpone_extreme)不静默。
        for k in range(j + 1, n):
            if _sellable(limit_status[k], closes[k], closes[k - 1]):
                pd = _postpone_days(trade_day_idx, k, j)
                return HoldingPath(entry_idx, entry_price, k, closes[k], reason, stop, brk,
                                   k - entry_idx, k - j, pd,
                                   pd > POSTPONE_EXTREME_DAYS, False)
        # 顺延至末端仍卖不掉 → G5 末端 close 截断(触发因保留 + 标删失;极端标注同式)
        last = n - 1
        pd = _postpone_days(trade_day_idx, last, j)
        return HoldingPath(entry_idx, entry_price, last, closes[last], reason, stop, brk,
                           last - entry_idx, last - j, pd,
                           pd > POSTPONE_EXTREME_DAYS, True)

    # 全程未触发离场 → G5 右删失,末端后复权 close 标记平仓(mark-to-market,不剔除)
    last = n - 1
    return HoldingPath(entry_idx, entry_price, last, closes[last], "right_censored",
                       False, False, last - entry_idx, 0, 0, False, True)


if __name__ == "__main__":
    NS = ["none"] * 400  # 默认全可成交

    # ── G1/G3 break_ma20:建仓后价缓跌破 20 日线,触发日收盘成交 ──────────────────────
    #   前 30 日横盘 100(ma20=100),建仓于 idx=30(open=100),之后跌到 <ma20 触发破线。
    closes = [100.0] * 30 + [99.0, 98.0, 97.0, 96.0]
    opens = [100.0] * 34
    p = simulate_holding_path(closes, opens, NS[:34], entry_idx=30)
    assert p is not None and p.exit_reason == "break_ma20", p
    assert p.trigger_ma20 and not p.trigger_stop  # 单触发:仅破线
    assert p.postpone_bars == 0 and not p.right_censored and not p.postpone_extreme
    assert p.entry_price == 100.0 and p.exit_idx == 30  # 建仓当日收盘 99<ma20≈100 即破
    # 净收益乘式手算对照(engine 用 execution.net_return,同式)
    bf, sf = 0.00125, 0.00225
    exp_net = p.exit_price * (1 - sf) / (p.entry_price * (1 + bf)) - 1.0
    assert exp_net < 0  # 破线离场亏损

    # ── G8① 双触发:同日 close 既≤成本×0.8 又<ma20 → 双 flag 均记账、主因强平 ────────
    #   横盘 100 至 idx=29,建仓 idx=30(open=100,强平线=80),当日暴跌到 79(<80 且 <ma20)。
    c2 = [100.0] * 30 + [79.0]
    o2 = [100.0] * 31
    p2 = simulate_holding_path(c2, o2, NS[:31], entry_idx=30)
    assert p2 is not None and p2.exit_reason == "stop_loss", p2   # 主因归强平(G2)
    assert p2.trigger_stop and p2.trigger_ma20                    # 双 flag 均记账(G2)
    assert p2.exit_price == 79.0 and p2.exit_idx == 30            # 离场日/价与单触发同式,数值不受归因影响

    # ── G8② G4 顺延:触发日一字跌停卖不掉 → 顺延日**收盘价**出(非 open),登记顺延 ────
    #   建仓 idx=30(open100);idx=31 收盘 79 触发强平但一字跌停(close<prev)卖不掉;idx=32 可成交。
    c3 = [100.0] * 31 + [79.0, 78.0]
    o3 = [100.0] * 31 + [79.0, 77.5]
    ls3 = ["none"] * 31 + ["one_word", "none"]   # idx31 一字(79<80 跌向→卖不掉)
    p3 = simulate_holding_path(c3, o3, ls3, entry_idx=30)
    assert p3 is not None and p3.exit_reason == "stop_loss", p3
    assert p3.postpone_bars == 1 and p3.postpone_days == 1 and not p3.postpone_extreme, p3
    assert p3.exit_idx == 32 and p3.exit_price == 78.0, p3  # G4:顺延日 close 78.0(非 open 77.5)

    # ── G8② 跌停连板 >20 日:21 个 limit_down 后方可卖 → 可卖首日收盘出 + 极端标注 ──
    c8 = [100.0] * 31 + [79.0 - i for i in range(22)]        # idx31 触发,idx32..52 连板,idx53 可卖
    o8 = [100.0] * 31 + [79.0 - i for i in range(22)]
    ls8 = ["none"] * 31 + ["limit_down"] * 22 + ["none"]
    c8, o8 = c8 + [56.0], o8 + [56.5]                        # idx53 可成交 bar(close=56.0)
    p8 = simulate_holding_path(c8, o8, ls8, entry_idx=30)
    assert p8 is not None and p8.exit_reason == "stop_loss" and not p8.right_censored, p8
    assert p8.exit_idx == 53 and p8.exit_price == 56.0, p8   # 可卖首日**收盘**出(非 open 56.5)
    assert p8.postpone_bars == 22 and p8.postpone_days == 22 and p8.postpone_extreme, p8  # >20 → 极端标注

    # ── G8② 停牌顺延交易日口径:present 缺行,trade_day_idx 证 >20 上限按交易日计 ────
    #   idx31 触发跌停卖不掉;idx32 为停牌 25 个交易日后的复牌 bar(present 序列仅隔 1 bar)。
    c9 = [100.0] * 31 + [79.0, 70.0]
    o9 = [100.0] * 31 + [79.0, 69.0]
    ls9 = ["none"] * 31 + ["limit_down", "none"]
    tdi = list(range(32)) + [31 + 25]                         # 复牌 bar 的交易日序号跳 25
    p9 = simulate_holding_path(c9, o9, ls9, entry_idx=30, trade_day_idx=tdi)
    assert p9 is not None and p9.exit_idx == 32 and p9.exit_price == 70.0, p9  # 复牌日 close 出
    assert p9.postpone_bars == 1 and p9.postpone_days == 25 and p9.postpone_extreme, p9  # 交易日口径触上限

    # ── G4→G5 顺延卖不掉到末端 → 截断(触发因保留 + right_censored) ────────────────
    c4 = [100.0] * 31 + [79.0, 78.0]
    o4 = [100.0] * 31 + [79.0, 77.5]
    ls4 = ["none"] * 31 + ["limit_down", "limit_down"]  # 触发后连续跌停到末端
    p4 = simulate_holding_path(c4, o4, ls4, entry_idx=30)
    assert p4 is not None and p4.exit_reason == "stop_loss" and p4.right_censored, p4
    assert p4.exit_idx == 32 and p4.exit_price == 78.0  # 末端 close 截断

    # ── G8③ G5 右删失 mark-to-market:全程未触发离场,末端 close 标记平仓、不剔除 ────
    #   建仓后价一直在 ma20 上、不破 80% → 持有到末端(open_position;计数/占比在 engine 报告层)。
    c5 = [100.0] * 30 + [100.0, 101.0, 102.0, 103.0]
    o5 = [100.0] * 34
    p5 = simulate_holding_path(c5, o5, NS[:34], entry_idx=30)
    assert p5 is not None and p5.exit_reason == "right_censored" and p5.right_censored, p5
    assert not p5.trigger_stop and not p5.trigger_ma20            # 未触发任一离场
    assert p5.exit_idx == 33 and p5.exit_price == 103.0 and p5.holding_bars == 3

    # ── G6 one_word 方向自决:一字跌向卖不掉 → 顺延无 bar → 末端截断 ────────────────
    c6 = [100.0] * 30 + [96.0]   # 建仓 open100,idx30 收盘 96<ma20≈99.87 破线
    o6 = [100.0] * 31
    ls6 = ["none"] * 30 + ["one_word"]  # 一字且 96<100(跌向)→ 卖不掉
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

    print("holding_path.py 自检 OK(附录G):G1收盘确认/G2双flag主因强平/G3触发日close/"
          "G4顺延日close+>20交易日极端标注(bar口径+停牌trade_day_idx口径)/G4→G5截断/G5末端mark-to-market/"
          "G6 one_word判向/越界价缺→None/建仓即末bar;STOP_FRAC=%.2f MA_LONG=%d POSTPONE_EXTREME_DAYS=%d"
          % (STOP_FRAC, MA_LONG, POSTPONE_EXTREME_DAYS))
