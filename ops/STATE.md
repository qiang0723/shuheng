# 枢衡 quant · STATE(会话无关权威状态)

> 状态持久化纪律(仓根 CLAUDE.md,v1.5)载体。**开工第一动作读此文件;阶段完成/收工必更新。**
> 本文件 + 数据库实物 = 真身;会话记忆是草稿。**断链恢复第一动作 = 查库 + 读本文件。**
> 改判纪律:口径/指针改判须在此**显式作废旧条目(内容+原因)**,不留新旧并存。

最后更新:2026-07-07(v1.5 批复生效 + 我侧三件激活后收工)

## 当前切片

**Q2 行情主线 ✅ 全部收口**。v1.5 A–G 全批生效。三题拍板(2026-07-07):走A先补切片1→验收→切片2;切片2用合成fixture不建mock视图、reader按explore_reader契约写死Q3零改造接入;十一条核对单于切片1验收后随切片2开工令给出、入 taosha/docs/。
**切片1 台账 ✅ 已终签(2026-07-07,1f879d4)。**
**切片2(检验引擎)开工中(2026-07-07):** 核对单十一条已落档 `taosha/docs/slice2-acceptance-checklist.md`。**item 1 ✅**:estudy2 **0.10.0** 装自 GitHub 归档源(tarball sha256 199978d3…)、源码快照入仓 `taosha/vendor/estudy2-0.10.0`(PROVENANCE 留档)、aliyun R 4.5.2 安装+加载验证过。**四口径已人拍(2026-07-07,冻结配置不可覆写,详见〈已裁决口径〉+ slice2 核对单文末〔四口径拍板〕),建 compute 台架进行中。**〔台架进度〕**冻结配置模块 ✅ 已建**:`taosha/compute/frozen_config.py`(四口径落只读 MappingProxyType、自洽断言挡"120"复燃、audit_digest=`b88a43ef7bd88b8e…`、`python -m taosha.compute.frozen_config` 自检全绿含只读校验);regressor 基准复用 `pap.FROZEN_BENCHMARK` 单一真源。**对数收益原语 ✅ 已建**:`taosha/compute/returns.py` 逐行忠实复刻 estudy2 `src/rates.cpp`(getMultiDayRates/getSingleDayRates,行号在案);要害=Close 口径跨缺口对数收益落**恢复日前一行 k-1**(cpp:35)、缺口起始行置 NA、全程 None 禁零填充(item 3/5);`python -m taosha.compute.returns` 自检全绿(Close·Open·single 三路)。**compute 层(item2/3/5)✅ 四块砖全成**:`frozen_config.py`(四口径只读)、`returns.py`(跨缺口对数收益复刻 rates.cpp)、`market_model.py`(SIM-OLS α/β/AR,est_ar_sd 对齐 BMP 尺度,x̄/Sxx 对齐 estudy2 market_estimation)、`abnormal_tests.py`(BMP=estudy2 boehmer 逐点对齐 + ADJ-BMP KP2010 我方扩展,ρ̄ 按行业内估计=口径④ tushare industry)。四模块 `python -m` 自检全绿。
**task4 对数台架 ✅ 全过、证据留档**(`taosha/docs/slice2-logbench-evidence-2026-07-07.md`;harness=`taosha/harness/` fixture/estudy2_ref.R/run_double/mc_size_test):**BMP 段双跑对台机器精度对齐**(rates 2e-16/αβ 4e-15/AR 5e-17/**BMP 3.7e-14**,含 S3 停牌缺口;归因并消解一处 estudy2 x̄/Sxx 口径细节);**ADJ-BMP 段**手算 KP 因子一致 + **零假设 MC 尺寸检验(2000次)**:朴素 BMP 拒绝率 0.461(假阳性复现)、ADJ-BMP 0.0475≈α。运行在 aliyun,输出在 /tmp/s2bench(非 git)。
**剩余 item 7-11 建设中**(停牌剔除按年份/涨跌停窗+板块分层/偏差声明/口径审计/结果落库对接 Experiment)。:对数(ADJ-BMP/KP2010+三法,含聚集场景,multi_day跨缺口收益对齐)、A股口径(禁零填充NA/**估计窗门槛112·160(70%)**/停牌剔除按年份+>5%告警/涨跌停[0,+2]主+[0,+5]稳健·逐日AR·板块分层含2020-08-24创业板regime/偏差方向声明)、纪律接口(参数冻结配置只读+审计、结果append-only落库对接Experiment、N_eff+剔除率同报)。引擎只认台账frozen、reader对合成fixture跑按explore_reader契约、真实数据留切片3、报告无建议口吻。
**item 7-11 开工令(人下发 2026-07-07,三段串行:引擎骨架→A股口径件→纪律收尾;交付=切片2总验收包一次交验)。开工前两裁 + 三条自决设计已落痕(下〈已裁决口径〉S2-DEC2/S2-DEC3 + 〔item7-11 施工设计〕),裁决留痕单 `d1919c4` 先于施工代码(F 条)。**
**〔段1+段2 施工 ✅ 跑通(2026-07-07,施工代码,与留痕分单)〕** 引擎骨架闭环 + A股口径件(item 6/7/8/9)全建、对合成 fixture end-to-end 跑通:
  - 新件:`reader/contract.py`+`reader/synthetic.py`(explore_reader 列契约机器镜像 + 合成 reader,holdout 结构隔离)、`docs/explore-reader-contract.md`(供 Q3 零改造)、`compute/frozen_ashare.py`(A股制度事实冻结·只读·audit=`c795b21e…`:涨跌停各板限幅/2020-08-24 regime/事件窗几何/停牌告警阈)、`engine/{cleaning,benchmark,runner,report}.py`、`harness/make_ashare_fixture.py`(48证券×1270日/48事件/跨2020-23/跨2020-08-24/注停牌·一字板·ST)、`harness/run_ashare_study.py`(驱动)。
  - **合成跑通实况**:48 事件→有效 N_eff=35(≥30 过样本闸)、剔除13(按年份分解:2020剔6/2021剔3/2022剔2/2023剔2;原因 suspension6+coverage1+st6)、剔除率0.271 触>5%告警;覆盖有效日 min157/mean158/max160(<160 但≥112,item6 计数真);逐日 AR τ=0 注入信号 BMP=13.9/ADJ-BMP=6.58、τ1-5≈0;主窗[0,+2] CAAR=0.022 ADJ-BMP_CAR=3.66→verdict SIG;板块分层 main18/chinext16/star8/ST6,创业板 regime 前6后7;ρ̄=0.090(行业内80对)。偏差方向声明段 + 无建议口吻 footer + 口径审计摘要在报告内。
  - **调和留痕(报总验收,待终审确认)**:①**ST**:spec §5"ST 剔除"↔ item8"ST 分层"→ 读为 ST 从池化检验剔除、板块分层作"ST 已剔除层"计数留痕(engine 已落此读法)。②**τ=0 一字板**:注入于 T+1 的极端收益因顺延被移出 τ=0(保守低估,偏差声明已述)。
  - **剩**:item10(口径审计验收贴不可覆写实测)、item11(落库=专设合成冒烟登记行 S2-DEC2,补 ledger start_running/finish)、总验收包。commit=施工单(见 git log,与 d1919c4 分单)。
