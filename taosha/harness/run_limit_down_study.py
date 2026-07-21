"""驱动:对真实数据跑 exp13 limit_down_open(连续一字跌停开板)事件版 → 报告(冻结令 2026-07-21)。

令原文档 = taosha/docs/limit-down-open-freeze-order-2026-07-21.md(原文即口径):
  · engine_params **逐字消费冻结 PAP**(digest 583c4c94…0c42),driver 不保留任何运行时
    自由选择(键集不符=fail-closed);
  · 向引擎传 pap_sha256_assert(仅逐字断言;digest 唯一权威=引擎对实收 pap 重算);
  · --recon-only = 本单元唯一授权模式(Snapshot 121 同批次向量下逐层复现交付档既有漏斗,
    零收益读取、零 manifest 生成、零引擎调用);
  · 正式运行(另令)前 exp13 须另行生成自己的研究 manifest(PAP snapshot_batch_req):
    StudySnapshot 121 不得冒充 exp13 正式 manifest → 全量模式对 --snapshot-id 121 fail-closed。

数据流(镜像 exp8 run_limit_open_study 设计):
  台账已冻结 pap(铁律③)→ ViewReader(sample=listing 全A键集)prices 全宇宙流 →
  groupby 逐票 → limit_down_rules.select_limit_down_events(冻结纯函数,A 主漏斗+B 口径
  NFV 镜像)→ merge_selections → EventRow(layer=recent_listing|seasoned)→
  ViewReader(sample=事件票)→ runner.run_study(events=显式事件源)→ report.render。
**只算+出报告+可选 dump,不改 ledger**(persist 另令,台账结果槽不写)。

用法:
  set -a; . /opt/quant/.env; set +a
  # 本单元唯一授权模式(冻结令:Snapshot 121 同向量漏斗逐层复现):
  python -m taosha.harness.run_limit_down_study --exp-id 13 --recon-snapshot-id 121 \
      --pap-sha256-assert <digest> --recon-only [--json OUT]
  # 正式运行(另令;须 exp13 自己的研究 manifest):
  python -m taosha.harness.run_limit_down_study --exp-id 13 --snapshot-id N \
      --pap-sha256-assert <digest> [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json

from taosha.compute.limit_down_rules import (
    merge_selections, select_limit_down_events)
from taosha.reader.contract import EventRow

# 冻结 PAP engine_params 键集(冻结件逐字消费;缺键/多键=fail-closed,不许运行时补选)。
# note=PAP 内说明文字,非引擎参数,消费时校验在场但不传引擎。
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "st_mode", "st_policy", "strata_enabled", "verdict_policy"})

LAYER_RECENT = "recent_listing"
LAYER_SEASONED = "seasoned"
# 逐条入 audit 的剔除类(PAP reporting_commitments:重复映射、listing fail-closed 及
# reversal_hijack 剔除逐条入 audit;右删失∧hijack 正交标志逐条,补充令1)
ITEMIZED_REJECT_REASONS = (
    "duplicate_event_date_mapping", "listing_missing_fail_closed",
    "pre_listing_bar_fail_closed", "listing_window_anomaly_fail_closed",
    "reversal_hijack")

# PAP snapshot_batch_req(终版收口令二.3):StudySnapshot 121 仅冻结前只读对账锚,
# 不得冒充 exp13 正式 manifest → 全量模式 fail-closed 名单。
RECON_ANCHOR_SNAPSHOT_ID = 121


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 PAP engine_params → run_study 关键字参数(逐字消费,fail-closed)。

    键集与冻结件不符(缺/多)→ 拒;值原样透传零改写(diagnostic_dims list→tuple 系
    run_study 签名的容器形态要求,元素逐字不动,st 居首=令三.2)。"""
    ep = pap.get("engine_params")
    if not isinstance(ep, dict):
        raise SystemExit("fail-closed: 冻结 PAP 缺 engine_params 或非对象(冻结令:逐字消费)")
    got = set(ep)
    if got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params 键集与冻结件不符(缺={sorted(set(ENGINE_PARAM_KEYS) - got)} "
            f"多={sorted(got - set(ENGINE_PARAM_KEYS))});driver 不保留运行时自由选择")
    return {"benchmark_mode": ep["benchmark_mode"],
            "strata_enabled": ep["strata_enabled"],
            "st_mode": ep["st_mode"],
            "st_policy": ep["st_policy"],
            "verdict_policy": ep["verdict_policy"],
            "nfv_structured": ep["nfv_structured"],
            "postpone_policy": ep["postpone_policy"],
            "diagnostic_dims": tuple(ep["diagnostic_dims"])}


