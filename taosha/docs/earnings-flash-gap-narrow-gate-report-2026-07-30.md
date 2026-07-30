# exp17 `earnings_flash_gap` 冻结前只读准确性窄闸报告

日期：2026-07-30（UTC+8）  
人令：`earnings-flash-gap-narrow-gate-order-2026-07-30.md`  
边界：只读；零生产代码、零数据库写入、零批量采集、零收益读取、零 PAP/冻结/manifest/运行/persist。

## 结论（二选一）

**可进入 PAP 草案。**

现有 signed 单判决能力足够，`forecast` 数据与 `express` 官方接口的连接键、日期字段和单位换算
均可确定；未发现需要新增统计能力的阻塞。与此同时，**本结论不等于可冻结**：qbase 当前没有
`express` 数据实物；快报 `n_income` 与预告净利润区间的会计归属口径，以及快报修订时的首次披露
锚，须在冻结前用全量入库实物闭合。未闭合前不得冻结或运行。

## 1. 状态基线（全符）

- exp17=`earnings_flash_gap#1`，family trial=1，`status=registered`，来源/效力=`llm/prescreen`；
  `frozen_at/result_json/done_at` 均为空。
- `study_snapshot`、addendum、仓内与阿里云均无 exp17 正式 manifest、运行或遗留产物。
- ledger 共 26 行：`registered 9 / frozen 2 / done 13 / closed 2`。
- 开工 HEAD=`6674b28e42c1843b4880866f60904aa5b4ef0cf0`；本地、GitHub、阿里云一致，工作树净。
- 登记裁定保持：exp17 与 `forecast_drift` 不同 family，本轮不重开。

## 2. 数据实物盘点

### 2.1 forecast 已备

qbase 只有 `forecast_snap`、`explore_reader_forecast`、`explore_reader_forecast_snap` 三个相关
对象；现值批次=`fact_batch 1 / tushare:forecast / asof 2026-07-07`：

- 138,458 行、5,707 票，首次公告锚覆盖 1998-12-16 起；
- `first_ann_date` 缺失 91 行；区间上下沿任一缺失 28,130 行；
- `ann_date != first_ann_date` 的修订行 13,437 行；
- 研究窗 2011-01-01 至 2024-07-01 前共有 86,902 个 `(ts_code,end_date)` 组、
  106,703 行；其中 7,648 组存在多个公告日，78,129 组至少有一行完整净利润区间；
- 同票/同期/同公告日多行键 11,957 个；其中区间值冲突 10 键、21 行。该面必须 fail-closed，
  不能任取一行。

### 2.2 express 未入库

qbase/taosha 表、视图、批次与采集配置中均无 `express`、`express_vip` 或业绩快报实物；
只有 forecast 批次。故本轮不能给出全量快报行数、候选事件数、逐年分布、快报修订数或孤儿数。

