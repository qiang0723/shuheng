# exp8 limit_open · §7 单次正式运行交付取证档(冻结令 2026-07-17 深夜五;运行实际时刻 2026-07-18 00:38–00:42 CST)

> 令原文档:`taosha/docs/limit-open-freeze-order-2026-07-17.md`(commit `9a52f08`,原文即口径)。
> **本档=令四要求的运行后交付件:原始 result / report / run log / SHA256 清单 / manifest 读回 / 只读台账基线。**
> **persist 未执行、未授权**:exp8 保持 frozen、result_json 与 done_at 为空、addendum 零行;结果验收后另令。

## §0 授权链执行实录(commit 链)

| 节点 | 实物 | commit |
|---|---|---|
| 令留痕 | limit-open-freeze-order-2026-07-17.md + STATE 头 | `9a52f08` |
| 前置六项+冻结+读回验收 | limit-open-freeze-acceptance-2026-07-17.md(全 PASS;frozen_at=2026-07-18 00:26:26+08,DB canonical SHA==`afd8443a…addb`,载荷 md5 `ec74f93f…`) | `5651dd1` |
| driver 最小施工+专项验收 | run_limit_open_study.py + verify_limit_open_adapter.py **24/24 两台**;全家福两台绿;合成 e2e 两台四跑 `3116ba9b` 逐字节==基线 | `a62929d` |
| pap_gate 探针标本修复 | F1 原硬编码 exp8 为 registered 标本,exp8 真冻结后失效(22/23);动态化后 **23/23** 复绿(探针语义不变,生产零触碰) | `99a42bf` |
| manifest 生成发布 | snapshot_id=**121**(见 §2) | 库实物 |
| §7 单跑+取证 | /root/s8run/ 三件+SHA256SUMS(见 §3) | 本档 commit |

## §1 driver 门通过实录(run8.log 头,逐字)

```
exp_id=8 limit_open/连续一字涨停开板 status=frozen family_trial=1 verdict_power=prescreen
pap canonical digest=afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb(断言通过)
engine_params(逐字消费冻结件)= {'benchmark_mode': 'market', 'strata_enabled': False,
 'st_mode': 'event_day', 'st_policy': 'keep', 'verdict_policy': 'adj_bmp_main_only',
 'nfv_structured': True, 'postpone_policy': 'unified', 'diagnostic_dims': ('listing_age', 'st')}
```
= 铁律③ frozen 门 + digest 断言(driver 先行断言;runner 内重算权威断言同过)+ engine_params 逐字消费(键集 fail-closed)三道全过。

## §2 研究 manifest(生成发布+读回)

- 生成:`--create --from-source-snapshot 74`(承 exp4/manifest87 再种收口范式;qbase 半=已发布源级快照 74 向量,taosha 半=派生批现值 {market_return:88, pool_b1:18, pool_b1_return:18})。
- **snapshot_id=121,digest=`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`**(content 与 manifest 87 全等——qbase 源自 07-16 后零刷新、派生批未动,digest 同值系必然;content md5 `aa940b61aedbe738d1f60402dbdc5dd9` 两库同)。
- 发布三件:taosha `study_snapshot` 行(created_by=taosha_app @2026-07-18 00:36:14+08)= qbase `study_snapshot_mirror` digest = qbase `study_snapshot_publication` attested_digest,三处同 digest。
- 运行后读回复核:三处 digest 仍全等;`result.audit.study_snapshot` = {snapshot_id:121, digest:`21e9095e…efcd`}(硬化② result 记 manifest ID+digest,已核)。
- DB 套件:镜像 11/11、血缘 24/24、状态机 46/46、pap 硬门 23/23、addendum 14/14、集成探针 7/7 全绿(manifest 121 生成后实测)。

## §3 §7 单次正式运行(RC=0)

- 命令(aliyun,taosha_app/engine DSN 经 .env;单次,未重跑):
  `python -m taosha.harness.run_limit_open_study --exp-id 8 --snapshot-id 121 --pap-sha256-assert afd8443a…addb --json /root/s8run/result_exp8.json --report /root/s8run/report_exp8.txt`(nohup 全程日志 run8.log;00:38 起跑,00:42 落盘,RC=0)。
- **产物 SHA256(/root/s8run/SHA256SUMS 实物)**:
  - `result_exp8.json` = `282bda4fdc404eed7cf409b2566a77ae94aa6d57954c0ed0b03c7f81d1018a10`
  - `report_exp8.txt` = `278456d5bad1e88055114b2dd3e83c36e3fca19d035383640185f781687c3e99`
  - `run8.log` = `d2940c311aecc045b5fc46219604b1362feb1e2bbeb8c52b6cf7fb31098e1c76`

