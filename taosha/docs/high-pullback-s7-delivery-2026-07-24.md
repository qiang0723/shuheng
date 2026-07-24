# exp11 high_pullback 研究 manifest + §7 单次正式运行 · 交付档(2026-07-24 八)

> 人令留痕:`taosha/docs/high-pullback-manifest-run-order-2026-07-24.md`(F 条先行,commit `5636c80`)。
> 行为验收外部复核通过转授权;本单元零代码修改、零重跑、零 persist;完成停取证点。

## 1. 前置只读读回(令一前半)——20/20 全 PASS

exp11 frozen(frozen_at=2026-07-24 20:09:53.513217+08 不变)/三槽空/DB PAP canonical==令 digest
`eaa54b3d…b6fc`/台账 25=13/3/8/1/snap 基线 10 行 max=212;**源快照 74 读回:digest
`075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`,权威行+qbase 镜像+
attestation 三处全等;五键批次向量精确==人令要求 daily=6/adj_factor=7/stock_basic=6/
namechange=7/trade_cal=10;current 五键现值==源快照(向量停报线未触)**。读回件=
`preflight_readback.txt` 入取证包。

## 2. 研究 manifest 生成与发布(令一)

**exp11 自有研究 manifest = StudySnapshot 235**(`--create --from-source-snapshot 74`,
沿 exp8/exp20/exp13/exp12 全链血缘范式;非 212 或任何既有 manifest 冒充)。
**权威行/qbase 镜像/publication attestation 三处 digest 一致=
`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`**(==87/121/166/189/212
同 content 系必然,五键向量同);study_snapshot 10→**11 行 max=235**(本单元恰增一行);
血缘自检 24/24+镜像自检 11/11 PASS。

## 3. §7 单次正式运行(令二)——RC=0 单跑干净,verdict=NOT_SIG

- 单次执行(2026-07-24 21:27 启动,nohup;log 零 Traceback,未重跑):digest 断言过
  (driver+runner 双保险);engine_params 逐字消费(benchmark_mode=market/strata=False/
  adj_bmp_main_only/nfv=True/missing_bar_only/diag=());
- **全宇宙扫描:输入 15,099,011 行→阶段 124,614→最终事件=42,784==令停止线精确相等**
  (新高日 361,296=阶段+重置 236,682 恒等 OK/五分结局和==阶段数 OK/期外 pre2011=23,961/
  事件键唯一性违背 0/事件恒等式 OK;MA20 通过率 0.9655 NFV;42,719 参考对账段照冻结
  reporting_commitments 在场);
- **N_valid=39,290**(剔除 3,494,率 0.0817 ⚠告警>5% 如实报,逐年逐因入 result);
  ρ̄=0.0970(行业内 2,659,709 对)Kish≈10.3/KP≈9.3;样本量闸 30→OK;
- **verdict=NOT_SIG:主窗 [0,+4] CAAR=−0.00412(N=38,888)ADJ-BMP=−0.110 双侧不显著**
  (朴素 t=−11.533/Corrado=−4.516/日历=−6.249 均名义显著,NFV 疑聚集假阳性,不得改判);
  次级 [0,+19] CAAR=−0.02054(ADJ-BMP −0.350)/稳健 [0,+59] −0.04511(−0.449)全 NFV;
- 板块/逐年/可交易口径净收益段全 NFV;exp11 真锚标题+「事件后首个有真实bar的价格观察日」
  术语渲染在场(tau_axis 特判生效,「首个可交易日」零命中);
- result 锚定:study_snapshot=235+digest 全录;bias_statement 真锚三元组 pap_sha256==
  冻结 digest;顶层外 verdict 键计数=0(全文档唯一 verdict=顶层)。

## 4. 运行后只读读回(令二后半)——7/7 全 PASS

exp11 仍 frozen(frozen_at 冻结值不变)/result_json·done_at 仍空/DB PAP canonical 不变/
**台账 25=13/3/8/1 零写入**/snap 11 行 max=235(本单元恰增 manifest 一行)/生产 git 净
(HEAD `5636c80`)。读回件=`postrun_readback.txt`。

