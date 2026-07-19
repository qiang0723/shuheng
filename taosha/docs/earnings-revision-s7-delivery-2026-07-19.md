# exp20 业绩预告修正 §7 单次正式运行取证交付档(2026-07-19)

> 授权=人令 2026-07-19(原文档 `earnings-revision-run-order-2026-07-19.md`,留痕 commit `54193ae`)。
> **persist 不在本令授权范围,未执行未触碰**;本档即取证点交付,停等人验收+外审复核。

## 1. 单元 commit 链(F 条:留痕先行)

`54193ae`(人令留痕)→ `af46bf6`(注记内嵌施工:driver 注入 result.provenance_note 冻结原文+
report 沿 bias_statement 同机制消费渲染+adapter fixture 三断言 19→24)→ 本档+STATE。
两台 HEAD 同、git 净(运行时生产 HEAD=`af46bf6`,dirty=0,见 postrun_readback)。

## 2. 令一:注记内嵌+三断言(随令一次完成)

- 机制:driver 正式运行路径注入 `result["provenance_note"]`={key, text=冻结原文, source_anchor};
  report 自 result 注记字段直接消费渲染(沿 bias_statement 同机制);无键零新行 → 旧路径零回归。
- fixture 面(合成,verify_earnings_revision_adapter **24/24** 两台):driver 常量==独立字面量逐字/
  渲染报告完整注记逐字在场/"不可归因旧口径差额−12"+"不可重放"在场/"5,225已复现"零命中/无键渲染逐字节零回归。
- **真实产物面(report_exp20.txt + result_exp20.json 双件)**:断言①完整注记逐字在场=True;
  断言②"不可归因旧口径差额−12"在场=True、"不可重放"在场=True;断言③"5,225已复现"命中=**0**。三断言无例外全过。
- 零回归:e2e 合成基线 `3116ba9b74f7c53b…` 改前改后两台双跑逐字节同;全家福两台全绿
  (aliyun 钉版:pap 23/状态机 46/addendum 14/镜像 11/血缘 24/探针 19/集成 7/7+非 DB 全套;AWS 非 DB 同清单)。

## 3. 令二:manifest 生成与发布

- **前置读回(生成前,入取证包 preflight_readback.txt)**:源快照 74 权威行/qbase 镜像/attestation
  三处 digest 同=`075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`;向量 forecast:1
  == qbase forecast_snap 唯一实物批 batch_id=1(138,458 行,ann_date 1999-01-08..2026-07-07);
  与 recon-only(07-18)所读现值面批[1]一致=本次正式运行经 manifest 路由将读之批,一致性判定成立。
- **研究 manifest=166**(`--create --from-source-snapshot 74`,沿 exp8 血缘范式;taosha 半=派生批现值
  market_return:88/pool_b1:18/pool_b1_return:18)。发布三步毕:taosha 权威行+qbase 镜像+publication
  attestation **三处 digest 同=`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`**
  (==87/121 同 content 系必然;content md5 `aa940b61` 双库同)。
- 血缘 fail-closed 照既有:verify_manifest_lineage **24/24**+verify_snapshot_mirror **11/11**,零异常。

## 4. 令三:§7 单次正式运行(单次执行,RC=0)

- 命令面:`run_earnings_revision_study --exp-id 20 --snapshot-id 166 --pap-sha256-assert e1d18dc1…7fd5`
  (aliyun,/opt/venvs/qbase-ingest 解释器;2026-07-19 17:47 单次执行,未重跑)。
- 锚定:台账 status=frozen 放行;driver 重算 canonical digest==断言值**通过**;engine_params 11 键逐字消费
  (market/strata F/st reject/adj_bmp_main_only/nfv T/unified_announcement/dims=(direction,)/signed T/raw/adj_bmp_sign)。
