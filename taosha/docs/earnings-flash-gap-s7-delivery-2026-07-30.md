# exp17 `earnings_flash_gap` · manifest + §7 单次正式运行交付

日期：2026-07-30（UTC+8）
结论：**唯一一次正式运行 RC=0，顶层 verdict=`NOT_SIG`。** 已停在取证点，未 persist。

## 1. 授权与运行前硬闸

- John 授权原文：“批准生成 exp17 自有研究 manifest，并执行 §7 单次正式运行。”
- F-first 运行令：`earnings-flash-gap-s7-order-2026-07-30.md`，commit `86f54c8`。
- preflight `33/33 PASS`：exp17 仍 `frozen`，`frozen_at=2026-07-30 22:36:24.132972+08`，
  结果双槽空；PAP canonical=`92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`；
  台账26=`registered8/frozen3/done13/closed2`。
- source snapshot340 三处 digest 一致：
  `b32c5b7f0c333c4f157822c99cd150f87cff6b450a3c12f3686437b46357af4c`。current qbase
  与340的11键向量逐项相等，taosha 三键为
  `market_return=88/pool_b1=18/pool_b1_return=18`；三批依赖键血缘及父池关系均通过。
- 无 exp17 既有正式 manifest、原件或遗留研究进程；两台 Git 起步 HEAD
  `86f54c8d96c2b3beecc65403429371aaba427132`且净。

## 2. exp17 自有研究 manifest

以 `--create --from-source-snapshot 340` 一次生成：

- StudySnapshot=`363`；
- digest=`2e6f25863fb2f41b3f781c971c325456fe045a4602d1e9175a03828e4d70380b`；
- 完整键集恰为14项：qbase 11键（含 `express=15/forecast=1`）+ taosha 3键；
- taosha 权威行、qbase 镜像、publication attestation 三处 content/digest 一致；
- 血缘自检 `24/24 PASS`，镜像自检 `11/11 PASS`；
- manifest 后只读状态核验 `14/14 PASS`，experiment ledger 未写入。

## 3. 收益前选择硬闸

新 manifest363 下，在正式研究引擎之前独立复算：

- 最终 signed 事件=`2,529`（up=`997`/down=`1,532`）；
- selection SHA256=
  `cd1433f0e9cc5d60dea807dc7f4f7b26fbcf324392602205c466aa7be5bb05ac`；
- 冻结18项计数参考逐项相等，分类/事件/逐年三条恒等式均为 true；
- 向量键集与 manifest363 精确一致。

上述硬闸在 driver 正式路径中再执行一次后，才构造 `ViewReader` 读取正式收益。

## 4. §7 唯一一次正式运行

- 运行环境：镜像 `shuheng-quant:579a354`，image ID
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`，当前 HEAD
  只读挂载；strict runtime 验证通过。
- 时间：`2026-07-30 23:39:07+08`至`23:40:12+08`；只执行一次，RC=`0`，log
  无 Traceback。
- driver 逐字消费冻结 11 个 engine_params、4 个 signed_ar 与
  `axes.direction=[up,down]`；PAP digest 断言通过；result/report 皆带
  `exp17/earnings_flash_gap/trial1/llm/prescreen` 水印。

核心结果：

- 事件总数=`2,529`，N_valid=`1,841`，剔除=`688`，剔除率=`27.2044%`（告警）；
  原因合计=coverage 422/postpone 142/ST 109/history 15；
- 主窗 `[0,+4]`：N=`1,822`，signed CAAR=`0.001648578486047189`（`+0.1649%`），
  ADJ-BMP=`0.2783298113335189`，双侧不显著，顶层 `NOT_SIG`；
- 主窗辅助统计：朴素 t=`1.1504`、Corrado=`1.001`、日历法=`0.258`，均
  `NOT_FOR_VERDICT`；
- 次级 `[0,+19]`：CAAR=`+0.3596%`、ADJ-BMP=`0.1120`；稳健 `[0,+59]`：
  CAAR=`+1.9957%`、ADJ-BMP=`0.5205`，两者均 `NOT_FOR_VERDICT`；
- ρ̄=`0.0098157`，Kish N_eff≈`96.6`，KP≈`95.6`；
- 行业 unknown=`173/1,841=9.3971%`，触发升级上报，但不进入 market benchmark 判决路径；
- raw direction 层、可交易口径净额、辅助三法和次/稳窗均不得改写顶层判决；
  本实验效力仍为 `llm/prescreen`。

人的密封原文“正，把握度80%”仍原样封存；本单元不做密封开封对照，对照与校准册入册
留待 persist 终令。

## 5. 运行后状态与取证

运行后只读核验 `27/27 PASS`：

- exp17 仍 `frozen`，`frozen_at`不变，`result_json/done_at`仍空；
- PAP canonical、manifest363 三处 content/digest 不变；
- 台账仍26=`8/3/13/2`，experiment ledger 零写入；
- 递归 `verdict` 键恰一个，身份水印、PAP 绑定与 manifest 锚均通过；
- 正式研究进程零残留，Git 工作树净。

三件原件 SHA256：

- result：`a5249ec4554aff2476bc33b33b2e2600dd7cdcba01a0c98fb04e27a382394db7`；
- report：`cb29f575f9ef4a607852df518c44e8db8c542b60e63613fe51c90a3bd6878745`；
- log：`daa31bb87e072d73678baf0d5e51f5af757d6ced0737ce6e9d750f3babc7b489`。

取证目录=`/root/s17run/`；29件 `SHA256SUMS -c` 全部通过，13类秘密扫描
`TOTAL_HITS=0`，原件未修改。

## 6. 停止线

已停取证点。本令未授权 persist；结果经 Fable 只读复核后，只能由 John 另行授权
persist。未令不动台账结果槽，不重跑、不作敏感性分析。
