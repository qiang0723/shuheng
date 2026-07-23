"""驱动:对真实数据跑 exp12 st_removal(ST/风险警示完整撤销)事件版 → 报告(冻结令 2026-07-23)。

令原文档 = taosha/docs/st-removal-freeze-order-2026-07-23.md(原文即口径):
  · engine_params **逐字消费冻结 PAP**(digest 62a387a2…4353),driver 不保留任何运行时
    自由选择(键集不符=fail-closed);
  · 向引擎传 pap_sha256_assert(仅逐字断言;digest 唯一权威=引擎对实收 pap 重算);
  · --recon-only = 本单元唯一授权模式(explore_reader_namechange 现值面漏斗按冻结规则复现,
    641 仅作 batch 7 参考数、差异按血缘归因、不追数不改规则;零收益读取、零 manifest、
    零引擎调用);
  · 正式运行(另令)前 exp12 须另行生成自己的研究 manifest(PAP snapshot_batch_req)。

driver 定值(非 PAP 键,冻结 PAP 语义的唯一相容读法;fixture 专项验证,行为验收点报人):
  st_mode='event_day'(生产唯一合法值,硬化③)、st_policy='keep'——冻结 PAP engine_params.note
  原文"本假设无st诊断轴(事件本体=ST摘帽,前段ST为构造性事实,不设分层)"+event_def(事件=ST
  状态名撤销公告):锚日事件票名称仍属 ST 状态,st_policy='reject' 将剔除全部事件=归谬,
  与冻结 event_def 不相容;'keep' 不设 st 分层(diagnostic_dims=[] 照冻结件)。

数据流(镜像 exp13/exp20 设计):
  台账已冻结 pap(铁律③)→ ViewReader.namechange_rows(019 视图对 _snap 面,manifest 路由)
  → 逐票 → st_removal_rules.select_st_removal_events(冻结纯函数,主漏斗十一档)→
  merge_selections → EventRow → ViewReader(sample=事件票)→ runner.run_study(events=显式
  事件源)→ execution_limit_audit(τ0日一字板,NFV)→ report.render。
**只算+出报告+可选 dump,不改 ledger**(persist 另令,台账结果槽不写)。

用法:
  set -a; . /opt/quant/.env; set +a
  # 本单元唯一授权模式(冻结令三节:漏斗按冻结规则复现):
  python -m taosha.harness.run_st_removal_study --exp-id 12 \
      --pap-sha256-assert <digest> --recon-only [--json OUT]
  # 正式运行(另令;须 exp12 自己的研究 manifest):
  python -m taosha.harness.run_st_removal_study --exp-id 12 --snapshot-id N \
      --pap-sha256-assert <digest> [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

from taosha.compute.st_removal_rules import (
    funnel_identity_ok, merge_selections, select_st_removal_events)
from taosha.reader.contract import EventRow

# 冻结 PAP engine_params 键集(冻结件逐字消费;缺键/多键=fail-closed,不许运行时补选)。
# note=PAP 内说明文字,非引擎参数,消费时校验在场但不传引擎。
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "strata_enabled", "verdict_policy"})

# driver 定值(非 PAP 键;模块头注=唯一相容读法论证;fixture verify_st_removal_adapter 专项)
ST_MODE_FIXED = "event_day"
ST_POLICY_FIXED = "keep"

EVENT_LAYER = "st_removal"     # 单一层(无分层假设;strata_enabled=false 照冻结件)

# batch 7 参考数(冻结令三节:"641仅作batch 7参考数,差异按血缘归因,不追数、不改规则";
# 来源=PAP 草案单元只读漏斗复算 2026-07-23,st-removal-pap-draft-delivery §3。
# ⚠非硬断言:019 视图面含 holdout 焊死((ann IS NULL OR ann<2024-07-01))与北交所排除,
# 参考数出自视图前的原始表全量读,期外(2024-07 后)候选在视图面结构上不可见 → 上游档位
# 预期系统性小于参考数,血缘=视图 holdout/BJ 子句;最终事件集(研究期内)预期不变。)
REFERENCE_BATCH7 = {
    "batch_id": 7,
    "input_rows": 20005, "segments": 18113, "transitions_with_prev": 12253,
    "removal_candidates": 1063, "state_unjudgeable_fail_closed": 0,
    "anchor_missing": 296, "anchor_conflict_fail_closed": 0,
    "ann_after_start_fail_closed": 0, "out_of_period": 126,
    "event_key_duplicate_fail_closed": 0, "final_events": 641,
    "yearly": {"2011": 35, "2012": 68, "2013": 73, "2014": 45, "2015": 32, "2016": 42,
               "2017": 50, "2018": 37, "2019": 21, "2020": 18, "2021": 92, "2022": 62,
               "2023": 40, "2024": 26},
    "gap_dist": {"0": 2, "1-3": 583, "4-10": 56, ">10": 0},
    "destar_all": 458, "destar_in_window_clean_anchor": 222,
    "star_on_all": 419, "st_to_delist_all": 143,
}


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 PAP engine_params → run_study 关键字参数(逐字消费,fail-closed)。

    键集与冻结件不符(缺/多)→ 拒;值原样透传零改写(diagnostic_dims list→tuple 系
    run_study 签名的容器形态要求,冻结件=[] 空轴)。st_mode/st_policy=driver 定值
    (非 PAP 键;模块头注论证,fixture 专项)。"""
    ep = pap.get("engine_params")
    if not isinstance(ep, dict):
        raise SystemExit("fail-closed: 冻结 PAP 缺 engine_params 或非对象(冻结令:逐字消费)")
    got = set(ep)
    if got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params 键集与冻结件不符(缺={sorted(set(ENGINE_PARAM_KEYS) - got)} "
            f"多={sorted(got - set(ENGINE_PARAM_KEYS))});driver 不保留运行时自由选择")
    if ep["postpone_policy"] != "missing_bar_only":
        raise SystemExit(
            f"fail-closed: 冻结件 postpone_policy={ep['postpone_policy']!r} != 'missing_bar_only'"
            "(冻结 PAP 唯一冻结值;driver 只认冻结件,不映射不回退)")
    return {"benchmark_mode": ep["benchmark_mode"],
            "strata_enabled": ep["strata_enabled"],
            "st_mode": ST_MODE_FIXED,
            "st_policy": ST_POLICY_FIXED,
            "verdict_policy": ep["verdict_policy"],
            "nfv_structured": ep["nfv_structured"],
            "postpone_policy": ep["postpone_policy"],
            "diagnostic_dims": tuple(ep["diagnostic_dims"])}


