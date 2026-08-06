"""exp19 dividend_surprise driver：冻结规则 recon 与正式运行共用同一路径。"""
from __future__ import annotations

import argparse
import json

from taosha.compute.dividend_surprise_rules import select_events
from taosha.reader.contract import EventRow


PAP_DIGEST = "4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4"
SOURCE_ANCHOR_SNAPSHOT_ID = 375
RAW_BATCH_ROWS_REFERENCE = 177_873
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "direction_display", "direction_signed_main",
    "effect_alignment_source", "nfv_structured", "note", "postpone_policy", "st_policy",
    "strata_enabled", "verdict_policy",
})
SIGNED_AR_KEYS = frozenset({"application_level", "estimand", "formula", "single_verdict"})
REFERENCE = {
    "annual_scope_rows": 97_543, "annual_scope_groups": 52_027,
    "qualified_initial_groups": 26_467, "initial_missing_groups": 25_560,
    "full_period_classification": {
        "missing_prior": 2_451, "unresolvable_prior": 2_804,
        "zero_undefined": 6_501, "up": 2_679, "down": 3_436, "inside": 8_596,
    },
    "final_events": 5_055, "final_up": 2_253, "final_down": 2_802,
}


def engine_kwargs_from_pap(pap: dict) -> dict:
    ep = pap.get("engine_params")
    got = set(ep) if isinstance(ep, dict) else set()
    if not isinstance(ep, dict) or got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(f"fail-closed: engine_params键集不符(缺={sorted(ENGINE_PARAM_KEYS-got)} "
                         f"多={sorted(got-ENGINE_PARAM_KEYS)})")
    signed = pap.get("signed_ar")
    if not isinstance(signed, dict) or set(signed) != set(SIGNED_AR_KEYS):
        raise SystemExit("fail-closed: signed_ar缺失或键集不符")
    axes = ((pap.get("diagnostic_dimensions") or {}).get("axes") or {}).get("direction")
    if axes != ["up", "down"]:
        raise SystemExit("fail-closed: exp19方向白名单须唯一来自PAP axes.direction=[up,down]")
    if ep["postpone_policy"] != "unified_announcement" or ep["st_policy"] != "keep":
        raise SystemExit("fail-closed: exp19 postpone_policy/st_policy冻结值不符")
    return {
        "benchmark_mode": ep["benchmark_mode"],
        "diagnostic_dims": tuple(ep["diagnostic_dims"]),
        "direction_display": ep["direction_display"],
        "direction_signed_main": ep["direction_signed_main"],
        "effect_alignment_source": ep["effect_alignment_source"],
        "nfv_structured": ep["nfv_structured"],
        "postpone_policy": ep["postpone_policy"], "st_policy": ep["st_policy"],
        "strata_enabled": ep["strata_enabled"], "verdict_policy": ep["verdict_policy"],
    }


def attach_experiment_identity(result: dict, row) -> dict:
    audit = result.get("audit")
    if not isinstance(audit, dict) or "experiment_identity" in audit:
        raise SystemExit("fail-closed: exp19身份水印缺审计容器或试图覆盖")
    identity = {key: row[key] for key in
                ("exp_id", "family", "family_trial", "source_type", "verdict_power")}
    expected = {"exp_id": 19, "family": "dividend_surprise", "family_trial": 1,
                "source_type": "llm", "verdict_power": "prescreen"}
    if identity != expected:
        raise SystemExit(f"fail-closed: exp19台账身份不符:{identity}")
    audit["experiment_identity"] = identity
    return identity


def event_rows(selection: dict, batch: str) -> list[EventRow]:
    return [EventRow(ts_code=row["ts_code"],
                     event_id=f"s19:{row['event_date']}:{row['ts_code']}",
                     first_ann_date=row["event_date"], event_type_layer=row["direction"],
                     snapshot_batch=batch) for row in selection["events"]]


def assert_reference(selection: dict) -> None:
    counters = selection["counters"]
    mismatches = {key: {"expected": expected, "got": counters.get(key)}
                  for key, expected in REFERENCE.items() if counters.get(key) != expected}
    identities = selection.get("identities") or {}
    if mismatches or not identities or not all(identities.values()):
        raise SystemExit(f"fail-closed: exp19同锚参考不符:{mismatches};identity={identities}")
    if counters.get("implementation_backfill_hits") != 0:
        raise SystemExit("fail-closed: exp19禁止以实施/后续阶段值回填初始预案")


def assert_formal_snapshot(snapshot_id: int) -> None:
    if snapshot_id == SOURCE_ANCHOR_SNAPSHOT_ID:
        raise SystemExit("fail-closed:snapshot375仅为源级锚,不得冒充exp19研究manifest")


def selection_audit(selection: dict) -> dict:
    return {"not_for_verdict": True, "raw_batch_rows_reference": RAW_BATCH_ROWS_REFERENCE,
            "counters": selection["counters"],
            "classification_yearly": selection["classification_yearly"],
            "selection_sha256": selection["selection_sha256"],
            "identities": selection["identities"]}


def _selection(snapshot_id: int):
    from taosha.reader.dividend_surprise import DividendSurpriseReader

    reader = DividendSurpriseReader(snapshot_id)
    selection = select_events(reader.dividend_rows())
    assert_reference(selection)
    return selection, reader.snapshot_info


def _load_frozen(exp_id: int, digest_assert: str):
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    row = ledger.get(exp_id)
    if row is None or row["status"] != "frozen":
        raise SystemExit(f"铁律③:exp{exp_id}须为frozen")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    digest = canonical_pap_sha256(pap)
    if digest != digest_assert or digest != PAP_DIGEST:
        raise SystemExit(f"fail-closed:PAP digest不符(db={digest}/arg={digest_assert})")
    return row, pap, engine_kwargs_from_pap(pap)


def _write(path: str | None, payload: dict) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, default=str)
            handle.write("\n")


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

    row, pap, kwargs = _load_frozen(args.exp_id, args.pap_sha256_assert)
    if args.recon_only:
        if args.recon_snapshot_id != SOURCE_ANCHOR_SNAPSHOT_ID:
            raise SystemExit("recon只允许source snapshot375")
        selection, info = _selection(args.recon_snapshot_id)
        payload = {"mode": "recon_only", "pap_sha256": PAP_DIGEST,
                   "source_snapshot": info, "selection_audit": selection_audit(selection)}
        _write(args.json, payload)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
        return
    if args.snapshot_id is None:
        raise SystemExit("正式运行须显式给exp19自有--snapshot-id")
    assert_formal_snapshot(args.snapshot_id)

    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    selection, info = _selection(args.snapshot_id)
    qbase = (info.get("content") or {}).get("qbase") or {}
    if qbase.get("dividend") != 17:
        raise SystemExit(f"fail-closed: exp19研究manifest dividend批次不符:{qbase}")
    events = event_rows(selection, f"study_snapshot:{args.snapshot_id}")
    reader = ViewReader(snapshot_id=args.snapshot_id, sample={event.ts_code for event in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=args.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    attach_experiment_identity(result, row)
    result["audit"]["dividend_surprise_selection"] = selection_audit(selection)
    rendered = report.render(result)
    _write(args.json, result)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    print("\n" + rendered)


if __name__ == "__main__":
    main()