def rows_from_price_rows(price_rows) -> "itertools.groupby":
    """PriceRow 流 → (ts_code, rows dict 列表) 逐票迭代(纯函数;规则消费 5 键最小面)。"""
    for ts_code, grp in itertools.groupby(price_rows, key=lambda r: r.ts_code):
        yield ts_code, [{"trade_date": r.trade_date, "limit_status": r.limit_status,
                         "open_limit_status": r.open_limit_status,
                         "board": r.board, "is_st": r.is_st} for r in grp]


def events_from_prices(price_rows, listing: dict, batch: str,
                       cal_index: dict | None = None) -> tuple[list[EventRow], dict]:
    """全宇宙 prices 行流 → EventRow 显式事件源(纯函数,零 I/O)。

    price_rows: PriceRow 迭代器,(ts_code, trade_date) 升序(SQL ORDER BY 钉死;fixture=构造行)。
    listing: {ts_code: {list_date, delist_date, ...}}(缺=该票 fail-closed)。
    cal_index: {trade_date: 日历轴序号}(B 口径 NFV 镜像;None → 不产 b_control)。
    返回 (events, selection)——selection 全量留痕(counters/rejects/b_control)入 audit。
    层键=recent_listing|seasoned 二值(规则 recent_listing 布尔标记直译;白名单对账在 runner)。"""
    per_security = []
    for ts_code, rows in rows_from_price_rows(price_rows):
        per_security.append(select_limit_down_events(
            ts_code, rows, listing=listing.get(ts_code), cal_index=cal_index))
    sel = merge_selections(per_security)
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["event_date"]),
                       event_type_layer=(LAYER_RECENT if e["recent_listing"]
                                         else LAYER_SEASONED),
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def _funnel_block(counters: dict) -> dict:
    """主漏斗七档(令七.4 固定顺序)+ 总恒等校验(纯函数)。"""
    chains = counters.get("chains_total", 0)
    layers = {
        "原始最大链": chains,
        "right_censored_no_event_day": counters.get("right_censored_no_event_day", 0),
        "out_of_period_pre2007": counters.get("out_of_period_pre2007", 0),
        "out_of_period_post": counters.get("out_of_period_post", 0),
        "listing_anomaly": counters.get("listing_anomaly", 0),
        "duplicate_chains_dropped": counters.get("duplicate_chains_dropped", 0),
        "reversal_hijack": counters.get("reversal_hijack", 0),
        "final_main_events": counters.get("final_main_events", 0)}
    layers["identity_ok"] = chains == sum(v for k, v in layers.items() if k != "原始最大链")
    return layers


