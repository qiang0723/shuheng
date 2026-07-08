# 枢衡 quant · STATE(会话无关权威状态)

> 状态持久化纪律(仓根 CLAUDE.md,v1.5)载体。**开工第一动作读此文件;阶段完成/收工必更新。**
> 本文件 + 数据库实物 = 真身;会话记忆是草稿。**断链恢复第一动作 = 查库 + 读本文件。**
> 改判纪律:口径/指针改判须在此**显式作废旧条目(内容+原因)**,不留新旧并存。

最后更新:2026-07-08(**切片3 步3 市场收益落库 ✅ 签收(a7639f1)+ 步4 ViewReader ✅ 完成验收**(`taosha/docs/slice3-step4-viewreader-acceptance-2026-07-08.md`)。引擎逻辑改造大块早已全完成(HEAD 8823580)。**剩步7=跑#4第一份真实体检报告**(前置见 §步7)。已完成:frozen_ashare语义标签裁定A、pap检验窗解析、步3a、步5 cleaning约束②、步3b删失诊断窗、**步3市场等权日收益落库(taosha market_eqw_return 8186行,签收a7639f1)**、**步4 ViewReader+runner两接缝(HEAD 6a04af6,合成逐字节零回归)+taosha_engine DSN配置+引擎身份三组断言绿**。北交所排除五条已成(886c708)、Q3签收ea59367、切片2终签b7e3b4b。慢比快好)

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

## 当前切片:切片3(#4 端到端·修正案三验收)开工(人下发 2026-07-07)

**开工令(原文即口径,六条 + 三约束):**
- **① 入口项先清**:(a) `cleaning.py` 改按缺行+calendar 判停牌(§6 承接,非 flag);(b) **coverage>1.0 之 242 票归因——归因结论先报后跑**,它关系"缺行=停牌"语义的最后一块地基。
- **② 事件源**:experiment 台账 `exp_id=5`(forecast_drift,frozen)之 pap_json,经 `explore_reader_events` 读取;**引擎拒绝 status≠frozen**。
- **③ 数据路径**:全程只走 explore_reader 三视图(引擎 role 已焊死),真实数据第一次入引擎。
- **④ 全链口径**:按冻结配置,**无任何运行时参数**;三法互证 + INSUFFICIENT 合法输出。
- **⑤ 产出** = #4 体检报告(统计事实,**无建议口吻**):三法结果、N_eff、剔除率按年份、逐日 AR 分解、板块分层、偏差声明段。
- **⑥ 报告完成即交,不做任何解读**——解读与密封卡开封对照是人的仪式,不是工地的活。
- **三约束**:四类上报照旧;阶段完成写 STATE;慢比快好。
- **密封**:已封存(见密封状态锚点),切片3 前置已闭合,不需再喊。
- **⚠ 体系原则新增(人裁 2026-07-07):北交所全体系不做**——排除北交所标的(样本池/事件宇宙/检验/交易)。板块分层维持四层(主板/创业板/科创板/ST)无北交所层。
- **即刻核查已做(库实物)**:北交所**存在**——entity_master 宇宙 5861=SH2455+SZ3078+**BJ328**;各 snap distinct .BJ = em/alias/bar/adj 各328、forecast187、holdertrade220。**识别口径=`ts_code ~ '\.BJ$'`(唯一零漏网);人给数字段「8开头及43/83/87」只命中6只、漏920段325只(920=北交所2024新段、9字头),勿用数字段。** 证据档 `qbase/quality/q3-coverage-gt1-attribution-2026-07-07.md` §7-8。
- **✅ 排除口径已裁 A(人 2026-07-07,原文即口径):视图层 WHERE `ts_code !~ '\.BJ$'`**,识别口径采纳核查结论 .BJ 后缀(**920段实证在案,数字段口径「8开头及43/83/87」作废——错误归因:架构窗口过时知识**)。**五条执行**:① explore_reader 三视图加排除条件、与 holdout **同一焊法(DDL层非应用层)**;② 底表不动、328 忠实存全;③ 完整性核对加**负面断言:三视图 .BJ 计数=0**,并留档排除量(prices 328票/forecast 187/holdertrade 220 票的行数),体检报告口径注记"事件宇宙=沪深,北交所按体系原则排除";④ **泄漏测试扩展**:经视图查 .BJ 返空,与 holdout 泄漏测试并列;⑤ 600018 归因结论入档、**coverage>1.0 项关闭**。**✅ 五条全成(886c708)**:三视图 prices/events 加 `!~'\.BJ$'`(calendar无ts_code不适用)、git版本apply后 prices/events .BJ=0 复核过、排除量留档(prices 252票/196807行=board bse行数闭环、forecast 53票、holdertrade 220票)入 `q3-rebackfill-integrity §7`、600018 结项入 `q3-coverage-gt1-attribution §9`。排除后视图沪深 prices5363票/events105584事件,板块四层无北交所。**→ 转原开工令续:改cleaning→接exp_id5→跑#4。**

**〔切片3 引擎适配路线(cleaning/runner 数据流分析 2026-07-07,下一专注单元)〕** 接 exp_id=5 完整工作面(比单改 cleaning 大,慢比快好):
1. **建真实 ViewReader(核心新件)**:切片2 只有 SyntheticReader(读csv);切片3 需 `reader/view.py` 读 explore_reader 三视图、用 role `taosha_engine`(只读物理隔离,DSN 待配 aliyun `.env`);接口同签名 prices_by_security()/events()/**calendar()**,engine 零改造(契约§SyntheticReader 已预留"Q3 ViewReader 同签名")。
2. **扩 calendar 契约**:`reader/contract.py` 现只有 PRICE/EVENT 契约、无 calendar;需加 CalendarRow + reader.calendar() 签名(explore_reader_calendar 权威轴,供缺行判停牌)。
3. **改 cleaning.py(停牌语义)**:现 line92 `t_row.is_suspended`/line104 `row.is_suspended` 依赖 flag;真实数据 is_suspended 恒 false、停牌=缺行(by_idx.get(idx) is None)。改为**停牌 = 缺行 OR flag**(真实靠缺行、合成 fixture flag 仍兼容→不回归切片2);一字板顺延(line100-108)区分**越界(tau0>=n_dates→break)vs 停牌缺行(row None 且在轴内→blocked 续顺延)**。
4. **改 runner.py(date 轴)**:现 `all_dates=全宇宙bar并集`(line ~run_study 头);改用 reader.calendar() 权威轴,缺行判停牌才严格(契约核对发现:并集≈完整轴但calendar更稳)。
5. **台账读 frozen pap**:从 experiment 台账读 exp_id=5(forecast_drift) pap_json,校验 status=frozen(拒非frozen,铁律③);benchmark_mode/pool 按 pap。
6. **跑 run_study→#4 体检报告**(report.py,无建议口吻):三法/N_eff/剔除率按年份/逐日AR/板块分层/偏差声明。
7. **验证**:合成回归不破(切片2 fixture 双跑一致)+ 真实数据跑通+报告。**报告完成即交,不解读(开工令⑥)。**

**〔随行三约束(人 2026-07-07,原文即口径,批①②开工)〕**:
- **约束① DSN 秘钥纪律 + 权限只收不扩**:DSN 按秘钥纪律(aliyun `.env` root 600、不进 git、不回显);`taosha_engine` 权限**只收不扩**——施工中发现"还需要"任何底表或写权限 = **设计问题上报**(四类②/③),**不自行加 GRANT**。
- **约束② 一字板语义钉死**:**一字板 = 有 bar + 触板(limit_status='one_word' 判)**;**停牌 = 缺行(calendar 断档判)**;两者判据**物理不同**(一字板必有 bar、停牌必无 bar)。遇"一字板但缺行"杂交样本(如 limit_status=one_word 却 close=None/缺行)**如实上报、不自行归类**。→ cleaning 一字板顺延须分离两判据 + 杂交检测上报。
- **约束③ 合成回归升格为验收硬项**:cleaning/runner 改动后**重跑切片2 对台全套(logbench)**,与真实 #4 跑通**并列交付**(双跑一致 + BMP 3.7e-14 级对齐不回归)。
- 通则:四类上报照旧;每步验证;不赶工。

**〔切片3 施工进度 + ⚠ 阻断发现(读 exp_id5 pap,2026-07-07)〕**
- **②契约扩 calendar ✅**:`reader/contract.py` 加 `CalendarRow`(trade_date/pretrade_date)+`CALENDAR_COLUMNS`+`enforce_holdout_calendar`;`SyntheticReader.calendar()` ✅=合成域权威轴(全证券 trade_date 并集,停牌用flag有行故并集=完整轴→runner改用calendar轴后合成域零变化、约束③回归不破)。语法自检过。
- **①ViewReader 暂缓**:规模(prices视图15M行不可全load)+ 事件窗打架未裁,待裁后建。
- **✅ 事件窗已裁(人 2026-07-07,原文即口径)**:**#4 检验窗=pap 之 20/60**(T+1 起算,S2-DEC3 的 τ=0:=T+1 锚对所有窗继续有效,即后20日=T+1..T+20)。**实现机制**:检验窗**从 pap_json 读取**(事件窗属事件定义,台账为唯一事实源),**不在 frozen_ashare 为 family 复制窗口参数**。**frozen_ashare [0,+2]/[0,+5] 保留但改语义标签=强制报告的删失诊断分解窗(R5 本义)**,对全部假设通用,与检验窗**并行输出、互不替代**。**打架归因**:核对单 item 8"主窗/稳健窗"措辞=架构窗口错误,S2-DEC3 据此锚定无过;**item 8 改读"[0,+2]/[0,+5]=删失诊断报告窗",留痕**。**合成回归复验须覆盖此改动**:检验窗改从 pap 读后,切片2 合成用例给 **pap 桩喂原短窗**,结果应**逐字节不变**。
- **✅ benchmark 已裁**:**#4 跑 market(全市场等权),单跑不双跑**。依据:#4 为全市场族,冻结基准规则(池内假设=雷达股池等权/全市场假设=全市场等权)早定,pap 的 pool/market 二项是**按假设归属选、非自由度**;双跑=多看一眼,不做。**15M 规模点解法**:**全市场等权日收益预计算落库**(≈8797行小表,带 batch 溯源,含**北交所排除后**的宇宙口径),引擎**读表不现算**。
- **停牌 modified_rank**:初判方向对(缺行=识别、modified_rank=Corrado 秩处理,互补非打架),**自核 `rank_test.py` 后报结果**即可(不阻断)。
- **ViewReader 按事件票取数照准**。pool.universe=全市场(业绩预告)→样本=有 forecast 事件的票;event_def=valid_time=first_ann_date、修正公告不进本假设;sample_gate=30;snapshot=forecast_snap Q2 batch#1;可交易 T+1 开盘/CAR 起点 T+1(合 S2-DEC3)。

**〔切片3 裁定后施工清单(2026-07-07,慢比快好每步验证)〕**
1. **检验窗从 pap 读 ✅ 步3a 完成(runner 重构 + 合成回归逐字节验证过)**:`pap.parse_test_windows(pap)` 从 window 文本读检验窗(#4=(20,60)/#3=(5,20,60);后N日=τ=0..N-1=N点;解析失败即raise)。runner run_study 解析检验窗→main_len/robust_len 驱动事件窗/per_tau/car/三法/verdict(不再用 fa.EVENT_WINDOW);car taus 标签改检验窗[0,+main_len-1]/[0,+robust_len-1];adj_bmp_by_tau 变长(n_tau=len 自适应)。**合成回归**:synth_pap window 改文本"后3/6日"(=原3/6点),**git stash 改前基线 vs 改后 diff = 逐字节完全一致**(约束③达成,切片2 不回归)。**步3b 删失诊断窗 ✅ 完成(2026-07-07)**——R5 三件套:①各 τ 逐日 AR(AAR+BMP/ADJ-BMP)②各 τ 一字板/触板/停牌计数占比③①②按板块四层(main/chinext/star/ST)分拆;全报告项不进 verdict。runner `_censor_diagnostic()`+se_meta diag_censor(诊断窗每日删失类型:缺行/flag=suspend、one_word、limit_up/down)+report 段。**验证**:合成跑 censor_diagnostic 纯新增(检验窗 car/verdict/n_eff 逐字节不变)、板块四层 15+13+7+ST0=35 与 strata 一致、τ=0 AAR=0.025/adj_bmp=6.58 反映注入信号。
2. **frozen_ashare 改语义标签 ✅ 已裁 A(人 2026-07-07):只改源码注释、不动 FROZEN**。digest 保持 `c795b21e` 不变、切片2 item10 冻结实证不破。语义变落 runner 层:runner **不再用 FROZEN.event_windows 驱动主检验**(检验窗从 pap 读),FROZEN.event_windows 原值 [0,+2]/[0,+5] 降格作**删失诊断窗**、由 runner 标注。FROZEN 字符串仍历史措辞"主窗/稳健窗",靠 **item8 改读留痕**注记"[0,+2]/[0,+5] 现读作删失诊断窗、S2-DEC3 锚定无过"。报告并行输出检验窗(pap 20/60)+删失诊断窗(frozen 2/5)。**✅ 注释改完(EVENT_WINDOW_MAIN/ROBUST 标注删失诊断窗、FROZEN dict 未动)、audit_digest 验证 == c795b21e 不变、python 自检过。**
3. **市场收益预计算落库 ✅ 完成落库+验收(2026-07-08,留档 `taosha/docs/slice3-step3-market-return-acceptance-2026-07-08.md`)**:全市场等权日收益 taosha(L2)`market_batch`#1 + `market_eqw_return`=**8186行**(002迁移postgres属主apply;append-only触发器对属主亦生效实测过;`market_return_current`路由max batch视图;授权taosha_app INSERT/taosha_engine SELECT只收不扩)。**口径**:ret_eqw=当日有present bar且有前序present bar的票 log(后复权close_d/close_前序)等权均(收益核=冻结returns.py multi_day/Close,视图无null行故相邻present比值=跨缺口收益落恢复日);n_stocks=分母(停牌缺行不进,诊断列);frozen_digest=`b88a43ef7bd8…`。**⚠改判:~~≈8797行~~作废**(8797=全日历交易日=泄漏红线)→**实落8186=8187日历交易日−1(首日无前序)**。**轴=日历(约束②):源=explore_reader_prices ∩ explore_reader_calendar**——off-calendar数据发现:prices视图8189 distinct交易日 vs calendar 8187,多2天=**1992-10-04/1993-01-03**(3主板bar,SSE trade_cal is_open=0周日,早年tushare非交易日bar噪声),结构性剔除(约束②实现非新口径,1992-93早holdout三十年零影响,登记qbase数据质量携带项)。**双算闸**:Python冻结核 vs SQL窗口 max|Δret|=6.5e-16/n_stocks全等(不过即中止)。**硬闸**:max_date=2024-06-28<holdout & out_rows=8186≪8797。落库=读QBASE_APP_DSN(视图结构性保证holdout/.BJ/后复权)写TAOSHA_APP_DSN。commit `98df86d`(建)/`e843a55`(日历轴修正)/`a7639f1`(验收留痕)。**✅人签收 a7639f1(2026-07-08)+日历轴处置追认**:市场基准轴权威唯一=官方日历,`prices ∩ calendar`=约束②正确实现;2根is_open=0周日bar保持「底表存真+视图不消费+质量携带项登记」三态,不为3根噪声另开batch。**⚖standing裁定(人2026-07-08,不需再裁):个股侧将来遇同类(bar落非交易日)按同一处置——收益跨到前一日历交易日,与estudy2跨缺口逻辑天然一致。**
4. **建 ViewReader ✅ 完成验收(2026-07-08,HEAD 6a04af6,留档 `taosha/docs/slice3-step4-viewreader-acceptance-2026-07-08.md`)**:`reader/view.py` 契约实现之二(同SyntheticReader签名 prices/prices_by_security/events/calendar+market_return),数据源=qbase explore_reader三视图(role taosha_engine只读)+taosha market_return_current。**DSN配置**:服务器端openssl生成密码→ALTER ROLE taosha_engine PASSWORD(scram)→TAOSHA_ENGINE_QBASE_DSN/TAOSHA_ENGINE_TAOSHA_DSN入`.env`(600 root:root/gitignored/密码未现身)。**事件票取数(非全宇宙)**:先events定样本(5356票)再ANY拉prices。**轴∩explore_reader_calendar(约束②+个股侧standing裁定2026-07-08:非交易日bar剔除、收益跨前一日历交易日)**。**runner两接缝(人批2026-07-08·STATE线80授权)**:①all_dates从reader.calendar()取(真实域8187日历日;合成域=by_sec并集不变)②market模式mkt若reader有market_return()读表否则回退equal_weight_market。**约束③安全证明**:合成端到端result_json逐字节完全一致(sha256 ba529594…前后同)。**引擎身份三组断言绿**(taosha_engine实测非DBA):6底表越权全denied/三视图holdout≥2024-07-01全0/三视图.BJ全0/taosha侧market可读+experiment+market_batch denied。真库冒烟:events=105584/样本5356/calendar 8187/market非空8186。**role权限只收不扩**(发现"还需要"=上报不GRANT)。
5. **改 cleaning(约束②)**:停牌=缺行 OR flag(真实缺行/合成flag兼容)、一字板=有bar+limit_status='one_word'分离两判据、"一字板但缺行"杂交检测上报。
6. **核 rank_test modified_rank ✅(2026-07-07,无需改)**:`rank_test.py` 已实现 Corrado&Zivney1992 标准化秩=pap 的 modified_rank 口径:缺项(None)不入排名(`idx_valid` 过滤)+ T_i=有效观测数(缺项减少)+ K=rank/(T_i+1)-0.5 用各证券 T_i 标准化;自检4 覆盖"禁零填充—缺项不入排名T_i减少"。与约束②互补确证(缺行停牌→AR None→modified_rank 处理),python -m 自检全绿。
7. **跑 #4 market 单跑 → 体检报告**(无建议口吻) + **合成回归硬项**(pap桩喂原短窗逐字节不变 + 切片2 logbench 对台不回归)。**§步7 前置(步4验收捎回,2026-07-08)**:①**clean_event 空价行硬化**——runner `clean_event` 首行取 `rows[0]`,对"有forecast事件但无价行"的票会 IndexError;真实全样本(events()=105584全事件、sample=5356票)跑前需空rows前置剔除(no_price)或事件↔样本一致性过滤。②**industry='nan' 桶**——如000004.SZ industry字面串'nan'(口径④ρ̄分组会出'nan'桶,属"行业非PIT二阶"携带项延伸),报告注记。③#4 pap冻结登记(台账experiment)。④规模:全事件票prices ~千万行加载评估。引擎读全市场等权基准=步3 market_return_current(读表不现算)。
- **coverage>1.0 归因(先报后跑)结论**:242票=241北交所(现全排除)+1沪市并购史(600018上港集团,first_bar2000上港集箱期)。排除北交所后仅剩600018=沪市连续竞价,"缺行=停牌"地基零威胁、无例外。
- **当前动作(待裁解锁)**:人裁排除口径→(A)改explore_reader三视图加 `!~'\.BJ$'`+完整性核对V项加北交所排除断言→改cleaning.py(缺行+calendar判停牌)→接事件源exp_id5→跑#4。

## Q3 ✅ 已签收(ea59367,2026-07-07)+ 切片3 承接项〔存档〕

**008 三视图 ✅ 建成验证 + 009 引擎角色 ✅ 焊死(commit 已 push):** `explore_reader_prices`(后复权close/board/is_st PIT[entity_alias名含ST闭区间]/limit_status[原始价分位取整,真抓涨跌停]/industry,holdout `<2024-07-01`焊WHERE,is_suspended=false真实bar) + `explore_reader_calendar`(trade_cal权威轴8187交易日) + `explore_reader_events`(forecast PIT原始披露去重105651唯一,type→附录C三层)。role `taosha_engine` 仅SELECT三视图、直查5底表全 permission denied、holdout三视图>=2024-07-01全返0——**越权/holdout 两件套 ✅ 过**。
**⚠ is_st PIT 正确性缺陷(2026-07-07 实测发现,✅ 已裁+✅ 已修已验 2026-07-07):** 写 limit_status/is_st 规则文档前在重灌真数据实测 000004.SZ(多次ST↔摘帽)暴露 bug——视图 is_st 用 `EXISTS(任一含ST区间覆盖当日)` + `end_date IS NULL 当至今有效`;而 entity_alias 忠实存全了 namechange 源脏孪生行(同一改名事件常并存 end填 + end=NULL 两行),NULL-end 的含ST行把已结束的ST区间**永久拉成 true**,摘帽后仍恒ST。**范围量化(查 entity_alias 2万行):1102 只有 NULL-end 含ST行,其中 446 只后来真摘帽→摘帽后被误判恒 is_st=true**,会污染切片3 ST剔除/分层。**修法(明确)**=is_st 改为「当日 PIT 生效名=start_date<=trade_date 中最大 start_date 段的名是否含ST」,用下一段 start 划界、免疫 NULL end_date(已验:该逻辑对 000004.SZ 2024-01-02 正确给'国华网安'/非ST)。**另 2 组同日ST冲突需拍口径**:000995.SZ(2020-12-16 ST皇台|皇台酒业)、002417.SZ(2023-06-15 *ST深南|深南退,退市整理期"XX退"不含ST字但性质仍风险警示)。**STATE 旧"is_st PIT 已验"结论作废**(008验证时抽验未覆盖摘帽段,验证不充分)。
**〔is_st 边缘裁定(人 2026-07-07,原文即口径)〕拆分判**:①**同日双名冲突(000995类)**=保守——任一名含ST(含*ST)即 is_st=true;过渡日一天粒度,宁多判勿漏,规则确定可复现。②**'XX退'退市整理期(002417类)**=字面——is_st=false;**依据制度事实非字面偏好**:整理期限幅=10%(首日不设限)非5%,判ST会令limit_status拿5%算板价、真实10%触板反而漏检,分层报告也会把10%删失强度错并入5%层;字面判恰好落回主板10%数值正确。③**否**选项3:不为两只票边角给切片3加三态复杂度。**两条已知近似入 is_st 规则文档**:整理期首日无限幅(334票×1行,不修);事件结构上不落整理期,估计窗触及由覆盖门槛与分层自然暴露。**裁定+两个脏点原样记录进 is_st 规则文档,随验收包交人过目。**
**〔主逻辑=我方施工设计(报否决权)〕** is_st 改 latest-effective-name PIT:GROUP BY (ts_code,start_date) 折叠 namechange 孪生行(免疫 NULL end_date,修 446 票跨段污染) + LEAD(start_date) 划段边界(当日=start<=trade_date<next_start);段内 is_st = CASE 段含'%退'→false(裁②) / 段 bool_or 含'%ST%'→true(裁①,'%ST%'天然覆盖'*ST') / else false。limit_pct 联动:退市整理期 is_st=false→落 board 主板 10%(合裁②数值)。**✅ 已施工落地(008 SQL 改 name_seg 段+CREATE OR REPLACE 到库):单票重验全过(000004.SZ 2024-01-02 修前误判true→修后false,六段全对/000995裁①true/002417裁②false+主板);全表分布对比 is_st rows 697819→580821(−116998=446票摘帽误判行消除,tickers 926不变=未误伤真ST);连带修正 limit_status none−3281=涨跌停(+2400/+311/+570)守恒,印证裁②机理(5%漏检真实10%触板)。证据入 `q3-is-st-rule-2026-07-07.md`+`q3-limit-status-rule-2026-07-07.md`。**
**契约核对发现(报切片3):** runner 日期轴=全宇宙bar并集(真实A股≈完整交易日轴),核心统计在"只吐真实bar"下成立;但 cleaning.py 92/104行直读 is_suspended/limit_status flag,真实数据停牌=缺行→**切片3引擎须改按缺行+trade_cal判停牌**(非flag)。Q3只交视图(含calendar轴),引擎适配属切片3。
**阻塞根因(增补①完整性核对发现):tushare `daily`/`adj_factor` 单票硬顶 6000 行截断。** 000001.SZ 仅6000行起2001-02-16(非1991)、长史票卡6000早年缺=采集缺行(非停牌),"断档=停牌"不成立。**人裁 A(分页全票重灌,理由:B转永久技术债否/C行数识别不可靠且路由常设复杂度否)。三条执行:①旧batch3/4标废不删(废弃原因写新batch note+文档,因fact_batch append-only改不了旧note)、视图取max batch路由新批;②重灌后完整性核对全量重跑、逐票闭合、复验分页拼接不重不漏(dedup重验);③adj_factor一并重灌同验。**
**✅ 重灌完成 + 完整性核对全部闭合(2026-07-07,证据档 `qbase/quality/q3-rebackfill-integrity-2026-07-07.md`):** 新批 **daily batch6=17,943,344**(旧b3 17,138,664,+804,680)/ **adj_factor batch7=18,762,389**(旧b4 17,680,484,+1,081,905),trade_cal未截断不重灌。核对四关全过:①**不重**=两批行数==distinct(ts,date)零重复;②**逐票闭合**=旧批恰好6000被截票 daily 883只/adj 1010只,新批 883/883、1010/1010 全部>6000(daily min6002/max8545,adj min6009/max8676),新批==6000=0、<6000可疑=0;③**早年补回**=底表最早1990-12-19、视图000001.SZ回到1991-04-04(旧起2001);④**视图路由新批**=explore_reader_prices按max(batch_id) source路由 daily→6/adj→7,新批note写supersedes旧批,票集daily⊆adj差集0,覆盖5860=5861-T600018.SH。**⚠改判(显式作废):~~"923只长史票"~~作废→精确核定 daily截断883只/adj截断1010只(并集1011)。作废原因:923为分页dry-run估计口径,非库精确GROUP BY计数。**
**契约核对发现 → 切片3 待办(已登记):** cleaning.py 92/104行直读 is_suspended/limit_status flag;真实数据停牌=缺行→**切片3引擎须改按缺行+trade_cal判停牌(非flag)**;日期轴改用 explore_reader_calendar 权威轴(比全宇宙bar并集更稳)。属切片3引擎适配,Q3已交calendar视图。
**其余完整性(次要,重灌后一并复核):** null存续245(holdout后上市,正常)/coverage>1.0共242(list_date晚于首bar,待归因)。
**Q3 全部交付物 ✅ 就绪,待人终审(2026-07-07):** ①两份规则文档 ✅ `q3-limit-status-rule-2026-07-07.md`(分位取整/limit_pct分档/整理期首日无限幅近似) + `q3-is-st-rule-2026-07-07.md`(latest-effective-name PIT+缺陷背景+裁定原文+两脏点+两近似+双验);②**Q3完整验收包 ✅ 已落 `q3-acceptance-2026-07-07.md`**(交付物A-H:三视图DDL/009角色/越权实测/holdout泄漏/重灌核对/两文档/is_st缺陷处置逐项映射)。**交人审→过则切片3开工令。** 008三视图/009角色已建验证(越权/holdout过)、重灌完整性核对四关闭合、is_st缺陷已修已验。

## 密封状态(永久锚点 · 人 2026-07-07 纠正,不可再动)

- **#4 密封预判已于 2026-07-07 完成封存**(载体=**architecture 仓**,我方**不可见**,内容与我无关、也不需知)。
- **切片3 的密封前置 = 已闭合。** 切片3 开跑前**不需要、也不得**再发起任何"喊人封存密封预判"动作。此前记忆/工作方式里"碰真实市场数据前先喊人封存"钩子**对切片3 已消解**(封存已完成),不得据旧钩子重启请求。
- **任何会话对密封状态存疑时,答案固定 = "已封存,问架构窗口确认"**;**不得请求重封、不得代为封存、不得追问内容**。
- 归因:早前会话把"密封预判钩子"当作切片3 的未决前置(未核架构仓封存实况),属旧认知;此锚点为准,旧钩子对切片3 作废。

## 已裁决口径与指针

- **Q2 范围** = `forecast` + `stk_holdertrade` 两张(tushare 源);~~"行情四件套"~~ **作废**(文档打架已裁 2026-07-07)。
- **库指针(aliyun-new qbase,实物为准)**:`forecast_snap`=138458(batch#1)/ `holdertrade_snap`=179843(batch#2)/ `entity_master`=5861(含退市 D=334)/ `entity_alias`=20005(忠实存全)。锚 entity_master batch=6。**行情(Q3-B,重灌后 2026-07-07)**:`bar_daily_snap`=**17,943,344(batch6,未复权 OHLCV,全史 min 1990-12-19)**/ `adj_factor_snap`=**18,762,389(batch7)**/ `trade_cal_snap`=13,162(batch5,SSE 1990-12-19→2026-12-31,8797 交易日)。~~旧 batch3/4(17,138,664/17,680,484)~~ 已被重灌批 supersede、append-only 保留不用。视图路由 max batch(daily→6/adj→7)。归一列(后复权/停牌/涨跌停/board/is_st/industry)留 008 视图算,facts 只存原始。
- **库指针(aliyun-new taosha,L2,实物为准)**:`experiment`=7(6创始+切片2 SMOKE exp_id7)/ **`market_eqw_return`=8186(batch#1,全市场等权连续对数日收益,轴=日历约束②,1990-12-20..2024-06-28,frozen_digest b88a43ef;`market_batch`#1溯源;append-only+max-batch路由视图`market_return_current`)**。off-calendar携带项:explore_reader_prices 8189 distinct交易日>calendar 8187(多1992-10-04/1993-01-03两周日,is_open=0早年bar),市场基准已∩calendar剔除。
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
