# 淘沙切片2 · 检验引擎验收文档(总验收包,2026-07-07)

> 验收标准 = 《切片2(检验引擎)验收核对单》十一条(`slice2-acceptance-checklist.md`)。
> **原则(人下发):验收凭实物;每项给可执行证据(代码位置/输出样例/查询结果),不收结论句。**
> 库/仓为唯一真身。对数段对台证据详 `slice2-logbench-evidence-2026-07-07.md`(本包引之,不复述数值);A股口径段本包给现场跑。
> 依据:spec v0.2 + 附录 A/B/C/D/E + 四口径拍板 + S2-DEC2/DEC3。commit 里程碑:留痕单(30fdf23/edafb7d/…/d1919c4/8e5c477)与施工单(29263cb/ea2784f/d50c6ca)分单(F 条)。

## 〇、交付物清单(代码实物)

- **compute 七模块**:`frozen_config`(四口径只读)、`returns`(复刻 rates.cpp 跨缺口对数收益)、`market_model`(SIM-OLS α/β/AR)、`abnormal_tests`(BMP + ADJ-BMP/KP2010)、`rank_test`(Corrado 秩)、`calendar_pf`(日历组合)、`frozen_ashare`(A股制度事实只读)。
- **engine 四件**:`cleaning`(停牌/覆盖/涨跌停/ST 剔除)、`benchmark`(SIM 基准)、`runner`(逐日 AR + 三法 verdict)、`report`(标准输出 + 偏差声明 + 口吻声明)。
- **reader 两件 + 契约**:`reader/contract.py`(explore_reader 列契约机器镜像)、`reader/synthetic.py`(合成 reader,holdout 结构隔离)、`docs/explore-reader-contract.md`(供 Q3 零改造)。
- **落库件**:`experiment/persist.py`(检验结果 append-only 对接台账 Experiment,复用切片1触发器)、`experiment/ledger.py` 新增 `start_running`/`finish` 既有路径 helper。
- **harness(证据)**:对台 `make_fixture.py`/`estudy2_ref.R`/`run_double.py`/`mc_size_test.py`(锚 estudy2,不动);A股 `make_ashare_fixture.py`/`run_ashare_study.py`;纪律 `verify_frozen_immutable.py`(item10)/`persist_synth_study.py`(item11)。

**自检全绿(本地现跑)**:`python -m taosha.compute.{frozen_config,returns,market_model,abnormal_tests,rank_test,calendar_pf,frozen_ashare}` 七模块 OK。

---

## 一、算法正确性(对数段)—— item 1/2/3/4

对台数值证据全在 `slice2-logbench-evidence-2026-07-07.md`(aliyun R 4.5.2 + estudy2 0.10.0,确定性种子)。摘映射:

| item | 要求 | 实物证据 |
|---|---|---|
| **1** | estudy2 0.10.0 版本钉死、源码快照入仓 | `taosha/vendor/estudy2-0.10.0`(PROVENANCE:tarball sha256 199978d3…、GitHub 归档源);aliyun R 4.5.2 安装+加载验证过(附录 D) |
| **2** | BMP 段锚 estudy2 逐点对数一致;ADJ-BMP 段手算+MC 尺寸检验;含聚集场景 | BMP 段双跑 **max\|diff\| BMP=3.73e-14**(rates 2e-16/αβ 4e-15/AR 5e-17);ADJ-BMP 手算 KP 因子差 <1e-12;**MC 尺寸检验 2000 次**:朴素 BMP 拒绝率 0.461 / ADJ-BMP 0.0475≈α(附录 E3)。聚集场景=fixture 6 证券共享事件日 + MC 同行业簇。估计窗无 KP 参照,按 S2-DOC1(附录 E)手算+模拟自活 |
| **3** | 我方收益 = estudy2 multi_day=TRUE 跨缺口,同样本对照 | §1 收益序列 max\|diff\|=**2.22e-16**;S3 停牌3日跨缺口对数收益落恢复日,`delta=157=160−3` |
| **4** | 分歧逐笔归因、先核 estudy2 未决 issue、CAR 分歧附手算 | 首轮 S3 BMP 差 ~3e-4 → 归因 estudy2 boehmer 的 x̄/Sxx 取 market 估计窗全部非缺观测(na.rm)非 complete.cases,`sim_fit` 对齐(commit 181d3c0)→ 降至 3.7e-14。**非我方错、非未决 issue**,属其内部分母口径,已对齐留痕 |

---

## 二、A股口径适配(estudy2 帮不上的部分)—— item 5/6/7/8/9