Tushare 官方资料确认：`express`/`express_vip` 提供全部历史并实时更新，当前账户的小样本调用成功；
但正式数据资产、append-only 批次、源快照和 manifest 路由尚不存在。来源：
[业绩快报接口说明](https://tushare.pro/document/2?doc_id=46)、
[接口权限说明](https://tushare.pro/document/1?doc_id=108%E3%80%82%EF%BC%9Bindex_global)。

## 3. 字段、单位与时序

官方字段定义：

- forecast：`ann_date`=公告日，`end_date`=报告期，`net_profit_min/max`=预告净利润上下限（万元），
  `first_ann_date`=首次公告日；来源：[业绩预告接口说明](https://tushare.pro/document/2?doc_id=45)。
- express：`ann_date`=公告日，`end_date`=报告期，`n_income`=净利润（元）；接口没有
  `first_ann_date` 或 `update_flag`。`end_date` 只能作连接键，严禁冒充事件日。

因此单位换算是确定的：`actual_wan = express.n_income / 10,000`。但官方快报文档只写“净利润”，
没有逐字写明“归属母公司股东的净利润”；预告文档的区间字段也简称“预告净利润”，同时另列
`last_parent_net`。**两侧会计归属口径的最终同一性仍须在全量数据落地时，以若干公司公告原文作
交叉核验后才能冻结**；不能仅凭字段名推定。

事件知情时序可无前视表达：同一 `(ts_code,end_date)` 下，只允许选择
`forecast.ann_date < express.ann_date` 的公开预告；快报事件锚只能取 express 实际公告日。
同日预告与快报不视为“快报前已公开预告”。

## 4. 极小样本探针（仅验语义，不外推）

探针 10 票、逐票调用，不落库；数据库连接 `transaction_read_only=on`。共见 express 92 行，
其中研究窗内 76 行：

- 与完整、严格早于快报的 forecast 区间可配对 47 行；
- `up 3 / down 4 / inside 40 / boundary 0`；
- 29 行无完整的快报前预告区间；
- 10 票样本内，同票同期快报多行=0；
- 可配对样本中未出现“首次预告区间与快报前最近预告区间不同”，**不能据此推断全量无差异**。

两个真实数值例仅用于证明负数和单位换算可机械执行：

- `000420.SZ / 2020-12-31`：快报实际 `-233,288,400 元 = -23,328.84 万元`，最近预告区间
  `[-29,800,-27,800] 万元`，严格高于上沿，机械归 `up`；
- `000520.SZ / 2012-12-31`：快报实际 `-1,879,685,600 元 = -187,968.56 万元`，预告区间
  `[-90,000,-80,000] 万元`，严格低于下沿，机械归 `down`。

该探针只证明接口、连接键、单位换算和严格比较可执行。它不是随机样本，禁止用
`3/47`、`4/47` 外推全量事件比例或功效。

## 5. 机械事件口径与待人裁定

未冻结机械口径可写为：同票同报告期存在快报前公开且上下沿完整的 forecast；
`n_income/10000 > upper` 记 `up`，`< lower` 记 `down`；区间内或恰等边界不成事件。

PAP 草案须把以下三项作为人裁菜单，工地不代裁：

1. **预告基准版本**：快报前最近一次公开预告，或首次预告。技术建议为最近一次，因为它对应
   事件前市场已知信息；但全量事件集合差异须待 express 入库后只读量化。
2. **快报首次披露锚**：接口无 `first_ann_date/update_flag`。全量采集后须审计同票同期多行；
   多公告日时是取最早快报日，还是冲突整组剔除，须人裁。源若只保留修订后的现值且无法恢复
   首次披露日，则相应组 fail-closed，不得用报告期末回填。
3. **实际利润会计口径**：`n_income/10000` 与 forecast 区间的归属范围经公司公告抽核一致后方可
   冻结；若不一致或无法证明，exp17 停止，不得改用同比幅度、文字类型或其他代理。

## 6. 判决形态与复用边界

- exp17 的 `up/down` 可直接复用 exp20 `direction_signed_main=True`：方向符号在逐 τ AR 上先翻转，
  再进入单一主判决；不需要组间差检验或新统计内核。
- 可复用：forecast snap 视图、公告日严格时序、现有 cleaning/benchmark/ADJ-BMP/report/PAP/
  manifest/状态机全链。
- 最小缺失件仅三项：`express_snap` append-only 数据批次与钉批视图；exp17 确定性配对/冲突
  fail-closed 事件生成器；专属 driver+fixture+报告分支。不得扩成通用财务平台。

## 7. 冻结前置与恢复条件

进入 PAP 草案不触发施工。冻结前须同时满足：

1. express 全量按既有事实批次范式落 qbase，发布源快照与只读 snap 视图；
2. 对全量 express 给出行数/证券数/报告期组数/时间覆盖/缺失/重复/修订/孤儿与逐年分布；
3. 量化最近预告 vs 首次预告的配对数、`up/down/inside/boundary` 与事件集合差异；
4. 用官方公司快报原文闭合 `n_income` 的会计归属口径；
5. 人对 §5 三项作最终裁定。

任何一项未闭合，终版 PAP 不得冻结。

## 8. 证据与边界

- 阿里云只读证据：`/root/s17gate/`；`inventory.log` SHA256=`9693e819…a95ae6b`，
  `probe.log` SHA256=`a37ed4df…655f92`，`SHA256SUMS -c` 全部通过。
- 网络访问仅官方文档与 10 票逐票小样本接口；零全市场 express 拉取、零缓存、零落库。
- 未读取任何事件日后价格、收益、CAR、显著性或既有正式结果；未改生产代码与数据库。
- 完成本报告即停交验点，等待人复核后另令 PAP 草案；未令不施工数据前置。
