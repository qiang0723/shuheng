from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "stage_review_analysis.ipynb"


def code(source: str):
    return nbf.v4.new_code_cell(source.strip())


def markdown(source: str):
    return nbf.v4.new_markdown_cell(source.strip())


cells = [
    markdown(
        """
## tl;dr

- 截至 2026-07-31（UTC+8），校准册正好 10 条：方向 5 命中 / 5 未命中。
- 10 条里只有 exp568 为 `SIG`，且效力为 `llm/prescreen`；4 条已完成的真实 `full` 研究全部 `NOT_SIG`。
- 当前证据支持暂停连续排产一个工作日，先收紧上游假设生成与排序；不支持把现有结果解释为已发现稳定 alpha。
"""
    ),
    markdown(
        """
## Context & Methods

目标：决定下一步是继续直接运行第 11 条校准实验，还是先修正假设供给与排产规则。

### Key Assumptions

- 校准方向以各实验 persist/闭卷档为权威；统计结果与台账状态来自阿里云 `experiment.result_json` 的只读抽取。
- `synthetic_smoke` 是平台冒烟，不计入真实研究的显著率。
- 方向命中只检验符号，不代表统计显著、经济显著或可交易。
- 不跨实验比较 CAAR 绝对大小，因为事件定义、signed 语义与样本结构不同。
"""
    ),
    markdown("## Data\n\n输入是同目录下的 `calibration_results.csv` 与 `ledger_snapshot.csv`。"),
    code(
        """
import csv
import math
from collections import Counter
from pathlib import Path

BASE = Path.cwd()

def load_csv(name):
    with (BASE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

calibration = load_csv("calibration_results.csv")
ledger = load_csv("ledger_snapshot.csv")

len(calibration), len(ledger)
"""
    ),
    markdown("### Validate inputs"),
    code(
        """
assert len(calibration) == 10
assert len({row["exp_id"] for row in calibration}) == 10
assert Counter(row["direction_hit"] for row in calibration) == Counter({"true": 5, "false": 5})
assert Counter(row["verdict"] for row in calibration) == Counter({"NOT_SIG": 9, "SIG": 1})
assert len(ledger) == 26
assert Counter(row["status"] for row in ledger) == Counter(
    {"done": 14, "registered": 8, "frozen": 2, "closed": 2}
)
print("Input checks: PASS")
"""
    ),
    markdown("## Results"),
    code(
        """
def wilson_interval(successes, total, z=1.959963984540054):
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius

hits = sum(row["direction_hit"] == "true" for row in calibration)
sig_calibrated = sum(row["verdict"] == "SIG" for row in calibration)
real_done = [row for row in ledger if row["status"] == "done" and row["family"] != "synthetic_smoke"]
real_sig = [row for row in real_done if row["verdict"] == "SIG"]
full_done = [row for row in real_done if row["verdict_power"] == "full"]
full_sig = [row for row in full_done if row["verdict"] == "SIG"]

summary = {
    "direction_hits": f"{hits}/10",
    "direction_hit_rate": hits / 10,
    "direction_hit_wilson_95": wilson_interval(hits, 10),
    "calibrated_sig": f"{sig_calibrated}/10",
    "real_study_sig": f"{len(real_sig)}/{len(real_done)}",
    "full_study_sig": f"{len(full_sig)}/{len(full_done)}",
    "ledger_status": dict(Counter(row["status"] for row in ledger)),
}
summary
"""
    ),
    markdown("### Ten calibration observations"),
    code(
        """
for row in calibration:
    outcome = "hit" if row["direction_hit"] == "true" else "miss"
    print(
        f'{row["calibration_order"]:>2}. exp{row["exp_id"]:<3} '
        f'{row["family"]:<28} {outcome:<4} {row["verdict"]:<7} '
        f'ADJ-BMP={float(row["adj_bmp"]):+.3f}'
    )
"""
    ),
    markdown("### Reasonableness checks"),
    code(
        """
assert {row["exp_id"] for row in real_sig} == {"568"}
assert len(full_done) == 4 and not full_sig
assert sum(int(row["n_valid"]) <= int(row["n_events"]) for row in calibration) == 10
assert sum(int(row["main_n"]) <= int(row["n_valid"]) for row in calibration) == 10
print("Portfolio checks: PASS")
print(f"Direction hit 95% Wilson interval: {summary['direction_hit_wilson_95'][0]:.1%}–{summary['direction_hit_wilson_95'][1]:.1%}")
print(f"Real-study SIG rate: {len(real_sig)}/{len(real_done)}")
print(f"Full-power SIG rate: {len(full_sig)}/{len(full_done)}")
"""
    ),
    markdown(
        """
## Takeaways

1. **研究流水线已经可用，但 alpha 尚未建立。** 10 条方向命中率为 50%，95% Wilson 区间很宽；不能据此声称预测能力高于随机。
2. **唯一真实 `SIG` 是 exp568，且只是 `llm/prescreen`。** 它应被视为值得 human/full 重做的线索，而不是可交易结论。
3. **下一步瓶颈在假设供给，不在运行吞吐。** 六周期目标已超额，继续跑相似 prescreen 的边际信息低于先做一次上游时间戳与来源纪律复盘。
4. **建议的下一个研究动作是窄闸而非正式运行。** 先完成分析师预期类时间戳口径核查；若仍选择现有池，则优先对 exp18 `audit_qualified` 做只读窄闸，不直接冻结。
"""
    ),
]

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
)

client = NotebookClient(
    notebook,
    timeout=120,
    kernel_name="python3",
    resources={"metadata": {"path": str(BASE)}},
)
executed = client.execute()
nbf.write(executed, OUTPUT)
print(OUTPUT)
