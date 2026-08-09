# exp14 `ex_div_gap` · manifest + §7 单次正式运行令

日期：2026-08-09（UTC+8 / Asia/Shanghai）

> John 在冻结与行为验收外部复核通过后亲自授权：
>
> 批准 exp14 ex_div_gap 生成自有研究 manifest，并执行 §7 单次正式运行。完整 manifest 键集须恰等
> snapshot375 的13个 qbase 键及 taosha market_return=88 / pool_b1=18 / pool_b1_return=18，
> 共16键；source375 digest=2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7。
> 绑定 PAP digest=a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7。
> 正式事件必须精确为4,035、恰等边界1,083、selection SHA=
> ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f；任一不符即停，
> 不自动重跑。运行后保持 exp14 frozen、双槽空、ledger零写入；本令不授权 persist，完成停取证点。

Fable 限域复核结论：`A级0 / B级0 / C级1 → 行为验收通过，可进入 manifest + §7 单次正式运行
授权点`。C 级要求正式令自钉参考数与完整向量，本令已逐项落实。

## 一、运行前只读硬闸

任一不符立即停止，不生成 manifest、不读取事件后收益：

1. exp14 仍为 `frozen`，`frozen_at=2026-08-09 14:33:15.200827+08`不变，
   `result_json/done_at`为空；台账身份须为 `exp14/ex_div_gap/trial1/llm/prescreen`；
2. 台账26行，分布须为 `registered=6/frozen=3/done=15/closed=2`；不存在 exp14 既有研究
   manifest、正式结果或遗留研究进程；
3. DB PAP canonical 须为
   `a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；
4. source snapshot375 在 taosha 权威行、qbase 镜像与 publication attestation 三处 digest 均为
   `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，且无 taosha 半；
5. snapshot375 qbase 键集须恰等下列13项，值须逐项相等：
   `adj_factor=7 / daily=6 / dividend=17 / express=15 / fina_audit=16 / forecast=1 /
   holder_sell_predisclose=12 / namechange=7 / sox_daily=13 / stk_holdertrade=2 /
   stock_basic=6 / sw_member=14 / trade_cal=10`；
6. taosha 派生批须为 `market_return=88 / pool_b1=18 / pool_b1_return=18`；三批血缘须可证，
   实际 qbase 依赖须与 snapshot375 对应子向量逐项一致，`pool_b1_return=18`父池须为
   `pool_b1=18`。

## 二、正式路径硬闸补正

运行令施工前审计发现：验收 commit `146eea5` 的 `assert_reference()` 只由 recon 分支调用，正式
分支虽复用同一 selection 路径，但缺少 driver 内层三值断言。Fable 对“正式路径已调用”的描述与实物
不符。正式单跑额度尚未消耗。

按最小修复上限，只允许：

1. 在正式 `_run_formal` 得到 selection 后、构造 `ViewReader` 与读取收益前调用既有
   `assert_reference(selection)`；
2. adapter fixture 新增一条静态顺序攻击断言，证明三值硬闸早于 `ViewReader` 与
   `runner.run_study`；
3. 重新执行 exp14 专项、全部既有离线回归、数据库硬门与规模闸门。零统计规则、零 PAP、零 SQL、
   零报告语义改动。任一失败即停，不进入 manifest。

## 三、exp14 自有研究 manifest

1. 只允许一次以 `--create --from-source-snapshot 375` 生成 exp14 自有研究 manifest；
2. 完成 taosha 权威行、qbase 镜像、publication attestation 三处发布，content 与 digest 须一致；
3. 完整 manifest 键集必须恰等第一节的13个 qbase 键与3个 taosha 键，共16键；多一键、少一键或
   值异均停；
4. 生成后重验三个派生批血缘、父池关系及镜像与发布凭证；
5. 本节只授权 StudySnapshot manifest 相关表写入，不授权 experiment ledger 写入。

## 四、收益前选择硬闸

在构造 `ViewReader`、读取事件后收益与调用正式研究引擎前，新 manifest 须独立且在 driver 内再次通过：

- 最终事件数恰为 `4,035`；Decimal 恰等边界恰为 `1,083`；
- selection SHA256 恰为
  `ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；
- 六条选择恒等式全部为真；manifest 完整键集与第一节精确一致。

任一不符立即停止，不追数、不改冻结规则、不读取收益。

## 五、§7 单次正式运行

1. `--snapshot-id`必须为本令新生成的 exp14 自有研究 manifest，不得为375；
2. 必须传完整 `--pap-sha256-assert=a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；
3. driver 须逐字消费8个 `engine_params`键、三处 `τ0=ex_date当日`冻结文本，启用
   `tau0_on_anchor=True`，拒绝 `signed_ar`，并从台账注入
   `exp14/ex_div_gap/trial1/llm/prescreen`身份水印；
4. 只允许一次正式执行；RC 非零或任一断言失败即停，不修改代码、不自动重跑。

## 六、运行后边界与取证

1. exp14 保持 `frozen`、`frozen_at`不变、`result_json/done_at`为空；experiment ledger 零写入，
   台账仍为 `26=6/3/15/2`；
2. 封存 result/report/log 原件及 SHA256，执行13类秘密扫描；
3. 回报 source375、16键向量、manifest ID与三处digest、收益前三值硬闸、正式命令与UTC+8时间窗、
   RC、核心统计、身份水印、运行后状态与Git身份。

本令不授权自动重跑、敏感性分析或 persist。完成后停在取证点，结果复核后只能由 John 另行授权 persist。
