# exp16 `yearend_strength` · manifest + §7 单次正式运行令（2026-07-30）

> John 在外部行为复核通过后明确回复：**“批准”**，承接上一条所列下一阶段=
> exp16 自有研究 manifest + §7 单次正式运行。本令不授权代码修改、自动重跑或 persist。

## 一、运行前只读硬闸

1. exp16 必须仍为 `frozen`，`frozen_at=2026-07-30 11:01:09.498726+08` 不变，
   `result_json/done_at` 为空；DB PAP canonical 必须为
   `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
2. 台账必须仍为 26 行：`registered 9 / frozen 3 / done 12 / closed 2`；
3. source snapshot 必须为 74，digest 必须为
   `075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`；完整研究
   manifest 向量键集须恰等十一项：qbase `daily=6 / forecast=1 / trade_cal=10 /
   adj_factor=7 / namechange=7 / stock_basic=6 / stk_holdertrade=2 /
   holder_sell_predisclose=12`，taosha `market_return=88 / pool_b1=18 /
   pool_b1_return=18`；多键、少键或值异即停；
4. 三个 taosha 派生批的 source anchor 必须指向 snapshot 74，且
   `pool_b1_return=18` 的父池必须为 `pool_b1=18`；
5. 不得存在 exp16 既有正式研究 manifest、正式结果或遗留运行进程；任一不符立即停止，不生成
   manifest、不运行、不修补。

## 二、exp16 自有研究 manifest

- 以 `--create --from-source-snapshot 74` 一次生成 exp16 自有研究 manifest；
- 完成 taosha 权威行、qbase 镜像、publication attestation 三处发布并核对 digest 一致；
- 不得使用 snapshot 74 或其他既有 snapshot 冒充；
- 仅授权 manifest 相关表写入，不授权 experiment ledger 写入。

## 三、收益前选择硬闸

在调用正式研究引擎和读取事件后收益前，以新 manifest 独立执行冻结选择规则，只读断言：

- 最终事件数必须为 `7,751`；
- selection SHA256 必须为
  `057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`；
- 面板、事件锚、逐年分布三条恒等式必须全部为真；
- manifest 事件选择向量必须与冻结前 snapshot74/market88 对账向量一致。

任一不符立即停止，不调用正式研究引擎，不作运行后解释、不追数、不改规则。

## 四、§7 单次正式运行

- `--snapshot-id` 必须为本令新建的 exp16 自有研究 manifest；
- 必须传
  `--pap-sha256-assert=3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- driver 必须逐字消费冻结 8 键，`st_policy=keep`、`tau0_on_anchor=True` 的正文锚均须通过；
- 只允许一次正式执行；RC 非零、PAP/manifest/选择硬闸或任何运行断言失败即停，不修改代码、
  不自动重跑。

## 五、运行后边界与取证

- exp16 保持 `frozen`，`result_json/done_at` 为空，experiment ledger 零写入；
- 不授权 persist；
- 封存 result/report/log 原件与 SHA256 清单，传输前执行既有 13 类秘密扫描；
- 回报 source snapshot、完整十一键向量、manifest 三处 digest、收益前选择硬闸、运行命令与时间窗、
  RC、核心统计、执行限制审计、运行后状态与 git 状态；
- 外部复核提出的 recon app 连接只读机制 B 级项不进入正式路径：正式运行只使用 engine 身份与
  manifest 路由；本轮不扩大为平台修复。C 级 `rows[0].tau` 顺序显式化默认不采。

完成后停在取证点，等待结果复核；persist 另令。

