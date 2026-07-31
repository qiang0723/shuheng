# Fable 终签收口：exp568 persist + exp16 v2 persist

日期：2026-07-31（UTC+8）

来源：John 转达的 Fable 独立复核回执。请求范围见
`taosha/docs/fable-persist-review-handoff-2026-07-31.md`。本档只登记复核结论和证据边界，
不修改既有 result、PAP、manifest、校准册或数据库状态。

## 1. exp568 `st_imposition`

结论：**`A0 / B0 / C1`，终签通过。**

Fable 独立核实：

- 两份权威档 SHA 逐字命中；
- `6827032 → c82b561` 中间无其他提交，diff 恰为交付档与 STATE，零研究代码、PAP、SQL；
- 终令、COMMIT、闭卷留痕的时间顺序无倒挂；
- 三件原件 SHA、PAP canonical、manifest 294、六项关键统计与其此前 §7 复核记录一致；
- `560+205=765`，`383+4+64=451`，`451/565=79.8230%`，
  `179/565=31.6814%`，CAAR=`-15.9295%`，台账
  `10/3/11/2 → 10/2/12/2` 均守恒；
- trial 2 的 `alpha=0.025` 下 `|ADJ-BMP|=5.5229` 超过双侧临界值，`SIG` 自洽；
- 固定读法完整：校准只记方向命中，`SIG` 独立陈述；价格观察不等于可成交收益；
  `llm/prescreen SIG` 不升级为 human/full；行业 unknown 不得表述为已完成行业中性检验。

依施工凭证采信、不作独立确认：前置 `28/28`、事务内 `FOR UPDATE` 与单次 COMMIT、
`done_at`、库内 `parsed_equal` 与 canonical、manifest 三处实物、台账实况、
`/root/s568persist/` 及其 SHA 自检。

C 级注记直接收口：闭卷节 canonical `3aa01a38…52f35` 是库侧序列化 SHA，文件 SHA
`6e96183c…c8afa` 是文件字节 SHA；两者口径不同，档内未专门解释，但不构成缺陷，不改档。

## 2. exp16 `yearend_strength` v2

结论：**`A0 / B0 / C1`，终签通过。**

Fable 独立核实：

- 两份权威档 SHA 逐字命中；
- `03dd8f2 → dcc61ba` 中间无其他提交，diff 恰为交付档与 STATE，零研究代码、PAP、SQL；
- 终令、COMMIT、闭卷留痕的时间顺序无倒挂；
- v1 三件与 v2 两件 SHA 在终令和闭卷档逐字一致，且与其水印窄修复核记录一致；
- v1 永久保留不覆盖，入库权威对象唯一为 v2 result；
- B1/B2 未软化：v1 重渲染 fail-closed 不导致放宽硬门；v2 report 不冒充单跑直出或
  `render(v2_result)` 的逐字输出；
- 第一次前置的 `study_snapshot` 键集穷尽断言并非终令要求，收窄回 ID/digest 逐字段核对
  属回到令文口径，不是结果后放松预注册判据；
- CAAR=`-0.3197%`、ADJ-BMP=`-0.1118`、`NOT_SIG` 与其 §7 复核一致，台账
  `9/3/12/2 → 9/2/13/2` 守恒；
- 校准册第九条、方向未命中、`4命中/5未命中` 与 STATE 一致；效力和价格观察边界完整。

依施工凭证采信、不作独立确认：失败版与最终前置、事务内断言、单次 COMMIT、
`done_at`、库内 `parsed_equal` 与 canonical、库内身份、manifest 317、postverify 与数据库
套件、`/root/s16persist_v2/`。

C 级注记直接收口：终令的两条“删除后逐字还原”断言已有水印窄修 fixture 覆盖，
但闭卷档未区分 persist 前置脚本是独立重跑还是引用既有取证；属留痕颗粒度，不构成缺陷。

## 3. 总结与停止线

- 两条均终签通过，2026-07-30 起挂账的两项外审欠账自本档关闭；
- 两个 C 级只作注记，不施工、不改历史档；
- 十条校准册仍为 `5命中/5未命中`；本次复核不改变任何判决或计数；
- `0ece5ed` 十实验阶段复盘包及 exp17 persist 不在本次复核范围，不得顺带视为已审。

至此停在外审欠账闭合点，不启动新研究任务。
