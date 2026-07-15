"""淘沙 · PAP 构造与校验(切片1)。

红线(spec §2⑤ / CLAUDE.md):LLM 只做"想法→PAP 草稿翻译",不发明事件定义、不选参数终值。
本模块只**结构化承载人冻结的 PAP 原文**并做完整性校验;所有数值/定义均转录自
spec v0.2 冻结版 §6,一个数不改。pap_json 一旦经 ledger 冻结即不可变(触发器焊死)。

pap_json 必备键(spec §4 注:事件定义/窗口/池/基准/成本/holdout/清洗/数据快照批次要求):
  event_def, window, pool, benchmark, cost, holdout, cleaning, snapshot_batch_req
"""
from __future__ import annotations

import re
from typing import Optional

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

# ── 修法#1(外审五项,人终签 2026-07-13): PAP 执行 schema ──────────────────────
# 三层 fail-closed 之层①(本模块)/层②(011 迁移 _pap_freeze_gate 冻结触发器)/
# 层③(策略驱动启动校验)。存量 legacy 实验唯一判据 = pap_legacy_registry 物化登记表
# (011 迁移时刻写入,append-only,taosha_app/引擎零写权)——不认调用方自称、不认 registered_at。
PAP_SCHEMA_VERSION = 2                 # v2=显式执行 schema;无此键=legacy(仅 registry 在册者合法)
VALID_ANALYSIS_TYPES = ("event", "strategy", "event_and_strategy")

# 执行模式白名单(人令原文;保留原裁定允许的两类合法执行方式)
CLOSE_TO_NEXT_OPEN_FROZEN = {          # 四字段须逐字冻结值
    "decision_time": "close_confirmed",
    "fill_time": "next_open",
    "fill_price": "next_adjusted_open",
    "slippage_rule": "frozen_cost",
}
PRECLOSE_TO_TAIL_REQUIRED = (          # 必填结构字段;取值由人在冻结前选定,代码不得自行默认
    "decision_cutoff", "decision_price_source", "fill_window", "fill_price_rule", "slippage_rule")
# ⚠窄补(外审第二轮 2026-07-13): preclose_to_tail 为白名单可冻结,但**真实执行模拟未实现**
# (日内数据不足)——已实现执行 profile 的唯一judgment来源=engine.drawdown_strategy
# .IMPLEMENTED_EXECUTION_PROFILES;驱动/引擎对未实现 profile 一律 fail-closed 拒运行,
# 在日内数据足以支撑真实执行前不得宣称该模式"已可执行"。

# 已知时点记号 → 同轴时序序数(信息时序判定: 决策时点必须严格早于成交窗口)
_TIME_ORDER = {"preclose_cutoff": 10, "tail_window": 20,
               "close_confirmed": 30, "same_close": 30, "close": 30, "next_open": 40}

# 窄补(2026-07-13): preclose_to_tail 时间字段=结构化可解析(非字符串非空判断)
_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _hhmm_minutes(v) -> Optional[int]:
    """'HH:MM' → 当日分钟数;非法结构 → None(调用方拒,不猜)。"""
    if isinstance(v, str) and _HHMM_RE.fullmatch(v):
        h, m = v.split(":")
        return int(h) * 60 + int(m)
    return None


