"""exp568 ST/风险警示实施专属报告片段。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    snapshot = audit.get("study_snapshot")
    if (not isinstance(snapshot, dict) or snapshot.get("snapshot_id") is None
            or not snapshot.get("digest")):
        raise SystemExit(
            "report fail-closed: audit.st_imposition_selection 在场但缺真实 "
            "audit.study_snapshot.snapshot_id/digest")
    identity = audit.get("experiment_identity")
    if not isinstance(identity, dict):
        raise SystemExit("report fail-closed: exp568报告缺台账实验身份水印")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp568 ST/风险警示实施·事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp568 family={identity.get('family')} trial={identity.get('family_trial')} "
        f"α={audit.get('family_alpha')} source={identity.get('source_type')} "
        f"power={identity.get('verdict_power')}",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters = selection.get("counters") or {}
    composition = selection.get("composition_audit") or {}
    reference = selection.get("reference_reconciliation") or {}
    return [
        "【exp568 事件生成漏斗(冻结规则;组成审计全部 NOT_FOR_VERDICT)】",
        f"  入库行={counters.get('input_rows')}(start缺失={counters.get('start_missing_rows')}) "
        f"段={counters.get('segments')} 有前段转换={counters.get('transitions_with_prev')} "
        f"普通→ST候选={counters.get('imposition_candidates')}",
        f"  fail-closed/剔除逐档: 状态不可判={counters.get('state_unjudgeable_fail_closed')} "
        f"锚缺失={counters.get('anchor_missing')} "
        f"锚冲突={counters.get('anchor_conflict_fail_closed')} "
        f"ann>start={counters.get('ann_after_start_fail_closed')} "
        f"研究期外={counters.get('out_of_period')} "
        f"事件键重复剔除={counters.get('event_key_duplicate_fail_closed')}",
        f"  最终事件集={counters.get('final_events')} 恒等式="
        f"{'OK' if selection.get('funnel_identity_ok') else '⚠不成立(fail-closed复核)'}",
        f"  组成审计 [NOT_FOR_VERDICT]: 带星ST={composition.get('starred_events')} "
        f"不带星ST={composition.get('plain_st_events')} "
        f"恒等式={'OK' if composition.get('identity_ok') else '⚠不成立(fail-closed复核)'};"
        "仅数量/比例/逐年分布,不计算分层CAR或显著性",
        f"  batch7参考对账(765仅参考非硬断言): {reference.get('summary', '(见result_json)')}",
        "",
    ]
