from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "cycle_end_review_analysis.ipynb"


def code(source: str):
    return nbf.v4.new_code_cell(source.strip())


def markdown(source: str):
    return nbf.v4.new_markdown_cell(source.strip())


cells = [
    markdown(
        """
# 六周期期末复盘底稿 v1

**DRAFT / NOT-FINAL · 2026-08-12 · Asia/Shanghai（UTC+8）**

## tl;dr

- 台账快照有 16 条 `done`；剔除 exp7 `synthetic_smoke` 后为 **15 条正式真实研究**。
- 其中 12 条进入方向校准册：**5 命中 / 7 未命中**。方向命中不等于显著或可交易。
- 唯一真实 `SIG` 是 exp568，效力仍为 `llm/prescreen`；4 条真实 `full` 研究全部 `NOT_SIG`。
- exp18 / exp21 / exp23 均在公告证据硬门 fail-closed；exp22 在官方分页集合漂移后跨期暂停。
- 8 月 25 日只做最终只读增量核对与签字，不是复盘首次开工日。
"""
    ),
    markdown(
        """
## Context & Methods

本底稿回答两个问题：当前研究组合积累了多少可复核证据；下一周期的主要瓶颈是统计能力、研究吞吐，还是公司公告证据链。

### Key assumptions

- 结果与台账使用 2026-08-09 22:14:05.537694（UTC+8）的已外审只读快照；研发停点使用 2026-08-12 的 STATE 与对应权威档。两时点不合并。
- `synthetic_smoke` 只用于平台冒烟，不计入正式真实研究。
- 方向命中由 `predicted_direction` 与主窗 CAAR 符号重新推导，不信任 CSV 的 `direction_hit` 自报值。
- exp18 / exp21 / exp23 的分子分母是抽核结果；exp22 的 51/646 是合法路由 marker 进度，四者不可作同类比率比较。
- 本底稿不是最终期末签字件；2026-08-25 必须重新执行只读增量核对。
"""
    ),
    markdown("## Data\n\n输入为同目录的台账、校准、硬门与 exp22 失败链 CSV。"),
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
gates = load_csv("evidence_bottlenecks.csv")
exp22_chain = load_csv("exp22_failure_chain.csv")

len(calibration), len(ledger), len(gates), len(exp22_chain)
"""
    ),
    markdown("### Validate ledger and independently re-derive calibration"),
    code(
        """
assert len(ledger) == 26
assert Counter(row["status"] for row in ledger) == Counter(
    {"registered": 6, "frozen": 2, "done": 16, "closed": 2}
)
real_done = [row for row in ledger if row["status"] == "done" and row["family"] != "synthetic_smoke"]
assert len(real_done) == 15

assert len(calibration) == 12
assert len({row["exp_id"] for row in calibration}) == 12

def derived_hit(row):
    caar = float(row["caar"])
    actual = "positive" if caar > 0 else "negative" if caar < 0 else "zero"
    return actual == row["predicted_direction"]

for row in calibration:
    assert derived_hit(row) == (row["direction_hit"] == "true")
    assert int(row["main_n"]) <= int(row["n_valid"]) <= int(row["n_events"])

assert Counter(derived_hit(row) for row in calibration) == Counter({False: 7, True: 5})
print("Ledger and calibration checks: PASS")
"""
    ),
    markdown("## Portfolio results"),
    code(
        """
def wilson_interval(successes, total, z=1.959963984540054):
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius

hits = sum(derived_hit(row) for row in calibration)
real_sig = [row for row in real_done if row["verdict"] == "SIG"]
full_done = [row for row in real_done if row["verdict_power"] == "full"]
full_sig = [row for row in full_done if row["verdict"] == "SIG"]
wilson = wilson_interval(hits, len(calibration))

assert {row["exp_id"] for row in real_sig} == {"568"}
assert len(full_done) == 4 and not full_sig
assert {row["exp_id"] for row in real_done} - {row["exp_id"] for row in calibration} == {"3", "4", "5"}

summary = {
    "formal_real_done": len(real_done),
    "direction_calibrated": len(calibration),
    "direction_hits": hits,
    "direction_misses": len(calibration) - hits,
    "direction_hit_rate": hits / len(calibration),
    "direction_hit_wilson_95": wilson,
    "real_sig": len(real_sig),
    "full_done": len(full_done),
    "full_sig": len(full_sig),
}
summary
"""
    ),
    markdown("### Twelve calibration observations"),
    code(
        """
for row in calibration:
    outcome = "hit" if derived_hit(row) else "miss"
    print(
        f'{int(row["calibration_order"]):>2}. exp{int(row["exp_id"]):<3} '
        f'{row["family"]:<28} {outcome:<4} {row["verdict"]:<7} '
        f'CAAR={float(row["caar"]):+.4%} ADJ-BMP={float(row["adj_bmp"]):+.3f}'
    )

print(f"Direction hit 95% Wilson interval: {wilson[0]:.1%}–{wilson[1]:.1%}")
print(f"Formal-real SIG: {len(real_sig)}/{len(real_done)}")
print(f"Full-power SIG: {len(full_sig)}/{len(full_done)}")
"""
    ),
    markdown("## Evidence bottlenecks"),
    code(
        """
assert {row["exp_id"] for row in gates} == {"18", "21", "22", "23"}
gate = {row["exp_id"]: row for row in gates}
assert int(gate["18"]["numerator"]) + 10 == int(gate["18"]["denominator"]) == 22
assert 1 + 21 + 1 == int(gate["21"]["denominator"]) == 23
assert int(gate["23"]["numerator"]) + 13 == int(gate["23"]["denominator"]) == 28
assert int(gate["22"]["numerator"]) == 51 <= int(gate["22"]["denominator"]) == 646
assert gate["22"]["metric_kind"] == "route_progress"
assert len(exp22_chain) == 8
assert [row["version"] for row in exp22_chain] == [f"v{i}" for i in range(1, 9)]
assert all(row["outcome"] == "FAIL" for row in exp22_chain)
print("Evidence-gate checks: PASS")
"""
    ),
    markdown(
        """
## Count reconciliation

旧 STATE 的“判决闭卷 14 条”是 exp14 完成后未同步递增的滚动叙述，不是另一套样本定义。已外审台账快照的可重导口径是：`done=16`，剔除 exp7 `synthetic_smoke` 后为 **15 条正式真实 done**。其中 12 条有方向密封并进入校准册；exp3 / exp4 / exp5 三条早期正式 `full` 研究没有进入当前方向校准序列。

本底稿采用三层定义并停止混称：

1. 台账 `done`：16 条；
2. 正式真实 `done`：15 条；
3. 方向校准册：12 条，5 命中 / 7 未命中。
"""
    ),
    markdown(
        """
## Takeaways

1. **工程吞吐不是当前主瓶颈。** 正式真实研究已达 15 条，状态机、单次运行、persist、规模与架构棘轮均已形成稳定闭环。
2. **alpha 证据仍弱。** 12 条方向校准的 Wilson 区间很宽；唯一真实 `SIG` 仍是 exp568 且只有 `llm/prescreen` 效力，4 条 `full` 研究全部 `NOT_SIG`。
3. **公告证据工程成为系统性瓶颈。** exp18 / exp21 / exp23 在不同联合证据门停止；exp22 连续 v1–v8 因官方分页集合不稳定跨期暂停。正确动作是保留 fail-closed，而不是降低首次披露、金额、方案身份或用途标准。
4. **8 月 25 日做定版，不做首次分析。** 现在完成底稿与外审；届时只读补差、修订、签字并裁下一周期排产。
"""
    ),
    markdown(
        """
## Further Questions for 2026-08-25

- 下一周期是否把资源从“更多 prescreen 题目”转向“官方公告证据合同和 human/full 复验”？
- exp18 / exp21 / exp23 / exp22 四连停点，哪些值得投入证据工程，哪些应继续封存？
- exp568 是否值得另立 human/full 复验，同时把可成交性作为新假设边界，而不是事后改写原实验？
- 是否把“正式真实 done / 方向校准 / 判决闭卷”三种计数定义写成持久化治理规则，避免滚动 STATE 再次滞后？
"""
    ),
    markdown(
        """
## Caveats and Assumptions

- 结果快照截至 2026-08-09，研发状态截至 2026-08-12；本稿不把两者伪装成同一“最新”时点。
- 方向命中不代表统计显著、经济显著或可交易；`NOT_SIG` 也不得改写成“证明无效应”。
- exp568 的 trial 2 双侧临界值是 **±2.241**，不是通用图上的名义 ±1.96；其 `SIG` 不得升级为荐股依据。
- exp22 的 51/646 是合法路由 marker 进度，不是公告证据通过率，不能与 12/22、1/23、15/28 并列比较优劣。
- 本稿为 DRAFT / NOT-FINAL；2026-08-25 签字前必须刷新只读快照并复核所有增量。
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
    kernel_name="shuheng-tmp",
    resources={"metadata": {"path": str(BASE)}},
)
executed = client.execute()
nbf.write(executed, OUTPUT)
print(OUTPUT)
