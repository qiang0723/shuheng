"""exp14 ex_div_gap driver：冻结规则 recon 与正式运行共用同一路径。"""
from __future__ import annotations

import argparse
import json

from taosha.compute.ex_div_gap_rules import (
    finalize_events, prepare_events, required_factor_keys,
)
from taosha.reader.contract import EventRow
from taosha.reader.ex_div_gap import ExDivGapReader


PAP_DIGEST = "a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7"
SOURCE_SNAPSHOT_ID = 375
EXPECTED_BATCHES = {"dividend": 17, "adj_factor": 7, "trade_cal": 10}
EXPECTED_VIEW_BATCHES = {"dividend": "batch17", "factor": "batch7"}
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "st_policy", "strata_enabled", "verdict_policy",
})
REFERENCE = {
    "final_events": 4_035,
    "final_exact_boundary": 1_083,
    "selection_sha256": "ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f",
}
EVENT_LAYER = "ex_div_gap"


def engine_kwargs_from_pap(pap: dict) -> dict:
    ep = pap.get("engine_params")
    got = set(ep) if isinstance(ep, dict) else set()
    if not isinstance(ep, dict) or got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params键集不符(缺={sorted(ENGINE_PARAM_KEYS-got)} "
            f"多={sorted(got-ENGINE_PARAM_KEYS)})")
    if ep["postpone_policy"] != "missing_bar_only" or ep["st_policy"] != "keep":
        raise SystemExit("fail-closed: exp14 postpone_policy/st_policy冻结值不符")
    text_checks = {
        "event_def": "τ0=ex_date当日",
        "cleaning": "τ0=ex_date当日",
        "window": "τ0=ex_date当日",
    }
    missing = [key for key, phrase in text_checks.items() if phrase not in str(pap.get(key, ""))]
    if missing:
        raise SystemExit(f"fail-closed: exp14同日τ0冻结文本缺失:{missing}")
    if "signed_ar" in pap:
        raise SystemExit("fail-closed: exp14单事件集不得出现signed_ar")
    return {
        "benchmark_mode": ep["benchmark_mode"],
        "diagnostic_dims": tuple(ep["diagnostic_dims"]),
        "nfv_structured": ep["nfv_structured"],
        "postpone_policy": ep["postpone_policy"],
        "st_policy": ep["st_policy"],
        "strata_enabled": ep["strata_enabled"],
        "verdict_policy": ep["verdict_policy"],
        "tau0_on_anchor": True,
    }


def attach_experiment_identity(result: dict, row) -> dict:
    audit = result.get("audit")
    if not isinstance(audit, dict) or "experiment_identity" in audit:
        raise SystemExit("fail-closed: exp14身份水印缺审计容器或试图覆盖")
    identity = {key: row[key] for key in
                ("exp_id", "family", "family_trial", "source_type", "verdict_power")}
    expected = {"exp_id": 14, "family": "ex_div_gap", "family_trial": 1,
                "source_type": "llm", "verdict_power": "prescreen"}
    if identity != expected:
        raise SystemExit(f"fail-closed: exp14台账身份不符:{identity}")
    audit["experiment_identity"] = identity
    return identity


def event_rows(selection: dict, batch: str) -> list[EventRow]:
    return [EventRow(ts_code=row["ts_code"],
                     event_id=f"s14:{row['ex_date']}:{row['ts_code']}",
                     first_ann_date=row["ex_date"], event_type_layer=EVENT_LAYER,
                     snapshot_batch=batch) for row in selection["events"]]


def assert_formal_snapshot(snapshot_id: int) -> None:
    if snapshot_id == SOURCE_SNAPSHOT_ID:
        raise SystemExit("fail-closed:snapshot375仅为源级锚,不得冒充exp14研究manifest")


def _assert_snapshot(info: dict, snapshot_id: int = SOURCE_SNAPSHOT_ID) -> None:
    qbase = (info.get("content") or {}).get("qbase") or {}
    mismatches = {key: {"expected": value, "got": qbase.get(key)}
                  for key, value in EXPECTED_BATCHES.items() if qbase.get(key) != value}
    if info.get("snapshot_id") != snapshot_id or mismatches:
        raise SystemExit(f"fail-closed: exp14 snapshot{snapshot_id}向量不符:{mismatches}")


def _run_mode(snapshot_id: int, mode: str) -> dict:
    reader = ExDivGapReader(snapshot_id, mode)
    if reader.read_only_status() != "on":
        raise SystemExit(f"fail-closed: exp14 {mode}连接不是transaction_read_only=on")
    info = reader.snapshot_info
    _assert_snapshot(info, snapshot_id)
    source_batches = reader.source_batches()
    if source_batches != EXPECTED_VIEW_BATCHES:
        raise SystemExit(f"fail-closed: exp14 {mode}视图批次不符:{source_batches}")
    dividend, calendar = reader.dividend_rows(), reader.calendar_dates()
    prepared = prepare_events(dividend)
    factor_keys = required_factor_keys(prepared, calendar)
    factors = reader.factor_rows(factor_keys)
    selection = finalize_events(prepared, factors, calendar)
    return {"source_snapshot": info, "source_batches": source_batches,
            "input": {"dividend_rows": len(dividend), "calendar_dates": len(calendar),
                      "factor_keys_requested": len(factor_keys),
                      "factor_rows_returned": len(factors)},
            "selection": selection}


