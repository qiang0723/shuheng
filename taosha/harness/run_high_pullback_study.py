"""驱动:对真实数据跑 exp11 high_pullback(250日新高小幅回落)事件版 → 报告(冻结令 2026-07-24 五)。

令原文档 = taosha/docs/high-pullback-freeze-order-2026-07-24.md(原文即口径):
  · engine_params **逐字消费冻结 PAP**(digest eaa54b3d…b6fc),driver 不保留任何运行时
    自由选择(键集不符=fail-closed);missing_bar_only 引擎路径已收编(exp12),无需再扩;
  · 向引擎传 pap_sha256_assert(仅逐字断言;digest 唯一权威=引擎对实收 pap 重算);
  · --recon-only = 本单元唯一授权模式:按冻结规则复现漏斗(42,719 作双跑参考,差异按
    血缘归因,不追数不改规则);零收益读取、零 manifest 生成、零引擎调用;取数=既有钉批
    现值视图(explore_reader_prices × trade_cal max批开市日历轴,与 42,719 参考同源同序,
    close 以 DB numeric 原生 Decimal 保真读取=冻结闭区间精确算术);
  · 正式运行(另令)前 exp11 须另行生成自己的研究 manifest(PAP snapshot_batch_req);
    正式模式对 --snapshot-id 强制(硬化② fail-closed),事件生成走 snapshot GUC 视图
    同一 Decimal 保真查询,CAR 消费走 ViewReader 契约流。

数据流(镜像 exp13 run_limit_down_study 设计):
  台账已冻结 pap(铁律③)→ 价格行流(Decimal 保真)→ groupby 逐票 →
  high_pullback_rules.select_high_pullback_events(冻结纯函数,阶段状态机)→
  merge_selections → finalize_events(唯一性 fail-closed+研究期)→ EventRow(单层
  high_pullback)→ ViewReader(sample=事件票)→ runner.run_study(events=显式事件源)→
  report.render。**只算+出报告+可选 dump,不改 ledger**(persist 另令,台账结果槽不写)。

用法:
  set -a; . /opt/quant/.env; set +a
  # 本单元唯一授权模式(冻结令:漏斗按冻结规则复现,42,719 双跑参考;
  # recon 锚=批次向量==参考基的既有已发布 StudySnapshot,本单元=212):
  python -m taosha.harness.run_high_pullback_study --exp-id 11 --recon-snapshot-id 212 \
      --pap-sha256-assert <digest> --recon-only [--json OUT]
  # 正式运行(另令;须 exp11 自己的研究 manifest):
  python -m taosha.harness.run_high_pullback_study --exp-id 11 --snapshot-id N \
      --pap-sha256-assert <digest> [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json

from taosha.compute.high_pullback_rules import (
    OUTCOMES, W_OBS, finalize_events, merge_selections,
    select_high_pullback_events)
from taosha.reader.contract import EventRow

# 冻结 PAP engine_params 键集(冻结件逐字消费;缺键/多键=fail-closed,不许运行时补选)。
# note=PAP 内说明文字,非引擎参数,消费时校验在场但不传引擎。exp11 无 st 键(PAP 未设
# ST 处置=引擎 spec §5 默认,driver 不代传、不发明键)。
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "strata_enabled", "verdict_policy"})

EVENT_LAYER = "high_pullback"   # 单一层(无分层假设;strata_enabled=false 照冻结件)

# PAP reporting_commitments:草案重算参考(批次向量 daily6/adj7/cal10;
# 只读对账参考非硬断言,差异按血缘归因停下报人)。
REFERENCE_FINAL_EVENTS = 42719
REFERENCE_BATCH_VECTOR = "daily=6/adj_factor=7/trade_cal=10"

# 本单元 recon 只读对账锚(StudySnapshot 212=既有已发布 exp12 研究 manifest,批次向量
# ==参考基;仅只读取数)。PAP snapshot_batch_req:正式运行须 exp11 自有研究 manifest,
# 他实验 manifest 不得冒充 → 正式模式 fail-closed 名单(承 exp13 对 121 的同款闸)。
RECON_ANCHOR_SNAPSHOT_IDS = frozenset({212})


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 PAP engine_params → run_study 关键字参数(逐字消费,fail-closed)。

    键集与冻结件不符(缺/多)→ 拒;值原样透传零改写(diagnostic_dims list→tuple 系
    run_study 签名的容器形态要求,元素逐字不动)。"""
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
            "verdict_policy": ep["verdict_policy"],
            "nfv_structured": ep["nfv_structured"],
            "postpone_policy": ep["postpone_policy"],
            "diagnostic_dims": tuple(ep["diagnostic_dims"])}