def selection_audit(sel: dict) -> dict:
    """selection → audit 块(纯函数;冻结 PAP reporting_commitments 转录):
    主漏斗七档计数+恒等式+明确分母 / 剔除逐年逐因分解 / 重复映射·listing·hijack 逐条 /
    hijack 审计块(数量占比年份链长顺延结构,全 NFV,零收益零 CAR)/ B 口径对照块
    (链数/事件数/碰撞链数/相对 A 双向集合差异,全 NFV)/ ST·recent 层恒等 / 链长·逐年·
    聚集分布。诊断块零判决字段(F12 攻击 fixture 验收面)。"""
    def year_of(item: dict) -> str:
        return (item.get("event_date") or item["chain_end_date"])[:4]

    c = sel["counters"]
    events = sel["events"]
    chain_len_dist: dict = {}
    yearly: dict = {}
    layer_counts = {LAYER_RECENT: 0, LAYER_SEASONED: 0}
    st_counts = {"ST": 0, "non_ST": 0}
    board_counts: dict = {}
    evday_status: dict = {}
    evday_open_status: dict = {}
    per_day: dict = {}
    st_mismatch_items = []
    for e in events:
        chain_len_dist[str(e["chain_len"])] = chain_len_dist.get(str(e["chain_len"]), 0) + 1
        yearly[year_of(e)] = yearly.get(year_of(e), 0) + 1
        layer_counts[LAYER_RECENT if e["recent_listing"] else LAYER_SEASONED] += 1
        st_counts["ST" if e["is_st_event"] else "non_ST"] += 1
        board_counts[e["board_event"]] = board_counts.get(e["board_event"], 0) + 1
        evday_status[e["evday_status"]] = evday_status.get(e["evday_status"], 0) + 1
        evday_open_status[e["evday_open_status"]] = \
            evday_open_status.get(e["evday_open_status"], 0) + 1
        per_day[e["event_date"]] = per_day.get(e["event_date"], 0) + 1
        if e.get("st_flag_chain_vs_eventday_diff"):
            st_mismatch_items.append(e)
    rejects_yearly_by_reason: dict = {}
    for r in sel["rejects"]:
        by_year = rejects_yearly_by_reason.setdefault(r["reason"], {})
        by_year[year_of(r)] = by_year.get(year_of(r), 0) + 1
    itemized = {reason: [r for r in sel["rejects"] if r["reason"] == reason]
                for reason in ITEMIZED_REJECT_REASONS}
    censored_hijack_flagged = [
        r for r in sel["rejects"]
        if r["reason"] == "right_censored_no_event_day"
        and r.get("reversal_hijack_observed_before_censoring")]

    hijack_items = itemized["reversal_hijack"]
    hijack_n = c.get("reversal_hijack", 0)
    final_n = c.get("final_main_events", 0)
    hijack_audit = {
        "not_for_verdict": True,
        "note": "令二:hijack 逐条事件几何审计;禁收益/CAR/显著性/独立结论;"
                "右删失∧hijack=互斥主原因+正交标志(补充令1)",
        "count": hijack_n,
        "share": {"numerator": hijack_n,
                  "denominator_surviving_candidates": hijack_n + final_n,
                  "ratio_surviving": (round(hijack_n / (hijack_n + final_n), 6)
                                      if hijack_n + final_n else None),
                  "denominator_raw_chains": c.get("chains_total", 0),
                  "ratio_raw_chains": (round(hijack_n / c["chains_total"], 6)
                                       if c.get("chains_total") else None)},
        "years": _count_by(hijack_items, lambda r: r["event_date"][:4]),
        "chain_len_dist": _count_by(hijack_items, lambda r: str(r["chain_len"])),
        "deferred_up_dist": _count_by(hijack_items, lambda r: str(r["deferred_up"])),
        "censored_with_hijack_flag_count": len(censored_hijack_flagged),
        "censored_with_hijack_flag": censored_hijack_flagged}

    b = sel.get("b_control")
    b_block = None
    if b is not None:
        a_set = {(e["ts_code"], e["event_date"]) for e in events}
        b_set = {(e["ts_code"], e["event_date"]) for e in b["events"]}
        b_block = {
            "not_for_verdict": True,
            "note": "令一.4:B口径(交易所日历连续)=固定NFV诊断对照,不改变主事件集",
            "funnel": _funnel_block(b["counters"]),
            "vs_a_main_events": {
                "n_a": len(a_set), "n_b": len(b_set),
                "n_only_a": len(a_set - b_set), "n_only_b": len(b_set - a_set),
                "only_a": sorted(map(list, a_set - b_set)),
                "only_b": sorted(map(list, b_set - a_set))}}

    return {"counters": c,
            "reject_reasons": sel["reject_reasons"],
            "funnel": _funnel_block(c),
            "rejects_yearly_by_reason": rejects_yearly_by_reason,
            "itemized_rejects": itemized,
            "chain_len_dist": chain_len_dist,
            "chain_len_dist_all_chains": _count_by(
                events + sel["rejects"], lambda r: str(r["chain_len"])),
            "events_yearly": yearly,
            "layer_counts": layer_counts,
            "st_axis": {"not_for_verdict": True,
                        "note": "令三.2:ST 首要 NFV 诊断轴;归层=事件日 PIT(令三.3)",
                        "counts": st_counts,
                        "identity_ok": st_counts["ST"] + st_counts["non_ST"] == final_n,
                        "chain_vs_eventday_diff_count":
                            c.get("st_flag_chain_vs_eventday_diff", 0),
                        "chain_vs_eventday_diff_items": st_mismatch_items},
            "board_counts": board_counts,
            "evday_status": evday_status,
            "evday_open_status": evday_open_status,
            "shared_days_ge2": sum(1 for v in per_day.values() if v >= 2),
            "per_day_top10": sorted(per_day.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
            "reversal_hijack_audit": hijack_audit,
            "b_axis_control": b_block}


def _count_by(items, key) -> dict:
    out: dict = {}
    for it in items:
        k = key(it)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _recon_flag_rows_and_calendar(snapshot_id: int):
    """对账模式取数(冻结令:Snapshot 121 同向量漏斗逐层复现;零收益读取):

    正式 ViewReader 语义逐字镜像 = 会话 GUC set_config('shuheng.study_snapshot_id') +
    explore_reader_prices_snap JOIN explore_reader_calendar_snap USING (trade_date),
    ORDER BY (ts_code, trade_date);SELECT 列表 **无任何价格/收益列**(仅事件几何 5 列+主键)。
    正式运行(另令)必须走 ViewReader.prices()(全列契约流),本函数不得用于正式跑。
    返回 (flag_rows 生成器封装列表, 日历轴列表, listing dict)。"""
    import os

    import psycopg

    from taosha.reader.view import _ENV_QBASE, _load_env
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dsn = _load_env(os.path.join(root, ".env")).get(_ENV_QBASE)
    if not dsn:
        raise SystemExit(f"缺 {_ENV_QBASE}(.env);对账需引擎只读 DSN")
    conn = psycopg.connect(dsn)
    conn.execute("SET default_transaction_read_only = on")
    conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                 (str(snapshot_id),))
    calendar = [d for (d,) in conn.execute(
        "SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")]
    listing = {}
    for ts, ld, dd in conn.execute(
            "SELECT ts_code, list_date, delist_date FROM explore_reader_listing_snap"):
        listing[ts] = {"list_date": ld, "delist_date": dd}

    from collections import namedtuple
    FlagRow = namedtuple("FlagRow",
                         "ts_code trade_date limit_status open_limit_status board is_st")

    def flag_rows():
        with conn.cursor(name="s13_recon_flags") as cur:
            cur.itersize = 200_000
            cur.execute(
                "SELECT p.ts_code, p.trade_date, p.limit_status, p.open_limit_status, "
                "       p.board, p.is_st "
                "FROM explore_reader_prices_snap p "
                "JOIN explore_reader_calendar_snap cal USING (trade_date) "
                "ORDER BY p.ts_code, p.trade_date")
            for ts, d, ls, ols, board, st in cur:
                yield FlagRow(ts, d, ls, ols, board, bool(st))
    return conn, flag_rows, calendar, listing


