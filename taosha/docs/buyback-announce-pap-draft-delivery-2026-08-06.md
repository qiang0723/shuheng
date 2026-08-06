# exp23 `buyback_announce` · NOT-FROZEN PAP 草案交付

- 日期：2026-08-06（UTC+8 / Asia/Shanghai）
- 授权令：`taosha/docs/buyback-announce-pap-draft-order-2026-08-06.md`
- 草案：`taosha/docs/buyback-announce-pap-draft-2026-08-06.json`
- 状态：**NOT-FROZEN**
- 文件 SHA256 / canonical digest：`695aeb28a1025ea4c432da1b9ca90de949e814d16ed95dcbb9822945278df2a6`
- 结构：18键；`validate_pap=PASS`；窗口解析=`(5,20,60)`；文件字节与canonical串本体逐字相等。

## 一、授权链闭合

Fable 对窄闸的二元结论为“可进入 NOT-FROZEN PAP 草案、当前不可冻结”，并把五日期窗
返回539票的范围偏差列为B级。John已逐字追认该替代口径，限定所有探针数字只作字段与污染
形态证据，不外推市场频率、候选数量或历史覆盖；本单元未重探。

## 二、窄闸事实到PAP键位

| 窄闸事实或纪律 | 草案落点 |
|---|---|
| 候选阶段只能精确取`proc=预案` | `event_def`、`reporting_commitments` |
| `ann_date`只是候选公告锚，首次披露与修订关系尚未证明 | `event_def`、`bias_statement`、`snapshot_batch_req` |
| 后续通过/实施/完成/终止不得回填或反向删除预案事件 | `event_def`、`bias_statement` |
| 接口无update_flag、公告/方案ID、用途字段 | `bias_statement`、`diagnostic_dimensions` |
| 注销式/库存式不得用标题或后验状态代理 | `event_def`、`diagnostic_dimensions`、`snapshot_batch_req` |
| 同票同日多行、重复和方案身份不可判须呈拍fail-closed口径 | `event_def`、`reporting_commitments` |
| 五窗630行/539票只作形态证据 | `bias_statement`、`reporting_commitments` |
| 合并主事件集可复用单顶层ADJ-BMP路径 | `verdict_authority`、`engine_params` |
| `llm/prescreen`水印缺失即fail-closed | `verdict_power_note`、`reporting_commitments` |

## 三、首次披露硬门（非代理选项）

冻结前必须同时满足：

1. 形成append-only全量 `repurchase` 数据资产及current/snap最小只读视图；
2. 以官方公告原件或可追溯官方索引证明 `proc=预案,ann_date` 为该方案首次披露；
3. 证明同票的修订、延期、再次回购与后续进展之间的方案身份关系；
4. 给出抽核分子、分母、逐年覆盖和失败原因。

不能证明即停止冻结。不存在“改用最早/最晚结构化行”“改用后续阶段日期”“使用标题关键词”
或“使用observed_time”的降级选项。

## 四、注销式/库存式完整处置菜单

### B1：保留分层，仅作NFV组成审计（技术建议）

- 主事件集仍合并产生一个顶层ADJ-BMP verdict，不按用途拆alpha；
- 冻结前必须取得可靠官方公告原件用途来源与可复现分类规则；
- 报告注销式、库存式、其他明确用途与不可分类的数量、占比、逐年和清洗存活；
- 优点：忠实保留登记的“分层”信息且不新增统计能力；代价：用途证据不能闭合时仍不可冻结。

### B2：用途进入收益判决轴

- 须由John明确选择单判决、分层判决或组间差，并冻结族内alpha与字段角色；
- 须先核现有统计能力是否足够；若需要新组间差能力，按治理冻结边界停止报人，不在本单元建设；
- 优点：直接检验用途差异；代价：改变判决形态与多重比较口径，工程和解释成本最高。

### B3：显式改判为不分用途的合并回购预案事件

- 须由John逐字改判登记语义并留痕；施工方不能因接口缺字段静默删除分层；
- 优点：数据与统计形态最小；代价：不再回答原登记中的注销式/库存式差异。

三案共同禁令：不得用标题关键词、后验实施结果、进展阶段或回购完成情况代理用途。

## 五、重复与方案身份菜单

### C1：多行或身份不可判整组fail-closed（技术建议）

同一 `(ts_code,ann_date)` 只要出现多行、重复、字段冲突或无法证明属于同一方案，涉事组全部
剔除；不任取、不折叠。口径最保守、证据链最简单，代价是可能损失源端机械重复行。

### C2：仅逐字段完全相同的重复行折叠

只允许对官方九字段逐字/数值完全相同的重复行折为一行；任何字段不同或方案身份不明仍整组
fail-closed。可减少机械重复损失，但须在冻结前证明规范化比较规则，不得容差合并。

## 六、沿承项待John确认

1. `postpone_policy=unified_announcement`：公告日后首个交易所交易日为τ0，缺bar统一顺延≤5；
2. `st_policy`：草案技术建议`keep`，备选`reject`；选择reject须知情接受对困境回购样本的
   选择性删除；
3. 研究期建议`2011-01-01 ≤ 首次预案ann_date < 2024-07-01`，但须受全量历史覆盖与首次
   披露证据约束，不得因事件数量调整；
4. 检验窗5/20/60，主窗`[0,+4]`唯一判决，次级与稳健窗均NFV；
5. 估计期250..91、覆盖门112/160、`sample_gate=30`；
6. 全市场等权benchmark与`adj_bmp_main_only`唯一顶层判决；
7. cost四值仅作schema与执行审计，不控制CAR取样；
8. holdout、field roles、canonical digest binding及llm/prescreen效力水印沿既有冻结范式；
9. 全量数据落地后只能补覆盖、污染、证据与用途计数，不得按事件数、方向比例或收益结果
   修改公告锚、研究期、用途规则或重复处置。

## 七、冻结前数据硬门

须由后续另令形成并验收：

1. `repurchase` append-only全量事实批次和current/snap最小只读视图；
2. 阶段、年份、缺失、完全重复、同票同日多行、冲突与生命周期连接的全量画像；
3. 首次披露与方案身份官方原件抽核；
4. 按人裁B案闭合用途来源，或按B3显式改判登记语义；
5. 源级StudySnapshot及终版PAP所需实测对账数。

任一硬门失败均不得冻结，不允许更换锚、发明代理或根据样本量放宽。

## 八、边界与交验

- 草案不含正式候选数、selection SHA锚值、快照ID或研究manifest ID；
- 登记方向“正”没有被平移为冻结密封；方向与把握度须在终版digest复核后由John另拟；
- 本单元零接口重探、零全量采集、零缓存入仓、零数据库写入、零生产代码、零终版PAP、
  零冻结、零StudySnapshot/研究manifest、零收益读取、零运行、零persist；
- exp23应仍为registered三槽空；exp18继续停原语义硬门，其余候选不并行。

下一步只能先做草案外部复核，再由John逐项裁B/C菜单及沿承项；数据闭合须另令。
