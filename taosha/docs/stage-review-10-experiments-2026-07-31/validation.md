# 十条实验阶段复盘 · 验证记录

验证时间：2026-07-31（UTC+8）

## 结论

**Ready to share，附一项显示层限制。** 数据、算术、口径、notebook 执行状态与 HTML 结构均通过；应用内浏览器因安全策略拒绝访问本地 `file://` 页面，因此未完成浏览器截图级视觉验收，不据此声称“已目测通过”。

## 已验证

- 校准册 10 条，方向命中 5、未命中 5；Wilson 95% 区间约为 23.7%–76.3%。
- 正式真实研究 13 条，`SIG` 1 条；唯一 `SIG` 为 exp568，效力为 `llm/prescreen`。
- `human/full` 正式研究 4 条，`SIG` 0 条。
- 台账 26 行：registered 8 / frozen 2 / done 14 / closed 2。
- 每条校准记录满足 `main_n <= n_valid <= events`；实验 ID 唯一。
- notebook 共 13 个单元，其中 5 个代码单元按 1–5 顺序完整执行，错误输出为 0。
- HTML 产物通过 artifact schema、打包与结构校验；图表含零线与名义 ±1.96 参考线，并在正文单独说明 exp568 的 trial 2 临界值为 ±2.241。
- 报告明确区分：方向校准、正式统计判决、效力等级和排产建议，不把方向命中改读为显著性证据。

## 来源与边界

- 结果数值：阿里云数据库内正式 `result_json` 只读提取，查询见 `result_extract.sql`。
- 校准原文：各实验闭卷交付档与 `ops/STATE.md`。
- 台账状态：数据库只读读回与 `ledger_snapshot.csv`。
- Fable 尚未独立终签复核 exp568 persist 与 exp16 v2 persist；本报告直接核了库内正式结果和闭卷档，可用于当前排产，但该复核欠账仍应在 2026-08-04 检查点前关闭。

## 复现入口

- `stage_review_analysis.ipynb`：可执行分析与守恒断言。
- `build_notebook.py`：notebook 生成器。
- `artifact.json`：HTML 报告的结构化源。
- `build_report_artifact.py`：报告构建器。
- `stage_review_report.html`：交付报告。
