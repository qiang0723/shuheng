"""exp20 earnings_revision driver 适配自检(冻结令 2026-07-18 深夜六 令三;零 DB,合成域)。

预注册攻击 fixture 清单(交付档 §5+§7.3)本件覆盖适配层各组:
  #10 对账产出=12,569/5,225 逐层归因表落 audit 的结构断言(reference_reconciliation/
      selection_audit 全键+差值算术+report 渲染消费)。
  #11(引擎全):含 flat 候选的输入端到端——运行不终止、flat 进计数块、主事件集不含 flat、
      主检验正常产出(合法四态终态)。
  另:engine_params 逐字消费冻结 PAP v2 **实物**(键集对账+digest==e1d18dc1…7fd5+缺键/
  多键 fail-closed)、events_from_forecast 契约转译(layer=direction/锚=ann_date/event_id
  形制/snapshot_batch)、fail-closed 行不入引擎。
用法: python taosha/harness/verify_earnings_revision_adapter.py
"""
import datetime as dt
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import report as report_mod                # noqa: E402
from taosha.engine import runner as rn                        # noqa: E402
from taosha.experiment.pap import canonical_pap_sha256        # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv  # noqa: E402
from taosha.harness.run_ashare_study import synth_pap         # noqa: E402
from taosha.harness.run_earnings_revision_study import (       # noqa: E402
    ENGINE_PARAM_KEYS, REFERENCE_NUMBERS, engine_kwargs_from_pap, events_from_forecast,
    reference_reconciliation, selection_audit,
)
from taosha.reader.synthetic import SyntheticReader           # noqa: E402

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAP_V2_PATH = os.path.join(ROOT, "docs", "earnings-revision-pap-final-v2-2026-07-18.json")
FROZEN_DIGEST = "e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5"

# ── 冻结 PAP v2 实物对账(driver 逐字消费面)─────────────────────────────────────────
with open(PAP_V2_PATH, encoding="utf-8") as fh:
    pap_v2 = json.load(fh)
check("PAP v2 实物:canonical 重算 == 冻结 digest e1d18dc1…7fd5",
      canonical_pap_sha256(pap_v2), FROZEN_DIGEST)
check("PAP v2 engine_params 键集 == driver ENGINE_PARAM_KEYS(逐字消费面对账)",
      sorted(pap_v2["engine_params"].keys()), sorted(ENGINE_PARAM_KEYS))
kw = engine_kwargs_from_pap(pap_v2)
check("engine_kwargs:冻结值逐字透传(signed/顺延/诊断轴/alignment/判决门)",
      kw, {"benchmark_mode": "market", "strata_enabled": False, "st_policy": "reject",
           "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
           "postpone_policy": "unified_announcement", "diagnostic_dims": ("direction",),
           "direction_signed_main": True, "direction_display": "raw",
           "effect_alignment_source": "adj_bmp_sign"})
for mut, name in ((lambda ep: ep.pop("st_policy"), "缺键(st_policy)"),
                  (lambda ep: ep.update(st_mode="event_day"), "多键(st_mode)")):
    ep_bad = dict(pap_v2["engine_params"])
    mut(ep_bad)
    try:
        engine_kwargs_from_pap(dict(pap_v2, engine_params=ep_bad))
        check(f"engine_params {name} → fail-closed", "未拒", "SystemExit")
    except SystemExit:
        check(f"engine_params {name} → fail-closed", "SystemExit", "SystemExit")
try:
    engine_kwargs_from_pap(dict(pap_v2, engine_params=None))
    check("engine_params 缺失/非对象 → fail-closed", "未拒", "SystemExit")
except SystemExit:
    check("engine_params 缺失/非对象 → fail-closed", "SystemExit", "SystemExit")
check("窄闸参考数常量=12,569/5,225(冻结原文转录,仅对账参考)",
      REFERENCE_NUMBERS, {"candidates": 12569, "baseline_decidable": 5225})

# ── events_from_forecast 契约转译 + #11 端到端 ─────────────────────────────────────
D = dt.date


def frow(ts, ann, end, first, pmin, pmax):
    return {"ts_code": ts, "ann_date": ann, "end_date": end, "first_ann_date": first,
            "p_change_min": pmin, "p_change_max": pmax}


