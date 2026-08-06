"""exp19 专属报告片段；通用 report.py 只保留显式路由。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    snapshot = audit.get("study_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("snapshot_id") is None \
            or not snapshot.get("digest"):
        raise SystemExit("report fail-closed: exp19缺真实StudySnapshot锚")
    identity = audit.get("experiment_identity")
    required = ("exp_id", "family", "family_trial", "source_type", "verdict_power")
    if not isinstance(identity, dict) or any(identity.get(key) is None for key in required):
        raise SystemExit("report fail-closed: exp19报告缺台账实验身份水印")
    if identity["source_type"] != "llm" or identity["verdict_power"] != "prescreen":
        raise SystemExit("report fail-closed: exp19报告身份非llm/prescreen")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp19 年度分红预案大幅变动·signed事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp{identity['exp_id']} family={identity['family']} "
        f"trial={identity['family_trial']} source={identity['source_type']} "
        f"power={identity['verdict_power']}",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters, identities = selection.get("counters") or {}, selection.get("identities") or {}
    if not identities or not all(identities.values()):
        raise SystemExit("report fail-closed: exp19选择漏斗恒等式不成立")
    full = counters.get("full_period_classification") or {}
    study = counters.get("research_classification") or {}
    return [
        "【exp19 A1/B2-P1/C1/D1/E1事件生成漏斗】 [NOT_FOR_VERDICT]",
        f"  输入={counters.get('input_rows')} →年度行={counters.get('annual_scope_rows')}"
        f"/组={counters.get('annual_scope_groups')} →E1严格初始="
        f"{counters.get('qualified_initial_groups')}；无初始="
        f"{counters.get('initial_missing_groups')} 多行/冲突="
        f"{(counters.get('initial_multiple_identical_groups') or 0) + (counters.get('initial_multiple_conflict_groups') or 0)} "
        f"必需字段无效={counters.get('initial_required_invalid_groups')}",
        f"  全期A1/C1/D1互斥分类={full}；恰等±50%="
        f"{counters.get('full_period_exact_boundary')}；后续阶段回填命中="
        f"{counters.get('implementation_backfill_hits')}",
        f"  B2-P1分类={study}；恰等±50%={counters.get('research_exact_boundary')} "
        f"→候选={counters.get('directed_group_rows')}",
        f"  事件键重复组={counters.get('event_key_duplicate_groups')} "
        f"方向冲突组={counters.get('direction_conflict_groups')} →最终signed事件="
        f"{counters.get('final_events')}(up={counters.get('final_up')}/down="
        f"{counters.get('final_down')}); selection SHA={selection.get('selection_sha256')}",
        "  direction轴、全期/B2-P1漏斗与边界只作结构化审计；顶层仅合并signed事件集产生一个verdict。",
        "",
    ]