def validate_strategy_execution(se) -> None:
    """修法#1: 结构化 strategy_execution 白名单校验(层①;层②③同则)。违规即 raise。"""
    if not isinstance(se, dict) or not se:
        raise ValueError("修法#1: analysis_type 含 strategy 须结构化 strategy_execution(执行模式白名单)")
    # 信息时序显式禁组合(先于白名单判,close_confirmed+same_close 等直接拒绝)
    d = _TIME_ORDER.get(str(se.get("decision_time", "")))
    f = _TIME_ORDER.get(str(se.get("fill_time", "")))
    if d is not None and f is not None and d >= f:
        raise ValueError(
            f"修法#1: 禁止组合(信息时序): 决策时点 {se.get('decision_time')!r} 必须严格早于"
            f"成交窗口 {se.get('fill_time')!r}(close_confirmed+same_close 等直接拒绝)")
    prof = se.get("execution_profile")
    if prof == "close_to_next_open":
        for k, v in CLOSE_TO_NEXT_OPEN_FROZEN.items():
            if se.get(k) != v:
                raise ValueError(
                    f"修法#1: close_to_next_open 字段 {k} 须为冻结值 {v!r}(得到 {se.get(k)!r})")
    elif prof == "preclose_to_tail":
        missing = [k for k in PRECLOSE_TO_TAIL_REQUIRED if se.get(k) in (None, "", {})]
        if missing:
            raise ValueError(
                f"修法#1: preclose_to_tail 缺必填结构字段 {missing}"
                "(截止时点/代理价规则由人在 PAP 冻结前选定,代码不得自行默认)")
        # 窄补(2026-07-13): 时间字段结构化可解析+强制断言,~~字符串非空判断/LIKE close_confirmed~~ 作废
        dc = _hhmm_minutes(se.get("decision_cutoff"))
        if dc is None:
            raise ValueError(
                f"修法#1(窄补): preclose_to_tail decision_cutoff 须为结构化时间 'HH:MM'"
                f"(得到 {se.get('decision_cutoff')!r};不接受自由文本)")
        fw = se.get("fill_window")
        ws = _hhmm_minutes(fw.get("start")) if isinstance(fw, dict) else None
        we = _hhmm_minutes(fw.get("end")) if isinstance(fw, dict) else None
        if ws is None or we is None:
            raise ValueError(
                f"修法#1(窄补): preclose_to_tail fill_window 须为结构化 "
                f"{{'start':'HH:MM','end':'HH:MM'}}(得到 {fw!r})")
        if not dc < ws:
            raise ValueError(
                f"修法#1(窄补): 强制断言 decision_cutoff < fill_window.start 不成立"
                f"({se.get('decision_cutoff')} >= {fw.get('start')}):决策必须严格早于成交窗口,拒")
        if not ws < we:
            raise ValueError(f"修法#1(窄补): fill_window.start 须严格早于 end(得到 {fw!r})")
        for k in ("decision_price_source", "fill_price_rule", "slippage_rule"):
            if not str(se.get(k) or "").strip():
                raise ValueError(f"修法#1: preclose_to_tail 字段 {k} 须非空(人选定,代码不默认)")
    else:
        raise ValueError(f"修法#1: execution_profile 白名单外: {prof!r}"
                         "(合法={close_to_next_open, preclose_to_tail})")


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
    """完整性校验:必备键齐全、非空。不校验语义(语义是人冻结的,不由代码评判)。
    修法#1 层①(2026-07-13): 本函数辖此后新构造/新登记的 PAP——须含 pap_schema_version
    与 analysis_type;含 strategy 则须过 validate_strategy_execution 白名单;纯事件不要求
    该字段。存量 legacy PAP 不经本函数重验(其合法性判据=pap_legacy_registry 物化表,层②③)。"""
    if not isinstance(pap, dict):
        raise ValueError("pap 必须是 dict")
    missing = [k for k in REQUIRED_KEYS if k not in pap or pap[k] in (None, "", {})]
    if missing:
        raise ValueError(f"pap_json 缺必备键或为空: {missing}")
    if "pap_schema_version" not in pap:
        raise ValueError("修法#1: 新 PAP 须含 pap_schema_version(不得靠文本推断是否含策略版;"
                         "存量 legacy 唯一判据=pap_legacy_registry 物化表,非本字段)")
    if pap["pap_schema_version"] != PAP_SCHEMA_VERSION:
        raise ValueError(f"修法#1: pap_schema_version 须为 {PAP_SCHEMA_VERSION}"
                         f"(得到 {pap['pap_schema_version']!r})")
    at = pap.get("analysis_type")
    if at not in VALID_ANALYSIS_TYPES:
        raise ValueError(f"修法#1: analysis_type 须为 {VALID_ANALYSIS_TYPES} 之一(得到 {at!r})")
    if at in ("strategy", "event_and_strategy"):
        validate_strategy_execution(pap.get("strategy_execution"))