- **漏斗(与 recon 对账层精确一致)**:输入 127,166→重复折叠 11,935→全期候选 12,559→研究期 8,181→
  fail-closed 六类{孤儿 416/时序 10/多链 0/数值不可判 2,587/同日冲突 0/600856=3}→flat 283(排除计数块)→
  **主事件集 4,892(up 2,054/down 2,838)**;同日折叠 0/冲突拒 0;候选层恒等 12,559+10=12,569 vs 参考 Δ=+0;
  可判层 5,175 vs 5,225 Δ=−50(注记见报告 provenance 块)。
- **样本**:N_valid=3,335(剔除率 0.3183 告警如实报;分年剔除原因=coverage/postpone/st/history 逐年入报告);
  ρ̄=0.0217(20,356 对),Kish N_eff≈45.4。
- **verdict=`NOT_SIG`**:主窗 [0,+4] signed CAAR=+0.00699(N=3,282)**ADJ-BMP=0.607 双侧不显著**
  (α=0.05 临界±1.960);朴素 t=5.688/Corrado=3.204/日历 t=3.476 名义显著仅报告不改判(疑聚集假阳性注记);
  次级窗 [0,+19] CAAR=+0.00630(ADJ-BMP 0.163,不判决);稳健窗 [0,+59] CAAR=+0.00840(ADJ-BMP 0.224,NFV)。
- **effect_alignment=ALIGNED**(CONTEXT 非 verdict 字段,source=adj_bmp_sign;四态不产生不改变判决)。
- direction 诊断轴(raw,NFV 零判决):up 层主窗 CAAR=+0.00776(ADJ-BMP 0.357)/down 层 CAAR=−0.00642
  (ADJ-BMP −0.201),诊断层 `_verdict` 调用=0 设计维持。
- 行业 unknown 残余组 224/3,335=6.7% 告警升级上报(如实记,不改判)。

## 5. 令四:取证与只读回报

- **取证包=AWS `~/shuheng/s20_run_delivery_2026-07-19/`**(aliyun 原件 /root/s20run/):
  result_exp20.json `7cf44b41…a6f0` / report_exp20.txt `3b5de3c4…a030e` / run20.log `ca66f7ea…d78c`
  +preflight_readback+manifest_create.log+manifest_readback+postrun_readback+secret_scan_report+SHA256SUMS
  +README;`sha256sum -c` 本地==远端逐项全 OK。
- **秘扫**:13 类(同 s7/s8 清单)TOTAL_HITS=**0**,原件零修改,传输放行。
- **只读回报**:①源快照 74 前置读回=三处 digest 全等(见 §3)②manifest 166 三处 digest 读回全等
  ③exp20 status=**frozen** 保持,**frozen_at=2026-07-19 00:26:27+08(冻结时既有非空值,未变)**,
  result_json 空、done_at 空 ④台账 **25 行=registered 16/frozen 3/done 5/closed 1**(运行全程零写入)
  ⑤注记三断言=①True/②True+True/③0 命中(双产物)⑥生产 git 净(HEAD `af46bf6`,dirty=0)。

## 6. 边界声明

- 只执行一次;RC=0;全部锚定/计数断言通过,无停报事项。
- **persist 未授权未执行**;结果解读效力=llm/prescreen(报告水印在场);密封预判开封对照属 persist
  阶段事项,本档不做。
- 下一步(须人令)=人验收本取证包+外审复核→另下 persist 令。

## 7. persist 终令执行与正式闭卷(2026-07-19 晚,人令原文=earnings-revision-persist-order-2026-07-19.md,留痕 `d69415f` 先行)

外部已直接核对原件;此前流通的错误数字组(51e0e79d / manifest 122 / CAAR −0.317% / REVERSED /
N_valid 4,829)经外部认定为串档转述,双方相关目录及权威留痕零命中,以权威实物为准恢复 persist。

### 7.1 前置断言(只读,22/22 全 PASS)

