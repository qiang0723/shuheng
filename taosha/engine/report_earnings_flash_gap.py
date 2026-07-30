"""exp17 专属报告片段；通用 report.py 只保留显式路由。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    snapshot = audit.get("study_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("snapshot_id") is None \
            or not snapshot.get("digest"):
        raise SystemExit("report fail-closed: exp17缺真实StudySnapshot锚")
    identity = audit.get("experiment_identity")
    required = ("exp_id", "family", "family_trial", "source_type", "verdict_power")
    if not isinstance(identity, dict) or any(identity.get(key) is None for key in required):
        raise SystemExit("report fail-closed: exp17报告缺台账实验身份水印")
    if identity["source_type"] != "llm" or identity["verdict_power"] != "prescreen":
        raise SystemExit("report fail-closed: exp17报告身份非llm/prescreen")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp17 业绩快报偏离预告·signed事件版)═══",
        f"快照批次: StudySnapshot={snapshot['snapshot_id']} digest={snapshot['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
        f"实验身份: exp{identity['exp_id']} family={identity['family']} "
        f"trial={identity['family_trial']} source={identity['source_type']} "
        f"power={identity['verdict_power']}",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters = selection.get("counters") or {}
    identities = selection.get("identities") or {}
    if not all(identities.values()):
        raise SystemExit("report fail-closed: exp17选择漏斗恒等式不成立")
    return [
        "【exp17 A1/B1/C1事件生成漏斗】 [NOT_FOR_VERDICT]",
        f"  express事实批参考={selection.get('raw_batch_rows_reference')} "
        f"视图输入={counters.get('input_express_rows')} "
        f"→报告期组={counters.get('report_groups')} "
        f"→B1剔除={counters.get('b1_rejected_groups')} "
        f"→B1存活={counters.get('b1_surviving_groups')}",
        f"  分类:孤儿={counters.get('orphan')} 无严格前置={counters.get('no_strict_prior')} "
        f"无完整区间={counters.get('no_complete_prior')} "
        f"A1最新日冲突={counters.get('forecast_conflict')} actual空={counters.get('actual_null')} "
        f"up={counters.get('up')} down={counters.get('down')} "
        f"inside={counters.get('inside')} boundary={counters.get('boundary')}",
        f"  事件键重复组={counters.get('event_key_duplicate_groups')} "
        f"方向冲突组={counters.get('direction_conflict_groups')} "
        f"→最终signed事件={counters.get('final_events')}"
        f"(up={counters.get('final_up')}/down={counters.get('final_down')}); "
        f"selection SHA={selection.get('selection_sha256')}",
        "  A1/B1/C1漏斗与direction轴只作结构化审计；顶层仅合并signed事件集产生一个verdict。",
        "",
    ]
