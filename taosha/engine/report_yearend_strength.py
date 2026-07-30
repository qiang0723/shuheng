"""exp16 年末相对强势专属报告片段。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    snapshot = audit.get("study_snapshot")
    if (not isinstance(snapshot, dict) or snapshot.get("snapshot_id") is None
            or not snapshot.get("digest")):
        raise SystemExit(
            "report fail-closed: audit.yearend_strength_selection在场但缺真实"
            "audit.study_snapshot.snapshot_id/digest")
    identity = audit.get("experiment_identity")
    required = ("exp_id", "family", "family_trial", "source_type", "verdict_power")
    if not isinstance(identity, dict) or any(identity.get(key) is None for key in required):
        raise SystemExit("report fail-closed: exp16报告缺台账实验身份水印")
    if identity["source_type"] != "llm" or identity["verdict_power"] != "prescreen":
        raise SystemExit("report fail-closed: exp16报告身份非llm/prescreen")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp16 年末相对强势·事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp{identity['exp_id']} family={identity['family']} "
        f"trial={identity['family_trial']} source={identity['source_type']} "
        f"power={identity['verdict_power']}",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters = selection.get("counters") or {}
    execution = selection.get("execution_limit_audit")
    if not isinstance(execution, dict):
        raise SystemExit("report fail-closed: exp16缺execution_limit_audit")
    reference = selection.get("reference_reconciliation") or {}
    return [
        "【exp16 事件生成漏斗(冻结规则;年度严格11-bar面板)】",
        f"  选择面板={counters.get('panel_any')} = 完整11-bar={counters.get('panel_full_11')} "
        f"+ 缺bar拒={counters.get('panel_partial_rejected')} "
        f"+ 非正close拒={counters.get('nonpositive_close_rejected')}；恒等式="
        f"{'OK' if selection.get('panel_identity_ok') else '⚠不成立(fail-closed复核)'}",
        f"  相对财富跑赢≥5%事件={counters.get('final_events')} "
        f"证券={counters.get('final_securities')} 事件日={counters.get('event_dates')} "
        f"重复键组={counters.get('event_key_duplicate_groups')} "
        f"selection SHA={selection.get('selection_sha256')}",
        f"  事件锚当日bar:在场={selection.get('event_bar_present')} "
        f"缺失={selection.get('event_bar_missing')}；锚恒等式="
        f"{'OK' if selection.get('anchor_identity_ok') else '⚠不成立'}；"
        f"逐年恒等式={'OK' if selection.get('yearly_identity_ok') else '⚠不成立'}；"
        "逐年分布见result_json "
        "[NOT_FOR_VERDICT]",
        f"  snapshot74/market88参考对账: events={reference.get('got_events')} "
        f"exact_match={reference.get('exact_match')}；仅冻结前对账参考 "
        "[NOT_FOR_VERDICT]",
        "【exp16 τ0执行限制审计】 [NOT_FOR_VERDICT]",
        f"  分母={execution.get('denominator_n_valid')} "
        f"一字板={execution.get('tau0_one_word')} "
        f"涨停={execution.get('tau0_limit_up')} 跌停={execution.get('tau0_limit_down')} "
        f"停牌/缺bar={execution.get('tau0_suspend')} "
        f"普通={execution.get('tau0_none')}",
        "  τ0为事件当日首个真实bar价格观察；涨跌停价格观察不等于可成交收益或策略证据。",
        "",
    ]
