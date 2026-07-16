"""驱动:对真实数据跑 exp4 holder_sell(减持计划首次预披露)事件版 → 报告(§5 白名单④,人批 2026-07-16)。

读台账**已冻结** pap(铁律③)→ ViewReader.holder_sell_rows()(qbase 只读视图,holdout 双重焊死)
→ holder_sell_rules.select_first_events(§2B 冻结确定性规则:六类判别/首次识别/关联/去重/1%门)
→ EventRow 显式事件源 → runner.run_study(benchmark_mode='market' 单跑=人裁②,strata 不适用)
→ report.render。**只算+出报告+可选 dump,不改 ledger**(persist 另走状态机,人验收后)。

exp4=legacy registry 事件版白名单(§6:无需 schema 升级/不触发策略驱动);legacy 策略路径照旧 fail-closed。
用法:
  set -a; . /opt/quant/.env; set +a
  python -m taosha.harness.run_holder_sell_study --exp-id 4 --snapshot-id N [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

from taosha.compute.holder_sell_rules import (
    ADJUDICATION_FILE, ADJUDICATION_SHA256, load_adjudication, select_first_events)
from taosha.reader.contract import EventRow


def read_adjudication() -> dict:
    """冻结裁决表装载(规则 v2,人裁 2026-07-16):SHA256 前置断言在 load_adjudication,改动即拒。"""
    import os
    from taosha.compute import holder_sell_rules
    path = os.path.join(os.path.dirname(holder_sell_rules.__file__), ADJUDICATION_FILE)
    with open(path, "rb") as fh:
        return load_adjudication(fh.read())


def events_from_rows(rows: list[dict], listing: dict | None = None,
                     adjudication: dict | None = None) -> tuple[list[EventRow], dict]:
    """冻结语料行 → EventRow 显式事件源(纯函数,零I/O;规则 v2=人裁 2026-07-16 冻结件)。
    返回 (events, selection)——selection 全量留痕(counters/rejects/conflicts/diagnostics)入 result.audit。"""
    sel = select_first_events(rows, listing=listing, adjudication=adjudication)
    batch = rows[0]["snapshot_batch"] if rows else "batch?"
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["event_date"]),
                       event_type_layer="holder_sell",
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def split_sensitivity_events(sel_events: list[dict], rows: list[dict],
                             batch: str) -> tuple[list[EventRow], int]:
    """敏感性事件子集(人令 2026-07-16 五.5):排除全部含 holder 未解析公告的事件(纯函数)。"""
    unresolved = {r.get("announcement_id") for r in rows if not r.get("holder_name")}
    kept = [e for e in sel_events if not (set(e["announcement_ids"]) & unresolved)]
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["event_date"]),
                       event_type_layer="holder_sell",
                       snapshot_batch=batch)
              for e in kept]
    return events, len(sel_events) - len(kept)


def sensitivity_block(sens_result: dict, n_events_main: int, n_excluded: int) -> dict:
    """敏感性块(report-only,NOT_FOR_VERDICT;人令 2026-07-16 五.5+批复边界:同 manifest 同一次运行,
    删除整块后主 result 逐字节不变——本函数只读 sens_result、只构造新键,不触碰主 result 任何既有键)。
    显式不含 verdict/verdict_note:不产判决,不得在两套结果间择优改判。"""
    study = {k: sens_result[k] for k in
             ("n_events_total", "n_events_valid", "n_valid", "n_eff_rho",
              "sample_gate", "coverage", "car", "robustness")}
    n_kept = n_events_main - n_excluded
    return {
        "not_for_verdict": True,
        "label": "NOT_FOR_VERDICT · 数据质量敏感性复算,不产判决、不参与判决、不得择优改判",
        "basis": "人令2026-07-16五.5: 排除全部holder未解析事件后复算,观察身份缺失样本是否改变结论方向",
        "n_events_main": n_events_main,
        "n_events_excluded": n_excluded,
        "n_events_kept": n_kept,
        "excluded_share": (n_excluded / n_events_main) if n_events_main else None,
        "study": study,
    }


def main():
    # DB 依赖延迟导入:fixture(verify_holder_sell_adapter)零 DB 消费 events_from_rows
    from taosha.engine import report, runner
    from taosha.experiment import ledger
    from taosha.reader.view import ViewReader

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, required=True,
                    help="StudySnapshot manifest ID(硬化② fail-closed,无 manifest 拒运行)")
    ap.add_argument("--diagnostic", action="store_true",
                    help="只读诊断模式(通路预裁 2026-07-12):放行非 frozen 态;零台账写入;不产判决")
    ap.add_argument("--reason", default=None, help="诊断事由(--diagnostic 必填;STATE 登记)")
    ap.add_argument("--st-mode", choices=("event_day", "legacy_row0"), default="event_day")
    ap.add_argument("--json", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    row = ledger.get(a.exp_id)
    if row is None:
        raise SystemExit(f"exp_id={a.exp_id} 不存在")
    if a.diagnostic and not a.reason:
        raise SystemExit("诊断跑必须给 --reason(事由,STATE 登记;通路预裁 2026-07-12)")
    if a.st_mode == "legacy_row0" and not a.diagnostic:
        raise SystemExit("st_mode=legacy_row0 仅限 --diagnostic 只读诊断域")
    if a.diagnostic:
        print("=" * 72)
        print("=== DIAGNOSTIC 只读诊断(不产判决,零台账写入;通路预裁 2026-07-12)===")
        print(f"=== 事由: {a.reason} | exp_id={a.exp_id} status={row['status']} ===")
        print("=" * 72, flush=True)
    elif row["status"] != "frozen":
        raise SystemExit(f"铁律③:引擎拒执行 status={row['status']}≠frozen(exp_id={a.exp_id})")

    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    print(f"exp_id={a.exp_id} {row['family']}/{row['title']} status={row['status']} "
          f"family_trial={row['family_trial']} verdict_power={row['verdict_power']}", flush=True)
    print(f"pap window={pap.get('window')!r} benchmark=market(全市场等权单跑,人裁② 2026-07-15)", flush=True)

    vr = ViewReader(snapshot_id=a.snapshot_id)
    rows_hs = vr.holder_sell_rows()
    events, sel = events_from_rows(rows_hs, listing=vr.listing(),
                                   adjudication=read_adjudication())
    # 事件票取数(非全宇宙),两次构造承 #2b sample=池宇宙范式
    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    print(f"holder_sell 行={sel['counters']['input']} → 事件={len(events)}"
          f"(六类/首次/关联/去重/1%门留痕入 audit)", flush=True)

    result = runner.run_study(reader, pap, benchmark_mode="market",
                              events=events, strata_enabled=False, st_mode=a.st_mode)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["holder_sell_selection"] = {
        "counters": sel["counters"],
        "reject_reasons": _reason_counts(sel["rejects"]),
        "cross_stock_id_conflicts": sel["conflicts"],
        "midkey_candidates_30d": sel["diagnostics"]["midkey_candidates_30d"],
        "adjudication_sha256": ADJUDICATION_SHA256,
    }

    # 敏感性块(人令 2026-07-16 五.5):同 manifest 同一次运行,主 result 键零触碰(仅新增一键)
    batch = rows_hs[0]["snapshot_batch"] if rows_hs else "batch?"
    sens_events, n_excl = split_sensitivity_events(sel["events"], rows_hs, batch)
    sens_reader = ViewReader(snapshot_id=a.snapshot_id,
                             sample={e.ts_code for e in sens_events})
    print(f"敏感性复算(NOT_FOR_VERDICT): 主事件={len(events)} 排除(holder未解析)={n_excl} "
          f"保留={len(sens_events)}", flush=True)
    sens_result = runner.run_study(sens_reader, pap, benchmark_mode="market",
                                   events=sens_events, strata_enabled=False, st_mode=a.st_mode)
    result["sensitivity_holder_resolved_only"] = sensitivity_block(
        sens_result, len(sel["events"]), n_excl)
    if a.diagnostic:
        result["diagnostic"] = {"diagnostic": True, "reason": a.reason, "st_mode": a.st_mode,
                                "exp_status_at_run": row["status"],
                                "note": "只读诊断: 零台账写入、不产判决;产物不得作 result 槽载荷"}

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


def _reason_counts(rejects: list[dict]) -> dict:
    out: dict = {}
    for x in rejects:
        out[x["reason"]] = out.get(x["reason"], 0) + 1
    return out


if __name__ == "__main__":
    main()
