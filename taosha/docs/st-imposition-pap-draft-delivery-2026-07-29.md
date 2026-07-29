# exp568（旧exp15）`st_imposition` · PAP草案交付（2026-07-29）

## 结论与身份

NOT-FROZEN草案已生成：`taosha/docs/st-imposition-pap-draft-2026-07-29.json`。研究对象仅为新承接行exp568=`delist_warning_financial/trial 2/registered`；旧exp15已关闭，不得用于冻结、driver或运行。

文件SHA256与引擎`canonical_pap_sha256()`均为：

`b84f93df8e6d63d98dc80faea35515e875aa331f22435d5d2df6a246032de6c3`

`validate_pap=PASS`，`parse_test_windows=(5,20,60)`，顶层18键；键集与exp12同源事件版终版PAP完全相同。逐字沿承5键=`analysis_type/cost/holdout/pap_schema_version/sample_gate`，其余13键按反向事件、trial 2与草案待裁边界改写。

该digest仅为草案候选，不得冻结；任何终版确认都会产生新文件与新digest。

## 已裁定内容→键位

| 已裁定内容 | PAP键位 |
|---|---|
| 普通→ST/风险警示为目标事件；退市优先排除；公告日锚；冲突与不可判fail-closed | `event_def` |
| exp568属于`delist_warning_financial` trial 2，族内α=0.025；禁止PAP/driver伪造trial | `verdict_authority`、`engine_params.note`、`reporting_commitments` |
| exp22原因不可识别，`*ST`代理不得冒充其正式事件集 | `event_def`、`bias_statement`、`diagnostic_dimensions` |
| 来源llm、效力prescreen | `verdict_power_note`、`reporting_commitments` |
| batch7参考765事件/646票、带星560/不带星205，非正式硬断言 | `snapshot_batch_req`、`reporting_commitments`、`diagnostic_dimensions` |
| M gate：本假设不新增数据与统计能力 | 草案结构维持单事件集`adj_bmp_main_only`，无组间差或收益分层轴 |

## 草案事件漏斗锚

沿窄闸只读双跑，仅作batch7冻结前参考：

`18,868输入行 → 17,133名称段 → 11,601有前段转换 → 1,277普通→ST候选 → 状态不可判1 → 锚缺510 → 研究期外1 → 最终765事件/646票`

锚冲突、`ann>start`、重复键均为0；事件键SHA=`93a8d08740b93da50a148b33ca8a4206fe9a4c2ba3b0d863d44d473f779fd89f`。这些数字不得用于正式运行追数；正式数量只认exp568自有manifest与冻结规则的确定性产出。

## 待John终版确认

1. 研究期是否采用`2011-01-01≤ann_date<2024-07-01`；
2. τ0是否沿exp12：公告日之后首个有真实bar的价格观察日，`missing_bar_only`顺延≤5，一字板有bar即入CAR；
3. 检验窗是否采用5/20/60日，首窗唯一判决；
4. 估计期250至91、有效门112/160与`sample_gate=30`是否沿承；
5. 全市场等权benchmark、cost四值仅审计、holdout/field roles/digest binding是否沿承；
6. 带星/不带星是否只做数量与构成NFV审计，**不做分层CAR或显著性**（草案建议）；
7. 终版digest复核通过后，由John亲拟并绑定方向与把握度；草案不登记预判。

family/trial/α不在本清单内，已由人裁并经数据库迁移闭合。

## 边界

本单元仅新增令文、草案与交付档。数据库exp568仍registered四槽空；零生产代码、零PAP冻结、零manifest、零收益读取、零正式运行、零persist。完成即停交验点。
