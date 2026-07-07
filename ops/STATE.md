# 枢衡 quant · STATE(会话无关权威状态)

> 状态持久化纪律(仓根 CLAUDE.md,v1.5)载体。**开工第一动作读此文件;阶段完成/收工必更新。**
> 本文件 + 数据库实物 = 真身;会话记忆是草稿。**断链恢复第一动作 = 查库 + 读本文件。**
> 改判纪律:口径/指针改判须在此**显式作废旧条目(内容+原因)**,不留新旧并存。

最后更新:2026-07-07(切片2 全部完工:总验收包已落 slice2-acceptance-2026-07-07.md,十一条实物齐、两台同步;**只差人终签**)

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
  - **三法 ✅ 补齐(S2-Q 裁决,施工单)**:`compute/rank_test.py`(Corrado 1989 秩检验,平均秩+尺寸检验自检)、`compute/calendar_pf.py`(日历时间组合法,聚集并单观测)已建、python -m 自检全绿;runner verdict 改 **spec §6 三法一致规则**(三法方向一致才确认/朴素t显著而ADJ-BMP不显著→聚集假阳性以ADJ-BMP为准/日历与截面反向→事件密集期AMBIGUOUS/方向不一致→AMBIGUOUS);`robustness_pending` 已撤。合成跑:主窗 ADJ-BMP_CAR=3.66[显著]/Corrado秩t=3.27[+]/日历t=4.77[+]→三法一致→SIG。七 compute 模块自检全绿、引擎确定性两跑一致。
  - **〔段3 纪律收尾 ✅ 跑通(2026-07-07,HEAD `d50c6ca`,已 push + aliyun ff 同步)〕** item10(口径审计验收贴+冻结不可覆写实测)、item11(结果落库 S2-DEC2)全建、commit。**DB 实物确认(查库为准)**:`taosha.experiment` exp_id **7** = `synthetic_smoke/1` `[SMOKE] slice2合成落库验收`(source_type=llm、verdict_power=prescreen、status=**done**、result_json 已写、contamination_note="切片2合成fixture,非真实结论,勿用于判决",快照批次 SYNTH);六条创始行(exp_id1-6)result 槽完好未动(仅 #2 closed 有 result)。走 registered→frozen→running→done 全路径,append-only 触发器未拒。
  - **总验收包 ✅ 已落(2026-07-07,`taosha/docs/slice2-acceptance-2026-07-07.md`,commit 已 push+两台同步)**:十一条逐项映射实物;对数段引 logbench-evidence(BMP 3.7e-14/MC 0.461→0.0475),A股段现场跑(确定性两跑逐字节一致:N_eff=35/剔除率按年份/双窗/板块分层含regime/偏差声明),item10 冻结不可覆写实测 PASS,item11 落库 exp_id7 SMOKE 库实物,四口径/改读/S2-DOC1/S2-Q/DEC2/DEC3 裁决留痕随包终审确认。
  - **切片2 = 全部完工,只差人终签。** 终签后→切片3(真实数据+密封预判钩子)+ v1.5 增补 L3 减持 PDF 件动工。
--- 切片1 存档 ---
**切片1 台账(已终签):** DB `taosha`(属主postgres,role `taosha_app` 非属主→禁不掉触发器)。表 `experiment`(§4+data_class/crowding_prior)。焊死触发器全自测过+重建后复检仍拒。**三裁已落地**(裁1 #3=literature+platform记note;裁2 closed编码+状态机注记;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填)。**登记终态五条齐(exp_id1-6):** radar_heat/holder_sell#3/forecast_drift/rv_resonance frozen + drawdown_rebuy #2closed+#2b frozen(family_trial自增1→2);#2b元数据量价/高。**pap_json↔§6 逐字核对 diff归零(12/12字段MATCH,verify_pap_vs_spec.py)**。入备份链。验收文档 `taosha/docs/slice1-ledger-acceptance-2026-07-07.md`。commit `d381af6→(本次)`。**待人终签→切片2(开工令+十一条核对单)。**

## 下一单:Q3(explore_reader 视图,切片3 硬前置)+ L3 并行(2026-07-07 开单)

**切片2 已终签(b7e3b4b)。** 下一单 = Q3 与 L3 并行;切片3 开工令待 Q3 验收后发。SMOKE family=synthetic_smoke(exp_id7)已确认为专用冒烟行(见密封状态下方)。

**Q3 要件(人下发 2026-07-07):** ①视图 DDL 焊死 holdout `WHERE trade_date < '2024-07-01'`(非应用层);②权限物理隔离=引擎 role 仅 SELECT 该视图、对底表(forecast_snap/holdertrade_snap/**marketdata 源**)零权限(仿台账焊死);③视图 schema 与切片2 `reader/contract.py` 逐字段核对零改造;④验收三件套=视图 DDL + 引擎 role 越权查底表被拒实测 + holdout 泄漏测试(经视图查 ≥2024-07-01 返空)。

**⚠ Q3 卡点(查库 2026-07-07,待人拍):** qbase **无任何行情底表**(仅 entity_master/alias/batch + forecast_snap/holdertrade_snap/fact_batch + audit)。契约 `PRICE_COLUMNS`=(ts_code,trade_date,close,is_suspended,limit_status,board,is_st,industry) 的价格半边(close/is_suspended/limit_status)**无底料**;event 半边(first_ann_date 等)qbase facts 可建。设计意图(ROADMAP〈Q3换源约束〉+施工清单v0.3)= explore_reader 经 **FDW/dblink 只读老库 `md` schema**(bar_daily_raw 1782万/adj_factor/trade_calendar,收益口径=后复权收盘 D3)。**两条红线待拍**:(a) 我方记忆〈ops-access〉记老机"数据不借阅"↔施工清单v0.3 provisions"老库只读账号 marketdata SELECT only" = **类④文档打架**,需人确认 marketdata(行情=梯队4公共事实)可借阅、区别于 radar/research_view/crucible 判断数据不借阅;(b) 建 FDW/开老机PG内网监听/建隧道 = **类③对老平台操作**必须先请示;且老机 PG 只绑 localhost(内网 5432 未开),FDW 需先解决连通。价格源三选项(A FDW只读老库/B 回填 marketdata 进 qbase 违换源约束但去跨机依赖/C 混合物化窗口缓存)已报人。**另注**:industry 口径 D5(申万一级)↔切片2 口径④(entity_master tushare industry,ρ̄ 冻结)潜在张力,待 Q3 拍价格源后一并核。

**L3(减持预披露 PDF 解析件)✅ 完工 + L4 ✅ 关闭(2026-07-07):** 件=`qbase/ingest/parse_holder_reduction.py`(已 push),依赖 pypdf(装入 qbase-ingest venv),证据档 `qbase/quality/l3-holder-reduction-parser-2026-07-07.md`。**L4 结论=巨潮 type/category 码不稳(同类公告 code 不一致,实证)→靠 title 判别减持预披露、不依赖 category/type。** L3 承 cninfo(只抓列表)下游:title 筛→pypdf 抽正文→抽 股东名/拟减持比例上限/减持期间(相对式期间存原文+kind)。**实采验证 27 份/全中 22/81%**(字段级 比例~96%/期间~93%/股东~81%);残余 5 全 holder-only 干净失败(特定股东/多主体异构),**精度优先·零错值**(噪声词过滤+角色剥离,曾出垃圾已消解为干净失败,守骗不了人)。本刀**不入库**(落库对接 #3 另定 schema)。**L3/L4 已交付,与 Q3 并行的这条腿收口。**

## ⚠ Q3 进行中 + 阻塞点(2026-07-07,待人裁)

**008 三视图 ✅ 建成验证 + 009 引擎角色 ✅ 焊死(commit 已 push):** `explore_reader_prices`(后复权close/board/is_st PIT[entity_alias名含ST闭区间]/limit_status[原始价分位取整,真抓涨跌停]/industry,holdout `<2024-07-01`焊WHERE,is_suspended=false真实bar) + `explore_reader_calendar`(trade_cal权威轴8187交易日) + `explore_reader_events`(forecast PIT原始披露去重105651唯一,type→附录C三层)。role `taosha_engine` 仅SELECT三视图、直查5底表全 permission denied、holdout三视图>=2024-07-01全返0——**越权/holdout 两件套 ✅ 过**。
**⚠ is_st PIT 正确性缺陷(2026-07-07 实测发现,待人裁口径后修):** 写 limit_status/is_st 规则文档前在重灌真数据实测 000004.SZ(多次ST↔摘帽)暴露 bug——视图 is_st 用 `EXISTS(任一含ST区间覆盖当日)` + `end_date IS NULL 当至今有效`;而 entity_alias 忠实存全了 namechange 源脏孪生行(同一改名事件常并存 end填 + end=NULL 两行),NULL-end 的含ST行把已结束的ST区间**永久拉成 true**,摘帽后仍恒ST。**范围量化(查 entity_alias 2万行):1102 只有 NULL-end 含ST行,其中 446 只后来真摘帽→摘帽后被误判恒 is_st=true**,会污染切片3 ST剔除/分层。**修法(明确)**=is_st 改为「当日 PIT 生效名=start_date<=trade_date 中最大 start_date 段的名是否含ST」,用下一段 start 划界、免疫 NULL end_date(已验:该逻辑对 000004.SZ 2024-01-02 正确给'国华网安'/非ST)。**另 2 组同日ST冲突需拍口径**:000995.SZ(2020-12-16 ST皇台|皇台酒业)、002417.SZ(2023-06-15 *ST深南|深南退,退市整理期"XX退"不含ST字但性质仍风险警示)。**STATE 旧"is_st PIT 已验"结论作废**(008验证时抽验未覆盖摘帽段,验证不充分)。Q3验收包不带病交付,待口径裁定后重写 is_st 段+全表重验+两文档。
**契约核对发现(报切片3):** runner 日期轴=全宇宙bar并集(真实A股≈完整交易日轴),核心统计在"只吐真实bar"下成立;但 cleaning.py 92/104行直读 is_suspended/limit_status flag,真实数据停牌=缺行→**切片3引擎须改按缺行+trade_cal判停牌**(非flag)。Q3只交视图(含calendar轴),引擎适配属切片3。
**阻塞根因(增补①完整性核对发现):tushare `daily`/`adj_factor` 单票硬顶 6000 行截断。** 000001.SZ 仅6000行起2001-02-16(非1991)、长史票卡6000早年缺=采集缺行(非停牌),"断档=停牌"不成立。**人裁 A(分页全票重灌,理由:B转永久技术债否/C行数识别不可靠且路由常设复杂度否)。三条执行:①旧batch3/4标废不删(废弃原因写新batch note+文档,因fact_batch append-only改不了旧note)、视图取max batch路由新批;②重灌后完整性核对全量重跑、逐票闭合、复验分页拼接不重不漏(dedup重验);③adj_factor一并重灌同验。**
**✅ 重灌完成 + 完整性核对全部闭合(2026-07-07,证据档 `qbase/quality/q3-rebackfill-integrity-2026-07-07.md`):** 新批 **daily batch6=17,943,344**(旧b3 17,138,664,+804,680)/ **adj_factor batch7=18,762,389**(旧b4 17,680,484,+1,081,905),trade_cal未截断不重灌。核对四关全过:①**不重**=两批行数==distinct(ts,date)零重复;②**逐票闭合**=旧批恰好6000被截票 daily 883只/adj 1010只,新批 883/883、1010/1010 全部>6000(daily min6002/max8545,adj min6009/max8676),新批==6000=0、<6000可疑=0;③**早年补回**=底表最早1990-12-19、视图000001.SZ回到1991-04-04(旧起2001);④**视图路由新批**=explore_reader_prices按max(batch_id) source路由 daily→6/adj→7,新批note写supersedes旧批,票集daily⊆adj差集0,覆盖5860=5861-T600018.SH。**⚠改判(显式作废):~~"923只长史票"~~作废→精确核定 daily截断883只/adj截断1010只(并集1011)。作废原因:923为分页dry-run估计口径,非库精确GROUP BY计数。**
**契约核对发现 → 切片3 待办(已登记):** cleaning.py 92/104行直读 is_suspended/limit_status flag;真实数据停牌=缺行→**切片3引擎须改按缺行+trade_cal判停牌(非flag)**;日期轴改用 explore_reader_calendar 权威轴(比全宇宙bar并集更稳)。属切片3引擎适配,Q3已交calendar视图。
**其余完整性(次要,重灌后一并复核):** null存续245(holdout后上市,正常)/coverage>1.0共242(list_date晚于首bar,待归因)。
**剩余Q3(重灌+核对已闭合,2026-07-07):** ①两份规则文档(limit_status推导含分位取整/is_st PIT源=entity_alias,增补②待人过目) + ②Q3完整验收包(四件套=008三视图DDL+009越权实测+holdout泄漏测试+核对档,加两文档)交人审→过则切片3开工令。008三视图/009角色已建验证(越权/holdout过)、重灌完整性核对四关闭合(见 q3-rebackfill-integrity-2026-07-07.md)。

## 密封状态(永久锚点 · 人 2026-07-07 纠正,不可再动)

- **#4 密封预判已于 2026-07-07 完成封存**(载体=**architecture 仓**,我方**不可见**,内容与我无关、也不需知)。
- **切片3 的密封前置 = 已闭合。** 切片3 开跑前**不需要、也不得**再发起任何"喊人封存密封预判"动作。此前记忆/工作方式里"碰真实市场数据前先喊人封存"钩子**对切片3 已消解**(封存已完成),不得据旧钩子重启请求。
- **任何会话对密封状态存疑时,答案固定 = "已封存,问架构窗口确认"**;**不得请求重封、不得代为封存、不得追问内容**。
- 归因:早前会话把"密封预判钩子"当作切片3 的未决前置(未核架构仓封存实况),属旧认知;此锚点为准,旧钩子对切片3 作废。

## 已裁决口径与指针

- **Q2 范围** = `forecast` + `stk_holdertrade` 两张(tushare 源);~~"行情四件套"~~ **作废**(文档打架已裁 2026-07-07)。
- **库指针(aliyun-new qbase,实物为准)**:`forecast_snap`=138458(batch#1)/ `holdertrade_snap`=179843(batch#2)/ `entity_master`=5861(含退市 D=334)/ `entity_alias`=20005(忠实存全)。锚 entity_master batch=6。**行情(Q3-B,重灌后 2026-07-07)**:`bar_daily_snap`=**17,943,344(batch6,未复权 OHLCV,全史 min 1990-12-19)**/ `adj_factor_snap`=**18,762,389(batch7)**/ `trade_cal_snap`=13,162(batch5,SSE 1990-12-19→2026-12-31,8797 交易日)。~~旧 batch3/4(17,138,664/17,680,484)~~ 已被重灌批 supersede、append-only 保留不用。视图路由 max batch(daily→6/adj→7)。归一列(后复权/停牌/涨跌停/board/is_st/industry)留 008 视图算,facts 只存原始。
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

- **✅ Q3 daily+adj_factor 重灌已完成(2026-07-07,`REBACKFILL_ALL_DONE` 已打印、进程退出)**:分页版 `seed_marketdata.py`(commit eb401a9)。终值 daily batch6=17,943,344 / adj_factor batch7=18,762,389。完整性核对四关闭合(见 q3-rebackfill-integrity-2026-07-07.md)。log=`/tmp/q3b-rebackfill.log`(非 git)。**无在跑重灌进程。**
- **旧截断批保留(append-only 不删,已被新批 supersede)**:daily=batch3(17,138,664 截断)/adj_factor=batch4(17,680,484 截断)。新批 note 记 supersedes 废弃原因;视图取 max batch 自动路由新批(daily→6/adj→7,已验)。
- `seed_facts.py` Q2 回填已完成并 COMMIT;守望 `b097j3l62` 已触发结束。
- **root cron(aliyun-new)**:哨兵 08:30 / 备份 03:00 / 到期提醒 09:00。查验 = `ssh aliyun-new 'crontab -l'` + 各日志;飞书秘钥 `/etc/shuheng/sentinel.env`。

## 待答点(挂账,见 qbase/quality/caveats-and-ledger.md)

- **L1**:巨潮 secCode/orgId 填充验收(行数 + secCode↔orgId 对射抽查)——巨潮件采集时。
- **L2**:alias 映射约束基数——反向唯一取 batch scoped 是有意容跨批复用还是应收紧全局?待 Q2 真数据核实基数后定死(现不焊)。
- **L4**:`cninfo.py` `category=""` 是否稳定返回减持预披露公告——实采抽验。
- **~~S2-DOC1(待人裁)~~ 已裁(2026-07-07,附录 E 落地)**:裁定①认工作解——**estudy2 0.10.0 参照仅覆盖至 BMP(boehmer);spec 行88"(含KP实现)"作废**(归因:引包描述页未核源码,KP 在描述不在源码);核对单 item 2 改读"BMP 段锚 estudy2、ADJ-BMP 段手算+模拟复核";**不引替代 KP 参照**。**加验一道**:ADJ-BMP 零假设蒙特卡洛尺寸检验(无效应+截面相关聚集样本 → 朴素 BMP 拒绝率>α 复现假阳性、ADJ-BMP 拒绝率≈α),一次性模拟、与 item 2 聚集场景合并同一 fixture。落 `taosha/docs/taosha-spec-appendix-E.md`(同附录 D 效力)。
- **S2-Q(三法范围)已裁(人 2026-07-07)= ①现补建三法(spec §7 完整)**:补 Corrado(1989) 秩检验 + 日历时间组合法两 compute 模块,verdict 走 spec §6 三法一致规则(三法方向一致才确认;朴素 t 显著而 ADJ-BMP 不显著→聚集假阳性以 ADJ-BMP 为准;日历法与截面法反向→查事件密集期/补事件加权;三法不一致→AMBIGUOUS)。秩/日历无 estudy2 对台(item2 只锚 BMP),手算+模拟自活。robustness_pending 补齐后撤。
- **C1**:tushare 对 2007 前退市不完备(T00018.SH),默认不捞、挂老机退役迁移单(≈2027 H1)。
- **切片1 三裁已落地(2026-07-07,✅ 待终签)**:裁1 #3 source_type=literature+platform记note(已补登);裁2 closed编码批准+状态机注记入验收文档;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填(ledger焊)。仅剩人终签。
