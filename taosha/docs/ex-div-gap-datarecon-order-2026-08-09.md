# exp14 `ex_div_gap` · 最小只读视图与数据对账施工令

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 状态：获授权施工；完成后停数据对账交验点
- 前置草案：`taosha/docs/ex-div-gap-pap-draft-2026-08-08.json`
- 草案 digest：`b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`（NOT-FROZEN，不得冻结）
- 人裁：`taosha/docs/ex-div-gap-predata-rulings-2026-08-08.md`

## 一、John 授权原文与限域解释

John 原文（2026-08-09，UTC+8）：

> 继续下一步

九十四笔已把当前唯一下一步登记为“exp14最小只读视图与数据对账”。本令据此只授权该单元，
不扩解为终版PAP、密封、冻结、StudySnapshot生成、研究manifest、收益读取、正式运行或persist。

## 二、已裁口径（不得改写）

1. A1：除权日`adj_factor`相对前一SSE开市日发生变化，才具备事件资格；静态因子候选剔除留痕。
2. B1：同一`(ts_code,end_date)`多行仅在六字段全部非NULL且日期/Decimal逐项精确一致时折叠；
   任一NULL或冲突整组fail-closed。
3. C1：后复权总回报是唯一主CAR，`tau0=ex_date`当日；本单元只核事件侧和因子，不读取任何
   事件后收益。不复权机械跳空仅NFV，不进入对账选择规则。
4. D1：监管阶段只做数量与组成NFV，不建设板块历史映射或收益诊断轴。
5. `st_policy=keep`、`postpone_policy=missing_bar_only`；其余沿承项保持已裁值。

## 三、授权施工面

1. **qbase最小视图**：基于既有`dividend_snap`批17新增exp14专属current/snap忠实投影；另以
   exp14专属current/snap视图只投影`adj_factor_snap`的`ts_code/trade_date/adj_factor`事实。
   视图只做批次路由、holdout和SH/SZ证券范围，不判阶段、阈值、版本、因子变化或事件资格。
2. **taosha纯规则与fixture**：实现A1/B1及Decimal `stk_div>=0.5`闭区间、分项一致、事件键冲突
   整组剔除、逐年/监管组成、确定性selection SHA和互斥恒等式；单文件≤300行、函数≤60行。
3. **只读recon**：以源级snapshot375显式钉批，current与snap分别运行并双跑；输出完整漏斗、
   多版本NULL/冲突、恰等边界、因子缺失/静态/变化、逐年和监管三分、事件数与selection SHA。
   current与snapshot375不一致立即停止，不追数、不调整规则。
4. **生产应用**：代码经本地/Docker验证并推送GitHub后，阿里云只允许`qbase_app`应用上述视图
   DDL；不得修改事实表、批次、snapshot375、既有视图语义或授权边界。recon连接从建立起强制
   `transaction_read_only=on`，并实测只读状态。

## 四、停止线

- 零接口重探、零全量采集、零缓存入仓、零事实表写入；
- 零终版PAP、零密封、零冻结、零新StudySnapshot、零研究manifest；
- 零事件后收益读取、零CAR/显著性、零正式运行、零result写入、零persist；
- snapshot375同锚参考数不是正式运行硬断言；本单元只形成冻结前数据对账锚；
- 完成代码、视图、双跑和报告后立即停交验点，终版PAP须John另令。