def _assert_equal(current: dict, snapshot: dict) -> None:
    if current["source_batches"] != snapshot["source_batches"]:
        raise SystemExit("fail-closed: exp14 current与snapshot375视图批次不一致")
    left = json.dumps(current["selection"], ensure_ascii=False, sort_keys=True, default=str)
    right = json.dumps(snapshot["selection"], ensure_ascii=False, sort_keys=True, default=str)
    if left != right:
        raise SystemExit("fail-closed: exp14 current与snapshot375选择不一致")


def assert_reference(selection: dict) -> None:
    counters = selection["counters"]
    got = {"final_events": counters.get("final_events"),
           "final_exact_boundary": counters.get("final_exact_boundary"),
           "selection_sha256": selection.get("selection_sha256")}
    if got != REFERENCE or not selection.get("identities") \
            or not all(selection["identities"].values()):
        raise SystemExit(f"fail-closed: exp14冻结前参考不符:{got}")


def selection_audit(selection: dict) -> dict:
    return {"not_for_verdict": True, "counters": selection["counters"],
            "identities": selection["identities"],
            "events_yearly": selection["events_yearly"],
            "regulatory_composition": selection["regulatory_composition"],
            "factor_mechanism_audit": selection["factor_mechanism_audit"],
            "raw_price_mechanical_audit": {
                "not_for_verdict": True,
                "main_car_price": "adjusted_total_return_close",
                "raw_price_enters_car": False,
                "equivalent_factor_ratio": selection["factor_mechanism_audit"],
            },
            "selection_sha256": selection["selection_sha256"],
            "reference_reconciliation": {
                "reference_snapshot_id": SOURCE_SNAPSHOT_ID, **REFERENCE,
                "got_events": selection["counters"].get("final_events"),
                "got_exact_boundary": selection["counters"].get("final_exact_boundary"),
                "got_selection_sha256": selection["selection_sha256"],
                "exact_match": (selection["counters"].get("final_events") ==
                                REFERENCE["final_events"] and
                                selection["counters"].get("final_exact_boundary") ==
                                REFERENCE["final_exact_boundary"] and
                                selection["selection_sha256"] == REFERENCE["selection_sha256"]),
            }}


def execution_limit_audit(result: dict) -> dict:
    rows = ((result.get("censor_diagnostic") or {}).get("all") or {}).get(
        "by_tau_censor") or []
    tau0 = rows[0] if rows else {}
    if rows and tau0.get("tau") != 0:
        raise SystemExit("fail-closed: exp14执行限制审计首行不是tau0")
    denominator = tau0.get("n", 0) or 0
    counts = {key: tau0.get(key, 0) or 0
              for key in ("one_word", "limit_up", "limit_down", "suspend", "none")}
    return {"not_for_verdict": True, "denominator_n_valid": denominator,
            **{f"tau0_{key}": value for key, value in counts.items()},
            "tau0_one_word_ratio": ((counts["one_word"] / denominator)
                                    if denominator else None)}


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


def _run_recon(args) -> None:
    if args.recon_snapshot_id != SOURCE_SNAPSHOT_ID:
        raise SystemExit("recon只允许source snapshot375")
    current = _run_mode(SOURCE_SNAPSHOT_ID, "current")
    snapshot = _run_mode(SOURCE_SNAPSHOT_ID, "snapshot")
    _assert_equal(current, snapshot)
    assert_reference(snapshot["selection"])
    payload = {"mode": "recon_only", "pap_sha256": PAP_DIGEST,
               "current_snapshot_exact_match": True,
               "source_snapshot": snapshot["source_snapshot"],
               "selection_audit": selection_audit(snapshot["selection"])}
    _write(args.json, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))


def _run_formal(args, row, pap: dict, kwargs: dict) -> None:
    if args.snapshot_id is None:
        raise SystemExit("正式运行须显式给exp14自有--snapshot-id")
    assert_formal_snapshot(args.snapshot_id)
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    selected = _run_mode(args.snapshot_id, "snapshot")
    selection = selected["selection"]
    assert_reference(selection)
    events = event_rows(selection, f"study_snapshot:{args.snapshot_id}")
    reader = ViewReader(snapshot_id=args.snapshot_id, sample={event.ts_code for event in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=args.pap_sha256_assert, **kwargs)
    result["per_tau"]["tau_axis"] = "τ=0:=ex_date当日首个真实bar价格观察日(exp14冻结口径)"
    audit = selection_audit(selection)
    audit["execution_limit_audit"] = execution_limit_audit(result)
    result["audit"]["study_snapshot"] = selected["source_snapshot"]
    attach_experiment_identity(result, row)
    result["audit"]["ex_div_gap_selection"] = audit
    rendered = report.render(result)
    _write(args.json, result)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    print("\n" + rendered)


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
        _run_recon(args)
    else:
        _run_formal(args, row, pap, kwargs)


if __name__ == "__main__":
    main()
