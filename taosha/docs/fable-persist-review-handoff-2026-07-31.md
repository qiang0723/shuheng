# Fable 只读复核交接：exp568 persist + exp16 v2 persist

日期：2026-07-31（UTC+8）

性质：关闭两条既有外审欠账；仅审 GitHub 实物，不重开研究。

## 1. 请求与停止线

请 Fable 独立复核以下两条已闭卷 persist：

1. exp568 `st_imposition`：persist 与 `done/SIG` 闭卷；
2. exp16 `yearend_strength`：以水印修正版 v2 result persist 与 `done/NOT_SIG` 闭卷。

复核范围只限下列提交和文件。请一次出清 `A/B/C` 分级、二元结论与证据边界；不要求访问阿里云，不要求重跑研究，不提出新实验、敏感性分析、统计内核或平台建设。

## 2. exp568 精确范围

提交链：

- persist 终令：`6827032`；
- persist 闭卷：`c82b561`；
- 建议检视：`git show 6827032`、`git diff 6827032 c82b561`。

文件：

- `taosha/docs/st-imposition-persist-order-2026-07-30.md`；SHA256=`2433bf5e2f604d6607f3b074b9c2779799cf34d22db857f1b0f83e7bad889ada`
- `taosha/docs/st-imposition-s7-delivery-2026-07-29.md`；SHA256=`b846cd546bdce8f722ddc7ea5cbbd564de1af5ab5ec7c8c07ccb8010c4a86934`
- `ops/STATE.md` 中“2026-07-30 三十三笔”。

请核：

- 终令锚定的 result/report/log、PAP、manifest 294 与六项关键结果是否在闭卷节原样保持；
- 状态守恒是否为 26 行、`10/3/11/2 → 10/2/12/2`，且只迁 exp568 一行；
- `560+205=765`、`451/565=79.82%`、`179/565=31.68%` 与档载是否自洽；
- 预判原文“负，把握度60%”是否只登记方向命中，不与独立 `SIG` 合写；
- 固定读法是否明确：一字板/涨跌停只是价格观察，不是可成交收益；`llm/prescreen SIG` 不得升级为 human/full 或“发现 alpha”；行业 unknown 不得写成已完成行业中性检验；
- `6827032..c82b561` 是否只含交付档与 STATE 的闭卷留痕，没有研究代码、PAP 或 SQL 变化。

## 3. exp16 v2 精确范围

提交链：

- v2 persist 终令：`03dd8f2`；
- v2 persist 闭卷：`dcc61ba`；
- 建议检视：`git show 03dd8f2`、`git diff 03dd8f2 dcc61ba`。

文件：

- `taosha/docs/yearend-strength-persist-v2-order-2026-07-30.md`；SHA256=`f7ba90dc541b9249cda37dcead331b9a1960c418bbb09439a4c3cf2f3bf4548b`
- `taosha/docs/yearend-strength-persist-v2-delivery-2026-07-30.md`；SHA256=`28c9833e65ec8ee7f24ac3992187026a416bfa67684544bac6b86577fcece1f7`
- `ops/STATE.md` 中“2026-07-30 四十笔”。

水印窄修实现与 fixture 已在前一轮通过，本次不要重审该实现；只核 persist 是否忠实使用已验收 v2 result。

请核：

- v1 三件与 v2 两件 SHA 是否在终令和闭卷档逐字一致；
- 入库权威对象是否唯一指向 v2 result，且 v1 原件永久保留、不覆盖；
- B1 是否准确保留：当前 HEAD 对缺身份水印的 v1 result 重渲染会 fail-closed，历史 v1 report 永久留存，不因此放宽新报告硬门；
- B2 是否准确保留：v2 report 是 renderer 验证水印后向 v1 report 插入唯一一行所得，不冒充单跑直出或 `render(v2_result)` 的逐字输出；
- 前置第一次因自造 `study_snapshot` 键集穷尽断言停止，后续收窄是否回到终令仅要求的 ID/digest 逐字段核对，而非结果后放松预注册判据；
- 状态守恒是否为 26 行、`9/3/12/2 → 9/2/13/2`，且只迁 exp16 一行；
- 预判原文与 `NOT_SIG` 固定读法、`llm/prescreen` 效力、价格观察非策略证据是否一致；
- `03dd8f2..dcc61ba` 是否只含交付档与 STATE 的闭卷留痕，没有研究代码、PAP 或 SQL 变化。

## 4. 证据边界

GitHub 可独立核实：提交顺序、diff 触碰面、终令与交付档文本、档内算术、SHA 字符串的一致性、STATE 校准册和固定读法。

GitHub 不足以独立确认，须明确标为“依施工凭证采信”或“未核”：阿里云数据库事务实况、`FOR UPDATE` 与单次 COMMIT、库内 `parsed_equal`、manifest 三处实物、远端取证目录及 `SHA256SUMS -c`。不要因缺通道把这些写成已独立确认，也不要据此要求重跑研究。

## 5. 期望回执

请分别给 exp568、exp16：

1. `A/B/C` 分级；
2. 二元结论：`终签通过`或`不通过`；
3. 自己独立核实的项目；
4. 仅依施工凭证采信的项目；
5. 若仅为 B/C 级文字注记，直接收口，不另开施工循环。

两条均通过后，这两项外审欠账即关闭；不修改既有 result、PAP、manifest、校准册或数据库状态。
