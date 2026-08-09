"""exp14 实际高送转除权专属报告片段。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    snapshot = audit.get("study_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("snapshot_id") is None \
            or not snapshot.get("digest"):
        raise SystemExit("report fail-closed: exp14缺真实StudySnapshot锚")
    identity = audit.get("experiment_identity")
    required = ("exp_id", "family", "family_trial", "source_type", "verdict_power")
    if not isinstance(identity, dict) or any(identity.get(key) is None for key in required):
        raise SystemExit("report fail-closed: exp14报告缺台账实验身份水印")
    if identity["source_type"] != "llm" or identity["verdict_power"] != "prescreen":
        raise SystemExit("report fail-closed: exp14报告身份非llm/prescreen")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp14 实际高送转除权·事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp{identity['exp_id']} family={identity['family']} "
        f"trial={identity['family_trial']} source={identity['source_type']} "
        f"power={identity['verdict_power']}",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters = selection.get("counters") or {}
    identities = selection.get("identities") or {}
    execution = selection.get("execution_limit_audit")
    factor = selection.get("factor_mechanism_audit")
    raw = selection.get("raw_price_mechanical_audit")
    if not identities or not all(identities.values()):
        raise SystemExit("report fail-closed: exp14选择漏斗恒等式不成立")
    if not isinstance(execution, dict):
        raise SystemExit("report fail-closed: exp14缺execution_limit_audit")
    if not isinstance(factor, dict) or not isinstance(raw, dict):
        raise SystemExit("report fail-closed: exp14缺结构化因子/raw机械审计")
    reference = selection.get("reference_reconciliation") or {}
    return [
        "【exp14 A1/B1/C1/D1事件生成漏斗】 [NOT_FOR_VERDICT]",
        f"  研究期实施行={counters.get('implementation_rows')} →方案组="
        f"{counters.get('implementation_groups')} →B1合格={counters.get('group_qualified')} "
        f"(多行NULL={counters.get('group_multi_null')}/冲突="
        f"{counters.get('group_multi_conflict')}) →Decimal阈值="
        f"{counters.get('threshold_groups')} →事件键={counters.get('pre_factor_candidates')}",
        f"  A1因子门:变化={counters.get('factor_factor_changed')} 静态="
        f"{counters.get('factor_factor_static')} 缺失/无效="
        f"{sum(counters.get('factor_' + key, 0) or 0 for key in ('calendar_missing','current_missing','previous_missing','factor_invalid'))} "
        f"→最终={counters.get('final_events')}；恰等0.5="
        f"{counters.get('final_exact_boundary')}；selection SHA="
        f"{selection.get('selection_sha256')}",
        f"  逐年={selection.get('events_yearly')}；监管粗分="
        f"{selection.get('regulatory_composition')}（非精确法律制度分层）",
        f"  snapshot375冻结前参考 exact_match={reference.get('exact_match')}；"
        "仅同锚行为参考，不是正式运行硬断言。",
        f"  因子比(前一SSE开市日→除权日): n={factor.get('events')} min="
        f"{factor.get('ratio_min')} mean={factor.get('ratio_mean')} max={factor.get('ratio_max')}；"
        f"主CAR={raw.get('main_car_price')}、raw进入CAR={raw.get('raw_price_enters_car')}。",
        "  因子机械审计、raw除权跳空与监管组成均为NFV，不产生收益层、额外verdict或拆alpha。",
        "【exp14 τ0执行限制审计】 [NOT_FOR_VERDICT]",
        f"  分母={execution.get('denominator_n_valid')} 一字板="
        f"{execution.get('tau0_one_word')} 涨停={execution.get('tau0_limit_up')} "
        f"跌停={execution.get('tau0_limit_down')} 停牌/缺bar="
        f"{execution.get('tau0_suspend')} 普通={execution.get('tau0_none')}",
        "  τ0=ex_date当日真实bar价格观察；涨跌停价格观察不得表述为可成交收益或策略证据。",
        "",
    ]