## 5. 取证(令三)

- 三件原件 SHA256(双侧核对一致):result_exp11.json=`67678ca1dacea84e8f937cf8aba301362bf1f65cfdb725d9e592b41351b26e69`
  /report_exp11.txt=`59ecf89ac459725e1966858fd1d49c114b751358f7856edb526ec087504f6159`
  /run11.log=`c86f86e36cc7dcda856d36ba6a2cab13564ba9c83ba6b11f32de03185cb1df74`;
- **传输前 13 类秘密扫描 TOTAL_HITS=0**(逐类零命中,原件零修改,传输放行);
- 取证包=AWS `~/shuheng/s11_run_delivery_2026-07-24/`(三件原件+preflight/manifest/postrun
  读回+秘扫报告+脚本+令文+SHA256SUMS 全 OK);aliyun 原件 `/root/s11run/`(SHA256SUMS.core)。

## 6. ⚠预判开封对照(persist 阶段事项,未做未写入)

预判(冻结令 2026-07-24 五原文,绑 digest `eaa54b3d…b6fc`)=「主窗市场调整后 CAR 为正,
把握度 60%;仅押方向、不押幅度、不预判统计显著性」vs 实测主窗 CAAR=−0.412%/NOT_SIG:
**开封对照属 persist 阶段,本单元未做未写入,预判原文永不改述。**

## 7. 待人

**▶停取证点:验收取证包与结果→另行决定 persist(校准册第五条随 persist 落笔);
未令不动 result/manifest/台账/冻结载荷。开工首动作=读 ops/STATE.md+查库。**

## 8. persist 闭卷留痕(2026-07-24 九终令;原文永不改述)

persist 执行毕:既有状态机 taosha_app 单事务 `start_running(11)`→`finish(11, 已验收原件)`
一次 **COMMIT,done_at=2026-07-24 21:58:14.608103+08**(脚本/root/s11persist/,前置断言 9/9+
事务内 7/7,后核验 14/14:done/NOT_SIG/parsed_equal=True/canonical 双侧同 `26bfbd42…`/库 md5
`0c212495…3572`/**台账 25=registered13/frozen2/done9/closed1** 恰迁一行/manifest 235 三处
digest 不变/三件产物 SHA 不变/两台 git 净)。事务前置动作已一并闭合:①AWS 仓根 SHA256SUMS
(0 字节、git 未跟踪,系 termfix 取证轮 cwd 误操作产物)确认后删除;②aliyun 无真实研究
runner 进程确认后,仅终止 pgrep 自匹配残留监看壳(PID 389264+sleep 子进程),零误伤。

**闭卷留痕四条(人令原文即口径):**

1. **校准册第五条**:冻结预判原文**「主窗[0,+4]市场调整后CAR为正,把握度60%。」**;该预判
   仅押方向、不押幅度、不预判统计显著性,绑定 PAP digest `eaa54b3d…b6fc`。实测 CAAR
   **−0.4118%,方向未命中;ADJ-BMP 不显著,终态 NOT_SIG**。校准册五条:**2 命中、3 未命中**
   (exp8 命中不显著/exp20 未命中/exp13 未命中/exp12 命中不显著/exp11 未命中)。
2. 剔除率 8.17% 告警如实留;朴素 t(−11.533)/Corrado(−4.516)/日历(−6.249)名义显著
   **不得改读**为有效结论(NFV,疑聚集假阳性,判决唯一=主窗 ADJ-BMP)。
3. MA20 通过率 0.9655(66,745/69,130,正式运行实物)**仅审计**(裁定四:保留不删改);
   τ0 术语(「事件后首个有真实bar的价格观察日」)与一字板句(「τ0一字板事件仅为价格观察,
   不得表述为可执行策略证据。」)按冻结 PAP。
4. 效力=llm/prescreen,不得写成 full 证据;报告强制水印。

**▶exp11 正式闭卷 done/NOT_SIG。停工交终签,不再追加重跑或敏感性分析;
等人终签与下一项排产令(registered 余 13)。开工首动作=读 ops/STATE.md+查库。**
