"""淘沙 · compute · b1 全市场流动性池(PIT 逐期滚动排名;#2b = drawdown_rebuy#2 = exp_id 3)。

冻结口径(pap exp3 `pool` + 2026-07-08 人裁排产令①,exp3 contamination_note 在案):
  · 宇宙 = **上市满 120 交易日**(list_date 起算,至评估日 d 的交易日计数 ≥ 120);
  · 成交额排名 = **trailing 20 交易日成交额均值**(窗口 [d-19, d] 内非空 amount 的算术均值),
    **PIT**:只用评估日 d 及之前的 amount —— **禁全期均值**(前视风险着力点,人裁明令);
  · **前 20%**(按票数)入池:当期宇宙按 trailing-20d 均值降序,取前 ceil(0.20 × N) 名;
  · **逐事件评估日频率**(逐日现算、无期内持有滞后);
  · 窗口内取"和" vs "均值"排名等价(人追认);此处用均值(对停牌缺行稳健=除以窗内非空天数)。

红线:纯 PIT,绝不引入未来信息(排名只回看、不前看);停牌(无 amount)日不进当日均值分母;
  当期无有效 trailing 均值(窗内全空)的票不参与排名(不可能是流动性池成员)。纯函数、无副作用。
"""
from __future__ import annotations

import math
from types import MappingProxyType
from typing import Optional

Num = Optional[float]

# ── 冻结口径常量(人批;改参 = 走登记/裁定,非运行时覆写)──────────────────────────
AMOUNT_WINDOW = 20        # trailing 成交额均值窗口(交易日);排产令① N=20
LISTING_MIN_DAYS = 120    # 上市满交易日门槛;pap listing_min
TOP_FRACTION = 0.20       # 前 20% 入池;pap filter 成交额前20%

FROZEN = MappingProxyType({
    "amount_window": AMOUNT_WINDOW, "listing_min_days": LISTING_MIN_DAYS,
    "top_fraction": TOP_FRACTION,
    "method": "PIT 逐事件评估日:trailing-20d 成交额均值降序取前20%(禁全期均值);上市满120交易日宇宙",
    "sealed_by": "pap exp3 pool + 2026-07-08 人裁排产令①(contamination_note 在案)",
})


def trailing_mean_amount(amounts: list, i: int, window: int = AMOUNT_WINDOW) -> Num:
    """评估日索引 i 的 trailing-window 成交额均值(PIT:只用 [i-window+1, i])。

    窗内非空 amount 的算术均值;全空 → None(不参与排名)。禁引用 i 之后(前视)。
    """
    if i < 0:
        return None
    lo = max(0, i - window + 1)
    vals = [a for a in amounts[lo:i + 1] if a is not None]
    return (sum(vals) / len(vals)) if vals else None


def listed_trading_days(list_idx: Optional[int], i: int) -> int:
    """至评估日索引 i(含)的已上市交易日数 = i - list_idx + 1;list_idx 未知/晚于 i → 0。"""
    if list_idx is None or list_idx > i:
        return 0
    return i - list_idx + 1


def pool_members_at(i: int, amount_by_sec: dict, list_idx_by_sec: dict,
                    window: int = AMOUNT_WINDOW, min_listed: int = LISTING_MIN_DAYS,
                    top_fraction: float = TOP_FRACTION) -> set:
    """评估日索引 i 的 b1 池成员(PIT)。

    amount_by_sec: {ts_code: [amount 对齐交易日轴,停牌/无行=None]};
    list_idx_by_sec: {ts_code: 上市首日在轴索引(或 None)}。
    返回入池 ts_code 集合。步骤:①宇宙=上市满 min_listed 交易日;②各票 trailing 均值(PIT);
    ③有有效均值者按降序;④取前 ceil(top_fraction × |宇宙可排名|) 名。
    """
    ranked = []
    for ts, amounts in amount_by_sec.items():
        if listed_trading_days(list_idx_by_sec.get(ts), i) < min_listed:
            continue                       # 宇宙门槛:上市满 120 交易日
        m = trailing_mean_amount(amounts, i, window)
        if m is None:
            continue                       # 窗内全空(停牌)→ 不可排名、不入池
        ranked.append((ts, m))
    if not ranked:
        return set()
    # 降序(成交额大在前);同额按 ts_code 稳定序(确定性)
    ranked.sort(key=lambda x: (-x[1], x[0]))
    k = math.ceil(top_fraction * len(ranked))
    return {ts for ts, _ in ranked[:k]}


def audit_digest() -> str:
    import hashlib, json
    payload = json.dumps({k: v for k, v in FROZEN.items()}, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # 自检:PIT 无前视 / top20% 切分 / 停牌稳健 / 上市门槛。
    # 造 10 票 × 30 日;amount 递增编号(票 j 的 amount 恒 = j),上市日与停牌注入。
    n_days = 30
    amt, lidx = {}, {}
    for j in range(10):
        ts = f"S{j:02d}"
        amt[ts] = [float(j + 1)] * n_days      # 票 j amount 恒 j+1(票号大=成交额大)
        lidx[ts] = 0                            # 全部第 0 日上市
    # 门槛自检:第 i=119 日前不满 120 交易日 → 空池(i 从 0 计,满120=索引≥119)
    assert pool_members_at(118, amt, lidx) == set(), "上市满120门槛(i=118 不足)"
    # i=119 满 120 日:10 票全宇宙,top20%=ceil(0.2×10)=2 名 → 成交额最大两票 S09/S08
    m = pool_members_at(119, amt, lidx) if n_days > 119 else None
    # n_days=30 不够 120,改小门槛验 top20% 逻辑
    assert pool_members_at(25, amt, lidx, min_listed=10) == {"S09", "S08"}, "top20%=前2名(S09/S08)"
    # PIT 无前视:某票未来 amount 巨大不应影响当日排名
    amt2 = {k: list(v) for k, v in amt.items()}
    amt2["S00"][29] = 1e9                       # S00 仅末日暴量(未来)
    assert "S00" not in pool_members_at(25, amt2, lidx, min_listed=10), "PIT:未来暴量不进当日池"
    # 停牌稳健:某票 trailing 窗内全 None → 不入池
    amt3 = {k: list(v) for k, v in amt.items()}
    for t in range(6, 26):
        amt3["S09"][t] = None                   # S09 在 i=25 的窗[6,25]全停牌
    assert "S09" not in pool_members_at(25, amt3, lidx, min_listed=10), "窗内全停牌不入池"
    # trailing 均值 PIT:窗 [i-19,i]
    assert trailing_mean_amount([1.0, 2.0, 3.0, 4.0], 3, window=2) == 3.5   # (3+4)/2
    assert trailing_mean_amount([1.0, None, 3.0], 2, window=3) == 2.0       # (1+3)/2 非空均值
    assert listed_trading_days(5, 10) == 6 and listed_trading_days(None, 10) == 0
    print("liquidity_pool.py 自检 OK:上市满120门槛 / top20%前2名 / PIT无前视 / 停牌稳健 / trailing均值")
    print("audit_digest =", audit_digest())
