"""驱动:exp20 业绩预告修正(earnings_revision)事件版(冻结令 2026-07-18 深夜六 令三)。

令原文档 = taosha/docs/earnings-revision-freeze-order-2026-07-18.md(原文即口径):
  · engine_params **逐字消费冻结 PAP v2**(digest e1d18dc1…7fd5),driver 不保留任何运行时
    自由选择(键集不符=fail-closed);
  · 向引擎传 pap_sha256_assert(仅逐字断言;digest 唯一权威=引擎对实收 pap 重算);
  · 参数或 digest 不一致一律 fail-closed;
  · 不改变既有默认路径与其他实验输出(主干零触碰,纯新增文件)。

数据流(承 run_limit_open_study 先例):
  台账已冻结 pap(铁律③)→ ViewReader.forecast_rows(018 视图对,最小列面,holdout 焊死)
  → earnings_revision_rules.select_revision_events(冻结纯函数:L2 折叠/链/基准B/方向/
    fail-closed 六类/flat 计数/同日折叠)→ EventRow(layer=up|down)→ ViewReader(sample=事件票)
  → runner.run_study(events=显式事件源;signed 主检验/公告顺延/direction 诊断轴)→ report.render。
**只算+出报告+可选 dump,不改 ledger**(persist 另令,台账结果槽不写)。

两种模式:
  --recon-only:令三⑤对账模式——只读 explore_reader_forecast(现值 max-batch 面,零收益读取、
    零 manifest、零引擎调用),跑 L2 规则漏斗,产出 12,569/5,225 参考数逐层对账表。
    本单元(分段授权只到行为验收)只许此模式。
  全量模式(--snapshot-id):正式运行,**本单元禁止**,须外审通过后另令 manifest+单跑授权。

用法:
  set -a; . /opt/quant/.env; set +a
  python -m taosha.harness.run_earnings_revision_study --exp-id 20 \
      --pap-sha256-assert <digest> --recon-only [--json OUT]
  python -m taosha.harness.run_earnings_revision_study --exp-id 20 --snapshot-id N \
      --pap-sha256-assert <digest> [--json OUT] [--report OUT]   # 另令后方可
"""
from __future__ import annotations

import argparse
import json

from taosha.compute.earnings_revision_rules import select_revision_events
from taosha.reader.contract import EventRow

# PAP v2 engine_params 键集(冻结件逐字消费;缺键/多键=fail-closed,不许运行时补选)。
# note=PAP 内说明文字,非引擎参数,消费时校验在场但不传引擎。exp20 无 st_mode 键
# (引擎默认 event_day=生产口径,PAP 未开运行时选择)。
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "direction_display", "direction_signed_main",
    "effect_alignment_source", "note", "nfv_structured", "postpone_policy", "st_policy",
    "strata_enabled", "verdict_policy"})

