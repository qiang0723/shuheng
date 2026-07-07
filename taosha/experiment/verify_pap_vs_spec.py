"""切片1 终验:pap_json ↔ spec §6 冻结原文 逐字核对(独立第二转录 vs 库实物)。

SPEC6 = 从 taosha-spec-v0.2-frozen.md §6 表逐字转录的 event_def/window(独立于 seed)。
逐行比库里 pap_json 的对应字段,输出 MATCH / DIFF(附首个不同位置)。diff 全 MATCH=零偏差。
drawdown_rebuy 的 #2 与 #2b 均以 §6 #2 原文为准(#2b 事件定义/进出场逐字继承)。
"""
from __future__ import annotations

from . import ledger

# ── §6 冻结原文(逐字转录,event_def / window)────────────────────────────────
SPEC6 = {
    "radar_heat": dict(
        event_def="heat_signal 升温标记(沿雷达A7口径)",
        window="A7口径"),
    "drawdown_rebuy": dict(
        event_def="雷达股池(PIT)内收盘自60日高点回撤≥10%后,站上10日线且连续3日不破=进场;"
                  "破20日线=失效。策略版离场:成本−20%强平或收盘破20日线,先到先出",
        window="事件版20/60日;策略版按离场"),
    "holder_sell": dict(
        event_def="减持计划首次预披露公告(巨潮自建采集,announcementTime 为时间戳金标准),"
                  "减持比例≥总股本1%;2024新规前历史样本用当时口径首次公告日。"
                  "stk_holdertrade 仅作实施结果辅助表(按 ts_code+ann_date 聚合,"
                  "无公告ID局限入 pap_json)",
        window="后5/20/60日"),
    "forecast_drift": dict(
        event_def="业绩预告,valid_time=first_ann_date(非ann_date);"
                  "修正公告(ann_date≠first_ann_date)不进本假设;分预喜/预亏/扭亏三层",
        window="T+1起,后20/60日"),
    "rv_resonance": dict(
        event_def="观象节点日度 resonance 进全池当日分布前10%",
        window="卡面horizon_days"),
}


def _first_diff(a: str, b: str) -> str:
    if a == b:
        return ""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return f"@{i}: spec={a[i-2:i+3]!r} vs db={b[i-2:i+3]!r}"
    return f"长度差 spec={len(a)} db={len(b)}"


def main():
    rows = ledger.list_all()
    all_match = True
    # 取 pap_json 全文
    conn = ledger.connect()
    paps = {}
    try:
        import psycopg
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT exp_id, family, pap_json FROM experiment ORDER BY exp_id")
            for r in cur.fetchall():
                paps[r["exp_id"]] = (r["family"], r["pap_json"])
    finally:
        conn.close()

    print(f"{'exp':<4}{'family':<16}{'字段':<11}{'核对'}")
    for exp_id, (family, pap) in paps.items():
        spec = SPEC6[family]
        for field in ("event_def", "window"):
            db_val = pap.get(field)
            sp_val = spec[field]
            ok = db_val == sp_val
            all_match = all_match and ok
            tag = "✅MATCH" if ok else f"❌DIFF {_first_diff(sp_val, str(db_val))}"
            print(f"{exp_id:<4}{family:<16}{field:<11}{tag}")
    print("\n==== " + ("逐字核对: diff 归零(全 MATCH)" if all_match
                        else "存在 DIFF,见上") + " ====")
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
