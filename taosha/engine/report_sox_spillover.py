"""exp24 专属报告片段；保持通用 report.py 只留小型路由钩子。"""
from __future__ import annotations


def header_lines(audit: dict) -> list[str]:
    ss = audit.get("study_snapshot")
    if not isinstance(ss, dict) or ss.get("snapshot_id") is None or not ss.get("digest"):
        raise SystemExit("report fail-closed: exp24缺真实StudySnapshot锚")
    return [
        "═══ 淘沙 · 事件研究体检报告(exp24 SOX半导体链同向溢出·signed事件版)═══",
        f"快照批次: StudySnapshot={ss['snapshot_id']} digest={ss['digest']}"
        f"  |  基准口径: {audit['benchmark_mode']}(口径②)",
    ]


def selection_lines(selection: dict) -> list[str]:
    counters = selection.get("counters") or {}
    if selection.get("trigger_event_dates") != counters.get("surviving_trigger_dates"):
        raise SystemExit("report fail-closed: exp24触发事件日计数锚不一致")
    return [
        "【exp24 SOX触发与成员展开漏斗】 [NOT_FOR_VERDICT]",
        f"  SOX行={counters.get('input_sox_rows')} → ±3%触发={counters.get('triggers')}"
        f"(up={counters.get('trigger_up')}/down={counters.get('trigger_down')};"
        f"边界恰等={counters.get('exact_boundary')}) → 映射日={counters.get('mapped_dates')}",
        f"  D4碰撞={counters.get('collision_dates')}日/剔{counters.get('collision_triggers_dropped')}触发"
        f" → 存活触发事件日={counters.get('surviving_trigger_dates')}"
        f"(up={counters.get('surviving_up')}/down={counters.get('surviving_down')})",
        f"  池展开候选={counters.get('expanded_candidates')} "
        f"重复键={counters.get('duplicate_event_keys')}组/剔{counters.get('duplicate_events_dropped')} "
        f"→ 主事件集={counters.get('final_events')};恒等式="
        f"{'OK' if selection.get('funnel_identity_ok') else 'FAIL'}",
        "  低功效边界:正式result同时报告触发事件日数、ρ̄与N_eff；不因此调阈值或改判。",
        f"  数据质量披露:{selection.get('data_quality_disclosure')}",
        "",
    ]