**现场跑(确定性,两跑逐字节一致 ✅)**:`make_ashare_fixture`(48 证券×1270 日、48 事件、2019-01-02…2023-11-14、跨 regime 2020-08-24;注入停牌/一字板/覆盖不足/估计窗缺口)→ `run_ashare_study`。关键输出:

```
样本与剔除:  事件48 → 有效 N_eff=35  剔除13  剔除率0.2708 ⚠告警(>5%)  样本闸30→OK
估计窗覆盖:  分母160 门槛112(70%)  有效日 min/mean/max=157/158.3/160
剔除率按年份:2020 剔6{susp4,cov1,st1} / 2021 剔3{susp2,st1} / 2022 剔2{st2} / 2023 剔2{st2}
逐日 AR:     τ=0 AAR=0.02510 BMP=13.864 ADJ-BMP=6.577;τ1..5 均不显著
主窗[0,+2]:  CAAR=0.02201 BMP_CAR=7.710 ADJ-BMP_CAR=3.658
稳健[0,+5]:  CAAR=0.02045 BMP_CAR=4.459 ADJ-BMP_CAR=2.116
板块分层:    main18(有效15) chinext16(13) star8(7) ST6(有效0,已剔除层);regime 前6后7
三法:        ADJ-BMP_CAR=3.658[显著] / Corrado秩t=3.267[+] / 日历t=4.768[+] → 三法一致 → verdict SIG
```

| item | 要求 | 实物证据 |
|---|---|---|
| **5** | 禁零填充,停牌置 NA,无 0 填充路径 | `compute/returns.py` 缺口处 rates 恒 `None`、全程 None 禁零填充(自检 Close·Open·single 三路);对台 §1 缺口恒 None;跨缺口对数收益落恢复日 k-1(复刻 rates.cpp) |
| **6** | 覆盖门槛冻结参数=**112/160(70%)** | `frozen_config['coverage']`(只读,item10 实测拒覆写);现跑分母160/门槛112,有效日 min157≥112 合格;对台 S3 delta=157 亦合格。**改读裁决**:"84/120" 作废,详本包附〔四口径拍板〕 |
| **7** | 停牌剔除、剔除率按年份分解、>5% 告警 | 现跑剔除率 0.2708 触 ⚠告警;按年份分解 2020/21/22/23 逐年剔除数+原因(suspension/coverage/st)已出;`engine/cleaning.py` 落剔除逻辑 |
| **8** | 事件窗 [0,+2]主+[0,+5]稳健;逐日 AR;板块分层含 2020-08-24 regime | 主/稳健双窗 CAAR 已出;逐日 AR τ=0..5 标准输出;板块 main/chinext/star/ST 四层计数;创业板 regime 边界前(±10%)6/后(±20%)7。τ=0:=T+1 按 S2-DEC3 |
| **9** | 偏差方向声明固定文本段 | `engine/report.py` 固定段已输出:覆盖不足/停牌/ST/一字板顺延均**保守处置**(倾向缩小可测异常)→"若显著则真实效应不小于报告值(保守下界)" |

**调和留痕(报总验收,已在核对单/STATE 在案)**:①**ST**:spec §5"ST 剔除"↔ item8"ST 分层"→ 读为 ST 从池化检验剔除、分层作"ST 已剔除层"计数留痕(现跑 ST 层有效0、不进检验)。②**τ=0 一字板**:一字板不可成交日极端收益因顺延被移出 τ=0(保守低估首日反应,偏差声明已述)。

---

## 三、纪律接口 —— item 10/11

### item 10 · 口径参数冻结、运行时不可覆写、变更走审计留痕

`harness/verify_frozen_immutable.py` 现跑 **PASS**:`frozen_config` 7 键 + `frozen_ashare` 6 键 + 嵌套(price_limits/event_windows)+ 专项(覆盖门槛/估计窗长/事件窗)**全部覆写被拒=True**。审计摘要(变更须改源、摘要随之变):

```
frozen_config audit_digest = b88a43ef7bd88b8e22303c48dbfa20384d9372c12eb7c7b0884dcf618638110b
frozen_ashare audit_digest = c795b21ebc1a9d21690d307189dd93d8e416ced95e39cb954777f8504dc402c1
```

实现=只读 `MappingProxyType` + 自洽断言(挡"120"复燃);两 digest 在每次引擎跑的报告头打印(现跑报告头 `frozen_config=b88a43ef… frozen_ashare=c795b21e…`),口径漂移即摘要不符、留痕可查。

### item 11 · 结果 append-only 落库、对接台账 Experiment、N_eff+剔除率同报