def parse_test_windows(pap: dict) -> tuple[int, ...]:
    """从 pap['window'] 文本读**检验窗**日数(事件窗属事件定义,台账为唯一事实源;
    人裁 2026-07-07:检验窗从 pap 读、不在 frozen_ashare 复制)。

    window 文本形如 'T+1起,后20/60日' → 返回检验窗日数元组 (20, 60);
    语义: 后 N 日 = T+1..T+N = τ=0..N-1 = **N 个 τ 点**(τ=0:=T+1,S2-DEC3 锚对所有窗有效)。
    多窗按文本顺序、须升序(短→长,如 #4=20/60、#3=5/20/60)。runner 取首=主检验窗(唯一进
    verdict)、末=稳健检验窗;中间窗=预注册次级报告窗,完整产出、不参与判决(人裁 2026-07-15
    三窗判点①,留痕 docs/holder-sell-rulings-2026-07-15.md;不得据三窗结果择优改判)。
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

    # ── 修法#1 层① 自检(2026-07-13):白名单/禁组合/必填/schema ──
    _base = {k: {"x": 1} for k in REQUIRED_KEYS}
    _ok_c2n = dict(CLOSE_TO_NEXT_OPEN_FROZEN, execution_profile="close_to_next_open")
    _ok_pct = {"execution_profile": "preclose_to_tail", "decision_cutoff": "14:50",
               "decision_price_source": "人定代理价占位", "fill_window": {"start": "14:55", "end": "15:00"},
               "fill_price_rule": "人定成交价规则占位", "slippage_rule": "frozen_cost"}
    validate_pap(dict(_base, pap_schema_version=2, analysis_type="event"))                    # 纯事件不要求
    validate_pap(dict(_base, pap_schema_version=2, analysis_type="strategy",
                      strategy_execution=_ok_c2n))                                           # 白名单1
    validate_pap(dict(_base, pap_schema_version=2, analysis_type="event_and_strategy",
                      strategy_execution=_ok_pct))                                           # 白名单2
    for bad_pap, why in (
        (dict(_base), "缺 pap_schema_version"),
        (dict(_base, pap_schema_version=2), "缺 analysis_type"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy"), "缺 strategy_execution"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution={"execution_profile": "close_to_next_open",
                                  "decision_time": "close_confirmed", "fill_time": "same_close",
                                  "fill_price": "same_close", "slippage_rule": "frozen_cost"}),
         "close_confirmed+same_close 禁组合"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution={"execution_profile": "preclose_to_tail",
                                  "fill_window": "尾盘", "fill_price_rule": "x",
                                  "slippage_rule": "frozen_cost"}),
         "preclose 缺 decision_cutoff/decision_price_source"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution={"execution_profile": "same_close_exec"}),
         "白名单外 profile"),
        # ── 窄补(2026-07-13): 结构化时间字段+强制断言 ──
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution=dict(_ok_pct, decision_cutoff="15:00")),
         "decision_cutoff(15:00) ≥ fill_window.start(14:55) 反向时间窗口"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution=dict(_ok_pct, decision_cutoff="尾盘前(自由文本)")),
         "decision_cutoff 自由文本(非 HH:MM 结构)"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution=dict(_ok_pct, fill_window="尾盘窗占位(字符串)")),
         "fill_window 非结构化 {start,end}"),
        (dict(_base, pap_schema_version=2, analysis_type="strategy",
              strategy_execution=dict(_ok_pct, fill_window={"start": "14:55", "end": "14:55"})),
         "fill_window start==end 非严格窗口"),
    ):
        try:
            validate_pap(bad_pap)
            raise SystemExit(f"修法#1 自检: 应 raise 未 raise({why})")
        except ValueError:
            pass
    print("pap 修法#1 层① 自检 OK:纯事件/两白名单放行;缺schema/缺analysis_type/缺execution/"
          "禁组合/缺必填/白名单外/反向时间窗口/自由文本时间/非结构窗口(窄补) 全拒")