def main():
    # DB 依赖延迟导入:fixture(verify_limit_down_adapter)零 DB 消费上方纯函数
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, default=None,
                    help="正式运行 StudySnapshot manifest ID(硬化② fail-closed;"
                         "须 exp13 自己的研究 manifest,121 拒)")
    ap.add_argument("--recon-snapshot-id", type=int, default=None,
                    help="--recon-only 对账锚 snapshot(冻结令=121,仅只读对账)")
    ap.add_argument("--pap-sha256-assert", required=True,
                    help="冻结令绑定 digest(仅逐字断言;权威=引擎重算,不一致 fail-closed)")
    ap.add_argument("--recon-only", action="store_true",
                    help="冻结令授权模式:Snapshot 121 同向量下逐层复现交付档既有漏斗,"
                         "零收益读取零 manifest 零引擎调用")
    ap.add_argument("--json", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    row = ledger.get(a.exp_id)
    if row is None:
        raise SystemExit(f"exp_id={a.exp_id} 不存在")
    if row["status"] != "frozen":
        raise SystemExit(f"铁律③:引擎拒执行 status={row['status']}≠frozen(exp_id={a.exp_id})")

    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    # driver 侧先行断言(fail-fast;权威断言仍在 runner 内重算处,双保险不替代)
    driver_recalc = canonical_pap_sha256(pap)
    if driver_recalc != a.pap_sha256_assert:
        raise SystemExit(f"fail-closed: 台账冻结 pap 重算 canonical digest={driver_recalc} "
                         f"≠ --pap-sha256-assert={a.pap_sha256_assert}(冻结令绑定 digest)")
    kwargs = engine_kwargs_from_pap(pap)
    print(f"exp_id={a.exp_id} {row['family']}/{row['title']} status={row['status']} "
          f"family_trial={row['family_trial']} verdict_power={row['verdict_power']}", flush=True)
    print(f"pap canonical digest={driver_recalc}(断言通过)", flush=True)
    print(f"engine_params(逐字消费冻结件)= { {k: v for k, v in kwargs.items()} }", flush=True)

    if a.recon_only:
        # ── 冻结令:Snapshot 121 同批次向量下逐层复现交付档既有漏斗(零收益/零 manifest/零引擎)──
        if a.recon_snapshot_id is None:
            raise SystemExit("--recon-only 须 --recon-snapshot-id(冻结令=121 只读对账锚)")
        conn, flag_rows, calendar, listing = _recon_flag_rows_and_calendar(a.recon_snapshot_id)
        try:
            cal_index = {d: i for i, d in enumerate(calendar)}
            events, sel = events_from_prices(
                flag_rows(), listing, batch=f"recon_snapshot:{a.recon_snapshot_id}",
                cal_index=cal_index)
        finally:
            conn.close()
        aud = selection_audit(sel)
        print(f"\n[recon-only] snapshot={a.recon_snapshot_id} 钉批+日历轴: "
              f"输入行={sel['counters']['input_rows']} 成员行={sel['counters']['member_rows']} "
              f"日历轴={len(calendar)} 票(listing)={len(listing)}")
        print(f"主漏斗(令七.4): {json.dumps(aud['funnel'], ensure_ascii=False)}")
        print(f"hijack 审计: count={aud['reversal_hijack_audit']['count']} "
              f"share={json.dumps(aud['reversal_hijack_audit']['share'], ensure_ascii=False)}")
        print(f"ST 轴: {json.dumps(aud['st_axis']['counts'], ensure_ascii=False)} "
              f"identity_ok={aud['st_axis']['identity_ok']} "
              f"链vs事件日不一致={aud['st_axis']['chain_vs_eventday_diff_count']}")
        print(f"listing_age 层: {json.dumps(aud['layer_counts'], ensure_ascii=False)}")
        bb = aud["b_axis_control"]
        print(f"B 口径对照(NFV): {json.dumps(bb['funnel'], ensure_ascii=False)} "
              f"vs_A only_a={bb['vs_a_main_events']['n_only_a']} "
              f"only_b={bb['vs_a_main_events']['n_only_b']}")
        print(f"EventRow 已转译={len(events)}(未入引擎)")
        if a.json:
            with open(a.json, "w") as fh:
                json.dump({"mode": "recon_only",
                           "recon_snapshot_id": a.recon_snapshot_id,
                           "pap_sha256": driver_recalc,
                           "selection_audit": aud},
                          fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
            print(f"recon_json → {a.json}", flush=True)
        return

    # ── 正式运行(硬化② manifest 必需;本单元禁止,须另令授权)──────────────────────
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    if a.snapshot_id is None:
        raise SystemExit("正式运行须 --snapshot-id(硬化② fail-closed;本单元只授权 --recon-only)")
    if a.snapshot_id == RECON_ANCHOR_SNAPSHOT_ID:
        raise SystemExit(
            f"fail-closed: StudySnapshot {RECON_ANCHOR_SNAPSHOT_ID} 仅为冻结前只读对账锚,"
            "不得冒充 exp13 正式 manifest(PAP snapshot_batch_req);正式运行须另行生成、"
            "发布 exp13 自己的研究 manifest")

    # 全宇宙事件生成(镜像 exp8 设计):sample=listing 全A键集 → prices 流 → 逐票纯函数
    vr = ViewReader(snapshot_id=a.snapshot_id)
    listing = vr.listing()
    universe = ViewReader(snapshot_id=a.snapshot_id, sample=set(listing))
    cal_index = {c.trade_date: i for i, c in enumerate(universe.calendar())}
    batch = f"study_snapshot:{a.snapshot_id}"
    events, sel = events_from_prices(universe.prices(), listing, batch, cal_index=cal_index)
    print(f"limit_down 全宇宙扫描: 票={len(listing)} 输入行={sel['counters']['input_rows']} "
          f"链={sel['counters']['chains_total']} → 事件={len(events)}"
          f"(剔除留痕入 audit)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=a.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["limit_down_selection"] = selection_audit(sel)

    rendered = report.render(result)
    print("\n" + rendered)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
        print(f"\nresult_json → {a.json}", flush=True)
    if a.report:
        with open(a.report, "w") as fh:
            fh.write(rendered)
        print(f"report → {a.report}", flush=True)


if __name__ == "__main__":
    main()