with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    base_events = list(SyntheticReader(p, e).events())   # 48 事件,2020~2023(研究期内)

    # 合成 forecast 行:逐 base 事件造链(首披=事件日前 90 日历日;修正=事件日),
    # 方向按 (i//3)%2 交错;另注入 1 条 flat 链 + 1 条孤儿(fail-closed,不入引擎)。
    rows = []
    want_dir = {}
    for i, ev in enumerate(base_events):
        up = (i // 3) % 2 == 0
        first = ev.first_ann_date - dt.timedelta(days=90)
        end = D(ev.first_ann_date.year - 1, 12, 31)
        rows.append(frow(ev.ts_code, first, end, first, 0.0, 10.0))
        rows.append(frow(ev.ts_code, ev.first_ann_date, end, first,
                         *((20.0, 30.0) if up else (-40.0, -20.0))))
        want_dir[(ev.ts_code, ev.first_ann_date)] = "up" if up else "down"
    flat_ev = base_events[0]
    f_end = D(flat_ev.first_ann_date.year - 2, 12, 31)   # 异期链,避免同期多链
    rows.append(frow(flat_ev.ts_code, flat_ev.first_ann_date - dt.timedelta(days=200),
                     f_end, flat_ev.first_ann_date - dt.timedelta(days=200), 5.0, 5.0))
    rows.append(frow(flat_ev.ts_code, flat_ev.first_ann_date - dt.timedelta(days=100),
                     f_end, flat_ev.first_ann_date - dt.timedelta(days=200), 5.0, 5.0))
    rows.append(frow("Z99", D(2020, 4, 1), D(2019, 12, 31), D(2020, 1, 15), 1.0, 2.0))  # 孤儿

    events, sel = events_from_forecast(rows, batch="SYNTH_ADAPTER")
    check("#11 转译:flat 计数=1、孤儿 fail-closed=1、主事件=48(不含 flat/孤儿)",
          (sel["flat"]["chain_day_flat"],
           sel["fail_closed"]["by_class"]["orphan_no_first_disclosure"], len(events)),
          (1, 1, 48))
    check("#11 主事件集仅 up/down(flat 不在层内)",
          sorted({e_.event_type_layer for e_ in events}), ["down", "up"])
    check("转译:EventRow 锚=市场事件 ann_date、event_id 形制、批次转录",
          (events[0].first_ann_date, events[0].event_id, events[0].snapshot_batch),
          (sorted(want_dir)[0][1], f"{events[0].ts_code}:"
           f"{events[0].first_ann_date.strftime('%Y%m%d')}", "SYNTH_ADAPTER"))
    check("转译:方向逐事件与 L2 判定一致(48/48)",
          all(want_dir[(e_.ts_code, e_.first_ann_date)] == e_.event_type_layer
              for e_ in events), True)

    # #11 端到端:含 flat 候选的输入 → 引擎正常跑完,主检验产出合法四态终态
    pap20 = dict(synth_pap(), _family_trial=1,
                 bias_statement="合成测试偏差声明(adapter 自检)。",
                 diagnostic_dimensions={"axes": {"direction": ["up", "down"]}})
    res = rn.run_study(SyntheticReader(p, e), pap20, events=events, **kw)  # kw 含 benchmark_mode
    check("#11 端到端:flat 候选在输入中,运行不终止,verdict=合法四态",
          res["verdict"] in ("SIG", "NOT_SIG", "INSUFFICIENT", "AMBIGUOUS"), True)
    check("#11 端到端:n_events_total=48(flat 未混入)", res["n_events_total"], 48)

    # ── #10 对账结构断言(selection_audit / reference_reconciliation / report 消费)────
    aud = selection_audit(sel)
    check("#10 selection_audit 全键(counters/fail_closed/flat/fold_audit/600856/recon)",
          sorted(aud.keys()),
          ["counters", "fail_closed", "flat", "fold_audit", "itemized_600856",
           "reference_reconciliation"])
    recon = aud["reference_reconciliation"]
    check("#10 recon 全键(reference/layers/delta/summary/note)",
          sorted(recon.keys()), ["delta", "layers", "note", "reference", "summary"])
    check("#10 recon 逐层归因表:候选/可判/fail-closed 六类/主事件 up·down 全在场",
          {"candidate_event_keys_in_period", "baseline_decidable_chain_days",
           "fail_closed_by_class", "directed_chain_days", "flat_chain_days",
           "events_after_fold", "events_up", "events_down"} <= set(recon["layers"]), True)
    check("#10 recon 差值算术(Δ=实测−参考;基准可判=up/down+flat)",
          (recon["delta"]["candidates"],
           recon["delta"]["baseline_decidable"],
           recon["layers"]["baseline_decidable_chain_days"]),
          (recon["layers"]["candidate_event_keys_in_period"] - 12569,
           recon["layers"]["baseline_decidable_chain_days"] - 5225,
           recon["layers"]["directed_chain_days"] + recon["layers"]["flat_chain_days"]))
    check("#10 recon note=不改冻结规则声明(异常即停报人,令三)",
          "不改冻结规则" in recon["note"], True)
    # report 消费:audit 带 selection+真锚 → exp20 标题/漏斗段/对账行渲染
    res_r = json.loads(json.dumps(res, default=str))
    res_r["audit"]["study_snapshot"] = {"snapshot_id": 1, "digest": "d" * 8}
    res_r["audit"]["earnings_revision_selection"] = json.loads(
        json.dumps(aud, default=str))
    rend = report_mod.render(res_r)
    check("#10 report 渲染:exp20 标题+漏斗段+fail-closed 计数+flat 块+对账 summary",
          ("exp20 业绩预告修正·signed 事件版" in rend, "exp20 事件生成漏斗" in rend,
           "fail-closed 六类逐类计数" in rend, "flat 计数块" in rend,
           "窄闸参考数对账" in rend and recon["summary"] in rend),
          (True, True, True, True, True))

print("=" * 60)
print(f"verify_earnings_revision_adapter: {N - FAIL}/{N} PASS")
sys.exit(1 if FAIL else 0)
