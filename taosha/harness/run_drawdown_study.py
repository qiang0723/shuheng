"""驱动:对真实数据跑 #2b(回撤反抽·b1 池 事件版 = 台账 exp_id 3)端到端 → 体检报告(切片3 步②)。

读台账**已冻结** pap(铁律③;引擎拒 status≠frozen)→ b1 池宇宙(pool_b1_membership 全期成员并集)
→ ViewReader(sample=池宇宙)→ engine.drawdown_events 从后复权收盘价 PIT 生成进场事件(附录F-rev1
状态机)+ b1 池 PIT 过滤(进场日在当日池快照)→ runner.run_study(benchmark_mode='pool_pit' b1池等权PIT
活基准、events=生成事件、strata_enabled=False 三层不适用)→ report.render。

与 #4(run_forecast_study)对照:#4 事件读台账 forecast_snap、基准=全市场等权;#2b 事件从价格模式生成、
基准=b1 池等权 PIT(reader.pool_return,基准成分逐日=当日池快照)。流水线沿用 #4 全套(删失诊断/板块
分层/剔除分解/N_valid+折算N_eff/可交易口径),额外 D1/D2/D3 事件生成诊断入报告;三层(预喜/预亏/扭亏)
不适用。策略版(附录B 成本−20%强平或破20日线先到先出)=步③另跑,本驱动只跑事件版。

**本驱动只【算 + 出报告 + 可选 dump】,不改 ledger 状态**(result 落台账走 persist 状态机,人验收后另跑)。
红线(taosha CLAUDE.md):一个数不改 pap(铁律④);报告只陈述统计事实、无建议口吻(铁律⑤)。
用法:
  set -a; . /opt/quant/.env; set +a
  python -m taosha.harness.run_drawdown_study --exp-id 3 [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import json

from taosha.engine import report, runner
from taosha.engine.drawdown_events import generate_events, to_event_rows
from taosha.experiment import ledger
from taosha.reader.view import ViewReader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, default=3)
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
    print(f"exp_id={a.exp_id} {row['family']}/{row['title']} "
          f"status=frozen family_trial={row['family_trial']} verdict_power={row['verdict_power']}",
          flush=True)
    print(f"pap window={pap.get('window')!r} benchmark=pool_pit(b1 池等权 PIT 活基准,#2b)", flush=True)

    # ── b1 池成员快照(PIT)+ 池宇宙(全期成员并集=事件生成取数样本)────────────────
    membership = ViewReader().pool_membership()   # {trade_date: frozenset(ts_code)}(pool_b1_current)
    if not membership:
        raise SystemExit("pool_b1_current 空:先跑 seed_pool_b1(003)预计算池成员")
    universe = set().union(*membership.values())
    print(f"b1 池:评估日 {len(membership)} 天,池宇宙(全期成员并集)={len(universe)} 票", flush=True)

    def in_pool(ts, d):
        return ts in membership.get(d, ())

    # ── ViewReader(sample=池宇宙:只拉池宇宙票的价,非全市场 15M 行)────────────────
    reader = ViewReader(sample=universe)

    # ── 事件生成(附录F-rev1 PIT 状态机)+ b1 池 PIT 过滤(进场日在当日池快照)──────
    events = generate_events(reader, in_pool=in_pool)
    print(f"#2b 进场事件(池内)= {len(events)} 条", flush=True)
    if not events:
        raise SystemExit("池内进场事件为 0:核对事件定义/池成员(数据盲下不自行放宽)")

    snap = pap.get("snapshot_batch_req", "SYNTH")
    event_rows = to_event_rows(events, snapshot_batch=snap if isinstance(snap, str) else "b1_pool")

    # ── 跑流水线(benchmark_mode='pool_pit'、events=生成事件、strata 关)───────────
    result = runner.run_study(reader, pap, benchmark_mode="pool_pit",
                              events=event_rows, strata_enabled=False)

    # 复现留痕(spec §9):记池成员批次 + 池等权基准批次(引擎读表不现算,批次可溯源)。
    #   批次号从引擎可读的数据表(membership/return,带 batch_id 列)取 max,不读 *_batch 元表(不扩权)。
    result["audit"]["pool_snapshot"] = {
        "pool_b1_batch": _batch_id(reader, "pool_b1_membership"),
        "pool_return_batch": _batch_id(reader, "pool_b1_return"),
        "note": "b1 池成员=pool_b1_current(max batch);池等权基准=pool_b1_return_current(max batch);"
                "基准成分逐日=当日池快照(验收硬项:seed_pool_b1_return --verify)。",
    }

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


def _batch_id(reader, table):
    """读 taosha 表的 max batch_id(复现留痕;失败不阻断报告,记 None)。"""
    try:
        with reader._connect(reader._tdsn) as c, c.cursor() as cur:
            cur.execute(f"SELECT max(batch_id) FROM {table}")
            return cur.fetchone()[0]
    except Exception:
        return None


if __name__ == "__main__":
    main()
