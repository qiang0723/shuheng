"""exp10 专属报告片段；通用 ``report.py`` 只保留路由。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    """渲染带真实 StudySnapshot 锚的 exp10 报告头。"""
    snapshot = audit.get("study_snapshot")
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("snapshot_id") is None
        or not snapshot.get("digest")
    ):
        raise SystemExit(
            "report fail-closed: audit.volume_drought_selection 在场但缺真实 "
            "audit.study_snapshot.snapshot_id/digest"
        )
    identity = audit.get("experiment_identity")
    required = ("exp_id", "family", "family_trial", "source_type", "verdict_power")
    if not isinstance(identity, dict) or any(identity.get(key) is None for key in required):
        raise SystemExit("report fail-closed: exp10报告缺台账实验身份水印")
    if identity["source_type"] != "llm" or identity["verdict_power"] != "prescreen":
        raise SystemExit("report fail-closed: exp10报告身份非llm/prescreen")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp10 成交额干涸后首次放量收阳·事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp{identity['exp_id']} family={identity['family']} "
        f"trial={identity['family_trial']} source={identity['source_type']} "
        f"power={identity['verdict_power']}",
    ]


def selection_lines(selection: dict) -> list[str]:
    """渲染冻结事件漏斗及非判决审计段。"""
    counters = selection.get("counters") or {}
    terminal = selection.get("breakout_terminal_audit") or {}
    reconciliation = selection.get("reference_reconciliation") or {}
    return [
        "【exp10 事件生成漏斗(L2 冻结规则;首次放量终局)】",
        f"  视图输入={counters.get('view_rows')} "
        f"日历外={counters.get('calendar_outside_rows')} "
        f"异常bar={counters.get('invalid_real_bar_rows')} "
        f"有效扫描={counters.get('eligible_real_rows')} "
        f"股票={counters.get('stocks')}",
        f"  armed阶段={counters.get('armed_segments')} "
        f"→ 事件={counters.get('events_all_periods')} "
        f"非收阳拒绝={counters.get('breakout_not_positive_all_periods')} "
        f"日历缺bar打断={counters.get('armed_gap_breaks')} "
        f"异常bar打断={counters.get('armed_invalid_breaks')} "
        f"右删失={counters.get('right_censored_armed')} 恒等式="
        f"{'OK' if selection.get('armed_terminal_identity_ok') else '⚠不成立(fail-closed 复核)'}",
        f"  首次放量终局={counters.get('first_breakout_terminals')} "
        f"恒等式={'OK' if selection.get('breakout_terminal_identity_ok') else '⚠不成立'}; "
        f"pre2011={counters.get('events_pre2011')} "
        f"最终事件={counters.get('events_study')} "
        f"事件键重复={counters.get('event_key_uniqueness_violations')} "
        f"selection SHA={selection.get('selection_sha256')}",
        f"  非收阳终局审计: 首次放量={terminal.get('first_breakout_total')} / "
        f"收阳入事件={terminal.get('positive_events')} / "
        f"非收阳拒绝={terminal.get('not_positive_rejected')}。"
        "仅报告事件几何计数,不得读取或展示其后收益。 [NOT_FOR_VERDICT]",
        "  τ0 口径: 事件后首个有真实bar的价格观察日(missing_bar_only;仅缺bar顺延"
        "≤5个交易所交易日,第6日剔);不得表述为可执行策略证据。",
        f"  冻结前参考对账: 事件={reconciliation.get('got_final_events')} "
        f"exact_match={reconciliation.get('exact_match')} [NOT_FOR_VERDICT]",
        "",
    ]
