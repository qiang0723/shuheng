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
  · G3(P5) 触发日收盘成交:正常触发日以后复权 **close** 成交。⚠已采纳定性(addendum_id=1,
    人批;修法#1 措辞统一 2026-07-13):P1 收盘确认+P5 同刻收盘成交=**冻结口径下的不可执行
    诊断值,存在同刻成交前视与倾向乐观的偏置,不构成真实可交易表现证据**;与进场"τ=0 后复权
    open"不对称。~~"各为其信息可得时点的最早可执行价"正当化表述~~ 作废(修法#1)。
  · G6 one_word 方向判定:按 close 对前收判向(追认入档)。
  ~~旧 P3 口径"顺延首个可成交日 open 成交"~~ 作废(附录 G4 改判,2026-07-11 落地)。

分层红线:本件在 compute 层,**不 import engine**(净收益用成本乘式由 engine/execution 算);本件只产
路径几何(进/出场 bar 索引·价·双触发 flag·主因·顺延·极端标注·删失)+ 进出场价,成本净收益留 engine 单一来源。
PIT:ma20 仅用评估日及之前 present-bar;进场价/离场价均事实价,无未来信息(除 P1+P5 同刻成交
前视偏置——addendum_id=1 采纳定性,附录 G3 登记)。
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

# ── 窄补第三轮 #1-b(2026-07-13):next_open 可成交判定只消费开盘时点字段 ─────────────
# 值域 = reader.contract.OPEN_LIMIT_STATUS(开盘时点口径,qbase 015 视图列;compute 不 import
# reader,字面值单点声明于此,engine 侧自检交叉断言两处一致)。
OPEN_AT_DOWN_LIMIT = "open_at_down_limit"
# fill_source 值域(#1-a:事件级成交证据字段,直接断言/直接渲染,禁由聚合净收益反推)
FILL_SOURCES = ("same_close", "postponed_close",          # legacy 域(生产不可达)
                "next_open", "postponed_open",            # close_to_next_open 白名单
                "censored_close_mark")                    # G5 末端 close 截断=标记非成交


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
    same_close 域成交价为后复权 close(G3/G4/G5);next_open 域成交价为后复权 open(截断除外)。

    窄补第三轮 #1-a(2026-07-13)成交证据字段(直接断言/直接渲染,禁由聚合净收益反推):
      · trigger_idx  = 收盘确认决策 bar(signal_date 对应索引);从未触发的右删失路径 = None。
      · fill_source  ∈ FILL_SOURCES:exit_price 的来源枚举;'censored_close_mark'=末端 close
        截断(mark-to-market 标记,**非成交**),不得表述为成交。
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
    trigger_idx: Optional[int]
    fill_source: str

    def __post_init__(self):
        if self.fill_source not in FILL_SOURCES:
            raise ValueError(f"fill_source 非法: {self.fill_source!r}(值域={FILL_SOURCES})")


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


def _sellable_at_open(open_limit: Optional[str], open_price: Optional[float]) -> bool:
    """开盘时点可成交(卖出)**日线代理判定**(窄补第三轮 #1-b,冻结代理规则,2026-07-13)。

    只消费开盘时点(集合竞价撮合后)已可得的信息,日终字段(close/limit_status/one_word)
    结构上不进入本判定:
      · R-open-1(opening print 存在):open 有值>0 = 当日市场发生过开盘竞价成交。
      · R-open-2(开盘价不在跌停价位):open_limit != 'open_at_down_limit'(qbase 015 视图
        开盘时点列:原始 open 恰= round(原始前收×(1−limit_pct),2);limit_pct 复用视图既有口径)。
        开盘价恰在跌停位 → 视为卖单堆积按不可成交处理(保守)。
    **能力边界(如实标注,不得夸大)**:两条均为日线代理——市场存在开盘成交/开盘价不在跌停位
    ≠ 我方委托单能排上队成交(排队优先级不可得);本判定是代理规则,非真实委托成交验证。
    """
    if open_price is None or open_price <= 0:
        return False                          # R-open-1 不满足:无 opening print
    return open_limit != OPEN_AT_DOWN_LIMIT   # R-open-2:开盘恰在跌停位 → 保守判不可成交


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
    fill_mode: str = "same_close",
    open_limit_status: Optional[list] = None,
) -> Optional[HoldingPath]:
    """给定建仓 bar(τ=0,事件版同源进场已定位的可成交进场日),模拟离场路径。纯函数、PIT。

    closes/opens/limit_status: present-bar 序列(交易日轴升序,close 已过滤 None;与信号侧同轴)。
    entry_idx: 建仓 present-bar 索引(τ=0);进场价 = opens[entry_idx](后复权;事件版进场口径)。
    trade_day_idx: 各 present-bar 的日历交易日序号(G4 顺延天数口径;None→退化 bar 差)。
    open_limit_status: 各 present-bar 的开盘时点涨跌停位标记(qbase 015 视图列,值域=
      reader.contract.OPEN_LIMIT_STATUS);**next_open 模式必传**(fail-closed),same_close 不消费。
    fill_mode(修法#1 窄补 2026-07-13,离场成交口径;离场**决策**两模式同=附录G 收盘确认判据):
      · 'same_close' = 附录G 原口径(触发日 close 成交;G3 同刻前视诊断值,addendum_id=1 定性)
        ——仅 legacy 域语义保留(生产策略驱动对 legacy 一律拒,修法#1 层③);
      · 'next_open'  = 白名单 close_to_next_open:收盘确认(bar j)→ 次一 present-bar 后复权
        **open** 成交;可成交判定=_sellable_at_open **日线代理规则**(窄补第三轮 #1-b:只消费
        开盘时点字段,日终 limit_status/close 结构上不进入——当天开盘可成交而收盘跌停之日照常
        按当日 open 成交,不顺延);不可成交(open 缺/开盘恰在跌停位)→ 顺延至首个代理可成交
        bar 的 open;顺延天数自名义成交 bar(j+1)起计,>20 交易日极端单列(G4 上限条款同式);
        触发后至样本末无可成交 bar(含触发即末 bar 无次日)→ 末端 close 截断(G5 mark-to-market,
        非成交,fill_source='censored_close_mark')。
    返回 None:建仓越界 / 建仓价缺(open None/≤0 = 不可建仓,engine 记同源差集)。
    """
    if fill_mode not in ("same_close", "next_open"):
        raise ValueError(f"fill_mode 非法: {fill_mode!r}(合法={{'same_close','next_open'}},不默认不猜)")
    if fill_mode == "next_open" and open_limit_status is None:
        raise ValueError("窄补第三轮 #1-b: next_open 模式必传 open_limit_status(开盘时点字段;"
                         "禁用日终 limit_status 判开盘可成交,不默认不猜)")
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
        if fill_mode == "next_open":
            # 修法#1(窄补): close_to_next_open——决策=收盘确认(bar j),成交=次一可成交
            # present-bar 的后复权 open(fill_price=next_adjusted_open,白名单冻结值)。
            # 窄补第三轮 #1-b: 可成交判定=_sellable_at_open 日线代理规则(只消费开盘时点字段;
            # ~~_sellable(日终 limit_status/close)~~ 在本分支作废=决策用了决策时点之后的信息)。
            # 不可成交(open 缺/开盘恰在跌停位)顺延至首个代理可成交 bar 的 open,顺延自名义
            # 成交 bar(j+1)起计;至末端仍无 → G5 末端 close 截断(mark-to-market,非成交)。
            for k in range(j + 1, n):
                if _sellable_at_open(open_limit_status[k], opens[k]):
                    pd = _postpone_days(trade_day_idx, k, j + 1)
                    return HoldingPath(entry_idx, entry_price, k, opens[k], reason, stop, brk,
                                       k - entry_idx, k - (j + 1), pd,
                                       pd > POSTPONE_EXTREME_DAYS, False,
                                       trigger_idx=j,
                                       fill_source=("next_open" if k == j + 1
                                                    else "postponed_open"))
            last = n - 1
            nominal = min(j + 1, last)
            pd = _postpone_days(trade_day_idx, last, nominal)
            return HoldingPath(entry_idx, entry_price, last, closes[last], reason, stop, brk,
                               last - entry_idx, last - nominal, pd,
                               pd > POSTPONE_EXTREME_DAYS, True,
                               trigger_idx=j, fill_source="censored_close_mark")
        # 触发日 j:G3 收盘成交(若可卖);否则 G4 顺延至下一可成交 bar 按其 close 成交
        prev_c = closes[j - 1] if j > 0 else None
        if _sellable(limit_status[j], c, prev_c):
            return HoldingPath(entry_idx, entry_price, j, c, reason, stop, brk,
                               j - entry_idx, 0, 0, False, False,
                               trigger_idx=j, fill_source="same_close")
        # G4 顺延:向后找首个可成交 present-bar,按该顺延日**收盘价**成交(非 open);
        # >20 交易日仍不可卖 → 仍按可卖首日收盘出,极端案例标注(postpone_extreme)不静默。
        for k in range(j + 1, n):
            if _sellable(limit_status[k], closes[k], closes[k - 1]):
                pd = _postpone_days(trade_day_idx, k, j)
                return HoldingPath(entry_idx, entry_price, k, closes[k], reason, stop, brk,
                                   k - entry_idx, k - j, pd,
                                   pd > POSTPONE_EXTREME_DAYS, False,
                                   trigger_idx=j, fill_source="postponed_close")
        # 顺延至末端仍卖不掉 → G5 末端 close 截断(触发因保留 + 标删失;极端标注同式)
        last = n - 1
        pd = _postpone_days(trade_day_idx, last, j)
        return HoldingPath(entry_idx, entry_price, last, closes[last], reason, stop, brk,
                           last - entry_idx, last - j, pd,
                           pd > POSTPONE_EXTREME_DAYS, True,
                           trigger_idx=j, fill_source="censored_close_mark")

    # 全程未触发离场 → G5 右删失,末端后复权 close 标记平仓(mark-to-market,不剔除)
    last = n - 1
    return HoldingPath(entry_idx, entry_price, last, closes[last], "right_censored",
                       False, False, last - entry_idx, 0, 0, False, True,
                       trigger_idx=None, fill_source="censored_close_mark")


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

    # ── #1-a 字段断言(same_close 域):trigger_idx/fill_source 直接断言 ──────────────
    assert p.trigger_idx == 30 and p.fill_source == "same_close", (p.trigger_idx, p.fill_source)
    assert p3.trigger_idx == 31 and p3.fill_source == "postponed_close", p3.fill_source
    assert p4.fill_source == "censored_close_mark" and p4.trigger_idx == 31, p4.fill_source
    assert p5.trigger_idx is None and p5.fill_source == "censored_close_mark", p5.fill_source

    # ══ 修法#1 窄补(2026-07-13):fill_mode='next_open'(close_to_next_open 白名单) ══
    # 窄补第三轮 #1-b(2026-07-13):可成交判定改 _sellable_at_open 日线代理规则(只消费
    # 开盘时点字段)→ N 系列全部改传 open_limit_status;N2/N5 原"日终跌停顺延"样例按新
    # 代理规则改判为"开盘恰在跌停位顺延"(期望值改判归因=验收档,非删自检,宪章⑦)。
    NOL = ["none"] * 400   # 开盘时点全不在跌停位

    # ── N1 正常路径:触发日 j 收盘确认 → 次日 open 成交(非同刻 close) ─────────────
    #   建仓 idx30(open100);idx31 close 96<ma20 触发;idx32 open=97.5 成交。
    cn1 = [100.0] * 31 + [96.0, 98.0]
    on1 = [100.0] * 31 + [96.5, 97.5]
    pn1 = simulate_holding_path(cn1, on1, NS[:33], entry_idx=30, fill_mode="next_open",
                                open_limit_status=NOL[:33])
    assert pn1 is not None and pn1.exit_reason == "break_ma20", pn1
    assert pn1.exit_idx == 32 and pn1.exit_price == 97.5, pn1   # 次日 open(非触发日 close 96.0)
    assert pn1.postpone_bars == 0 and pn1.postpone_days == 0 and not pn1.right_censored, pn1
    assert pn1.trigger_idx == 31 and pn1.fill_source == "next_open", (pn1.trigger_idx, pn1.fill_source)
    # 同一序列 same_close 对照:触发日 close 96.0 出(证两口径分流、决策判据同)
    ps1 = simulate_holding_path(cn1, on1, NS[:33], entry_idx=30)
    assert ps1.exit_idx == 31 and ps1.exit_price == 96.0

    # ── N2 名义成交日开盘恰在跌停位 → 顺延至首个代理可成交 bar 的 open(#1-b 改判) ──
    cn2 = [100.0] * 31 + [79.0, 75.0, 74.0]
    on2 = [100.0] * 31 + [79.0, 74.5, 73.5]
    oln2 = ["none"] * 32 + ["open_at_down_limit", "none"]   # idx32 开盘恰在跌停位;idx33 可成交
    pn2 = simulate_holding_path(cn2, on2, NS[:34], entry_idx=30, fill_mode="next_open",
                                open_limit_status=oln2)
    assert pn2 is not None and pn2.exit_reason == "stop_loss", pn2   # idx31 close79≤80 触发
    assert pn2.exit_idx == 33 and pn2.exit_price == 73.5, pn2        # 顺延日 open(非 close 74.0)
    assert pn2.postpone_bars == 1 and pn2.postpone_days == 1 and not pn2.right_censored, pn2
    assert pn2.fill_source == "postponed_open" and pn2.trigger_idx == 31, pn2.fill_source

    # ── N2b 窄补第三轮反例(人令统一验收要求):当天 open 可成交但**收盘跌停** ─────────
    #   → 日终 limit_status='limit_down' 不得进入判定,照常按当日 open 成交,**不顺延**。
    cn2b = [100.0] * 31 + [96.0, 88.0, 87.0]                 # idx32 收盘跌停(88)
    on2b = [100.0] * 31 + [96.5, 97.0, 86.0]                 # 但 idx32 open=97 开盘可成交
    ln2b = ["none"] * 32 + ["limit_down", "none"]            # 日终字段(结构上不进判定)
    pn2b = simulate_holding_path(cn2b, on2b, ln2b, entry_idx=30, fill_mode="next_open",
                                 open_limit_status=NOL[:34])
    assert pn2b is not None and pn2b.exit_idx == 32 and pn2b.exit_price == 97.0, pn2b  # 当日 open 97
    assert pn2b.postpone_bars == 0 and pn2b.fill_source == "next_open", pn2b.fill_source
    # 反证:同序列旧判定(日终 limit_status)会错误顺延到 idx33 open=86.0——新规则已消灭该前视

    # ── N3 触发即末 bar(无次日)→ 末端 close 截断(mark-to-market,非成交) ─────────
    cn3 = [100.0] * 31 + [79.0]
    on3 = [100.0] * 31 + [79.5]
    pn3 = simulate_holding_path(cn3, on3, NS[:32], entry_idx=30, fill_mode="next_open",
                                open_limit_status=NOL[:32])
    assert pn3 is not None and pn3.right_censored and pn3.exit_idx == 31 and pn3.exit_price == 79.0, pn3
    assert pn3.trigger_stop and pn3.postpone_bars == 0, pn3
    assert pn3.fill_source == "censored_close_mark" and pn3.trigger_idx == 31, pn3.fill_source

    # ── N4 次日 open 缺(None)→ R-open-1 不满足(无 opening print),顺延 ─────────────
    cn4 = [100.0] * 31 + [96.0, 98.0, 99.0]
    on4 = [100.0] * 31 + [96.5, None, 98.5]
    pn4 = simulate_holding_path(cn4, on4, NS[:34], entry_idx=30, fill_mode="next_open",
                                open_limit_status=NOL[:34])
    assert pn4 is not None and pn4.exit_idx == 33 and pn4.exit_price == 98.5, pn4
    assert pn4.postpone_bars == 1 and pn4.fill_source == "postponed_open", pn4

    # ── N5 顺延 >20 交易日极端标注(G4 上限条款同式;开盘连续跌停位,#1-b 改判) ──────
    cn5 = [100.0] * 31 + [79.0] + [78.0 - i for i in range(22)] + [55.0]
    on5 = [100.0] * 31 + [79.0] + [77.5 - i for i in range(22)] + [54.5]
    oln5 = ["none"] * 32 + ["open_at_down_limit"] * 22 + ["none"]
    pn5 = simulate_holding_path(cn5, on5, NS[:55], entry_idx=30, fill_mode="next_open",
                                open_limit_status=oln5)
    assert pn5 is not None and pn5.exit_idx == 54 and pn5.exit_price == 54.5, pn5   # 可成交日 open
    assert pn5.postpone_bars == 22 and pn5.postpone_days == 22 and pn5.postpone_extreme, pn5

    # ── fill_mode 非法 → raise;next_open 缺 open_limit_status → raise(fail-closed) ──
    try:
        simulate_holding_path([100.0], [100.0], ["none"], entry_idx=0, fill_mode="same_close_exec")
        raise SystemExit("fill_mode 非法未拒")
    except ValueError:
        pass
    try:
        simulate_holding_path([100.0], [100.0], ["none"], entry_idx=0, fill_mode="next_open")
        raise SystemExit("next_open 缺 open_limit_status 未拒(日终判定复燃风险)")
    except ValueError as e:
        assert "open_limit_status" in str(e)

    print("holding_path.py 自检 OK(附录G):G1收盘确认/G2双flag主因强平/G3触发日close/"
          "G4顺延日close+>20交易日极端标注(bar口径+停牌trade_day_idx口径)/G4→G5截断/G5末端mark-to-market/"
          "G6 one_word判向/越界价缺→None/建仓即末bar/trigger_idx+fill_source字段直接断言(#1-a);"
          "next_open(修法#1窄补+第三轮#1-b代理规则):次日open成交≠同刻close/开盘可成交收盘跌停不顺延(反例)/"
          "开盘跌停位顺延open/触发即末bar截断/open缺顺延/极端标注/非法fill_mode拒/缺open_limit_status拒;"
          "STOP_FRAC=%.2f MA_LONG=%d POSTPONE_EXTREME_DAYS=%d"
          % (STOP_FRAC, MA_LONG, POSTPONE_EXTREME_DAYS))