def rows_from_price_rows(price_rows, cal_index: dict):
    """价格行流 → (ts_code, rows dict 列表) 逐票迭代(纯函数;规则消费 5 键最小面)。

    行的 trade_date 必须在日历轴内(recon/snap SQL 结构性内连接保证;缺=fail-closed)。
    close 原样透传(Decimal 保真责任在取数层)。"""
    for ts_code, grp in itertools.groupby(price_rows, key=lambda r: r.ts_code):
        rows = []
        for r in grp:
            rank = cal_index.get(r.trade_date)
            if rank is None:
                raise SystemExit(f"fail-closed: {ts_code} {r.trade_date} 不在日历轴内"
                                 "(取数层须日历轴内连接,不猜不补)")
            rows.append({"trade_date": r.trade_date, "close": r.close,
                         "cal_rank": rank, "board": r.board, "is_st": r.is_st})
        yield ts_code, rows


def events_from_prices(price_rows, cal_index: dict, last_cal_rank: int,
                       batch: str) -> tuple[list[EventRow], dict]:
    """全宇宙价格行流 → EventRow 显式事件源(纯函数,零 I/O)。

    price_rows: (ts_code, trade_date) 升序(SQL ORDER BY 钉死;fixture=构造行)。
    cal_index: {trade_date: 日历轴序号(开市日 1 起)};last_cal_rank=全局日历末序号。
    返回 (events, selection)——selection 全量留痕(counters/rejects)入 audit。"""
    per_security = []
    for ts_code, rows in rows_from_price_rows(price_rows, cal_index):
        per_security.append(select_high_pullback_events(ts_code, rows, last_cal_rank))
    sel = finalize_events(merge_selections(per_security))
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["event_date"]),
                       event_type_layer=EVENT_LAYER,
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def selection_audit(sel: dict) -> dict:
    """selection → audit 块(纯函数;冻结 PAP reporting_commitments 转录):
    主漏斗固定档序(bar行→新高日恒等式→阶段→结局五分→期外→最终)+计数恒等式+明确分母 /
    首触偏移(交易所交易日)分布 / MA20 筛选比例·逐年·板块全 NFV / 唯一性 fail-closed 逐条 /
    42,719 参考对账(非硬断言,差异血缘归因)。诊断块零判决字段。"""
    c = sel["counters"]
    events = sel["events"]
    stages = c.get("stages", 0)
    outcome = {o: c.get("outcome_" + o, 0) for o in OUTCOMES}
    yearly: dict = {}
    board_counts: dict = {}
    per_day: dict = {}
    for e in events:
        y = e["event_date"][:4]
        yearly[y] = yearly.get(y, 0) + 1
        board_counts[e["board_event"]] = board_counts.get(e["board_event"], 0) + 1
        per_day[e["event_date"]] = per_day.get(e["event_date"], 0) + 1
    ev, mk = outcome["EVENT"], outcome["MA_KILL"]
    final_n = c.get("final_events", 0)
    ref_delta = final_n - REFERENCE_FINAL_EVENTS
    return {
        "counters": c,
        "reject_reasons": sel["reject_reasons"],
        "funnel": {
            "输入行": c.get("input_rows", 0),
            "新高日": c.get("newhigh_days", 0),
            "阶段": stages,
            "阶段内重置": c.get("resets_within_stage", 0),
            **{"outcome_" + k: v for k, v in outcome.items()},
            "events_all_years": c.get("events_all_years", 0),
            "event_key_uniqueness_violations": c.get("event_key_uniqueness_violations", 0),
            "out_of_period_pre2011": c.get("out_of_period_pre2011", 0),
            "out_of_period_post": c.get("out_of_period_post", 0),
            "final_events": final_n},
        "newhigh_identity_ok": (c.get("newhigh_days", 0)
                                == stages + c.get("resets_within_stage", 0)),
        "funnel_identity_ok": stages == sum(outcome.values()),
        "events_identity_ok": (c.get("events_all_years", 0)
                               == final_n + c.get("out_of_period_pre2011", 0)
                               + c.get("out_of_period_post", 0)
                               + c.get("uniqueness_dropped_events", 0)),
        "first_touch_offset_exchange_days": {
            str(k): c.get(f"offset_{k}", 0) for k in range(1, W_OBS + 1)},
        "ma20_filter_audit": {
            "not_for_verdict": True,
            "note": "裁定四+裁定七:MA20 筛选比例=结构化 NOT_FOR_VERDICT;"
                    "筛选力弱也保留,不得据分布删改、不得据以改判",
            "in_band": ev + mk, "passed": ev,
            "pass_ratio": (round(ev / (ev + mk), 6) if ev + mk else None)},
        "events_yearly": dict(sorted(yearly.items())),
        "board_counts": dict(sorted(board_counts.items())),
        "shared_days_ge2": sum(1 for v in per_day.values() if v >= 2),
        "per_day_top10": sorted(per_day.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        "itemized_rejects": {
            "event_key_duplicate_fail_closed": [
                r for r in sel["rejects"]
                if r["reason"] == "event_key_duplicate_fail_closed"]},
        "reference_reconciliation": {
            "reference_final_events": REFERENCE_FINAL_EVENTS,
            "reference_batch_vector": REFERENCE_BATCH_VECTOR,
            "got_final_events": final_n,
            "delta": ref_delta,
            "summary": (f"最终事件集={final_n} vs 参考 {REFERENCE_FINAL_EVENTS} "
                        f"(Δ={ref_delta:+d};参考为 float 算术草案对账值,非硬断言;"
                        "差异按血缘归因〔含闭区间恰位边界的精确算术 vs float 舍入〕,"
                        "不追数不改规则,不一致须停下报人")}}


def _decimal_price_rows_snap(snapshot_id: int):
    """事件生成取数(snapshot GUC 钉批视图;recon 与正式同一函数=同构保真):
    explore_reader_prices_snap × explore_reader_calendar_snap(正式 ViewReader 轴语义;
    taosha_engine 角色结构上仅有 _snap 视图授权,现值视图零授权=引擎读数必经钉批),
    close=DB numeric 原生 Decimal(冻结闭区间精确算术保真)。仅事件几何列,零收益消费
    (CAR 由 ViewReader 契约流)。"""
    import os

    import psycopg

    from taosha.reader.view import _ENV_QBASE, _load_env
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dsn = _load_env(os.path.join(root, ".env")).get(_ENV_QBASE)
    if not dsn:
        raise SystemExit(f"缺 {_ENV_QBASE}(.env)")
    conn = psycopg.connect(dsn)
    conn.execute("SET default_transaction_read_only = on")
    conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                 (str(snapshot_id),))
    cal = [d for (d,) in conn.execute(
        "SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")]
    cal_index = {d: i + 1 for i, d in enumerate(cal)}

    from collections import namedtuple
    Row = namedtuple("Row", "ts_code trade_date close board is_st")

    def rows():
        with conn.cursor(name="s11_snap_prices") as cur:
            cur.itersize = 200_000
            cur.execute(
                "SELECT p.ts_code, p.trade_date, p.close, p.board, p.is_st "
                "FROM explore_reader_prices_snap p "
                "JOIN explore_reader_calendar_snap cal USING (trade_date) "
                "ORDER BY p.ts_code, p.trade_date")
            for ts, d, close, board, st in cur:
                yield Row(ts, d, close, board, bool(st))
    return conn, rows, cal_index, len(cal)


