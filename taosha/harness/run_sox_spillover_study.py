"""exp24 SOX spillover driver：recon 与正式运行共用同一 L2 规则。

本行为单元只授权 --recon-only；正式 manifest、收益运行与 persist 均须另令。
"""
from __future__ import annotations

import argparse
import json

from taosha.compute.sox_spillover_rules import select_events
from taosha.reader.contract import EventRow

SOURCE_ANCHOR_SNAPSHOT_ID = 247
PAP_DIGEST = "be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27"
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "direction_display", "direction_signed_main",
    "effect_alignment_source", "nfv_structured", "note", "postpone_policy", "st_policy",
    "strata_enabled", "verdict_policy",
})
SIGNED_AR_KEYS = frozenset({"application_level", "estimand", "formula", "single_verdict"})
REFERENCE = {
    "input_sox_rows": 3395, "triggers": 314, "trigger_up": 161, "trigger_down": 153,
    "mapped_dates": 301, "collision_dates": 9, "collision_triggers_dropped": 22,
    "surviving_trigger_dates": 292, "surviving_up": 150, "surviving_down": 142,
}


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 engine_params/signed_ar 全键消费；exp24 两个适配常量无运行时选择。"""
    ep = pap.get("engine_params")
    if not isinstance(ep, dict) or set(ep) != set(ENGINE_PARAM_KEYS):
        got = set(ep) if isinstance(ep, dict) else set()
        raise SystemExit(f"fail-closed: engine_params 键集不符(缺={sorted(ENGINE_PARAM_KEYS-got)} "
                         f"多={sorted(got-ENGINE_PARAM_KEYS)})")
    signed = pap.get("signed_ar")
    if not isinstance(signed, dict) or set(signed) != set(SIGNED_AR_KEYS):
        raise SystemExit("fail-closed: signed_ar 缺失或键集不符")
    if ep["postpone_policy"] != "missing_bar_only":
        raise SystemExit("fail-closed: exp24 postpone_policy 必须为 missing_bar_only")
    cleaning = str(pap.get("cleaning", ""))
    if "τ0=event_date当日" not in cleaning or "自event_date起" not in cleaning:
        raise SystemExit("fail-closed: 冻结 PAP 未明确 exp24 τ0=event_date 当日")
    if "up=+1/down=−1" not in str(pap.get("event_def", "")):
        raise SystemExit("fail-closed: 冻结 PAP 未明确 direction 白名单与符号")
    return {
        "benchmark_mode": ep["benchmark_mode"],
        "strata_enabled": ep["strata_enabled"],
        "st_policy": ep["st_policy"],
        "verdict_policy": ep["verdict_policy"],
        "nfv_structured": ep["nfv_structured"],
        "postpone_policy": ep["postpone_policy"],
        "diagnostic_dims": tuple(ep["diagnostic_dims"]),
        "direction_signed_main": ep["direction_signed_main"],
        "direction_display": ep["direction_display"],
        "effect_alignment_source": ep["effect_alignment_source"],
        "tau0_on_anchor": True,
        "direction_layers": ("up", "down"),
    }


def event_rows(selection: dict, batch: str) -> list[EventRow]:
    return [
        EventRow(ts_code=e["ts_code"], event_id=f"s24:{e['event_date']}:{e['ts_code']}",
                 first_ann_date=e["event_date"], event_type_layer=e["direction"],
                 snapshot_batch=batch)
        for e in selection["events"]
    ]


def assert_reference(selection: dict) -> None:
    counters = selection["counters"]
    mismatches = {k: {"expected": expected, "got": counters.get(k)}
                  for k, expected in REFERENCE.items() if counters.get(k) != expected}
    if mismatches or not selection["funnel_identity_ok"]:
        raise SystemExit(f"fail-closed: SOX冻结参考漏斗不符:{mismatches};"
                         f"identity={selection['funnel_identity_ok']}")


def selection_audit(selection: dict, pap: dict) -> dict:
    counters = selection["counters"]
    return {
        "not_for_verdict": True,
        "counters": counters,
        "funnel_identity_ok": selection["funnel_identity_ok"],
        "trigger_yearly": selection["trigger_yearly"],
        "holiday_collisions": selection["collision_items"],
        "member_rejects": selection["member_rejects"],
        "duplicate_items": selection["duplicate_items"],
        "pool_members_by_event_date": selection["pool_members_by_event_date"],
        "trigger_event_dates": counters["surviving_trigger_dates"],
        "data_quality_disclosure": pap["diagnostic_dimensions"]["data_quality_disclosure"],
        "note": "事件几何与数据质量审计，全部NOT_FOR_VERDICT；不拆分α、不改变顶层判决。",
    }


def _selection(snapshot_id: int, pap: dict):
    from taosha.reader.sox_spillover import SoxSpilloverReader
    from taosha.reader.view import ViewReader

    source = SoxSpilloverReader(snapshot_id)
    base = ViewReader(snapshot_id=snapshot_id)
    selection = select_events(source.sox_rows(), source.member_rows(),
                              [r.trade_date for r in base.calendar()])
    assert_reference(selection)
    return selection, base.snapshot_info


def _write_recon(path: str | None, pap: dict, selection: dict, snapshot_info: dict) -> None:
    audit = selection_audit(selection, pap)
    print(f"[recon-only] source_snapshot={snapshot_info['snapshot_id']} "
          f"digest={snapshot_info['digest']}")
    print(f"SOX漏斗={json.dumps(audit['counters'], ensure_ascii=False, default=str)}")
    print(f"正式A股展开事件参考={audit['counters']['final_events']} "
          f"(触发事件日={audit['trigger_event_dates']})")
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"mode": "recon_only", "pap_sha256": PAP_DIGEST,
                       "source_snapshot": snapshot_info, "selection_audit": audit},
                      fh, ensure_ascii=False, indent=2, default=str)


def _run_formal(args, pap: dict, kwargs: dict, selection: dict, snapshot_info: dict) -> None:
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    if args.snapshot_id == SOURCE_ANCHOR_SNAPSHOT_ID:
        raise SystemExit("fail-closed: snapshot247仅为源级锚,不得冒充exp24研究manifest")
    qvec = (snapshot_info.get("content") or {}).get("qbase") or {}
    if qvec.get("sox_daily") != 13 or qvec.get("sw_member") != 14:
        raise SystemExit(f"fail-closed: exp24研究manifest数据向量不符:{qvec}")
    events = event_rows(selection, f"study_snapshot:{args.snapshot_id}")
    reader = ViewReader(snapshot_id=args.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=args.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["sox_spillover_selection"] = selection_audit(selection, pap)
    rendered = report.render(result)
    print("\n" + rendered)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(rendered)


def main() -> None:
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int)
    ap.add_argument("--recon-only", action="store_true")
    ap.add_argument("--pap-sha256-assert", required=True)
    ap.add_argument("--json")
    ap.add_argument("--report")
    args = ap.parse_args()
    row = ledger.get(args.exp_id)
    if row is None or row["status"] != "frozen":
        raise SystemExit(f"铁律③:exp{args.exp_id}须为frozen")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    digest = canonical_pap_sha256(pap)
    if digest != args.pap_sha256_assert or digest != PAP_DIGEST:
        raise SystemExit(f"fail-closed:PAP digest不符(db={digest}/arg={args.pap_sha256_assert})")
    kwargs = engine_kwargs_from_pap(pap)
    snapshot_id = args.snapshot_id or SOURCE_ANCHOR_SNAPSHOT_ID
    selection, snapshot_info = _selection(snapshot_id, pap)
    if args.recon_only:
        _write_recon(args.json, pap, selection, snapshot_info)
        return
    if args.snapshot_id is None:
        raise SystemExit("正式运行须显式给exp24自有--snapshot-id")
    _run_formal(args, pap, kwargs, selection, snapshot_info)


if __name__ == "__main__":
    main()
