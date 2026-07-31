# Fable 限域复核交接：十条实验阶段复盘包

日期：2026-07-31（UTC+8 / Asia/Shanghai）

对象：commit `0ece5ed`，目录 `taosha/docs/stage-review-10-experiments-2026-07-31/`。

性质：复核一份已经入仓的阶段快照，不启动新研究，不重开已闭卷实验。

## 1. 时间口径

该包生成时点为 **2026-07-31 10:57:18+08:00**。请按这一时点核其事实、算术和决策逻辑；包内排期是历史快照，07-31 后已完成的时间戳窄核、Web MVP、exp18 停点及外审欠账收口，不构成本包的事后错误，也不要据此重开排产讨论。

## 2. 请求范围

请只核：

1. `calibration_results.csv`、`ledger_snapshot.csv`、`result_extract.sql` 的字段口径和内部守恒；
2. `stage_review_analysis.ipynb` 的单元顺序、断言、输出与源 CSV 是否一致；
3. `build_report_artifact.py` 是否能由源 CSV 确定性重建 `artifact.json`；
4. `artifact.json` 与 `stage_review_report.html` 的核心数字、表格和读法是否一致；
5. `validation.md` 是否准确披露验证范围和显示层限制。

不要复核 exp568/exp16/exp17 的 persist 事务，不访问或改动数据库，不重跑研究，不提出新实验、平台扩建或当前排产建议。

## 3. 核心停止线

以下数字应同时成立：

- 校准记录 10 条：方向命中 5、未命中 5，Wilson 95% 区间约 `23.7%–76.3%`；
- 正式真实研究 13 条：`SIG=1`，唯一 SIG 为 exp568，效力 `llm/prescreen`；
- `human/full` 正式真实研究 4 条：`SIG=0`；
- 台账 26 行：`registered=8 / frozen=2 / done=14 / closed=2`；
- 每条记录满足 `main_n <= n_valid <= events`；
- 报告不得把方向命中改读为统计显著，不得把 `llm/prescreen SIG` 改读为 human/full 或可执行策略证据。

## 4. 当前施工方预检

仅作复核导航，不代替 Fable 独立判断：

- 两份 CSV 复算得到上述全部计数；
- notebook 共 13 个单元、5 个代码单元，仓内执行序号为 1–5、错误输出为 0；
- 当前本地 Python 缺 `nbformat`，因此未覆盖原 notebook；改为按 notebook 原始代码顺序在隔离进程执行 5 个代码单元，全部通过；
- 在临时目录运行 `build_report_artifact.py`，重建 `artifact.json` SHA256 与仓内原件逐字相等：`17d2bdd780c7c9a8754904dda6ce67d705f5e4717eeb6748620eaf3bc51d02a0`；
- 未完成浏览器截图级视觉验收，`validation.md` 已明确不声称目测通过。

## 5. 证据边界

GitHub 可独立核实：提交触碰面、CSV/SQL/notebook/build 脚本、artifact/HTML 一致性、算术、措辞与复现入口。

GitHub 不能独立确认：当时阿里云数据库只读提取是否与活库逐字一致、各闭卷 result 原件的远端 SHA 和事务实况。对这些请写“依包内只读快照与既有闭卷凭证采信”，不要冒充实时数据库复核，也不要因此要求重跑。

## 6. 期望回执

请一次给出：

1. `A/B/C` 分级；
2. 二元结论：`通过`或`不通过`；
3. 自己独立核实的项目；
4. 仅依快照/凭证采信的项目；
5. 若只有 B/C 级显示或文字注记，直接收口，不开施工循环。

本次复核通过后，仅关闭 `0ece5ed` 阶段复盘包的外审欠账；不改变任何实验状态或当前排产。
