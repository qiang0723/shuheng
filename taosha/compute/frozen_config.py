"""淘沙 · 四统计口径冻结配置(切片2,人拍 2026-07-07)。

红线:本模块承载建 compute 前卡住的 **4 个统计口径(①铁律)** 的人拍终值。
四项均为**冻结配置、运行时不可覆写**(核对单 item 10)——引擎从此处只读取值,不接受
任何运行时参数注入或猜测。任何"试试别的口径"的念头都是违规(taosha CLAUDE.md 铁律④)。

人拍四口径(2026-07-07,留痕 = slice2-acceptance-checklist.md 文末〔四口径拍板〕+ ops/STATE.md):
  ① compounding = continuous(对数收益);我方与 estudy2 两侧同设(核对单 item 3)。
  ② AR 模型 = SIM(单指数市场模型);regressor 按冻结基准取(见 pap.FROZEN_BENCHMARK):
     池内假设 = 雷达股池等权;全市场假设 = 全市场等权。(否决"等权 market-adjusted"。)
  ③ 覆盖门槛 = 冻结估计窗 160 日(事件日前 250 至前 91,spec §5 行 66)内有效交易日
     ≥112(=70%),不足即剔、剔除率进报告(核对单 item 6,已改读)。
  ④ ρ̄ 行业分组 = entity_master 的 tushare industry(ADJ-BMP 截面相关 ρ̄ 分组键)。
     近似注记(在案,不修):行业分类为当前快照、非 PIT;对 ρ̄ 估计影响属二阶。

覆盖门槛改读裁决(留痕,item 6 配套):驳回我方"84=最小估计期/120=稳健窗门槛"倒推语义。
  "84/120" 本是"70%×120 日窗"的展开式(0.7×120=84);120 为架构窗口臆测、**未核 spec §5**
  的错误前提(错误归因=窗口 II,在案);spec §5 白纸黑字估计期=前 250 至前 91=**160** 交易日。
  70% 覆盖率为密封实质、维持不变、密封卡本体不改;**112/160** 即其在正确分母 160 上的实例化。

作用域:本模块只放**跨假设通用的四统计口径 + 估计窗/覆盖规则**。事件窗([0,+2]/[0,+5])、
板块分层、停牌剔除等其余 A股口径(核对单 item 5/7/8/9)属 per-PAP 或 compute/cleaning 层,不在此。
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType

# 单一真源:regressor 冻结基准复用 §6 pap.FROZEN_BENCHMARK(池内/全市场两假设),不另抄以防漂移。
from taosha.experiment.pap import FROZEN_BENCHMARK

# ── 口径① compounding ─────────────────────────────────────────────────────────
COMPOUNDING = "continuous"          # 对数收益;continuous ⇔ estudy2 log/continuous 语义

# ── 口径② AR 模型 ─────────────────────────────────────────────────────────────
AR_MODEL = "SIM"                    # 单指数市场模型(Single Index Market model)
#   regressor(市场/基准组合)= 冻结基准,按假设口径二选一(见下 REGRESSOR_BENCHMARK)。

# ── 口径③ 估计窗 + 覆盖门槛(spec §5 行 66)────────────────────────────────────
EST_WINDOW_OFFSET_START = -250      # 事件日前 250 交易日(含)
EST_WINDOW_OFFSET_END = -91         # 事件日前 91 交易日(含)
EST_WINDOW_LEN = EST_WINDOW_OFFSET_END - EST_WINDOW_OFFSET_START + 1  # = 160
COVERAGE_RATIO = 0.70               # 密封实质:70% 覆盖率(维持不变)
COVERAGE_MIN_VALID = 112            # = 70% × 160;窗内有效交易日门槛(不足即剔)

# ── 口径④ ρ̄ 行业分组 ────────────────────────────────────────────────────────
RHO_BAR_GROUP_KEY = "entity_master.tushare_industry"
RHO_BAR_GROUP_CAVEAT = (
    "行业分类为 entity_master 当前快照、非 PIT;对 ρ̄ 估计影响属二阶,在案不修。")

# ── 自洽断言(骗不了人:任何"120/84"复燃或分母漂移在 import 期即炸)─────────────
assert EST_WINDOW_LEN == 160, f"估计窗长必须=160(前250至前91),得到 {EST_WINDOW_LEN}"
assert COVERAGE_MIN_VALID == round(COVERAGE_RATIO * EST_WINDOW_LEN), (
    f"覆盖门槛必须=70%×160=112,得到 {COVERAGE_MIN_VALID}")
assert COMPOUNDING == "continuous", "口径①=continuous(对数收益)"
assert AR_MODEL == "SIM", "口径②=SIM(单指数市场模型)"

# ── 冻结只读视图(运行时不可覆写,item 10)─────────────────────────────────────
#   MappingProxyType 使 dict 变只读;赋值/改键在运行时抛 TypeError。
REGRESSOR_BENCHMARK = MappingProxyType(dict(FROZEN_BENCHMARK))

FROZEN = MappingProxyType({
    "compounding": COMPOUNDING,
    "ar_model": AR_MODEL,
    "regressor_benchmark": REGRESSOR_BENCHMARK,
    "estimation_window": MappingProxyType({
        "offset_start": EST_WINDOW_OFFSET_START,
        "offset_end": EST_WINDOW_OFFSET_END,
        "length": EST_WINDOW_LEN,
        "spec_ref": "spec §5 行66:估计期=事件日前250至前91交易日",
    }),
    "coverage": MappingProxyType({
        "ratio": COVERAGE_RATIO,
        "min_valid_days": COVERAGE_MIN_VALID,
        "denominator": EST_WINDOW_LEN,
        "on_insufficient": "剔除;剔除率进输出报告",
        "reread_note": "原'84/120'作废→112/160(70%);错误归因=窗口II(120未核spec§5),在案",
    }),
    "rho_bar_group": MappingProxyType({
        "key": RHO_BAR_GROUP_KEY,
        "caveat": RHO_BAR_GROUP_CAVEAT,
    }),
    "sealed_by": "人拍 2026-07-07;冻结配置·运行时不可覆写(核对单 item 10)",
})


def coverage_ok(n_valid_days: int) -> bool:
    """估计窗覆盖门槛判定:窗内有效交易日 ≥112(=70%×160)方合格。不足即剔(caller 记剔除率)。"""
    return n_valid_days >= COVERAGE_MIN_VALID


def regressor_benchmark(hypothesis: str) -> str:
    """按假设口径取 SIM regressor 的冻结基准。
    hypothesis ∈ {'pool','market'} → 池内假设=雷达股池等权 / 全市场假设=全市场等权。"""
    key = {"pool": "pool_hypothesis", "market": "market_hypothesis"}.get(hypothesis)
    if key is None:
        raise ValueError(f"hypothesis 须为 'pool' 或 'market',得到 {hypothesis!r}")
    return REGRESSOR_BENCHMARK[key]


def _canonical(obj):
    """把嵌套 MappingProxyType 归一为纯 dict/list,供稳定序列化。"""
    if isinstance(obj, (MappingProxyType, dict)):
        return {k: _canonical(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonical(v) for v in obj]
    return obj


def audit_digest() -> str:
    """冻结配置的稳定 sha256 摘要(item 10:参数变更走配置审计留痕)。
    任何口径值变动都会改变此摘要——落库/报告可据此固定'跑的是哪套冻结口径'。"""
    payload = json.dumps(_canonical(FROZEN), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # 自检:打印冻结口径 + 审计摘要,并证只读(改值抛错)。
    print(json.dumps(_canonical(FROZEN), ensure_ascii=False, indent=2))
    print("audit_digest =", audit_digest())
    try:
        FROZEN["compounding"] = "discrete"        # 应抛 TypeError
    except TypeError as e:
        print("只读校验 OK(FROZEN 不可覆写):", e)
