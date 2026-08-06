# exp23 `buyback_announce` · NOT-FROZEN PAP 草案令

日期：2026-08-06（UTC+8 / Asia/Shanghai）

## 一、外审结论与范围偏差追认

Fable 对 commit 区间 `526bc3d..58a8d53` 的限域复核结论为：

> A 级 0 / B 级 1 / C 级 2；二元结论成立：可进入 NOT-FROZEN PAP 草案，
> 当前不可冻结。

John 对 B 级项的追认原文为：

> 追认 exp23 窄闸因 repurchase 接口无 ts_code 参数，采用五个不重叠小日期窗替代30票探针；接受实际返回539票仅作字段与污染形态证据，不得外推市场频率、候选数量或历史覆盖。

该追认只闭合既有窄闸探针的授权链，不把630行、539票或阶段计数升级为正式候选锚，
也不授权重探。

## 二、草案授权原文

John 原文：

> 批准 exp23 buyback_announce 进入 NOT-FROZEN PAP 草案单元。草案须完整呈拍首次披露硬门、注销式/库存式处置菜单及沿承项，不代裁。零全量采集、零落库、零生产代码、零冻结、零 manifest、零收益读取、零运行、零 persist。完成停交验点。

## 三、交付要求

1. 生成事件版18键 NOT-FROZEN PAP 草案；`proc=预案`与`ann_date`只能作为候选事件语义，
   首次披露、修订关系与方案身份未闭合前不得写成冻结事实；
2. 完整呈拍注销式/库存式处置选项，说明每项对登记语义、数据前置、判决轴与工程面的影响，
   只给技术建议，不代裁；
3. 完整呈拍公告顺延、ST处置、研究期、三窗口、估计期覆盖门、sample gate、基准、cost、
   holdout、field roles、digest binding及效力水印等沿承项；
4. 首次披露与用途分类须登记为冻结硬门；不得以标题关键词、后验实施结果、进展阶段、
   `end_date/exp_date/observed_time`或任取最早/最晚代理；
5. 输出文件SHA、canonical digest、`validate_pap`、窗口解析、键数与残留态扫描；
6. 草案时点不得生成正式候选数、selection SHA、源级快照或研究manifest。

## 四、停止线

本单元仅生成文本并更新 STATE：零接口重探、零全量采集、零缓存入仓、零数据库写入、
零生产代码、零终版PAP、零冻结、零StudySnapshot/研究manifest、零收益读取、零运行、零persist。
完成即停交验点；exp18继续停既有语义硬门，其余候选不并行。
