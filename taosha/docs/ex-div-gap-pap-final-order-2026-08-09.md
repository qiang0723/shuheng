# exp14 `ex_div_gap` · PAP 终版文本收口令

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 状态：获授权施工；完成后停终版候选复核点
- 草案：`taosha/docs/ex-div-gap-pap-draft-2026-08-08.json`
- 草案 digest：`b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`
- 人裁：`taosha/docs/ex-div-gap-predata-rulings-2026-08-08.md`
- 数据对账：`taosha/docs/ex-div-gap-datarecon-report-2026-08-09.md`

## 一、John 授权原文

John 原文（2026-08-09，UTC+8）：

> 批准 exp14 ex_div_gap 进入终版 PAP 文本收口。逐字落实既有人裁 A1/B1/C1/D1、st_policy=keep、postpone_policy=missing_bar_only、tau0=ex_date 当日及其余沿承项；草案 digest b2fa1b22…e7d77 作废。将 snapshot375 下 4,035、恰等 1,083、selection SHA ef9529b1…7f2f 仅登记为冻结前同锚参考，不得升格为正式运行硬断言。只生成终版 PAP、新 digest、逐键 diff 与交付档；零冻结、零 manifest、零收益读取、零运行、零 persist。完成停交复核。

本令中的缩写分别展开为草案 digest
`b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77` 与 selection SHA
`ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；展开只补全既有实物锚，
不改变授权语义。

## 二、终版裁定

1. A=A1：除权日 `adj_factor` 相对前一 SSE 开市日必须发生变化，才具事件资格；静态候选剔除。
2. B=B1：同一 `(ts_code,end_date)` 多行仅在六个比较字段全部非 NULL，且日期或 Decimal
   逐项精确一致时折叠；任一 NULL 或冲突整组 fail-closed。
3. C=C1：既有后复权总回报是唯一主 CAR；`tau0=ex_date` 当日。不复权机械跳空只作结构化
   NOT_FOR_VERDICT 诊断；不得进入 CAR、方向或显著性。
4. D=D1：监管阶段仅作组成 NFV，不计算分阶段收益、显著性或 verdict，不拆 alpha。
5. `st_policy=keep`；`postpone_policy=missing_bar_only`。除权日有真实 bar 即为 τ0，仅缺 bar/
   停牌可沿 SSE 开市日轴顺延不超过 5 日。
6. 研究期、三窗口、估计期覆盖门、sample gate、全市场等权 benchmark、ADJ-BMP 唯一判决、
   cost、holdout、field roles、digest binding、无收益分层轴与 `llm/prescreen` 水印均按已确认值。

## 三、数据身份与冻结前参考

1. 数据锚为 source snapshot 375，digest=
   `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；实际消费
   `dividend=17 / adj_factor=7 / trade_cal=10`。375 仅为源级快照，不得冒充 exp14 研究 manifest。
2. snapshot375 同锚参考为最终事件 `4,035`、恰等 `0.5` 事件 `1,083`、selection SHA
   `ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`。
3. 上述数字只作冻结前 NFV 漏斗与确定性参考，**不得自动升格为正式运行硬断言**；未来正式
   运行令须另行钉定研究 manifest、事件数与 selection SHA。
4. Fable 数据对账复核 C 级的 8 个多行组分类交叉表默认不在本单元扩做，留待冻结取证包收口。

## 四、文本收口与交付

1. 新建终版 PAP 文件；草案本体保持原样并另立 NOT-FROZEN/SUPERSEDED 标记。
2. 删除全部菜单、建议、待裁、数据未闭及 NOT-FROZEN 措辞；逐键落实第二节裁定。
3. 写入第三节数据身份、漏斗、逐年与监管组成，全部保持 NFV/非正式运行硬断言身份。
4. 人的方向与把握度不得代填；须在终版 digest 独立复核通过后由 John 另行密封。
5. 交付文件 SHA/canonical 双口径、schema/窗口、草案到终版逐键 diff、残留态扫描与交付档。

## 五、停止线

本单元只生成终版 PAP 文本候选、草案取代标记、逐键 diff 结果与交付档。零生产代码、零数据库
写入、零冻结、零 StudySnapshot、零研究 manifest、零收益读取、零正式运行、零 result、零
persist。完成即停终版候选复核点。