def events_from_namechange(rows: list[dict], batch: str) -> tuple[list[EventRow], dict]:
    """namechange 视图行 → EventRow 显式事件源(纯函数,零 I/O)。

    rows: dict 行列表((ts_code,start_date,alias,ann_date) 升序,SQL ORDER BY 钉死;
    fixture=构造行,本函数内再稳定排序一道=同键,幂等)。
    返回 (events, selection)——selection 全量留痕(counters/rejects)入 audit。"""
    rows = sorted(rows, key=lambda r: (r["ts_code"], r["start_date"] or dt.date.min,
                                       str(r["alias"]), r["ann_date"] or dt.date.min))
    per_security = []
    cur_ts, buf = None, []
    for r in rows:
        if r["ts_code"] != cur_ts:
            if buf:
                per_security.append(select_st_removal_events(cur_ts, buf))
            cur_ts, buf = r["ts_code"], []
        buf.append(r)
    if buf:
        per_security.append(select_st_removal_events(cur_ts, buf))
    sel = merge_selections(per_security)
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['ann_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["ann_date"]),
                       event_type_layer=EVENT_LAYER,
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def _gap_bucket(g) -> str:
    if g is None:
        return "none"
    if g == 0:
        return "0"
    if 1 <= g <= 3:
        return "1-3"
    if 4 <= g <= 10:
        return "4-10"
    return ">10"


def reference_reconciliation(sel: dict) -> dict:
    """batch 7 参考数逐档对账(冻结令三节:641 仅参考数,差异按血缘归因,不追数不改规则)。
    纯函数:逐档 delta + 血缘归因注记;**无硬断言**(对账结论如实报告,判读在人)。"""
    c = sel["counters"]
    ref = REFERENCE_BATCH7
    layer_keys = ("input_rows", "segments", "transitions_with_prev", "removal_candidates",
                  "state_unjudgeable_fail_closed", "anchor_missing",
                  "anchor_conflict_fail_closed", "ann_after_start_fail_closed",
                  "out_of_period", "event_key_duplicate_fail_closed", "final_events")
    deltas = {k: c.get(k, 0) - ref[k] for k in layer_keys}
    yearly = {}
    for e in sel["events"]:
        y = e["ann_date"][:4]
        yearly[y] = yearly.get(y, 0) + 1
    gap = {}
    for e in sel["events"]:
        b = _gap_bucket(e["gap_days"])
        gap[b] = gap.get(b, 0) + 1
    upper_note = ("上游档位差异血缘=019 视图 holdout 焊死(ann≥2024-07-01 段不可见)+北交所"
                  "排除(参考数出自视图前原始表全量读);" if any(
                      deltas[k] != 0 for k in ("input_rows", "segments",
                                               "transitions_with_prev",
                                               "removal_candidates", "out_of_period"))
                  else "")
    return {
        "reference": ref, "layer_deltas": deltas,
        "yearly": yearly, "yearly_match": yearly == ref["yearly"],
        "gap_dist": gap, "gap_match": gap == {k: v for k, v in ref["gap_dist"].items() if v},
        "nfv_deltas": {k: c.get(k, 0) - ref[k] for k in
                       ("destar_all", "destar_in_window_clean_anchor",
                        "star_on_all", "st_to_delist_all")},
        "summary": (f"最终事件集 {c.get('final_events')}(参考 641,Δ={deltas['final_events']});"
                    f"逐年分布{'一致' if yearly == ref['yearly'] else '有差异(见 layer 明细)'};"
                    f"{upper_note}参考数非硬断言,判读在人"),
    }


def selection_audit(sel: dict) -> dict:
    """selection → audit 块(纯函数;冻结 PAP reporting_commitments 转录):
    主漏斗十一档计数+恒等式+明确分母 / 剔除逐档逐条留痕槽位 / 逐年分布 / 锚→生效日差分布 /
    摘星·戴星·ST→退市 NFV 报数 / batch 7 参考数对账。诊断块零判决字段,全部 NFV。"""
    c = sel["counters"]
    recon = reference_reconciliation(sel)
    itemized = {}
    for r in sel["rejects"]:
        itemized.setdefault(r["reason"], []).append(r)
    return {"counters": c,
            "funnel_identity_ok": funnel_identity_ok(c),
            "reject_reasons": sel["reject_reasons"],
            "itemized_rejects": itemized,          # 全档逐条留痕(postpone/fail-closed 分别)
            "events_yearly": recon["yearly"],
            "gap_dist": recon["gap_dist"],
            "nfv_counts": {"not_for_verdict": True,
                           "note": "裁定二/四:摘星未摘帽/戴星/ST→退市仅报数;"
                                   "禁收益/CAR/显著性/独立结论",
                           "destar_all": c.get("destar_all", 0),
                           "destar_in_window_clean_anchor":
                               c.get("destar_in_window_clean_anchor", 0),
                           "star_on_all": c.get("star_on_all", 0),
                           "st_to_delist_all": c.get("st_to_delist_all", 0)},
            "reference_reconciliation": recon}


def execution_limit_audit_from_result(result: dict) -> dict:
    """τ0日一字板执行限制审计(冻结 PAP diagnostic_dimensions.execution_limit_audit,
    人终版令 2026-07-23):数量+占有效存活比例,结构化 NFV;数据源=result.censor_diagnostic
    (runner 既有 τ 轴删失诊断,τ=0 行 one_word 计数;零新统计路径)。"""
    cd = (result.get("censor_diagnostic") or {}).get("all") or {}
    rows = cd.get("by_tau_censor") or []
    tau0 = rows[0] if rows else {}
    n = tau0.get("n", 0) or 0
    ow = tau0.get("one_word", 0) or 0
    return {"not_for_verdict": True,
            "note": "人终版令2026-07-23:τ0日一字板事件数量与比例=结构化NOT_FOR_VERDICT"
                    "执行限制报告;一字板不控制CAR取样(照冻结口径进入CAR不顺延),不改判决;"
                    "cost键(含limit_up_board_untradeable)仅schema/执行审计字段;"
                    "结果不得表述为可成交策略证据",
            "tau0_one_word_n": ow, "denominator_n_valid": n,
            "ratio": (ow / n) if n else None}


def _recon_namechange_rows_currentview() -> list[dict]:
    """对账模式取数:explore_reader_namechange **现值面**(max-batch 路由;零 manifest 依赖)。

    只读名称段元数据、零收益读取(冻结令三节授权面)。列面/holdout/排北与 _snap 面同口径
    (019 视图对同体)。正式运行(另令)必须走 ViewReader.namechange_rows(_snap manifest
    路由),本函数不得用于正式跑。"""
    import os

    import psycopg

    from taosha.reader.view import _ENV_QBASE, _load_env
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dsn = _load_env(os.path.join(root, ".env")).get(_ENV_QBASE)
    if not dsn:
        raise SystemExit(f"缺 {_ENV_QBASE}(.env);对账需引擎只读 DSN")
    out: list[dict] = []
    with psycopg.connect(dsn) as conn:
        conn.execute("SET default_transaction_read_only = on")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ts_code, alias, start_date, ann_date, snapshot_batch "
                "FROM explore_reader_namechange "
                "ORDER BY ts_code, start_date, alias, ann_date NULLS FIRST")
            for (ts, alias, sd, ad, batch) in cur.fetchall():
                out.append({"ts_code": ts, "alias": alias, "start_date": sd,
                            "ann_date": ad, "snapshot_batch": str(batch)})
    return out


