# 十条实验阶段复盘包 · Fable 外审收口

日期：2026-07-31（UTC+8 / Asia/Shanghai）

对象：commit `0ece5ed`，目录 `taosha/docs/stage-review-10-experiments-2026-07-31/`。

交接：`taosha/docs/stage-review-fable-handoff-2026-07-31.md`。

本档只登记 Fable 对历史快照的限域复核结论，不修改复盘包、实验状态、数据库或当前排产。

## 1. 结论

**`A0 / B1 / C2 → 通过`。**

`0ece5ed` 阶段复盘包外审欠账关闭。该包继续作为生成时点 `2026-07-31 10:57:18+08:00` 的历史快照使用；包内排期不冒充当前排期。

## 2. Fable 独立核实

- 校准 CSV 10 行、实验 ID 唯一，方向命中 5、未命中 5；逐行由 CAAR 符号重新推导命中结果，零错标；Wilson 95% 区间为 `23.7%–76.3%`。
- 十行均满足 `main_n <= n_valid <= events`。
- exp24/10/568/16/17 五条全精度 CAAR 与 ADJ-BMP，和 Fable 自有历史复核锚逐位一致。
- 台账 CSV 26 行=`registered 8 / frozen 2 / done 14 / closed 2`；排除 synthetic smoke 后，正式真实研究 13 条，唯一 SIG 为 exp568 且效力为 `llm/prescreen`；full 效力真实研究 4 条、SIG 0。
- `result_extract.sql` 的 JSON 路径与排序口径成立。
- notebook 共 13 单元、5 个代码单元；Fable 独立解析并按原顺序重执行，全部断言通过、RC=0。
- 临时重建 `artifact.json` SHA256=`17d2bdd780c7c9a8754904dda6ce67d705f5e4717eeb6748620eaf3bc51d02a0`，与仓内原件及交接件三方逐字相等。
- artifact 与 HTML 的核心数字、表格和读法一致；HTML 明确区分方向命中、统计显著、效力等级与可交易性。

## 3. 分级注记

- **B1**：`validation.md` 把“图表含名义 ±1.96 参考线且正文单独说明 exp568 trial 2 临界值 ±2.241”列入已验证，但该说明仅存在于 artifact 的图表 subtitle/显示层，HTML 文本层未承载；又因浏览器截图级视觉验收未完成，该条应视为显示层限制。判决与固定读法不受影响。下次自然触碰时可补 HTML 正文或修正验证说明，本轮不施工。
- **C1**：交接件把 4 条 full 效力真实研究简称为“human/full”；实物为 human 2 条、literature 2 条。包内 HTML 使用“4 条真实 full 研究”，口径准确；本轮不改历史交接件。
- **C2**：`ledger_snapshot.csv` 未含 `done_at`，校准顺序不能仅凭包内台账 CSV 独立重导；Fable 已用 STATE 闭卷顺序交叉核实。列示备查，不补列、不重建历史快照。

## 4. 证据边界

Fable 独立核实：提交触碰面、CSV 守恒与逐行方向、Wilson 区间、五实验历史锚交叉、SQL 字段口径、notebook 结构及执行、artifact 确定性重建、HTML 文本层读法。

依包内只读快照与既有闭卷凭证采信：生成时点阿里云只读提取与活库逐字一致性、各闭卷 result 远端原件、渲染后图表视觉内容；不冒充实时数据库或截图级独立确认，也不据此要求重跑。

## 5. 停止线

- 本次仅关闭 `0ece5ed` 外审欠账；
- B/C 只作注记，零返工、零研究重跑、零数据库写入；
- 不改变任何实验状态、PAP、manifest、result 或校准册；
- exp18 继续停在首次披露语义硬门，恢复须 John 另令。
