# exp12 `st_removal` §7 单次正式运行取证交付档(2026-07-23)

> 授权=人令 2026-07-23 二深夜(原文档 `st-removal-manifest-run-order-2026-07-23.md`,
> 留痕 commit `8b96570` F 条先行)。**代码修改、重跑与 persist 不在本令授权范围,未执行未触碰**;
> 本档即取证点交付,停等人验收。

## 1. 单元 commit 链(F 条:留痕先行)

`8b96570`(人令留痕:行为验收通过+两裁定〔st_policy='keep' 必然实现固定消费·不可判 2 例批准〕
+manifest/§7 授权)→ 本档+STATE(纯 docs,零代码施工——行为代码基线止于 `b0229ef` 既有件)。
运行时生产 HEAD=`8b96570`,两台同、git 净(postrun 实测 dirty=0)。

## 2. 前置只读读回(preflight_readback.txt,16/16 ALL_PASS)

- exp12 status=**frozen**、frozen_at=2026-07-23 19:45:23.251569+08、result_json/done_at 空;
  DB PAP canonical 重算 == 令 digest `62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`。
- 台账 25=registered14/frozen3/done7/closed1;study_snapshot 9 行基线(max=189,零新增)。
- **源快照读回(令:生成前读回 source snapshot 及 namechange 批次)**:源快照 74 三处
  (权威行/qbase 镜像/attestation)digest 全等=`075efda777bd3bcd…8ac1015c`;
  **current qbase 五键现值 = daily 6/adj_factor 7/stock_basic 6/namechange 7/trade_cal 10
  == 源快照 74 五键逐项相等(向量停报线未触)**;
  **namechange 批次=7 == 事件数据实际来源**(适配单元 recon 现值面=batch7,一致)。

## 3. manifest 生成与发布(令:三处 digest 必须一致)

- **研究 manifest=212**(`--create --from-source-snapshot 74`,沿 exp8/exp20/exp13 血缘范式;
  qbase 半=源快照 74 向量,taosha 半=派生批现值 market_return 88/pool_b1 18/pool_b1_return 18)。
- 发布三步毕:taosha 权威行+qbase 镜像+publication attestation **三处 digest 同=
  `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`**(==87/121/166/189
  同 content 系——源自 07-16 后零刷新、派生批未动,digest 同值系必然;study_snapshot 恰增
  1 行至 10)。血缘 fail-closed 照既有:verify_manifest_lineage **24/24**+verify_snapshot_mirror
  **11/11**,零异常。result.audit.study_snapshot 记 212。

## 4. §7 单次正式运行(单次执行,2026-07-23 20:28:46+08 起;RC 干净未重跑)

- 命令面:`run_st_removal_study --exp-id 12 --snapshot-id 212 --pap-sha256-assert 62a387a2…4353`
  (aliyun,/opt/venvs/qbase-ingest 解释器;log 完整落尾、零 Traceback、result/report 双件写出)。
- 锚定:台账 status=frozen 放行;driver 重算 canonical digest==断言值**通过**;engine_params
  逐字消费(market/strata F/adj_bmp_main_only/nfv T/**missing_bar_only**/dims=());
  **st_mode='event_day'/st_policy='keep'=driver 定值(裁定一),实际值已写入
  result.audit.premend_params(st_policy="keep"/postpone_policy="missing_bar_only")**。
- **事件生成(与适配单元 recon 精确一致,停止条件未触)**:namechange 行 18,868→段 17,133→
  转换 11,601→候选 944→(不可判 2/锚缺失 296/期外 5,fail-closed 其余零)→**最终事件集
  641==batch 7 参考 Δ=0**,恒等式 OK,逐年 14 年逐字一致;NFV=摘星全史 429(窗内锚干净 222)/
  戴星 361/ST→退市 110。
- **样本**:N_valid=473(剔除 168=coverage 115/postpone 27/history 26,剔除率 0.2621
  ⚠告警>5% 如实报,逐年逐因入报告);ρ̄=0.1289,Kish N_eff≈7.6/KP≈6.7;样本量闸 30→OK。
- **verdict=`NOT_SIG`**:主窗 [0,+4] CAAR=**+0.01795**(N=463)**ADJ-BMP=+0.246 双侧不显著**
  (α=0.05 临界±1.960);朴素 t=+2.221 名义显著不改判(疑聚集假阳性注记在场);
  **Corrado 秩 t=−3.818 与 ADJ-BMP 反向,方向分歧如实报告不改判**;日历 t=+2.220 名义显著
  仅报告;次级窗 [0,+19] CAAR=−0.00246(ADJ-BMP −0.211,不判决);稳健窗 [0,+59]
  CAAR=−0.01222(ADJ-BMP −0.087,NFV)。
- **一字板执行限制(execution_limit_audit,NFV)**:τ0 日一字板事件 **71/473=15.01%**;
  一字板未控制 CAR 取样(照冻结口径进入 CAR 不顺延);cost 键仅 schema/执行审计;
  结果不表述为可成交策略证据(口径句入报告)。
- **行业 unknown 残余组 60/473=12.7% ⚠升级上报**(如实记,不改判;exp13 同类项 26.8%/exp20 6.7%)。
- ⚠预判(绑定本 digest:主窗[0,+4]CAR 正约+5%,把握 70%)vs 实测 CAAR +1.795%/NOT_SIG:
  **开封对照属 persist 阶段,本单元未做未写入,原文永不改述**(exp13 先例同轨)。

## 5. 取证与只读回报

- **取证包=AWS `~/shuheng/s12_run_delivery_2026-07-23/`**(aliyun 原件 /root/s12run/,600 权限):
  result_exp12.json `92ff3eac…4a7f` / report_exp12.txt `ac2230d0…c53d` / run12.log `f6bffbd0…01c8`
  +preflight_readback `24cbb3b9…` +manifest_create.log `3627947d…` +manifest_readback `e232efa1…`
  +postrun_readback `faec7597…` +SHA256SUMS;**`sha256sum -c` AWS 侧逐项全 OK**。
- **秘扫**:13 类(同 s13/s20 清单)TOTAL_HITS=**0**,原件零修改,传输放行。
- **只读回报(postrun_readback.txt)**:exp12 status=**frozen** 保持,
  **frozen_at=2026-07-23 19:45:23.251569+08(冻结既有值,未变)**,result_json 空、done_at 空;
  台账 25=14/3/7/1 **零写入**;study_snapshot=10 行 max=212(本单元恰增 manifest 一行,
  属令内授权);两台 git 净。

## 6. 停取证点 · 待人

人验收取证包(§4 统计终态+§5 SHA/秘扫凭证)→ **另行决定 persist**(本令明示不授权,
未做:预判开封对照/校准册/台账写入均属 persist 阶段)。未令不动。