**DB 实物(aliyun-new `taosha.experiment`,查库为准)**:S2-DEC2 专设合成冒烟行已永久留台账——

```
exp_id=7  family=synthetic_smoke  trial=1  title=[SMOKE] slice2合成落库验收
source_type=llm  verdict_power=prescreen  status=done  result_json=已写(快照批次 SYNTH)
contamination_note=切片2合成fixture,非真实结论,勿用于判决
```

- 走 `registered→frozen→running→done` **既有全路径**(复用切片1终签台账触发器,`persist.py` 不另建通路);`result_json` 内含 `N_eff=35`/剔除率/verdict(门②成色报告数据前提)。
- **六条创始行(exp_id 1-6)result 槽完好未动**——一次性 `result` 槽留给切片3真实数据(触发器焊死不可回滚);现跑负测:二次 `finish` 被"一次性写入"拒、`DELETE` 被拒(append-only)。
- 备选(事务内 ROLLBACK)已否决:不留 append-only 实证,与 item11"落库"字面不符(S2-DEC2)。

---

## 四、开工令六要点核对

| 要点 | 落实 |
|---|---|
| ① 引擎只认台账(拒 status≠frozen、从 pap_json 取事件定义) | `runner`/`persist` 从 frozen 行 pap_json 取定义;非 frozen 拒 |
| ② reader 对合成 fixture、签名按 explore_reader 契约、不建 mock 视图、holdout 隔离归 Q3 | `reader/synthetic.py` 按 `reader/contract.py` 列契约;`docs/explore-reader-contract.md` 供 Q3 零改造;holdout `<2024-07-01` 焊视图 WHERE(reader 结构拿不到) |
| ③ estudy2 按附录 D | 0.10.0 钉死、源码快照入仓 |
| ④ A股口径实现为冻结配置读取、运行时不可覆写 | item10 实测 PASS |
| ⑤ 合成跑通、门槛校正人工可核、真实数据留切片3 | 本包 §二现场跑;真实数据不碰 |
| ⑥ 报告只陈述统计事实、无建议口吻 | `report.py` 口吻声明段(铁律⑤"用其手不引其忆") |

---

## 五、口径裁决留痕(冻结,随本包终审确认)

- **〔四口径拍板〕(人 2026-07-07,冻结配置不可覆写)**:①compounding=continuous 对数收益;②AR 模型=SIM 单指数、regressor 冻结基准(池内=雷达股池等权/全市场=全市场等权,否决等权 market-adjusted);③覆盖门槛=160日内有效日≥112(70%);④ρ̄ 分组=entity_master tushare industry(非 PIT、二阶影响、在案不修)。
- **覆盖门槛改读**:~~"84/120"~~ 作废 → **112/160(70%)**。归因=窗口 II(把 120 当估计窗是未核 spec §5 的臆测,实为前250至前91=160);密封实质 70% 覆盖率不变、密封卡本体不改。**#2b"上市满120日"参数不动**、其"与估计窗对齐"理由作废 → 台账注记改"人拍池定义"。
- **S2-DOC1(附录 E)**:estudy2 0.10.0 参照仅至 BMP(boehmer);spec 行88"(含KP实现)"作废;ADJ-BMP 段手算+MC 尺寸检验自活、不引替代参照。
- **S2-Q(三法范围)**:补 Corrado 秩 + 日历组合,verdict 走 spec §6 三法一致规则(三法方向一致才确认/朴素t显著而ADJ-BMP不显著→以ADJ-BMP为准/日历与截面反向→事件密集期 AMBIGUOUS)。秩/日历无 estudy2 对台、手算+模拟自活。
- **S2-DEC2**(item11 落库=专设合成冒烟行)/ **S2-DEC3**(τ=0:=T+1)见 §三 / 核对单。

---

## 六、结论

切片2 检验引擎:**对数段对台机器精度对齐(BMP 3.7e-14)+ ADJ-BMP 尺寸检验校正确证(0.461→0.0475)**;**A股口径合成端到端跑通、确定性两跑逐字节一致**(N_eff=35、剔除率按年份分解、双窗、板块分层含 regime、偏差声明);**口径冻结运行时不可覆写实测 PASS**;**结果 append-only 落库、台账 exp_id7 SMOKE 行库实物在案、六创始行未动**;三法一致 verdict=SIG(合成注入信号)。十一条核对单逐项有实物。**真实数据不碰,留切片3。**

**待人终签。** 终签后:切片3(真实数据接入,含密封预判钩子)+ v1.5 增补项(L3 减持 PDF 解析件)动工。
