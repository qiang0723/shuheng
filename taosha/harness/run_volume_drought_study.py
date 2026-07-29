"""exp10 volume_drought_break driver：冻结事件生成 → recon / 正式事件研究。

当前授权仅允许 --recon-only；正式 manifest、收益读取与运行须另令。
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
from collections import namedtuple

from taosha.compute.volume_drought_rules import (
    finalize_events, merge_selections, select_volume_drought_events,
)
from taosha.reader.contract import EventRow


ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "strata_enabled", "verdict_policy",
})
EVENT_LAYER = "volume_drought_break"
REFERENCE_FINAL_EVENTS = 13_889
REFERENCE_SELECTION_SHA = "3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9"
REFERENCE_BATCH_VECTOR = "daily=6/trade_cal=10"
RECON_ANCHOR_SNAPSHOT_IDS = frozenset({248})


def engine_kwargs_from_pap(pap: dict) -> dict:
    ep = pap.get("engine_params")
    if not isinstance(ep, dict):
        raise SystemExit("fail-closed: 冻结 PAP 缺 engine_params 或非对象")
    got = set(ep)
    if got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            "fail-closed: engine_params 键集与冻结件不符"
            f"(缺={sorted(set(ENGINE_PARAM_KEYS) - got)} 多={sorted(got - set(ENGINE_PARAM_KEYS))})"
        )
    return {
        "benchmark_mode": ep["benchmark_mode"],
        "diagnostic_dims": tuple(ep["diagnostic_dims"]),
        "nfv_structured": ep["nfv_structured"],
        "postpone_policy": ep["postpone_policy"],
        "strata_enabled": ep["strata_enabled"],
        "verdict_policy": ep["verdict_policy"],
    }


def events_from_volume_rows(volume_rows, cal_index: dict, batch: str):
    """钉批成交额行流 → 纯规则 → EventRow；日历外 bar 只计数后剔除。"""
    per_security = []
    base = {"view_rows": 0, "calendar_outside_rows": 0, "stocks": 0}
    for ts_code, group in itertools.groupby(volume_rows, key=lambda row: row.ts_code):
        rows, seen_dates = [], set()
        for row in group:
            base["view_rows"] += 1
            if row.trade_date in seen_dates:
                raise SystemExit(f"fail-closed: {ts_code} {row.trade_date} 重复 raw bar")
            seen_dates.add(row.trade_date)
            rank = cal_index.get(row.trade_date)
            if rank is None:
                base["calendar_outside_rows"] += 1
                continue
            rows.append({"trade_date": row.trade_date, "cal_rank": rank,
                         "open": row.open, "close": row.close, "amount": row.amount})
        if rows:
            base["stocks"] += 1
            per_security.append(select_volume_drought_events(ts_code, rows))
    selection = finalize_events(merge_selections(per_security, base))
    events = [
        EventRow(ts_code=e["ts_code"],
                 event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                 first_ann_date=dt.date.fromisoformat(e["event_date"]),
                 event_type_layer=EVENT_LAYER, snapshot_batch=batch)
        for e in selection["events"]
    ]
    return events, selection


def selection_audit(selection: dict) -> dict:
    counters = selection["counters"]
    final = selection["events"]
    terminal_rejects = [r for r in selection["rejects"]
                        if r.get("reason") == "first_breakout_not_positive"]
    event_years, reject_years, event_days = {}, {}, {}
    for row in final:
        year = row["event_date"][:4]
        event_years[year] = event_years.get(year, 0) + 1
        event_days[row["event_date"]] = event_days.get(row["event_date"], 0) + 1
    for row in terminal_rejects:
        year = row["trade_date"][:4]
        reject_years[year] = reject_years.get(year, 0) + 1

    armed_terminal = (
        counters.get("events_all_periods", 0)
        + counters.get("breakout_not_positive_all_periods", 0)
        + counters.get("armed_gap_breaks", 0)
        + counters.get("armed_invalid_breaks", 0)
        + counters.get("right_censored_armed", 0)
    )
    return {
        "counters": counters,
        "reject_reasons": selection["reject_reasons"],
        "selection_sha256": selection["selection_sha256"],
        "armed_terminal_identity_ok": counters.get("armed_segments", 0) == armed_terminal,
        "breakout_terminal_identity_ok": (
            counters.get("first_breakout_terminals", 0)
            == counters.get("events_all_periods", 0)
            + counters.get("breakout_not_positive_all_periods", 0)
        ),
        "event_period_identity_ok": (
            counters.get("events_all_periods", 0)
            == counters.get("events_pre2011", 0) + counters.get("events_post", 0)
            + counters.get("events_study", 0)
            + counters.get("uniqueness_dropped_events", 0)
        ),
        "events_yearly": dict(sorted(event_years.items())),
        "rejected_terminal_yearly": dict(sorted(reject_years.items())),
        "shared_days_ge2": sum(value >= 2 for value in event_days.values()),
        "per_day_top10": sorted(event_days.items(), key=lambda item: (-item[1], item[0]))[:10],
        "breakout_terminal_audit": {
            "not_for_verdict": True,
            "first_breakout_total": counters.get("first_breakout_terminals", 0),
            "positive_events": counters.get("events_all_periods", 0),
            "not_positive_rejected": counters.get("breakout_not_positive_all_periods", 0),
            "note": "非收阳终局仅报告几何计数；不读取或展示其后收益，不形成第二判决",
        },
        "reference_reconciliation": {
            "reference_batch_vector": REFERENCE_BATCH_VECTOR,
            "reference_final_events": REFERENCE_FINAL_EVENTS,
            "reference_selection_sha256": REFERENCE_SELECTION_SHA,
            "got_final_events": len(final),
            "got_selection_sha256": selection["selection_sha256"],
            "exact_match": (len(final) == REFERENCE_FINAL_EVENTS
                            and selection["selection_sha256"] == REFERENCE_SELECTION_SHA),
        },
    }


def _volume_rows_snap(snapshot_id: int):
    import psycopg
    from taosha.reader.view import _ENV_QBASE, _resolve_dsn

    dsn = _resolve_dsn(_ENV_QBASE)
    if not dsn:
        raise SystemExit(f"缺 {_ENV_QBASE}(显式参数、环境变量或.env)")
    conn = psycopg.connect(dsn)
    conn.execute("SET default_transaction_read_only=on")
    conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                 (str(snapshot_id),))
    calendar = [row[0] for row in conn.execute(
        "SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")]
    cal_index = {day: idx + 1 for idx, day in enumerate(calendar)}
    Row = namedtuple("VolumeRow", "ts_code trade_date open close amount snapshot_batch")

    def rows():
        with conn.cursor(name="s10_volume_rows") as cur:
            cur.itersize = 200_000
            cur.execute(
                "SELECT ts_code,trade_date,open,close,amount,snapshot_batch "
                "FROM explore_reader_volume_drought_snap ORDER BY ts_code,trade_date"
            )
            for values in cur:
                yield Row(*values)
    return conn, rows, cal_index


def _load_frozen(exp_id: int, digest_assert: str):
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    row = ledger.get(exp_id)
    if row is None or row["status"] != "frozen":
        status = None if row is None else row["status"]
        raise SystemExit(f"铁律③: status={status}≠frozen(exp_id={exp_id})")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    recalculated = canonical_pap_sha256(pap)
    if recalculated != digest_assert:
        raise SystemExit(f"fail-closed: PAP canonical={recalculated}≠断言={digest_assert}")
    return row, pap, recalculated, engine_kwargs_from_pap(pap)


def _generate(snapshot_id: int):
    conn, rows, cal_index = _volume_rows_snap(snapshot_id)
    try:
        return events_from_volume_rows(rows(), cal_index, f"study_snapshot:{snapshot_id}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", type=int, required=True)
    parser.add_argument("--snapshot-id", type=int)
    parser.add_argument("--recon-snapshot-id", type=int)
    parser.add_argument("--pap-sha256-assert", required=True)
    parser.add_argument("--recon-only", action="store_true")
    parser.add_argument("--json")
    parser.add_argument("--report")
    args = parser.parse_args()

    row, pap, digest, kwargs = _load_frozen(args.exp_id, args.pap_sha256_assert)
    print(f"exp_id={args.exp_id} {row['family']}/{row['title']} status=frozen")
    print(f"pap canonical digest={digest}; engine_params={kwargs}")

    if args.recon_only:
        if args.recon_snapshot_id not in RECON_ANCHOR_SNAPSHOT_IDS:
            raise SystemExit(f"recon 只允许已核对锚 {sorted(RECON_ANCHOR_SNAPSHOT_IDS)}")
        events, selection = _generate(args.recon_snapshot_id)
        audit = selection_audit(selection)
        if not audit["reference_reconciliation"]["exact_match"]:
            raise SystemExit("fail-closed: daily6/trade_cal10 下事件数或 selection SHA 不等冻结参考")
        payload = {"mode": "recon_only", "pap_sha256": digest,
                   "selection_audit": audit}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2,
                          sort_keys=True, default=str)
                handle.write("\n")
        return

    if args.snapshot_id is None:
        raise SystemExit("正式运行须 --snapshot-id(exp10 自有研究 manifest；另令生成)")
    if args.snapshot_id in RECON_ANCHOR_SNAPSHOT_IDS:
        raise SystemExit("fail-closed: recon 锚不得冒充 exp10 正式 manifest")

    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    events, selection = _generate(args.snapshot_id)
    reader = ViewReader(snapshot_id=args.snapshot_id, sample={event.ts_code for event in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=args.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["volume_drought_selection"] = selection_audit(selection)
    rendered = report.render(result)
    print("\n" + rendered)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(rendered)


if __name__ == "__main__":
    main()