脚本+日志留档 aliyun `/root/s20persist/preassert_exp20.{py,log}`:
- 三件原始产物 SHA256 全等:result `7cf44b41…a6f0` / report `3b5de3c4…a030e` / log `ca66f7ea…d78c`;
- result 原件直接断言 10/10:顶层唯一 verdict=NOT_SIG / 主窗 signed CAAR=0.00698934637496006 /
  ADJ-BMP=0.6072938553928457 / effect_alignment.value=ALIGNED / N_valid=3335 / 主窗 N=3282 /
  manifest=166+digest / provenance 注记逐字在场(与人令冻结原文独立字面量逐字等)/ 顶层之外 verdict 键=0;
- exp20 库态:frozen / frozen_at 非空 / result_json·done_at 空 / DB pap_json canonical digest==
  `e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`;
- 台账 25 行=registered 16/frozen 3/done 5/closed 1;
- manifest 166 三处 digest(taosha 权威行/qbase 镜像/publication attestation)均==
  `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`。

### 7.2 执行(既有状态机,单连接单事务一次 COMMIT)

- 脚本+日志留档 aliyun `/root/s20persist/persist_exp20.{py,log}`(exp8 先例 `/root/s8persist/` 范式);
- 身份=taosha_app(ledger.connect 既有 DSN);解释器=/opt/venvs/qbase-ingest/bin/python3;
- 入事务前再断言 6 项(verdict/事件数 4892/N_valid 3335/manifest 166+digest/result 内 PAP digest)+
  事务内 FOR UPDATE 再断言(status=frozen + DB PAP canonical==e1d18dc1…7fd5)→
  `ledger.start_running(20)` → `ledger.finish(20, result)` → 一次 COMMIT;
- result 唯一来源=已验收原件 `/root/s20run/result_exp20.json`,零重跑/零重生成/零改写/零旁路 SQL;
- COMMIT OK @ **2026-07-19 20:13:42+08**(=done_at)。

### 7.3 persist 后核验(只读,14/14 全 PASS)

脚本+日志留档 aliyun `/root/s20persist/postverify_exp20.{py,log}`:
- exp20=done / done_at=2026-07-19 20:13:42.003687+08 / 顶层 verdict=NOT_SIG;
- 库内 result_json 与原件 parsed_equal=True;canonical 序列化 SHA 双侧一致=
  `49e5bcd42c6d4dd8c78bc61f7f29cc0deeac35d335ca3705df6ccbfd9ddc839c`(库侧 jsonb::text md5=`b433867b…b9a3`);
- 关键数值零删减零补写(库侧再断言 CAAR/ADJ-BMP/N/N_valid/事件数/alignment/manifest/注记全等);
- 台账仍 25 行=**registered 16 / frozen 2 / done 6 / closed 1**(恰迁 exp20 一行,零新增);
- manifest 166 三处 digest 不变;三件原始产物 SHA 不变;frozen_at=冻结既有值 00:26:27 未变;
- 生产 git 工作区净(核验时 HEAD `d69415f`)。

### 7.4 闭卷留痕三件(人令第三节;只入档,不写入、不反向改造 result_json)

**① 密封开封对照(校准册第二条)**
- 预判原文:"主窗[0,+4]市场调整后 signed CAR 为负,把握度 55%",绑定 PAP v2 digest `e1d18dc1…7fd5`。
- 实测 signed CAAR 为 +0.6989346%,**方向未命中**;ADJ-BMP 不显著,终态 NOT_SIG。
- 如实入册;预判原文永不改述。

**② 方法限制固定**
- NOT_SIG 仅在冻结的行业分组口径下成立;行业缺失组占 6.7%,未验证其他缺失行业处理方式下的稳健性。
- 不得结果后修改行业分组或追加敏感性重跑。

**③ 解读边界**
- 实测方向为正但不显著,不能认定存在沿修正方向或逆修正方向的可靠效应;
- 朴素 t、Corrado、日历时间法的名义显著均为 NOT_FOR_VERDICT,不得改读正式结论;
- 效力固定为 llm/prescreen,不得写成 full 证据。

### 7.5 终态

exp20 正式闭卷。不再追加复核、重跑或施工;停工交终签。
