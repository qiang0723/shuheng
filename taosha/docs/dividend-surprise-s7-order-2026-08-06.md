# exp19 `dividend_surprise` · manifest + §7 单次正式运行令

日期：2026-08-06（UTC+8 / Asia/Shanghai）

> John 在冻结与行为验收外部复核通过后亲自授权：
>
> 批准 exp19 生成自有研究 manifest 并执行§7单次正式运行。完整 manifest 键集须恰等
> snapshot375 的13个qbase键及 taosha market_return=88/pool_b1=18/pool_b1_return=18，共16键；
> 绑定PAP digest 4d5e6840…60b4。正式事件须精确为5,055=up2,253+down2,802，selection SHA须为
> 985e2312…a2e6b；任一不符即停，不自动重跑。运行后保持exp19 frozen、双槽空、ledger零写入；本令
> 不授权persist，完成停取证点。

Fable 限域复核结论：`A级0 / B级0 / C级2 → 通过，可进入 manifest + §7 单次正式运行
授权点`。C 级两项默认不采，不扩大施工。

## 一、运行前只读硬闸

任一不符立即停止，不生成 manifest、不读取事件后收益：

1. exp19 仍为 `frozen`，`frozen_at=2026-08-06 17:21:15.889471+08`不变，
   `result_json/done_at`为空；台账身份须为
   `exp19/dividend_surprise/trial1/llm/prescreen`；
2. 台账26行，分布须为 `registered=7/frozen=3/done=14/closed=2`；不存在 exp19
   既有研究 manifest、正式结果或遗留研究进程；
3. DB PAP canonical 须为
   `4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`；
4. source snapshot375 在 taosha 权威行、qbase 镜像与 publication attestation 三处
   digest 均为 `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，
   且无 taosha 半，身份只是源级快照；
5. snapshot375 qbase 键集须恰等下列13项，值须逐项相等：
   `adj_factor=7 / daily=6 / dividend=17 / express=15 / fina_audit=16 / forecast=1 /
   holder_sell_predisclose=12 / namechange=7 / sox_daily=13 / stk_holdertrade=2 /
   stock_basic=6 / sw_member=14 / trade_cal=10`；
6. taosha 派生批须为 `market_return=88 / pool_b1=18 / pool_b1_return=18`；三批血缘
   须可证，实际 qbase 依赖须与 snapshot375 对应子向量逐项一致，
   `pool_b1_return=18`的父池必须为 `pool_b1=18`。

人授权中的缩写 digest 仅为展示缩写；本节给出的已冻结全值是机器断言唯一值，不构成
口径改写。

## 二、exp19 自有研究 manifest

1. 只允许一次以 `--create --from-source-snapshot 375` 生成 exp19 自有研究 manifest；
2. 完成 taosha 权威行、qbase 镜像、publication attestation 三处发布，content 与
   digest 须逐字一致；
3. 完整 manifest 键集必须恰等第一节的13个 qbase 键与3个 taosha 键，共16键；
   多一键、少一键或值异均停；
4. 生成后重验三个派生批血缘、父池关系及镜像与发布凭证；
5. 本节只授权 StudySnapshot manifest 相关表写入，不授权 experiment ledger 写入。

## 三、收益前选择硬闸

在构造 `ViewReader`、读取事件后收益与调用正式研究引擎前，新 manifest 须独立通过：

- 最终 signed 事件数恰为 `5,055`，其中 `up=2,253 / down=2,802`；
- selection SHA256 恰为
  `985e2312a7de4aca489a888647913e15fbff914899dd3f8459e5d489304a2e6b`；
- driver 内冻结参考数、六类分类与五条恒等式全部通过；
- manifest qbase 向量中 `dividend=17`，完整键集与第一节精确一致。

任一不符立即停止，不作运行后归因、不追数、不改冻结规则。

## 四、§7 单次正式运行

1. `--snapshot-id`必须为本令新生成的 exp19 自有研究 manifest，不得为375；
2. 必须传
   `--pap-sha256-assert=4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`；
3. driver 须逐字消费11个 `engine_params`键、4个 `signed_ar`键与
   `axes.direction=[up,down]`，并从台账写入 `exp19/dividend_surprise/trial1/llm/prescreen`
   身份水印；
4. 只允许一次正式执行；RC 非零、PAP/manifest/选择硬闸或任一运行断言失败
   即停，不修改代码、不自动重跑。

## 五、运行后边界与取证

1. exp19 保持 `frozen`，`frozen_at`不变，`result_json/done_at`为空；experiment ledger
   零写入，台账仍为 `26=7/3/14/2`；
2. 封存 result/report/log 原件及 SHA256 清单，传输前执行既有13类秘密扫描；
3. 回报 source snapshot375、16键完整向量、manifest ID 及三处 content/digest、收益前
   四值选择硬闸、正式命令与 UTC+8 时间窗、RC、核心统计、身份水印、运行后状态
   与 Git 状态。

本令不授权修改代码、自动重跑或 persist。完成后停在取证点，结果复核后只能由
John 另行授权 persist。
