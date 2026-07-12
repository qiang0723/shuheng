"""驱动:对真实数据跑 #4(业绩预告漂移 = 台账 exp_id)端到端 → 体检报告(切片3 步7)。

读台账**已冻结** pap(铁律③;引擎拒 status≠frozen)→ ViewReader() 全事件票 → runner.run_study
(benchmark_mode='market' 全市场等权,读 market_return_current 表)→ report.render。

**本驱动只【算 + 出报告 + 可选 dump】,不改 ledger 状态**——result 落台账 exp_id result 槽是一次性写入
(触发器焊死),须人验收报告后另走 persist 既有状态机路径(start_running→finish),不在本驱动抢跑。

红线(taosha CLAUDE.md):一个数不改 pap(铁律④);报告只陈述统计事实、无建议口吻(铁律⑤)。
用法:
  set -a; . /opt/quant/.env; set +a   # TAOSHA_APP_DSN(ledger 读 pap);ViewReader 另从 .env 取引擎 DSN
  python -m taosha.harness.run_forecast_study --exp-id 5 --snapshot-id N [--json OUT] [--report OUT]
硬化②: 取数全按 StudySnapshot manifest 路由(先 python -m taosha.experiment.snapshot --create)。
"""
from __future__ import annotations

import argparse
import json

from taosha.engine import report, runner
from taosha.experiment import ledger
from taosha.reader.view import ViewReader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, required=True,
                    help="StudySnapshot manifest ID(硬化② fail-closed,无 manifest 拒运行)")
    ap.add_argument("--diagnostic", action="store_true",
                    help="只读诊断模式(通路预裁 2026-07-12):放行非 frozen 态;零台账写入;不产判决")
    ap.add_argument("--reason", default=None,
                    help="诊断事由(--diagnostic 必填;入产物 JSON 并 STATE 登记)")
    ap.add_argument("--st-mode", choices=("event_day", "legacy_row0"), default="event_day",
                    help="ST 判定源(硬化③;legacy_row0 仅 --diagnostic 域可用)")
    ap.add_argument("--json", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    row = ledger.get(a.exp_id)
    if row is None:
        raise SystemExit(f"exp_id={a.exp_id} 不存在")
    if a.diagnostic and not a.reason:
        raise SystemExit("诊断跑必须给 --reason(事由,STATE 登记;通路预裁 2026-07-12)")
    if a.st_mode == "legacy_row0" and not a.diagnostic:
        raise SystemExit("st_mode=legacy_row0 仅限 --diagnostic 只读诊断域(生产禁用旧缺陷口径)")
    if a.diagnostic:
        print("=" * 72)
        print("=== DIAGNOSTIC 只读诊断(不产判决,零台账写入;通路预裁 2026-07-12)===")
        print(f"=== 事由: {a.reason} | st_mode={a.st_mode} | exp_id={a.exp_id} status={row['status']} ===")
        print("=" * 72, flush=True)
    elif row["status"] != "frozen":
        raise SystemExit(f"铁律③:引擎拒执行 status={row['status']}≠frozen(exp_id={a.exp_id})"
                         "(诊断重跑走 --diagnostic 只读通路,通路预裁 2026-07-12)")
    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    print(f"exp_id={a.exp_id} {row['family']}/{row['title']} "
          f"status={row['status']} family_trial={row['family_trial']} verdict_power={row['verdict_power']}",
          flush=True)
    print(f"pap window={pap.get('window')!r} benchmark=market(全市场等权,#4 单跑)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id)
    result = runner.run_study(reader, pap, benchmark_mode="market", st_mode=a.st_mode)
    # 硬化②: result.audit 同记 manifest ID 与 digest(+批次向量)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    if a.diagnostic:
        result["diagnostic"] = {"diagnostic": True, "reason": a.reason, "st_mode": a.st_mode,
                                "exp_status_at_run": row["status"],
                                "note": "只读诊断: 零台账写入、不产判决(通路预裁 2026-07-12);产物不得作 result 槽载荷"}

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