# 窄闸参考数(冻结 PAP v2 event_def/reporting_commitments① 原文:仅对账参考,不是预写样本量;
# 对不上不得修改冻结规则,异常即停报人)。5,225 原脚本未归档(人裁 07-17 已留痕),按冻结
# p_change 规则重实现后逐层归因对账。
REFERENCE_NUMBERS = {"candidates": 12569, "baseline_decidable": 5225}


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 PAP v2 engine_params → run_study 关键字参数(逐字消费,fail-closed)。

    键集与冻结件不符(缺/多)→ 拒;值原样透传零改写(diagnostic_dims list→tuple 系
    run_study 签名的容器形态要求,元素逐字不动)。"""
    ep = pap.get("engine_params")
    if not isinstance(ep, dict):
        raise SystemExit("fail-closed: 冻结 PAP 缺 engine_params 或非对象(令三:逐字消费)")
    got = set(ep)
    if got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params 键集与冻结件不符(缺={sorted(set(ENGINE_PARAM_KEYS) - got)} "
            f"多={sorted(got - set(ENGINE_PARAM_KEYS))});driver 不保留运行时自由选择")
    return {"benchmark_mode": ep["benchmark_mode"],
            "strata_enabled": ep["strata_enabled"],
            "st_policy": ep["st_policy"],
            "verdict_policy": ep["verdict_policy"],
            "nfv_structured": ep["nfv_structured"],
            "postpone_policy": ep["postpone_policy"],
            "diagnostic_dims": tuple(ep["diagnostic_dims"]),
            "direction_signed_main": ep["direction_signed_main"],
            "direction_display": ep["direction_display"],
            "effect_alignment_source": ep["effect_alignment_source"]}


def events_from_forecast(rows: list[dict], batch: str) -> tuple[list[EventRow], dict]:
    """forecast 行集 → EventRow 显式事件源(纯函数,零 I/O)。

    rows: forecast_rows 面(ts_code/ann_date/end_date/first_ann_date/p_change_min/p_change_max)。
    L2 判别全部在 select_revision_events(冻结纯函数);此处只做契约转译:
    EventRow.first_ann_date=**市场事件锚 ann_date**(契约 §2 该字段义=事件日锚;exp20 公告
    日历锚语义,承 exp8 first_ann_date=event_date 先例)、layer=direction(up|down,白名单
    对账在 runner 二道闸)。返回 (events, selection)——selection 全量漏斗留痕入 audit。"""
    sel = select_revision_events(rows)
    events = [EventRow(ts_code=e["ts_code"], event_id=e["event_id"],
                       first_ann_date=e["ann_date"], event_type_layer=e["direction"],
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def reference_reconciliation(sel: dict) -> dict:
    """漏斗 → 12,569/5,225 参考数逐层对账块(纯函数;PAP reporting_commitments①)。

    参考层锚定:候选 12,569 ↔ candidate_event_keys_in_period(研究期内修正候选市场事件键数);
    基准B可判 5,225 ↔ baseline_decidable_chain_days(=方向已判 up/down/flat 链日合计,即当前值
    与基准B双双可判的候选)。差异只归因不改规则(对不上即停报人,冻结令三)。"""
    cnt = sel["counters"]
    decidable = cnt.get("directed_chain_days", 0) + sel["flat"]["chain_day_flat"]
    layers = {
        "input_rows": cnt.get("input_rows"),
        "rows_after_dedup": cnt.get("rows_after_dedup"),
        "candidate_rows_all_periods": cnt.get("candidate_rows_all_periods"),
        "candidate_rows_in_period": cnt.get("candidate_rows_in_period"),
        "candidate_event_keys_in_period": cnt.get("candidate_event_keys_in_period"),
        "chain_day_candidates_in_period": cnt.get("chain_day_candidates_in_period"),
        "fail_closed_by_class": dict(sel["fail_closed"]["by_class"]),
        "baseline_decidable_chain_days": decidable,
        "directed_chain_days": cnt.get("directed_chain_days"),
        "flat_chain_days": sel["flat"]["chain_day_flat"],
        "events_after_fold": cnt.get("events_after_fold"),
        "events_up": cnt.get("events_up"),
        "events_down": cnt.get("events_down"),
    }
    d_cand = layers["candidate_event_keys_in_period"] - REFERENCE_NUMBERS["candidates"]
    d_dec = decidable - REFERENCE_NUMBERS["baseline_decidable"]
    return {
        "reference": dict(REFERENCE_NUMBERS),
        "layers": layers,
        "delta": {"candidates": d_cand, "baseline_decidable": d_dec},
        "summary": (f"候选层: 实测事件键(研究期)={layers['candidate_event_keys_in_period']} "
                    f"vs 参考12,569(Δ={d_cand:+d}); 基准B可判层: 实测可判链日={decidable} "
                    f"(up/down={layers['directed_chain_days']}+flat={layers['flat_chain_days']}) "
                    f"vs 参考5,225(Δ={d_dec:+d})"),
        "note": "参考数仅对账,不是预写样本量;差异逐层归因,不改冻结规则(异常即停报人,令三)",
    }


def selection_audit(sel: dict) -> dict:
    """selection → audit 块(纯函数;PAP reporting_commitments①②③④转录):
    漏斗计数/fail-closed 六类逐类逐年+600856 逐条/flat 计数块/同日折叠审计/参考数对账。"""
    return {"counters": sel["counters"],
            "fail_closed": sel["fail_closed"],
            "flat": sel["flat"],
            "fold_audit": sel["fold_audit"],
            "itemized_600856": sel["itemized_600856"],
            "reference_reconciliation": reference_reconciliation(sel)}


def _recon_forecast_rows_currentview() -> list[dict]:
    """对账模式取数:explore_reader_forecast **现值面**(max-batch 路由;零 manifest 依赖)。

    只读 forecast 元数据、零收益读取(令三⑤授权面)。列面/holdout/排北与 _snap 面同口径
    (018 同一视图对);行序与 ViewReader.forecast_rows 同键钉死。正式运行(另令)必须走
    ViewReader.forecast_rows(_snap manifest 路由),本函数不得用于正式跑。"""
    import os

    import psycopg

    from taosha.reader.view import _ENV_QBASE, _load_env
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dsn = _load_env(os.path.join(root, ".env")).get(_ENV_QBASE)
    if not dsn:
        raise SystemExit(f"缺 {_ENV_QBASE}(.env);对账需引擎只读 DSN")
    out: list[dict] = []
    with psycopg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(
            "SELECT ts_code, ann_date, end_date, first_ann_date, "
            "       p_change_min, p_change_max, snapshot_batch "
            "FROM explore_reader_forecast "
            "ORDER BY ts_code, ann_date, end_date, first_ann_date")
        for (ts, ad, ed, fad, pmin, pmax, batch) in cur.fetchall():
            out.append({
                "ts_code": ts, "ann_date": ad, "end_date": ed, "first_ann_date": fad,
                "p_change_min": None if pmin is None else float(pmin),
                "p_change_max": None if pmax is None else float(pmax),
                "snapshot_batch": str(batch)})
    return out


def main():
    # DB 依赖延迟导入:fixture(verify_earnings_revision_adapter)零 DB 消费上方纯函数
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, default=None,
                    help="StudySnapshot manifest ID(正式运行必需,硬化②;--recon-only 不用)")
    ap.add_argument("--pap-sha256-assert", required=True,
                    help="冻结批复绑定 digest(仅逐字断言;权威=引擎重算,不一致 fail-closed)")
    ap.add_argument("--recon-only", action="store_true",
                    help="令三⑤对账模式:只跑 L2 漏斗+参考数对账,零收益读取零引擎调用")
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

    if a.recon_only:
        # ── 令三⑤:12,569/5,225 逐层对账(现值 forecast 面;零收益/零 manifest/零引擎)──
        rows = _recon_forecast_rows_currentview()
        batches = sorted({r["snapshot_batch"] for r in rows})
        events, sel = events_from_forecast(rows, batch="recon_currentview")
        recon = reference_reconciliation(sel)
        print(f"\n[recon-only] explore_reader_forecast 现值面: 行={len(rows)} 批次={batches}")
        print(f"漏斗: {json.dumps(sel['counters'], ensure_ascii=False)}")
        print(f"fail-closed 六类: {json.dumps(sel['fail_closed']['by_class'], ensure_ascii=False)}"
              f"(数值不可判子因 {json.dumps(sel['fail_closed']['value_undecidable_sub'], ensure_ascii=False)};"
              f"600856 逐条={len(sel['itemized_600856'])})")
        print(f"flat 计数块: {json.dumps(sel['flat']['chain_day_flat'], ensure_ascii=False)} "
              f"按年={json.dumps(sel['flat']['by_year'], ensure_ascii=False)}")
        print(f"同日折叠: {json.dumps(sel['fold_audit'], ensure_ascii=False)}")
        print(f"主事件集: up={sel['counters']['events_up']} down={sel['counters']['events_down']} "
              f"合计={sel['counters']['events_after_fold']}(EventRow 已转译={len(events)},未入引擎)")
        print(f"\n对账: {recon['summary']}")
        if a.json:
            with open(a.json, "w") as fh:
                json.dump({"mode": "recon_only", "source": "explore_reader_forecast(现值)",
                           "batches": batches, "selection_audit": selection_audit(sel)},
                          fh, ensure_ascii=False, indent=2, default=str)
            print(f"recon_json → {a.json}", flush=True)
        return

    # ── 正式运行(硬化② manifest 必需;本单元禁止,须外审后另令授权)────────────────
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    if a.snapshot_id is None:
        raise SystemExit("正式运行须 --snapshot-id(硬化② fail-closed;本单元只授权 --recon-only)")
    print(f"engine_params(逐字消费冻结件)= { {k: v for k, v in kwargs.items()} }", flush=True)
    vr = ViewReader(snapshot_id=a.snapshot_id)
    batch = f"study_snapshot:{a.snapshot_id}"
    events, sel = events_from_forecast(vr.forecast_rows(), batch)
    print(f"earnings_revision 事件生成: 输入行={sel['counters']['input_rows']} → "
          f"事件={len(events)}(up={sel['counters']['events_up']}/"
          f"down={sel['counters']['events_down']};漏斗留痕入 audit)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=a.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["earnings_revision_selection"] = selection_audit(sel)

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
