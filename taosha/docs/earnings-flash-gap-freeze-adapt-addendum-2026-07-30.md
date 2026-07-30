# exp17 `earnings_flash_gap` · 最小适配授权补充

日期：2026-07-30（UTC+8）

## 阻塞事实

冻结后施工盘点发现：exp17 事件定义必须消费 forecast 的 `net_profit_min/max`，但现有
`explore_reader_forecast(_snap)` 是 exp20 专属最小列面，只提供 `p_change_min/max`；
`023_express_reader.sql` 也只闭合 express 一侧。因此原令“qbase 视图不得修改”与冻结规则的
必要消费面发生冲突，施工方在生产代码修改前停下报人。

## 人裁原文

施工方请求：

> 批准本次 exp17 最小适配新增专属 forecast 利润区间 current/snap 只读视图，仅暴露事件规则必需列，不修改底表和既有 exp20 视图。

John 回复：

> 确认

## 授权边界

本补充仅放行 exp17 专属 forecast 利润区间 current/snap 视图及 taosha_engine 最小 SELECT
授权；视图只做 L1 忠实字段投影、现值/manifest 批次路由、holdout 与排北焊接，不做事件判断。
底表、既有 exp20 forecast 视图、统计与清洗内核、PAP 均不得修改。其余停止线沿原令不变。

