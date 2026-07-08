"""淘沙 · engine · 可交易口径净收益(切片3 步7 选项2;pap exp_id=5 `cost` 冻结定义)。

pap 既定可交易口径(**非新增设计、零调参**,rates 取自台账 exp_id=5 pap_json `cost` 块):
  · 进场 = τ=0(=T+1,含一字板顺延/放弃 by cleaning MAX_POSTPONE)当日**后复权 open**;
  · 出场 = 检验窗尾(主窗 τ=main_len−1 / 稳健窗 τ=robust_len−1)当日**后复权 close**;
  · 一字涨停不可成交(cost.limit_up_board_untradeable)= 进场侧,已由 cleaning 顺延/放弃处置;
  · 成本硬扣(cost 冻结率):
        买费 = commission + slippage_oneway
        卖费 = commission + stamp_tax_sell + slippage_oneway

成本**乘式净额**(骗不了人:买价上浮、卖价下折;此为 cost 冻结率的算术读法,验收档 §显式声明):
        net   = [close_exit·(1 − 卖费)] / [open_entry·(1 + 买费)] − 1
毛额(对照,不扣成本):
        gross = close_exit / open_entry − 1

⚠ 出场侧不可成交(窗尾一字跌停/停牌)pap 未定顺延规则 → **不发明**:窗尾 close 存在即按字面
  "窗尾收盘出"计入,单列 exit 诊断计数(一字/跌停);窗尾停牌缺 close → 该事件该窗排除、计
  exit_no_close(保守,不以不可成交价充数)。可交易口径为**报告与锚对照**用途,不改统计判决。
"""
from __future__ import annotations

from typing import Optional

Num = Optional[float]


def cost_fractions(cost: dict) -> tuple[float, float]:
    """从 pap `cost` 块取 (买费, 卖费)。缺键即 KeyError(冻结口径必须显式,不默认不猜)。"""
    c = cost["commission"]
    s = cost["stamp_tax_sell"]
    g = cost["slippage_oneway"]
    return c + g, c + s + g


def net_return(open_entry: Num, close_exit: Num, buy_fee: float, sell_fee: float) -> Num:
    """乘式净收益;进/出场价缺(None 或 open≤0)→ None(不可成交,排除)。"""
    if open_entry is None or close_exit is None or open_entry <= 0:
        return None
    return close_exit * (1.0 - sell_fee) / (open_entry * (1.0 + buy_fee)) - 1.0


def gross_return(open_entry: Num, close_exit: Num) -> Num:
    """毛收益(不扣成本;对照用)。价缺 → None。"""
    if open_entry is None or close_exit is None or open_entry <= 0:
        return None
    return close_exit / open_entry - 1.0


def aggregate(vals: list) -> dict:
    """截面汇总:n(非 None 数)/mean/median/pos_frac/std(ddof1)。空 → n=0 全 None。"""
    xs = [x for x in vals if x is not None]
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "median": None, "pos_frac": None, "std": None}
    xs_sorted = sorted(xs)
    mid = n // 2
    median = xs_sorted[mid] if (n % 2) else (xs_sorted[mid - 1] + xs_sorted[mid]) / 2.0
    mean = sum(xs) / n
    std = (sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5 if n >= 2 else None
    pos = sum(1 for x in xs if x > 0) / n
    return {"n": n, "mean": mean, "median": median, "pos_frac": pos, "std": std}


def window_block(trades: list, buy_fee: float, sell_fee: float, which: str,
                 taus_label: str) -> dict:
    """对一子集(某层/合并)算某窗(main/robust)的可交易口径净/毛额汇总 + 出场诊断。

    trades: 每元素 = se_meta['tradeable'](含 entry_open / exit_close_{which} / exit_status_{which})。
    which: 'main' | 'robust'。"""
    nets, grosses = [], []
    diag = {"one_word": 0, "limit_down": 0, "limit_up": 0, "suspend_or_missing": 0}
    excluded_no_close = 0
    entered = 0
    for tr in trades:
        oe = tr.get("entry_open")
        ce = tr.get(f"exit_close_{which}")
        stt = tr.get(f"exit_status_{which}")
        if stt in diag:
            diag[stt] += 1
        nr = net_return(oe, ce, buy_fee, sell_fee)
        gr = gross_return(oe, ce)
        if nr is None:
            excluded_no_close += 1
            continue
        entered += 1
        nets.append(nr)
        grosses.append(gr)
    return {
        "window": taus_label,
        "n_events": entered,
        "excluded_no_close": excluded_no_close,     # 窗尾停牌/缺 close → 排除(保守)
        "exit_censor": diag,                         # 窗尾删失计数(一字/涨跌停/停牌;字面收盘出仍计入)
        "net": aggregate(nets),
        "gross": aggregate(grosses),
    }


if __name__ == "__main__":
    bf, sf = cost_fractions({"commission": 0.00025, "stamp_tax_sell": 0.001, "slippage_oneway": 0.001})
    assert abs(bf - 0.00125) < 1e-15 and abs(sf - 0.00225) < 1e-15, "费率"
    # 无成本无涨跌:net<0(成本硬扣);gross=0
    assert abs(gross_return(10.0, 10.0)) < 1e-15
    assert net_return(10.0, 10.0, bf, sf) < 0
    # 价缺 → None(排除)
    assert net_return(None, 10.0, bf, sf) is None and net_return(10.0, None, bf, sf) is None
    ag = aggregate([0.01, -0.02, 0.03, None])
    assert ag["n"] == 3 and abs(ag["median"] - 0.01) < 1e-15 and abs(ag["pos_frac"] - 2/3) < 1e-12
    # 乘式净额手算:open10 close11 → 11*(1-0.00225)/(10*(1+0.00125))-1
    exp = 11.0 * (1 - 0.00225) / (10.0 * (1 + 0.00125)) - 1.0
    assert abs(net_return(10.0, 11.0, bf, sf) - exp) < 1e-15
    print("execution.py 自检 OK:费率 0.00125/0.00225 / 乘式净额 / 价缺排除 / 汇总")