--- 切片1 存档 ---
**切片1 台账(已终签):** DB `taosha`(属主postgres,role `taosha_app` 非属主→禁不掉触发器)。表 `experiment`(§4+data_class/crowding_prior)。焊死触发器全自测过+重建后复检仍拒。**三裁已落地**(裁1 #3=literature+platform记note;裁2 closed编码+状态机注记;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填)。**登记终态五条齐(exp_id1-6):** radar_heat/holder_sell#3/forecast_drift/rv_resonance frozen + drawdown_rebuy #2closed+#2b frozen(family_trial自增1→2);#2b元数据量价/高。**pap_json↔§6 逐字核对 diff归零(12/12字段MATCH,verify_pap_vs_spec.py)**。入备份链。验收文档 `taosha/docs/slice1-ledger-acceptance-2026-07-07.md`。commit `d381af6→(本次)`。**待人终签→切片2(开工令+十一条核对单)。**

## 已裁决口径与指针

- **Q2 范围** = `forecast` + `stk_holdertrade` 两张(tushare 源);~~"行情四件套"~~ **作废**(文档打架已裁 2026-07-07)。
- **库指针(aliyun-new qbase,实物为准)**:`forecast_snap`=138458(batch#1)/ `holdertrade_snap`=179843(batch#2)/ `entity_master`=5861(含退市 D=334)/ `entity_alias`=20005(忠实存全)。锚 entity_master batch=6。
- **#4 事件日锚** = `first_ann_date`,**无 fallback 分支**(~~回退 ann_date~~ 已撤销/严禁,2026-07-07 驳回)。
- **#4 type→三层映射(冻结)** = `taosha/docs/taosha-spec-appendix-C.md`:预喜{预增,略增,续盈}/预亏{预减,略减,首亏,续亏}/扭亏独立/层外{不确定,其他}。污染标注:LLM拟定·人批冻结·未触样本收益数据。
- **C3 关闭**:91 行 null-first_ann = 56 行'其他'(层外非#4)+ 35 行实层**排除**(缺锚不可定位,按年份分解入附录C)。
- **#3 = 档位二**:减持须 PIT 读取(含≥总股本1%门槛),不得 holdertrade 事后反筛。→ **L3 减持 PDF 解析增补件**(范围钉死:仅减持预披露类、仅抽 股东名/拟减持比例上限/减持期间 3 字段、失败行标注、不做通用框架);**v1.5 已入清单,切片 2 验收后动工**。
- **巨潮采集件** = `github.com/quant-newman/radar` 的 `src/radar/cninfo.py`(sha256 `7875485ceeb23f496bac6bf4550d0a7776e3af3603445df8b11dfd53670a4fde`),已借入 `qbase/ingest/cninfo.py`(逐字 copy)。本刀只抓公告列表元数据、不解析 PDF 正文。
- **切片 2 对数参照** = estudy2 **0.10.0 版本钉死**(附录D):GitHub 归档源装、源码快照入仓;未决 issue #12/#16;分歧逐笔归因先核参照未决 issue、CAR 聚合分歧附手算。
- **切片 2 四统计口径(人拍 2026-07-07,冻结配置·运行时不可覆写)**:①compounding=**continuous(对数收益)**,我方与 estudy2 两侧同设;②AR 模型=**SIM(单指数市场模型)**,regressor 按冻结基准:池内假设=雷达股池等权、全市场假设=全市场等权(否决等权 market-adjusted);③覆盖门槛=冻结估计窗 **160 日(前250至前91,spec §5 行66)内有效交易日 ≥112(=70%)**,不足即剔、剔除率进报告;④ρ̄ 行业分组=`entity_master` 的 **tushare industry**(附近似注记:当前快照非 PIT,对 ρ̄ 影响二阶,在案不修)。
- **~~估计窗门槛"84/120"~~ 作废(改读裁决 2026-07-07)**:改读 **112/160(=70%)**。作废原因:"84/120" 本是"70%×120 日窗"展开式,**120 为架构窗口臆测、未核 spec §5**(实为前250至前91=160 交易日);错误归因=**窗口 II(在案)**。密封实质=70% 覆盖率维持不变、密封卡本体不改,112/160 为其在正确分母 160 上的实例化。驳回我方"84=最小估计期/120=稳健窗门槛"倒推语义。核对单 item 6 已改读。
- **#2b(drawdown_rebuy b1)"上市满 120 日"参数不动**,但其"与估计窗对齐"理由**作废**(估计窗实为 160 非 120);台账注记改读"**人拍池定义**"(非估计窗派生)。
- **holdout 线** = 2024-07-01(焊在视图 WHERE)。
- **S2-DEC2(item 11 落库演示,人拍 2026-07-07)** = **专设合成冒烟登记行**:新登记一条 `[SMOKE] slice2合成落库验收`(source_type=`llm`、verdict_power=`prescreen`、contamination_note 明写"切片2合成fixture,非真实结论,勿用于判决"),走 registered→frozen→running→done **既有全路径**写 result_json(快照批次=`SYNTH`),永久留台账作 append-only 实证。**不写六条创始行**(保护其一次性 result 槽留给切片3真实数据,触发器焊死不可回滚)。**不另建影子表/通路**(复用切片1 已终签台账触发器)。
- **S2-DEC3(事件窗 τ 轴,人拍 2026-07-07,消解核对单 item 8 ↔ spec §5 潜在打架)** = **τ=0 := 首个可交易日 = T+1**(事件日 T 盘后披露→规避→观测自 T+1 起,spec §5)。主窗 **[0,+2]=T+1..T+3**、稳健窗 **[0,+5]=T+1..T+6**;逐日 AR 从 τ=0 记;**CAR 起点 = τ=0 = T+1**(=spec §5)。两文档对齐、无冲突,读法钉死。
- **〔item7-11 施工设计(我自决,报留否决权,2026-07-07)〕**:①**reader 列契约**——spec 未给 explore_reader 列级定义(Q3 真视图),我方现定《explore_reader 列契约(淘沙侧要求)》供 Q3 零改造照建,列含 `(ts_code,trade_date,close,is_suspended,limit_flag/一字板,industry,board,is_st,first_ann_date,mkt_return)`;②**fixture 分家**——86e905f 的 `harness/make_fixture.py` 是对台证据(锚 estudy2)**不动**;A股口径(item7/8)另建合成 fixture,需 **≥30 事件**(现 6 证券×1 事件=6 恒 INSUFFICIENT)、**跨年**(剔除率按年份分解)、**跨越 2020-08-24**(创业板 regime 边界)、注入停牌/涨跌停/板块/ST;③**新增 A股参数**(各板涨跌停限幅、regime 日期、事件窗 [0,+2]/[0,+5]、样本闸 30)全进 `frozen_config` 只读(item 10)。
- **机器**:`aliyun-new`(部署 `/opt/quant` + qbase 库,我有 root)/ `aliyun-old`(老平台**只读**,ProxyJump,坩埚判断数据任何情况不读)/ 老 aws `43.213.181.243`(巨潮源**备份**,`john-test.pem`,只借采集件·数据不碰)。部署 = `git push origin main && ssh aliyun-new 'cd /opt/quant && git pull --ff-only'`。

## 运行中后台任务

- **无运行中任务**。`seed_facts.py` Q2 回填已完成并 COMMIT;守望 `b097j3l62` 已触发结束。
- **root cron(aliyun-new)**:哨兵 08:30 / 备份 03:00 / 到期提醒 09:00。查验 = `ssh aliyun-new 'crontab -l'` + 各日志;飞书秘钥 `/etc/shuheng/sentinel.env`。

## 待答点(挂账,见 qbase/quality/caveats-and-ledger.md)

- **L1**:巨潮 secCode/orgId 填充验收(行数 + secCode↔orgId 对射抽查)——巨潮件采集时。
- **L2**:alias 映射约束基数——反向唯一取 batch scoped 是有意容跨批复用还是应收紧全局?待 Q2 真数据核实基数后定死(现不焊)。
- **L4**:`cninfo.py` `category=""` 是否稳定返回减持预披露公告——实采抽验。
- **~~S2-DOC1(待人裁)~~ 已裁(2026-07-07,附录 E 落地)**:裁定①认工作解——**estudy2 0.10.0 参照仅覆盖至 BMP(boehmer);spec 行88"(含KP实现)"作废**(归因:引包描述页未核源码,KP 在描述不在源码);核对单 item 2 改读"BMP 段锚 estudy2、ADJ-BMP 段手算+模拟复核";**不引替代 KP 参照**。**加验一道**:ADJ-BMP 零假设蒙特卡洛尺寸检验(无效应+截面相关聚集样本 → 朴素 BMP 拒绝率>α 复现假阳性、ADJ-BMP 拒绝率≈α),一次性模拟、与 item 2 聚集场景合并同一 fixture。落 `taosha/docs/taosha-spec-appendix-E.md`(同附录 D 效力)。
- **S2-Q(三法范围,待人裁,2026-07-07 提出)**:spec §6/§7 列切片2 检验为**三法**(主检验 ADJ-BMP + 稳健性两道:Corrado(1989) 秩检验 + 日历时间组合法),verdict 规则"三法方向一致才确认、不一致→AMBIGUOUS"须三法齐备;STATE 亦列"剩余...三法"。但**人的 item7-11 分段(骨架/item7-8/item9-11)未点名 秩/日历**,logbench(item1-6)只锚 BMP/ADJ-BMP。当前 engine verdict 仅 ADJ-BMP、标 `robustness_pending`。**待裁**:①现补建 Corrado 秩 + 日历组合两模块、verdict 走三法一致(spec §7 完整);还是 ②切片2 交 BMP/ADJ-BMP 版、秩/日历挪后续单。默认倾向①(spec 为权威),但涉额外两模块+verdict 逻辑,提请人拍。
- **C1**:tushare 对 2007 前退市不完备(T00018.SH),默认不捞、挂老机退役迁移单(≈2027 H1)。
- **切片1 三裁已落地(2026-07-07,✅ 待终签)**:裁1 #3 source_type=literature+platform记note(已补登);裁2 closed编码批准+状态机注记入验收文档;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填(ledger焊)。仅剩人终签。
