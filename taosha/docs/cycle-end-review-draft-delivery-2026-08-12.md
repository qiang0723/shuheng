# 六周期期末复盘底稿 v1 · 交付

时间口径：2026-08-12，Asia/Shanghai（UTC+8）。

状态：**DRAFT / NOT-FINAL；已验证，可交 Fable 限域复核。**

## 交付件

目录：`taosha/docs/cycle-end-review-draft-2026-08-12/`

- 权威输入：`extract.sql`、`ledger_snapshot.csv`、`calibration_results.csv`、`current-readback-2026-08-12.md`；
- 证据停点：`evidence_bottlenecks.csv`、`exp22_failure_chain.csv`；
- 可执行分析：`build_notebook.py`、`cycle_end_review_analysis.ipynb`；
- 报告：`build_report_artifact.py`、`artifact.json`、`cycle_end_review_report.html`；
- 验证：`validation.md`。

## 核心结果

1. 当前台账仍为 26=`6/2/16/2`；正式真实 `done=15`，不是旧 STATE 滞后叙述的 14；
2. 方向校准 12 条=`5 命中 / 7 未命中`，Wilson 95% 约 19.3%–68.0%；
3. 唯一真实 `SIG` 仍为 exp568，且只有 `llm/prescreen` 效力；4 条真实 `full` 研究全部 `NOT_SIG`；
4. exp18 / exp21 / exp23 在不同公告证据联合硬门停止；exp22 v1–v8 因官方分页集合漂移跨期暂停；
5. 当前瓶颈是官方公告证据合同，而不是统计内核或研究运行吞吐；
6. 2026-08-25 只做新的只读增量核对、最终修订、签字与下一周期排产裁定，不再等到当天才开始分析。

## 计数补正

旧 STATE 的“判决闭卷14条”在 exp14 persist 后未同步递增。现以库内只读可重导口径补正为：

- 台账 done：16；
- 剔除 exp7 synthetic smoke 后的正式真实 done：15；
- 其中进入方向校准：12；
- 未进入本轮方向校准的早期正式 full：exp3 / exp4 / exp5。

该补正只修台账叙述，不改变任何实验 result、verdict、校准命中或闭卷状态。

## 验证摘要

- Notebook 16 单元、5 个代码单元完整执行，1–5 连续、零错误；
- portable builder schema/package 通过，应用内浏览器 1440×900 与 390×844 均零横向溢出、console 0；
- 规模与架构闸门全绿，债务未增；
- 本单元只有文档、静态数据、notebook、artifact 与 HTML，零研究代码或数据库写入。

## 停止线

本底稿不得冒充 2026-08-25 终版，不授权恢复 exp18 / exp21 / exp22 / exp23，不授权新 PAP、冻结、StudySnapshot、研究 manifest、收益读取、正式运行或 persist。完成本地提交后停在未推送交验点。
