"""exp568 ST/风险警示实施事件研究 driver。

本 driver 只做名称事件选择、冻结参数消费、引擎调用及审计装配；不写台账。
``--recon-only`` 只读 namechange current 视图，正式模式必须使用 exp568 自有
StudySnapshot。family_trial=2 只从冻结台账身份注入，PAP 与 CLI 均不能覆盖。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

from taosha.compute.st_imposition_rules import (
    composition_identity_ok,
    funnel_identity_ok,
    merge_selections,
    select_st_imposition_events,
)
from taosha.harness.run_st_removal_study import (
    ENGINE_PARAM_KEYS,
    engine_kwargs_from_pap,
    recon_namechange_rows_currentview,
)
from taosha.reader.contract import EventRow

EXP_ID = 568
FAMILY = "delist_warning_financial"
FAMILY_TRIAL = 2
EVENT_LAYER = "st_imposition"
PAP_DIGEST = "56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58"

REFERENCE_BATCH7 = {
    "input_rows": 18_868,
    "segments": 17_133,
    "transitions_with_prev": 11_601,
    "imposition_candidates": 1_277,
    "state_unjudgeable_fail_closed": 1,
    "anchor_missing": 510,
    "anchor_conflict_fail_closed": 0,
    "ann_after_start_fail_closed": 0,
    "out_of_period": 1,
    "event_key_duplicate_fail_closed": 0,
    "final_events": 765,
    "starred_events": 560,
    "plain_st_events": 205,
}


def events_from_namechange(rows: list[dict], batch: str) -> tuple[list[EventRow], dict]:
    rows = sorted(rows, key=lambda row: (
        row["ts_code"], row["start_date"] or dt.date.min,
        str(row["alias"]), row["ann_date"] or dt.date.min))
    per_security: list[dict] = []
    current_ts: str | None = None
    buffer: list[dict] = []
    for row in rows:
        if row["ts_code"] != current_ts:
            if buffer:
                per_security.append(select_st_imposition_events(current_ts, buffer))
            current_ts, buffer = row["ts_code"], []
        buffer.append(row)
    if buffer:
        per_security.append(select_st_imposition_events(current_ts, buffer))

    selection = merge_selections(per_security)
    events = [
        EventRow(
            ts_code=event["ts_code"],
            event_id=f"{event['ts_code']}:{event['ann_date'].replace('-', '')}",
            first_ann_date=dt.date.fromisoformat(event["ann_date"]),
            event_type_layer=EVENT_LAYER,
            snapshot_batch=batch,
        )
        for event in selection["events"]
    ]
    return events, selection


def _yearly(events: list[dict], *, variant: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        if variant is not None and event["st_variant"] != variant:
            continue
        year = event["ann_date"][:4]
        counts[year] = counts.get(year, 0) + 1
    return counts


def reference_reconciliation(selection: dict) -> dict:
    counters = selection["counters"]
    deltas = {key: counters.get(key, 0) - value
              for key, value in REFERENCE_BATCH7.items()}
    return {
        "reference": REFERENCE_BATCH7,
        "layer_deltas": deltas,
        "summary": (
            f"最终事件集 {counters.get('final_events')}"
            f"(参考765,Δ={deltas['final_events']});"
            f"带星 {counters.get('starred_events')}"
            f"(参考560,Δ={deltas['starred_events']});"
            f"不带星 {counters.get('plain_st_events')}"
            f"(参考205,Δ={deltas['plain_st_events']});"
            "batch7参考数非正式硬断言,批次变化停下报人"
        ),
    }


def selection_audit(selection: dict) -> dict:
    counters = selection["counters"]
    if not funnel_identity_ok(counters) or not composition_identity_ok(counters):
        raise SystemExit("fail-closed: exp568事件漏斗或组成恒等式不成立")
    itemized: dict[str, list[dict]] = {}
    for rejected in selection["rejects"]:
        itemized.setdefault(rejected["reason"], []).append(rejected)
    final_n = counters["final_events"]
    composition = {
        "not_for_verdict": True,
        "starred_events": counters["starred_events"],
        "plain_st_events": counters["plain_st_events"],
        "starred_ratio": counters["starred_events"] / final_n if final_n else None,
        "plain_st_ratio": counters["plain_st_events"] / final_n if final_n else None,
        "starred_yearly": _yearly(selection["events"], variant="starred"),
        "plain_st_yearly": _yearly(selection["events"], variant="plain_st"),
        "identity_ok": composition_identity_ok(counters),
        "note": "名称组成代理只报数量/比例/逐年分布,不计算分层CAR、显著性或verdict",
    }
    return {
        "counters": counters,
        "funnel_identity_ok": funnel_identity_ok(counters),
        "reject_reasons": selection["reject_reasons"],
        "itemized_rejects": itemized,
        "events_yearly": _yearly(selection["events"]),
        "composition_audit": composition,
        "reference_reconciliation": reference_reconciliation(selection),
    }


def _load_frozen(exp_id: int, expected_digest: str) -> tuple[dict, dict, dict]:
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    if exp_id != EXP_ID:
        raise SystemExit(f"本driver仅允许 exp_id={EXP_ID},实收={exp_id}")
    row = ledger.get(exp_id)
    if row is None or row["status"] != "frozen":
        raise SystemExit(f"铁律③:exp{exp_id}须为frozen")
    if row["family"] != FAMILY or int(row["family_trial"]) != FAMILY_TRIAL:
        raise SystemExit("fail-closed: exp568 family/trial 与冻结身份不符")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    digest = canonical_pap_sha256(pap)
    if digest != expected_digest or digest != PAP_DIGEST:
        raise SystemExit(f"fail-closed: PAP digest={digest}与冻结令不符")
    return row, pap, engine_kwargs_from_pap(pap)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", type=int, default=EXP_ID)
    parser.add_argument("--snapshot-id", type=int)
    parser.add_argument("--pap-sha256-assert", required=True)
    parser.add_argument("--recon-only", action="store_true")
    parser.add_argument("--json")
    parser.add_argument("--report")
    args = parser.parse_args()

    row, pap, engine_kwargs = _load_frozen(args.exp_id, args.pap_sha256_assert)
    print(f"exp568 {row['family']}/trial{row['family_trial']} frozen; "
          f"PAP={PAP_DIGEST};engine_keys={sorted(ENGINE_PARAM_KEYS)}", flush=True)

    if args.recon_only:
        rows = recon_namechange_rows_currentview()
        events, selection = events_from_namechange(rows, "recon_currentview")
        audit = selection_audit(selection)
        output = {
            "mode": "recon_only",
            "batches": sorted({str(row["snapshot_batch"]) for row in rows}),
            "pap_sha256": PAP_DIGEST,
            "selection_audit": audit,
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, default=str))
        if args.json:
            with open(args.json, "w") as handle:
                json.dump(output, handle, ensure_ascii=False, indent=2,
                          sort_keys=True, default=str)
        print(f"EventRow={len(events)};未读收益、未调用引擎", flush=True)
        return

    if args.snapshot_id is None:
        raise SystemExit("正式运行须提供exp568自有 --snapshot-id")

    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    manifest_reader = ViewReader(snapshot_id=args.snapshot_id)
    events, selection = events_from_namechange(
        manifest_reader.namechange_rows(), f"study_snapshot:{args.snapshot_id}")
    reader = ViewReader(snapshot_id=args.snapshot_id,
                        sample={event.ts_code for event in events})
    result = runner.run_study(
        reader, pap, events=events,
        pap_sha256_assert=args.pap_sha256_assert, **engine_kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["experiment_identity"] = {
        "exp_id": EXP_ID,
        "family": row["family"],
        "family_trial": row["family_trial"],
        "source_type": row["source_type"],
        "verdict_power": row["verdict_power"],
    }
    result["audit"]["st_imposition_selection"] = selection_audit(selection)
    rendered = report.render(result)
    print(rendered)
    if args.json:
        with open(args.json, "w") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, default=str)
    if args.report:
        with open(args.report, "w") as handle:
            handle.write(rendered)


if __name__ == "__main__":
    main()
