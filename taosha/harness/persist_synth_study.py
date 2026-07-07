"""item 11 落库实测驱动(S2-DEC2:专设合成冒烟登记行)。在 aliyun 跑(需 TAOSHA_APP_DSN)。

流程:生成合成 fixture → 跑引擎 → persist_study 走 registered→frozen→running→done 既有路径
落 result_json → 验收(status=done / result 含 n_eff+剔除率 / 二次 finish 被拒 / DELETE 被拒)。
不写六条创始行;不另建通路。

用法(aliyun,先 source /opt/quant/.env 使 TAOSHA_APP_DSN 生效,勿回显):
  python -m taosha.harness.persist_synth_study --prices P --events E
"""
from __future__ import annotations

import argparse

from taosha.experiment import ledger, persist
from taosha.engine import runner
from taosha.harness.run_ashare_study import synth_pap
from taosha.reader.synthetic import SyntheticReader

SMOKE = dict(
    family="synthetic_smoke",
    title="[SMOKE] slice2合成落库验收",
    source_type="llm",                 # 触发器强制 verdict_power=prescreen
    verdict_power="prescreen",
    contamination_note="切片2合成fixture,非真实结论,勿用于判决(S2-DEC2)",
    data_class="synthetic",
    crowding_prior="n/a",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--events", required=True)
    a = ap.parse_args()

    reader = SyntheticReader(a.prices, a.events)
    pap = synth_pap()
    result = runner.run_study(reader, pap, benchmark_mode="market")
    print(f"引擎跑通:verdict={result['verdict']} N_eff={result['n_eff']} "
          f"剔除率={result['rejections']['reject_ratio']:.4f}")

    exp_id = persist.persist_study(result, pap=pap, **SMOKE)
    print(f"落库 OK:exp_id={exp_id}(registered→frozen→running→done 既有路径)")

    # ── 验收 ──────────────────────────────────────────────────────────────
    row = ledger.get(exp_id)
    assert row["status"] == "done", row["status"]
    assert row["result_json"]["n_eff"] == result["n_eff"]
    assert "reject_ratio" in row["result_json"]["rejections"]
    assert row["source_type"] == "llm" and row["verdict_power"] == "prescreen"
    print(f"  验收①: status=done / result 含 n_eff={row['result_json']['n_eff']} "
          f"+ 剔除率={row['result_json']['rejections']['reject_ratio']:.4f}(N_eff 与剔除率同报)")

    # 二次 finish 被拒(result 一次性;done 态无法再 running→done)
    try:
        ledger.finish(exp_id, {"tamper": 1})
        raise SystemExit("✗ 二次 finish 未被拒(触发器失效!)")
    except RuntimeError:
        print("  验收②: 二次 finish 被拒(status 非 running;result 一次性)")

    # DELETE 被拒(append-only 触发器)
    conn = ledger.connect()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM experiment WHERE exp_id=%s", (exp_id,))
                conn.rollback()
                raise SystemExit("✗ DELETE 未被拒(append-only 触发器失效!)")
            except Exception as e:
                conn.rollback()
                if "append-only" in str(e):
                    print("  验收③: DELETE 被拒(append-only 焊死)")
                else:
                    raise
    finally:
        conn.close()

    print(f"\nitem 11 落库实测 PASS:合成冒烟行 exp_id={exp_id} 永久留台账、append-only、result 一次性。")


if __name__ == "__main__":
    main()
