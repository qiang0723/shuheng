# exp13 冻结验收通过+manifest/§7 正式运行授权令(2026-07-21,人令原文即口径)

> 留痕纪律(F 条):人令留痕 commit 先于施工。本档为 2026-07-21 深夜人令逐字原文。
> 代码修改与 persist 不在本令授权范围。

## 人令原文(逐字)

> exp13冻结与适配行为验收通过。授权生成并发布exp13正式研究manifest,并以冻结PAP digest:
> 583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42
> 执行§7单次正式运行。
> 运行前确认数据向量与Snapshot 121对账向量一致;不一致即停报人。新manifest须完成权威行、镜像和attestation,且不得使用121冒充。
> 正式运行只允许一次;失败或主事件集不等于同向量基线2,794时不重跑、不修补。运行后保持exp13 frozen、结果槽为空、台账零写入。
> 按既有先例提交result/report/log、SHA256、秘密扫描、manifest读回、核心统计及运行后状态,随后停交验点。
> 本令不授权修改代码或persist。

## 执行边界(照令展开,先例=exp20 run order 2026-07-19 / exp8 s7 2026-07-17)

- **前置(只读)**:exp13 status=frozen、result/done 槽空、台账 25=15/3/6/1、PAP DB canonical
  重算 == 令 digest `583c4c94…0c42`;current qbase 五键向量(daily/adj_factor/stock_basic/
  namechange/trade_cal)与 Snapshot 121 对账向量(6/7/6/7/10)逐项相等,不等即停报人。
- **manifest**:`--create --from-source-snapshot`(沿 exp8/exp20 血缘范式),发布三步毕
  (taosha 权威行+qbase 镜像+publication attestation)三处 digest 一致;血缘/镜像 fail-closed
  套件照既有;**不得以 snapshot 121 冒充**(driver 对 --snapshot-id 121 fail-closed 已在场)。
- **§7 单跑**:driver 逐字消费冻结 engine_params,`--pap-sha256-assert 583c4c94…0c42`;
  只执行一次;RC 非零、任一锚定断言失败、或主事件集 ≠ 同向量基线 **2,794** 即停,不重跑不修补。
- **运行后**:exp13 保持 frozen(frozen_at=冻结既有值 2026-07-21 22:23:24.984414+08 不变)、
  result_json/done_at 空、台账 25 行零写入、两台 git 净。
- **取证**:result/report/log 三件+SHA256 清单+13 类秘密扫描(命中不改原件停报)+manifest
  三处 digest 读回+核心统计+运行后只读回报,交付包落 AWS,随后停交验点。
- **禁区**:零代码修改、零 persist、零台账写入;失败停报不自救。
