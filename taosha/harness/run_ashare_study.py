"""驱动:对 A股合成 fixture 跑完整引擎(reader→clean→compute→gates→report)。

切片2 骨架闭环 + item 6/7/8/9 的合成验收跑通证据来源(非落库;落库见 persist.py)。
用法:python -m taosha.harness.run_ashare_study --prices P --events E [--json OUT]
"""
from __future__ import annotations

import argparse
import json

from taosha.engine import report, runner
from taosha.experiment import pap as pap_mod
from taosha.reader.synthetic import SyntheticReader


def synth_pap() -> dict:
    """SYNTH 冒烟假设的 pap_json(合成验收用;字段转录自 §6 冻结通用件)。"""
    p = pap_mod.build_pap(
        event_def={"kind": "SYNTH_SMOKE", "anchor": "first_ann_date", "layer": "预喜"},
        # 检验窗从 pap 读(裁定 2026-07-07):合成回归桩喂**原短窗**文本"后3/6日"
        # → parse_test_windows=(3,6)点 = 原 frozen [0,+2]/[0,+5] 的 MAIN_LEN/ROBUST_LEN(3/6)
        # → 检验窗从 pap 读的重构对合成域结果**逐字节不变**(约束③);真实 #4 pap="后20/60日"。
        window="T+1起,后3/6日",
        pool={"kind": "全市场等权(合成)"},
        cleaning={"est_window": [-250, -91], "coverage_min": "112/160(70%)",
                  "suspension": "事件落停牌期剔除", "st": "剔除", "one_word": "顺延"},
        snapshot_batch_req="SYNTH",
    )
    # 可交易口径 cost 块(选项2;合成域也走该口径出新键,rates 对齐真实 exp_id5 pap 冻结值)
    p["cost"] = {"commission": 0.00025, "stamp_tax_sell": 0.001, "slippage_oneway": 0.001,
                 "limit_up_board_untradeable": True}
    p["_family_trial"] = 1
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    reader = SyntheticReader(a.prices, a.events)
    result = runner.run_study(reader, synth_pap(), benchmark_mode="market")
    print(report.render(result))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
        print(f"\nresult_json → {a.json}")


if __name__ == "__main__":
    main()
