# exp13 一字跌停开板 §7 单次正式运行取证交付档(2026-07-21)

> 授权=人令 2026-07-21 深夜(原文档 `limit-down-open-run-order-2026-07-21.md`,留痕 commit `e0a2cde`)。
> **代码修改与 persist 不在本令授权范围,未执行未触碰**;本档即取证点交付,停等人验收。

## 1. 单元 commit 链(F 条:留痕先行)

`e0a2cde`(人令留痕)→ 本档+STATE(纯 docs,零代码施工——本令不授权代码修改,行为代码基线止于
`0599a64` 既有件)。运行时生产 HEAD=`e0a2cde`,两台同、git 净(dirty=0,postrun 实测)。

## 2. 前置只读读回(preflight_readback.txt,17/17 ALL_PASS)

- exp13 status=**frozen**、frozen_at=2026-07-21 22:23:24.984414+08、result_json/done_at 空;
  DB PAP canonical 重算 == 令 digest `583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42`。
- 台账 25=registered15/frozen3/done6/closed1;study_snapshot 8 行(零新增基线,max_id=166)。
- **向量对账(令:不一致即停报人)**:current qbase 五键 max(batch_id)=daily 6/adj_factor 7/
  stock_basic 6/namechange 7/trade_cal 10 == manifest 121 qbase 五键 == 源快照 74 五键,逐项相等
  **未触停报线**;派生批现值 market_return 88/pool_b1 18/pool_b1_return 18 == manifest 121 taosha 半。
- 源快照 74 三处 digest(权威行/qbase 镜像/attestation)全等=`075efda7…015c`。

## 3. manifest 生成与发布(令:权威行+镜像+attestation,不得以 121 冒充)

- **研究 manifest=189**(`--create --from-source-snapshot 74`,沿 exp8/exp20 血缘范式;taosha 半=
  派生批现值 88/18/18)。发布三步毕:taosha 权威行+qbase 镜像+publication attestation
  **三处 digest 同=`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`**
  (==87/121/166 同 content 系——源自 07-16 后零刷新、派生批未动,digest 同值系必然)。
- **非 121 冒充**:snapshot_id=189 为新建权威行(study_snapshot 恰增 1 行至 9);driver 对
  `--snapshot-id 121` 的 fail-closed 闸在场未触发;result.audit.study_snapshot 记 189。
- 血缘 fail-closed 照既有:verify_manifest_lineage **24/24**+verify_snapshot_mirror **11/11**,零异常。

## 4. §7 单次正式运行(单次执行,RC=0)

- 命令面:`run_limit_down_study --exp-id 13 --snapshot-id 189 --pap-sha256-assert 583c4c94…0c42`
  (aliyun,/opt/venvs/qbase-ingest 解释器;2026-07-21 23:37:29+08 起单次执行,未重跑)。
- 锚定:台账 status=frozen 放行;driver 重算 canonical digest==断言值**通过**;engine_params 逐字消费
  (market/strata F/st_mode event_day/st keep/adj_bmp_main_only/nfv T/unified/dims=(st,listing_age))。
- **漏斗(与 Snapshot 121 同向量基线精确一致,令停报线未触)**:输入行 15,099,011→成员行 18,106→
  链 3,323→右删失 47→pre2007 456(post 0)→listing 0→duplicate 0→hijack 26→
  **主事件集 2,794==基线**;ST 1,480/非 ST 1,314;recent_listing 29/seasoned 2,765;
  ST 链起点 vs 事件日不一致 74;右删失∧hijack 正交 0——全部与 recon 权威数字逐档相等。
- **样本**:N_valid=2,124(剔除 670,剔除率 0.2398 ⚠告警>5% 如实报;逐年剔除原因=coverage/postpone
  入报告);ρ̄=0.0788(21,106 对),Kish N_eff≈12.6/KP≈11.6;估计窗覆盖 112/152.6/160。
- **verdict=`NOT_SIG`**:主窗 [0,+4] CAAR=**−0.04478**(N=2,036)**ADJ-BMP=−1.444 双侧不显著**
  (α=0.05 临界±1.960);朴素 t=−19.383/Corrado=−9.263/日历 t=−14.246 名义显著仅报告不改判
  (疑聚集假阳性注记在场);次级窗 [0,+19] CAAR=−0.05820(ADJ-BMP −1.079,不判决);
  稳健窗 [0,+59] CAAR=−0.08154(ADJ-BMP −0.576,NFV)。
- 正交诊断轴(NFV 零判决):ST 层主窗 CAAR=−0.03169(ADJ-BMP −0.936)/非 ST 层 CAAR=−0.05976
  (ADJ-BMP −2.210);listing_age:recent_listing 29 事件存活 0=UNESTIMABLE_BY_FROZEN_COVERAGE
  (逐因 coverage 29),seasoned=主集同值。可交易口径(NFV):主窗净均值+0.00212 胜率 0.494。
- **行业 unknown 残余组 570/2,124=26.8% ⚠升级上报**(如实记,不改判;exp20 先例同类项 6.7%)。

## 5. 取证与只读回报

- **取证包=AWS `~/shuheng/s13_run_delivery_2026-07-21/`**(aliyun 原件 /root/s13run/):
  result_exp13.json `c71a696d…8b83e` / report_exp13.txt `9ad456e9…77f8` / run13.log `fc499797…405f`
  +preflight_readback+manifest_create.log+manifest_readback+lineage_mirror_tail+postrun_readback
  +secret_scan_report+SHA256SUMS+README;`sha256sum -c` 本地==远端逐项全 OK。
- **秘扫**:13 类(同 s7/s8/s20 清单)TOTAL_HITS=**0**,原件零修改,传输放行。
- **只读回报(postrun_readback.txt,21/21 ALL_PASS)**:①exp13 status=**frozen** 保持,
  **frozen_at=2026-07-21 22:23:24.984414+08(冻结既有值,未变)**,result_json 空、done_at 空
  ②台账 **25 行=registered 15/frozen 3/done 6/closed 1**(运行全程零写入)③result 记
  manifest 189+digest(硬化②)④漏斗 13 键逐档==基线 ⑤PAP canonical 不变==令 digest
  ⑥生产 git 净(HEAD `e0a2cde`,dirty=0)。
- 读回工具痕如实记:第一次 postrun 读回件 6 条 FAIL=读回脚本 counters 键名笔误(如
  right_censored 应为 right_censored_no_event_day),**非数据不符**;原件保留为
  `postrun_readback_attempt1_wrongkeys.txt` 入包,键名修正后同一只读读回 21/21 ALL_PASS;
  库/result 实物零变化,正式运行未重跑。

## 6. 边界声明

- 只执行一次;RC=0;全部锚定/计数断言通过,主事件集==2,794 基线,无停报事项。
- **persist 未授权未执行**;结果解读效力=llm/prescreen(报告水印在场);**预判开封对照属 persist
  阶段事项,本档不做**(预判原文绑定 digest `583c4c94…0c42` 已在冻结验收档,原文永不改述)。
- 解读边界照冻结件:NOT_SIG 仅冻结口径下成立;偏差方向声明(bias_statement)在场=估计对象仅限
  冻结规则下存活主事件集,不得外推全体一字跌停链事件。
- 下一步(须人令)=人验收本取证包(+外审如需)→另下 persist 令;未令不动。
