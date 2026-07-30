"""exp16 yearend_strength driver：冻结选择规则 → recon / 正式事件研究。

当前行为单元只授权 ``--recon-only``；正式manifest、收益运行与persist须另令。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import namedtuple

from taosha.compute.yearend_strength_rules import build_windows, select_yearend_events
from taosha.reader.contract import EventRow


PAP_DIGEST = "3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345"
SOURCE_ANCHOR_SNAPSHOT_ID = 74
MARKET_BATCH_ID = 88
EVENT_LAYER = "yearend_strength"
REFERENCE_EVENTS = 7_751
REFERENCE_SELECTION_SHA = "057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7"
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "st_policy", "strata_enabled", "verdict_policy",
})


def engine_kwargs_from_pap(pap: dict) -> dict:
    """逐字消费exp16自己的8键参数；τ0同日是冻结文本的确定性适配常量。"""
    ep = pap.get("engine_params")
    got = set(ep) if isinstance(ep, dict) else set()
    if not isinstance(ep, dict) or got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params键集不符(缺={sorted(ENGINE_PARAM_KEYS-got)} "
            f"多={sorted(got-ENGINE_PARAM_KEYS)})")
    if ep["postpone_policy"] != "missing_bar_only" or ep["st_policy"] != "keep":
        raise SystemExit("fail-closed: exp16 postpone_policy/st_policy冻结值不符")
    if "τ0=event_date当日" not in str(pap.get("event_def", "")):
        raise SystemExit("fail-closed: event_def未明确τ0=event_date当日")
    if "已裁τ0=event_date当日" not in str(pap.get("cleaning", "")):
        raise SystemExit("fail-closed: cleaning未明确τ0=event_date当日")
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


def event_rows(selection: dict, batch: str) -> list[EventRow]:
    return [
        EventRow(
            ts_code=event["ts_code"],
            event_id=f"s16:{event['event_date']}:{event['ts_code']}",
            first_ann_date=dt.date.fromisoformat(event["event_date"]),
            event_type_layer=EVENT_LAYER,
            snapshot_batch=batch,
        )
        for event in selection["events"]
    ]


def assert_reference(selection: dict) -> None:
    got_n = selection["counters"]["final_events"]
    got_sha = selection["selection_sha256"]
    if got_n != REFERENCE_EVENTS or got_sha != REFERENCE_SELECTION_SHA:
        raise SystemExit(
            "fail-closed: snapshot74/market88冻结前参考不符"
            f"(events={got_n}/{REFERENCE_EVENTS},sha={got_sha}/{REFERENCE_SELECTION_SHA})")


def selection_audit(selection: dict) -> dict:
    counters = selection["counters"]
    panel_identity = counters.get("panel_any", 0) == (
        counters.get("panel_full_11", 0)
        + counters.get("panel_partial_rejected", 0)
        + counters.get("nonpositive_close_rejected", 0)
    )
    anchor_identity = counters.get("final_events", 0) == (
        selection["event_bar_present"] + selection["event_bar_missing"])
    yearly_identity = counters.get("final_events", 0) == sum(
        selection["events_yearly"].values())
    if not panel_identity or not anchor_identity or not yearly_identity:
        raise SystemExit(
            "fail-closed: exp16选择漏斗恒等式不成立"
            f"(panel={panel_identity},anchor={anchor_identity},yearly={yearly_identity})")
    return {
        "not_for_verdict": True,
        "counters": counters,
        "events_yearly": selection["events_yearly"],
        "selection_sha256": selection["selection_sha256"],
        "panel_identity_ok": panel_identity,
        "anchor_identity_ok": anchor_identity,
        "yearly_identity_ok": yearly_identity,
        "event_bar_present": selection["event_bar_present"],
        "event_bar_missing": selection["event_bar_missing"],
        "reference_reconciliation": {
            "reference_snapshot_id": SOURCE_ANCHOR_SNAPSHOT_ID,
            "reference_market_batch": MARKET_BATCH_ID,
            "reference_events": REFERENCE_EVENTS,
            "reference_selection_sha256": REFERENCE_SELECTION_SHA,
            "got_events": counters.get("final_events"),
            "got_selection_sha256": selection["selection_sha256"],
            "exact_match": (counters.get("final_events") == REFERENCE_EVENTS
                            and selection["selection_sha256"] == REFERENCE_SELECTION_SHA),
        },
    }


def execution_limit_audit(result: dict) -> dict:
    """复用runner既有τ轴删失事实，零新统计路径。"""
    rows = ((result.get("censor_diagnostic") or {}).get("all") or {}).get(
        "by_tau_censor") or []
    tau0 = rows[0] if rows else {}
    denominator = tau0.get("n", 0) or 0
    counts = {key: tau0.get(key, 0) or 0
              for key in ("one_word", "limit_up", "limit_down", "suspend", "none")}
    return {
        "not_for_verdict": True,
        "denominator_n_valid": denominator,
        **{f"tau0_{key}": value for key, value in counts.items()},
        "tau0_one_word_ratio": (counts["one_word"] / denominator) if denominator else None,
        "note": "τ0涨跌停/一字板仅为价格观察与执行限制审计，不控制CAR取样、不改判决。",
    }


def _connect(dsn: str, snapshot_id: int):
    import psycopg

    conn = psycopg.connect(dsn)
    conn.execute("SET default_transaction_read_only=on")
    conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                 (str(snapshot_id),))
    return conn


def _market_returns(tconn, panel_dates: set[dt.date], market_batch_id: int | None):
    """recon显式钉batch88；正式路径只走manifest路由视图。"""
    if market_batch_id is None:
        query = (
            "SELECT trade_date,ret_eqw FROM market_return_snap "
            "WHERE trade_date=ANY(%s) ORDER BY trade_date")
        params = (sorted(panel_dates),)
    else:
        query = (
            "SELECT trade_date,ret_eqw FROM market_eqw_return "
            "WHERE batch_id=%s AND trade_date=ANY(%s) ORDER BY trade_date")
        params = (market_batch_id, sorted(panel_dates))
    return {day: value for day, value in tconn.execute(query, params)}


def _selection(snapshot_id: int, market_batch_id: int | None = None) -> tuple[dict, dict]:
    """钉批日历/价格/市场收益最小列面 → 冻结选择规则。"""
    from taosha.reader.view import _ENV_QBASE, _ENV_TAOSHA, _resolve_dsn

    qdsn, tdsn = _resolve_dsn(_ENV_QBASE), _resolve_dsn(_ENV_TAOSHA)
    if not qdsn or not tdsn:
        raise SystemExit(f"缺 {_ENV_QBASE}/{_ENV_TAOSHA}")
    qconn, tconn = _connect(qdsn, snapshot_id), _connect(tdsn, snapshot_id)
    try:
        manifest = tconn.execute(
            "SELECT content,digest FROM study_snapshot WHERE snapshot_id=%s", (snapshot_id,)
        ).fetchone()
        if manifest is None:
            raise SystemExit(f"StudySnapshot {snapshot_id}不存在")
        content, digest = manifest
        calendar = [row[0] for row in qconn.execute(
            "SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")]
        windows = build_windows(calendar)
        panel_dates = {day for window in windows.values()
                       for day in (window["base_date"], *window["last10"])}
        event_dates = {window["event_date"] for window in windows.values()}
        market_returns = _market_returns(tconn, panel_dates, market_batch_id)

        Row = namedtuple("YearendRow", "ts_code trade_date close")
        price_rows = []
        with qconn.cursor(name="s16_selection_prices") as cur:
            cur.itersize = 100_000
            cur.execute(
                "SELECT ts_code,trade_date,close FROM explore_reader_prices_snap "
                "WHERE trade_date=ANY(%s) ORDER BY ts_code,trade_date", (sorted(panel_dates),))
            price_rows.extend(Row(*values) for values in cur)
        selection = select_yearend_events(price_rows, market_returns, windows)

        event_bar_keys = set()
        with qconn.cursor(name="s16_event_bar_keys") as cur:
            cur.itersize = 100_000
            cur.execute(
                "SELECT ts_code,trade_date FROM explore_reader_prices_snap "
                "WHERE trade_date=ANY(%s) ORDER BY ts_code,trade_date", (sorted(event_dates),))
            event_bar_keys.update(cur)
        selected_keys = {(event["ts_code"], dt.date.fromisoformat(event["event_date"]))
                         for event in selection["events"]}
        selection["event_bar_present"] = len(selected_keys & event_bar_keys)
        selection["event_bar_missing"] = len(selected_keys - event_bar_keys)
        return selection, {"snapshot_id": snapshot_id, "digest": digest, "content": content}
    finally:
        qconn.close()
        tconn.close()


def _load_frozen(exp_id: int, digest_assert: str):
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    row = ledger.get(exp_id)
    if row is None or row["status"] != "frozen":
        status = None if row is None else row["status"]
        raise SystemExit(f"铁律③:status={status}≠frozen(exp_id={exp_id})")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    digest = canonical_pap_sha256(pap)
    if digest != digest_assert or digest != PAP_DIGEST:
        raise SystemExit(f"fail-closed:PAP digest不符(db={digest}/arg={digest_assert})")
    return row, pap, digest, engine_kwargs_from_pap(pap)


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

    row, pap, digest, kwargs = _load_frozen(args.exp_id, args.pap_sha256_assert)
    if args.recon_only:
        if args.recon_snapshot_id != SOURCE_ANCHOR_SNAPSHOT_ID:
            raise SystemExit("recon只允许source snapshot74")
        selection, snapshot_info = _selection(
            args.recon_snapshot_id, market_batch_id=MARKET_BATCH_ID)
        assert_reference(selection)
        payload = {"mode": "recon_only", "pap_sha256": digest,
                   "source_snapshot": snapshot_info, "selection_audit": selection_audit(selection)}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
        _write(args.json, payload)
        return

    if args.snapshot_id is None:
        raise SystemExit("正式运行须显式给exp16自有--snapshot-id")
    if args.snapshot_id == SOURCE_ANCHOR_SNAPSHOT_ID:
        raise SystemExit("fail-closed:snapshot74仅为recon锚,不得冒充exp16正式manifest")
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    selection, snapshot_info = _selection(args.snapshot_id)
    events = event_rows(selection, f"study_snapshot:{args.snapshot_id}")
    reader = ViewReader(snapshot_id=args.snapshot_id, sample={event.ts_code for event in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=args.pap_sha256_assert, **kwargs)
    result["per_tau"]["tau_axis"] = (
        "τ=0:=event_date当日首个真实bar价格观察日(exp16冻结口径)")
    audit = selection_audit(selection)
    audit["execution_limit_audit"] = execution_limit_audit(result)
    result["audit"]["study_snapshot"] = snapshot_info
    result["audit"]["yearend_strength_selection"] = audit
    rendered = report.render(result)
    print("\n" + rendered)
    _write(args.json, result)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(rendered)


if __name__ == "__main__":
    main()