def main():
    # DB 依赖延迟导入:fixture(verify_high_pullback_adapter)零 DB 消费上方纯函数
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, default=None,
                    help="正式运行 StudySnapshot manifest ID(硬化② fail-closed;"
                         "须 exp11 自己的研究 manifest,另令生成)")
    ap.add_argument("--recon-snapshot-id", type=int, default=None,
                    help="--recon-only 只读对账锚 snapshot(承 exp13 先例;须为批次向量=="
                         "42,719 参考基〔daily6/adj7/cal10〕的既有已发布 StudySnapshot,"
                         "仅只读取数,不冒充 exp11 正式 manifest)")
    ap.add_argument("--pap-sha256-assert", required=True,
                    help="冻结令绑定 digest(仅逐字断言;权威=引擎重算,不一致 fail-closed)")
    ap.add_argument("--recon-only", action="store_true",
                    help="冻结令授权模式:既有钉批现值视图按冻结规则复现漏斗"
                         "(42,719 双跑参考),零收益读取零 manifest 零引擎调用")
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
        # ── 冻结令:按冻结规则复现漏斗(42,719 双跑参考;零收益/零 manifest 生成/零引擎)──
        if a.recon_snapshot_id is None:
            raise SystemExit("--recon-only 须 --recon-snapshot-id(既有已发布 StudySnapshot "
                             "只读对账锚,批次向量须==参考基 daily6/adj7/cal10;承 exp13 先例)")
        conn, rows, cal_index, last_rank = _decimal_price_rows_snap(a.recon_snapshot_id)
        try:
            events, sel = events_from_prices(
                rows(), cal_index, last_rank,
                batch=f"recon_snapshot:{a.recon_snapshot_id}")
        finally:
            conn.close()
        aud = selection_audit(sel)
        print(f"\n[recon-only] snapshot={a.recon_snapshot_id} 钉批+日历轴: "
              f"输入行={sel['counters']['input_rows']} 日历轴={last_rank}")
        print(f"主漏斗: {json.dumps(aud['funnel'], ensure_ascii=False)}")
        print(f"恒等式: newhigh={aud['newhigh_identity_ok']} "
              f"outcome={aud['funnel_identity_ok']} events={aud['events_identity_ok']}")
        print(f"MA20 审计(NFV): {json.dumps(aud['ma20_filter_audit'], ensure_ascii=False)}")
        print(f"42,719 参考对账: {aud['reference_reconciliation']['summary']}")
        print(f"EventRow 已转译={len(events)}(未入引擎)")
        if a.json:
            with open(a.json, "w") as fh:
                json.dump({"mode": "recon_only",
                           "pap_sha256": driver_recalc,
                           "selection_audit": aud},
                          fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
            print(f"recon_json → {a.json}", flush=True)
        return

    # ── 正式运行(硬化② manifest 必需;本单元禁止,须另令授权)──────────────────────
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    if a.snapshot_id is None:
        raise SystemExit("正式运行须 --snapshot-id(硬化② fail-closed;本单元只授权 --recon-only;"
                         "exp11 研究 manifest 须另令生成,不得冒用他实验 manifest)")
    if a.snapshot_id in RECON_ANCHOR_SNAPSHOT_IDS:
        raise SystemExit(
            f"fail-closed: StudySnapshot {a.snapshot_id} 仅为只读对账锚(他实验 manifest),"
            "不得冒充 exp11 正式 manifest(PAP snapshot_batch_req);正式运行须另行生成、"
            "发布 exp11 自己的研究 manifest")

    conn, rows, cal_index, last_rank = _decimal_price_rows_snap(a.snapshot_id)
    try:
        events, sel = events_from_prices(rows(), cal_index, last_rank,
                                         batch=f"study_snapshot:{a.snapshot_id}")
    finally:
        conn.close()
    print(f"high_pullback 全宇宙扫描: 输入行={sel['counters']['input_rows']} "
          f"阶段={sel['counters']['stages']} → 最终事件={len(events)}"
          f"(剔除留痕入 audit)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=a.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["high_pullback_selection"] = selection_audit(sel)

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
