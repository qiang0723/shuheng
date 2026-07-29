# exp568 `st_imposition` manifest + §7 单次正式运行令（2026-07-29）

> John 人令原文：**「批准生成 exp568 自有研究 manifest，并执行§7单次正式运行」**。
> 本令不授权代码修改、自动重跑或 persist。

## 一、运行前只读硬闸

1. exp568 必须仍为 `frozen`，`frozen_at` 保持既有值，`result_json/done_at` 为空；
   DB PAP canonical 必须为
   `56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`；
2. 台账必须仍为 26 行：`registered 10 / frozen 3 / done 11 / closed 2`；
3. 生成前读回所用 source snapshot 的 ID、digest 与完整批次向量；其
   `namechange` 必须为 batch 7，且与正式事件及引擎实际消费面一致；任一变化立即停止，
   不生成 manifest、不运行；
4. 不得存在 exp568 既有正式研究 manifest、正式运行结果或遗留运行进程；
5. 任一前置断言不符，立即停止并报人，不修补、不追数。

## 二、exp568 自有研究 manifest

- 绑定上述已发布 source snapshot，按既有全链血缘范式生成 exp568 自有研究 manifest；
- 完成 taosha 权威行、qbase 镜像与 publication attestation 三处发布，digest 必须一致；
- 运行前复核 manifest 完整向量与 source snapshot/派生批血缘相容；
- 仅授权 manifest 相关表写入，不授权 experiment ledger 写入。

## 三、§7 单次正式运行

- 必须传
  `--pap-sha256-assert=56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`；
- `--snapshot-id` 必须为本令新建的 exp568 自有研究 manifest；
- 正式选择审计须精确满足：`765` 个事件、`646` 个证券、带星 `560`、不带星
  `205`；四项任一不符立即停止，不调用正式研究引擎、不作运行后解释；
- 漏斗恒等式与组成恒等式必须全部为真；family 必须为
  `delist_warning_financial`、`family_trial=2`、双侧 `alpha=0.025`，且 trial 只来自台账；
- 只允许一次正式执行；RC 非零、锚定失败或任何硬闸不符即停，不修改代码、不自动重跑。

## 四、运行后边界与取证

- exp568 保持 `frozen`，`result_json/done_at` 保持空，experiment ledger 零写入；
- 不授权 persist；
- 封存 result/report/log 原件及 SHA256 清单；传输前完成 13 类秘密扫描，命中即停且
  不改原件；
- 只读回报 source snapshot、manifest 三处 digest、完整向量、四项事件硬闸、两条恒等式、
  family/trial/alpha、核心统计、运行时间窗与 RC、运行后台账及 git 状态；
- 完成后停在取证点，等待结果复核与另行 persist 授权。
