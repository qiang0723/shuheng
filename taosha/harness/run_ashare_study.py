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
        window={"tau0": "T+1(首个可交易日,S2-DEC3)", "main": [0, 2], "robust": [0, 5]},
        pool={"kind": "全市场等权(合成)"},
        cleaning={"est_window": [-250, -91], "coverage_min": "112/160(70%)",
                  "suspension": "事件落停牌期剔除", "st": "剔除", "one_word": "顺延"},
        snapshot_batch_req="SYNTH",
    )
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