### 3.1 事件生成漏斗(audit.limit_open_selection)

- 宇宙=listing 全 A 键集 **5,861 票 / 15,099,011 行**;一字涨停行(双判据)36,688;**链≥2 = 6,484**;顺延跳过一字行 90;制度前链 0;listing 异常票 0。
- 剔除唯一因=**event_date_out_of_study_range 479**(研究期 2007-01-01≤ed<2024-07-01 外);**重复映射 0**(逐条槽在档为空);→ **事件 6,005**。
- 层分布:recent_listing **1,521** / seasoned **4,484**;链长分布头部 len2=2,726 / len3=1,065 / len4=522 / len5=323 / len6=251 / len7=183(全分布+逐年分布在 result_json)。

### 3.2 主结果(唯一判决=主窗 ADJ-BMP,verdict_policy=adj_bmp_main_only)

- **verdict = `NOT_SIG`**。事件 6,005 → N_valid **3,742**(剔除 2,263=37.69%,⚠告警如实报;逐年逐因分解在档,coverage 为主因)。
- 主窗 [0,+4]:CAAR **−0.01482**,**ADJ-BMP_CAR=−0.473[不显著]**(临界±1.960);朴素t=−8.143 / Corrado秩t=−7.111[dir−1] / 日历t=−5.609[dir−1]——辅助三法同向负且名义显著,依冻结口径仅报告不改判;朴素 t 显著而 ADJ-BMP 不显著 → 疑聚集假阳性注记在档。
- 次级窗 [0,+19](NOT_FOR_VERDICT):CAAR −0.03824,ADJ-BMP −0.827。
- 稳健窗 [0,+59](NOT_FOR_VERDICT):CAAR −0.04993,ADJ-BMP −0.726。
- ρ̄=0.0691(行业内)→ N_eff:Kish≈14.4 / KP≈13.4;2015 事件集中(1,415/6,005)如实报,聚集警示在档(裁决三.6,不调参)。
- 偏差声明真锚三元组(P1-4):result.bias_statement={pap_sha256=`afd8443a…addb`, key=bias_statement, text=PAP 原文};报告来源锚行直接显示实际 digest。

### 3.3 诊断轴(NOT_FOR_VERDICT,零判决字段)

- listing_age 轴:recent_listing 事件 1,521 存活 **0** → 状态=**UNESTIMABLE_AFTER_FROZEN_CLEANING**(剔因 coverage 1,519 + postpone 2,逐年分解在档;C3 真实原因命名,未预判、未静默缺席);seasoned 4,484 存活 3,742(主窗 CAAR −0.01482 / ADJ-BMP −0.473)。
- st 轴:ST 1,184 存活 938(主窗 CAAR +0.01013 / ADJ-BMP +0.192);non_ST 4,821 存活 2,804(主窗 CAAR −0.02304 / ADJ-BMP −0.720)。方向分歧如实报,不判决。
- 二维仅计数核对(禁交叉统计):recent×non_ST 1,521(存活0)/ seasoned×ST 1,184 / seasoned×non_ST 3,300。
- NFV 结构化已标记块:per_tau/n_eff_rho/robustness/type_strata/tradeable/board_strata/censor_diagnostic/industry_coverage/diagnostic_dimensions/car.robust_window/car.secondary_windows;全文档唯一 verdict 键=顶层。

## §4 只读台账基线(运行后实测;令四边界证明)

- exp8:status=**frozen**(frozen_at=2026-07-18 00:26:26.780743+08 未变)/ **result_json IS NULL** / **done_at IS NULL** / pap_json md5=`ec74f93f678598016dcf5dbd4721b94f`(冻结读回同值,零触碰);addendum exp_id=8 = 0 行。
- 台账 25 行 = registered 17 / frozen 3 / done 4 / closed 1(与冻结验收后基线全等;§7 零写入)。
- 两台 git 净(HEAD 同一,aliyun 只 pull)。

## §5 工时(同期记)

- 本单元(冻结令全链:留痕/前置/冻结/driver/manifest/§7/取证):研究≈0.4h,维护≈0.6h。

## §6 待人

- **结果验收**:六件=①冻结验收档(§0 链)②driver+验收件 ③manifest 121 读回 ④result_exp8.json ⑤report_exp8.txt ⑥run8.log+SHA256SUMS。
- 验收通过后另下 **persist 令**(状态机 frozen→running→done 单事务,result 载荷=已验收原文件);未令不动。
