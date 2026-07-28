# exp24 021 + manifest + §7 单次正式运行授权 · 人令留痕（2026-07-28，UTC+8）

> 人的授权原文：**“执行上述 exp24 令”**。以下为该句明确指向、经 Fable 外审确认并由人批准执行的完整命令；不得善意改写。

## 一、运行前硬闸

只读对账 current 与 source snapshot 247 的完整消费向量，必须逐项相等：

`daily=6 / adj_factor=7 / stock_basic=6 / namechange=7 / trade_cal=10 / sox_daily=13 / sw_member=14`

- 任一不符立即停止，不应用021、不建manifest；
- 全部相等则追认此前 current 视图漏斗复现有效。

## 二、应用并验收021

按既有DDL发布路径应用`qbase/sql/021_sox_spillover_reader.sql`，验收：

- taosha_engine可读exp24 current/snapshot视图，底表仍不可读；
- holdout焊死；
- 以snapshot 247路由重跑漏斗，必须精确得到：314触发→301映射日→碰撞9日剔22→292触发日→19,258事件，重复键0；
- selection SHA必须为`7a7840e596b755746fe5f038928fad622e2df83a32ba64d6105e9a9513b2acee`。

任一不符立即停止，不建manifest、不作解释或修补。

## 三、manifest与§7单跑

- 由source snapshot 247生成exp24自有研究manifest，完成权威行、qbase镜像、publication attestation三处发布并核对digest；
- driver逐字消费冻结PAP，`pap_sha256_assert=be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`；
- 正式事件集必须为19,258；
- 只允许运行一次；RC非零或任何锚定不符即停，不自动重跑。

## 四、停止线

运行后保持exp24=`frozen`、`result_json/done_at`为空、台账零写入。交result/report/log原件、SHA清单、manifest三处读回、运行前后状态及核心统计。

本令不授权代码修改或persist。完成停取证点，结果验收后另令。