def main():
    # DB 依赖延迟导入:fixture(verify_st_removal_adapter)零 DB 消费上方纯函数
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, default=None,
                    help="正式运行 StudySnapshot manifest ID(硬化② fail-closed;"
                         "须 exp12 自己的研究 manifest,本单元禁生成)")
    ap.add_argument("--pap-sha256-assert", required=True,
                    help="冻结令绑定 digest(仅逐字断言;权威=引擎重算,不一致 fail-closed)")
    ap.add_argument("--recon-only", action="store_true",
                    help="冻结令授权模式:explore_reader_namechange 现值面漏斗按冻结规则复现,"
                         "641 仅 batch 7 参考数;零收益读取零 manifest 零引擎调用")
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
    print(f"engine_params(逐字消费冻结件;st_mode/st_policy=driver 定值,头注论证)= "
          f"{ {k: v for k, v in kwargs.items()} }", flush=True)

    if a.recon_only:
        # ── 冻结令三节:漏斗按冻结规则复现(零收益/零 manifest/零引擎)──────────────
        rows = _recon_namechange_rows_currentview()
        batches = sorted({r["snapshot_batch"] for r in rows})
        events, sel = events_from_namechange(rows, batch="recon_currentview")
        aud = selection_audit(sel)
        c = sel["counters"]
        print(f"\n[recon-only] explore_reader_namechange 现值面: 行={len(rows)} 批次={batches}")
        print(f"主漏斗(固定档序): 入库行={c['input_rows']}(start缺失={c['start_missing_rows']}) "
              f"→ 段={c['segments']} → 有前段转换={c['transitions_with_prev']} "
              f"→ 候选={c['removal_candidates']}")
        print(f"  fail-closed/剔除: 状态不可判={c['state_unjudgeable_fail_closed']} "
              f"锚缺失={c['anchor_missing']} 锚冲突={c['anchor_conflict_fail_closed']} "
              f"ann>start={c['ann_after_start_fail_closed']} 期外={c['out_of_period']} "
              f"键重复={c['event_key_duplicate_fail_closed']}")
        print(f"  最终事件集={c['final_events']} 恒等式="
              f"{'OK' if aud['funnel_identity_ok'] else '⚠不成立'}")
        print(f"逐年: {json.dumps(aud['events_yearly'], ensure_ascii=False, sort_keys=True)}")
        print(f"gap 分布: {json.dumps(aud['gap_dist'], ensure_ascii=False, sort_keys=True)}")
        print(f"NFV 报数: 摘星全史={c['destar_all']}(窗内锚干净="
              f"{c['destar_in_window_clean_anchor']}) 戴星={c['star_on_all']} "
              f"ST→退市={c['st_to_delist_all']}")
        print(f"对账: {aud['reference_reconciliation']['summary']}")
        print(f"EventRow 已转译={len(events)}(未入引擎)")
        if a.json:
            with open(a.json, "w") as fh:
                json.dump({"mode": "recon_only",
                           "source": "explore_reader_namechange(现值)",
                           "batches": batches, "pap_sha256": driver_recalc,
                           "selection_audit": aud},
                          fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
            print(f"recon_json → {a.json}", flush=True)
        return

    # ── 正式运行(硬化② manifest 必需;本单元禁止,须另令授权)──────────────────────
    from taosha.engine import report, runner
    from taosha.reader.view import ViewReader

    if a.snapshot_id is None:
        raise SystemExit("正式运行须 --snapshot-id(硬化② fail-closed;本单元只授权 --recon-only)")

    vr = ViewReader(snapshot_id=a.snapshot_id)
    nc_rows = vr.namechange_rows()
    batch = f"study_snapshot:{a.snapshot_id}"
    events, sel = events_from_namechange(nc_rows, batch)
    print(f"st_removal 全宇宙扫描: namechange 行={len(nc_rows)} → 事件={len(events)}"
          f"(剔除留痕入 audit)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=a.pap_sha256_assert, **kwargs)
    aud = selection_audit(sel)
    aud["execution_limit_audit"] = execution_limit_audit_from_result(result)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["st_removal_selection"] = aud

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
