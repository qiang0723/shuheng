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
