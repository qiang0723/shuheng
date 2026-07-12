"""驱动:对真实数据跑 #2b 策略版(附录B B1+附录G = 台账 exp_id 3)→ 策略版结果(步③模块③)。

与 run_drawdown_study(事件版)同形制:读台账**已冻结** pap(铁律③)→ b1 池宇宙 → ViewReader
→ drawdown_events 生成进场事件(附录F-rev1 + b1 池 PIT 过滤,**与事件版同一事件源代码路径=同源**)
→ engine.drawdown_strategy.run_strategy(同源清洗 → 附录G 持有路径 → 净收益 → ADJ-BMP 四件套
+ skew-adjusted t + DSR)。判决权归事件版(四件套④):本驱动不产/不改台账 verdict。

**本驱动只【算 + 出 JSON dump】,不改 ledger 状态**(result 落台账走 persist 状态机,人验收后另跑)。
红线:一个数不改 pap(铁律④);输出只陈述统计事实、无建议口吻(铁律⑤)。
用法:
  set -a; . /opt/quant/.env; set +a
  python -m taosha.harness.run_drawdown_strategy --exp-id 3 --snapshot-id N [--json OUT]
"""
from __future__ import annotations

import argparse
import json

from taosha.engine.drawdown_events import generate_events, to_event_rows
from taosha.engine.drawdown_strategy import run_strategy
from taosha.experiment import ledger
from taosha.reader.view import ViewReader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, default=3)
    ap.add_argument("--snapshot-id", type=int, required=True,
                    help="StudySnapshot manifest ID(硬化② fail-closed,无 manifest 拒运行)")
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
    print("策略版(附录B B1+附录G;判决权归事件版) benchmark=pool_pit(b1 池同跨度买入持有)", flush=True)

    # ── 事件源 = 与事件版完全同一代码路径(同源硬项):池成员 PIT → 生成 → 池过滤 ────────
    membership = ViewReader(snapshot_id=a.snapshot_id).pool_membership()
    if not membership:
        raise SystemExit("pool_b1_snap 空:核对 manifest 批次向量/先跑 seed_pool_b1(003)预计算池成员")
    universe = set().union(*membership.values())
    print(f"b1 池:评估日 {len(membership)} 天,池宇宙={len(universe)} 票", flush=True)

    def in_pool(ts, d):
        return ts in membership.get(d, ())

    reader = ViewReader(snapshot_id=a.snapshot_id, sample=universe)
    events = generate_events(reader, in_pool=in_pool)
    print(f"#2b 进场事件(池内)= {len(events)} 条(与事件版同一生成路径)", flush=True)
    if not events:
        raise SystemExit("池内进场事件为 0:核对事件定义/池成员(数据盲下不自行放宽)")

    snap = pap.get("snapshot_batch_req", "SYNTH")
    event_rows = to_event_rows(events, snapshot_batch=snap if isinstance(snap, str) else "b1_pool")

    result = run_strategy(reader, pap, event_rows)

    # 复现留痕(spec §9;硬化②: 批次=manifest 指定,audit 同记 manifest ID 与 digest)
    snap_info = reader.snapshot_info
    result["audit"]["study_snapshot"] = snap_info
    result["audit"]["pool_snapshot"] = {
        "pool_b1_batch": snap_info["content"]["taosha"]["pool_b1"],
        "pool_return_batch": snap_info["content"]["taosha"]["pool_b1_return"],
        "note": "b1 池成员=pool_b1_snap(manifest 路由);池等权基准=pool_b1_return_snap(manifest 路由)。",
    }

    sv = result["strategy_version"]
    print(f"\n消费事件 n={sv['n_consumed']}(同源存活 {sv['n_survivors_sourced']};闸 "
          f"{sv['sample_gate']['state']});净均值={_f(sv['net']['mean'])} "
          f"毛超额={_f(sv['bhar_gross']['mean'])} 净超额={_f(sv['bhar']['mean'])} "
          f"adj_z(毛主检验)={_f(sv['adj_bmp_bhar_gross']['adj_z'])} "
          f"[{sv['adj_bmp_bhar_gross']['sig_state']}(判决权归事件版)] "
          f"adj_z(净并报)={_f(sv['adj_bmp_bhar']['adj_z'])} "
          f"t_sa(毛)={_f(sv['skew_adjusted_t_gross']['t_sa'])} "
          f"DSR={_f((sv['dsr'] or {}).get('dsr'))}", flush=True)

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
        print(f"result_json → {a.json}", flush=True)
    if a.report:
        from taosha.engine.report import render_strategy
        rendered = render_strategy(result)
        with open(a.report, "w") as fh:
            fh.write(rendered)
        print(f"report → {a.report}", flush=True)


def _f(x):
    return "NA" if x is None else f"{x:.6f}"


if __name__ == "__main__":
    main()
