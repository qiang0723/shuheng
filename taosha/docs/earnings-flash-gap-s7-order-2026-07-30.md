# exp17 `earnings_flash_gap` · manifest + §7 单次正式运行令

日期：2026-07-30（UTC+8）

> John 在行为验收外部复核通过后亲自授权：
>
> 批准生成 exp17 自有研究 manifest，并执行 §7 单次正式运行。
>
> 本令不授权修改代码、自动重跑或 persist。

## 一、运行前只读硬闸

任一不符立即停止，不生成 manifest、不运行：

1. exp17 仍为 `frozen`，`frozen_at=2026-07-30 22:36:24.132972+08`不变，
   `result_json/done_at`为空；台账身份必须为
   `earnings_flash_gap/trial1/llm/prescreen`；
2. DB PAP canonical 必须为
   `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`；
3. source snapshot 必须为 340，digest 必须为
   `b32c5b7f0c333c4f157822c99cd150f87cff6b450a3c12f3686437b46357af4c`，权威行、qbase
   镜像与 publication attestation 三处一致；340 仅是源级快照，不得冒充研究
   manifest；
4. snapshot340 qbase 向量键集须恰等 11 项，且当前源批次须逐项相等：
   `adj_factor=7 / daily=6 / express=15 / forecast=1 /
   holder_sell_predisclose=12 / namechange=7 / sox_daily=13 /
   stk_holdertrade=2 / stock_basic=6 / sw_member=14 / trade_cal=10`；
5. taosha 派生批须为 `market_return=88 / pool_b1=18 / pool_b1_return=18`；
   三批实际 qbase 依赖键须与 snapshot340 对应子向量一致，
   `pool_b1_return=18`的父池必须为 `pool_b1=18`；
6. 研究 manifest 完整向量键集必须恰等上述 11 个 qbase 键与 3 个 taosha
   键，多一键、少一键或值异均停；
7. 不存在 exp17 既有正式研究 manifest、正式结果或遗留研究进程；台账必须
   仍为 26 行：`registered 8 / frozen 3 / done 13 / closed 2`。

## 二、exp17 自有研究 manifest

- 以 `--create --from-source-snapshot 340` 一次生成 exp17 自有研究 manifest；
- 完成 taosha 权威行、qbase 镜像、publication attestation 三处发布，digest
  必须一致；
- 生成后重验 14 键完整向量、三个派生批血缘与父池关系；
- 本节只授权 manifest 相关表写入，不授权 experiment ledger 写入。

## 三、收益前选择硬闸

在读取事件后收益和调用正式研究引擎前，新 manifest 须独立通过：

- 最终 signed 事件数恰为 `2,529`，其中 `up=997 / down=1,532`；
- selection SHA256 恰为
  `cd1433f0e9cc5d60dea807dc7f4f7b26fbcf324392602205c466aa7be5bb05ac`；
- driver 内冻结 18 项计数参考和分类、事件、逐年三条恒等式全部通过；
- manifest qbase 向量中 `express=15 / forecast=1`。

任一不符立即停止，不读取事件后收益，不作运行后解释、不追数、不改规则。

## 四、§7 单次正式运行

- `--snapshot-id`必须为本令新生成的 exp17 自有研究 manifest；
- 必须传
  `--pap-sha256-assert=92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`；
- driver 须逐字消费 11 个 `engine_params`键、4 个 `signed_ar`键与
  `axes.direction=[up,down]`，并从台账写入 `llm/prescreen` 身份水印；
- 只允许一次正式执行；RC 非零、PAP/manifest/选择硬闸或任一运行断言失败即停，
  不修改代码、不自动重跑。

## 五、运行后边界与取证

- exp17 保持 `frozen`，`result_json/done_at`为空，experiment ledger 零写入；
- 台账仍为 `26=8/3/13/2`，不授权 persist；
- 封存 result/report/log 原件及 SHA256 清单，传输前执行既有 13 类秘密扫描；
- 回报 source snapshot340、14 键完整向量、manifest ID 及三处 digest、收益前选择硬闸、
  运行命令与 UTC+8 时间窗、RC、核心统计、身份水印、运行后状态与 Git 状态。

Fable 行为复核的两条 C 级默认不采，不扩大施工。完成后停在取证点，等待结果复核；persist 另令。
