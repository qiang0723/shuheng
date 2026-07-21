# exp13 `limit_down_open` PAP 草案单元 · 交付档(2026-07-21)

> 授权依据 = 人裁定令 `taosha/docs/limit-down-open-pap-order-2026-07-21.md`(主令八节+补充确认令三条,
> F 条留痕 commit `133f32a` 先于本单元施工)。
> **本单元产物全部为草案与只读对账,不构成冻结、不构成运行授权。**
> 禁区遵守实录见 §8。交付四件(令七)=①PAP 草案 ②条款→键位映射 ③3 行差异只读对账+主事件漏斗
> ④攻击 fixture 设计。持久交付包=AWS `~/shuheng/s13_pap_delivery_2026-07-21/`。

## 1. PAP 草案

- 实物 = `taosha/docs/limit-down-open-pap-draft-2026-07-21.json`(canonical 字节本体:
  词典序排序键+紧凑分隔符+UTF-8+末尾单换行)。
- **文件 SHA256 == canonical digest == `a432877a0953c50b2bb3c1064faa19fc611f1cbeb1cfbd45a76ce1231a6189e2`**。
- **状态 = `NOT-FROZEN`(显式标记,工地指令 2026-07-21 一)**:此 digest 仅为草案 digest,
  未写入数据库、未入冻结记录、未入正式运行参数;"沿承 exp8"不视为自动批准,全部 18 键
  (含 8 沿承键)均待人终版逐项确认。冻结须人另下冻结令、绑定终版 digest;方向+把握度
  预判由人届时亲拟(令八)。
- `validate_pap` PASS;`parse_test_windows` = (5, 20, 60);`pap_schema_version=2`,`analysis_type='event'`。
- 程序化逐键对账(蓝本 = exp8 冻结 PAP v3 `limit-open-pap-final-v3-2026-07-17.json`):
  **键集完全相同(18 键)**;逐字节沿承 8 键 = analysis_type / benchmark / cost / holdout /
  pap_digest_binding / pap_schema_version / sample_gate / window;对偶改写 10 键 =
  bias_statement / cleaning / diagnostic_dimensions / engine_params / event_def / pool /
  reporting_commitments / snapshot_batch_req / verdict_authority / verdict_power_note。

## 2. 人裁条款 → PAP 键位映射(令七.2)

| 裁定条款 | 要点 | PAP 键位落点 |
|---|---|---|
| 一.1 | N=2 连续一字跌停真实交易行 | `event_def`("连续N≥2个一字跌停交易日") |
| 一.2 | 链成员唯一判据双条件 | `event_def`(one_word ∧ open_at_down_limit;prices_snap 实源) |
| 一.3 | A口径三则(停牌不重置/禁拼接/最大饱和链) | `event_def` 逐句 |
| 一.4 | B口径仅 NFV 诊断对照(链数/事件数/碰撞链数/相对A差异) | `event_def` + `diagnostic_dimensions.b_axis_control` + `verdict_authority` + `reporting_commitments` |
| 一.5 | (ts_code,event_date) 唯一,重复映射 fail-closed 全剔逐条留痕 | `event_def` + `reporting_commitments` |
| 二.1/二.2 | reversal_hijack 定义+不入主事件集、不与主假设混合判决 | `event_def`(定义原文对齐) |
| 二.3 | hijack 逐条 audit,数量/占比/年份/链长/顺延结构可报,全 NFV | `diagnostic_dimensions.reversal_hijack_audit` + `reporting_commitments` |
| 二.4 | 禁其收益/CAR/显著性/独立结论;另研究须另登假设 | `event_def` + `verdict_authority`(结构禁入) |
| 二.5 | 真开板(open_at_down_limit 非 one_word)保留 | `event_def` |
| 三.1 | st_policy='keep', st_mode='event_day' | `engine_params` 两键 + `cleaning` |
| 三.2 | ST 首要诊断轴紧随顶层主判决,全 NFV | `diagnostic_dimensions.st_primary_rule` + `engine_params.diagnostic_dims`(st 居首) + `reporting_commitments` |
| 三.3 | 链起点≠事件日 ST 单独计数留痕;归层=事件日 PIT | `diagnostic_dimensions.st_primary_rule` + `cleaning` |
| 三.4 | 三重核验(snapshot 钉定/视图实物逐项一致/层恒等对账) | `diagnostic_dimensions.st_primary_rule`(实现期验收面预登记) |
| 四.1/四.2 | 研究期 2007-01-01≤event_date<2024-07-01 | `event_def` |
| 四.3 | 全A排北交所;PIT 上市区间;全市场等权 | `pool` + `engine_params.benchmark_mode='market'` + `benchmark` |
| 四.4 | recent_listing=链起点上市交易龄≤30,第二 NFV 轴 | `event_def` + `diagnostic_dimensions.axes.listing_age` |
| 四.5 | 科创板零链/创业板改革后近零/聚集,预注册披露不改参数 | `diagnostic_dimensions.coverage_rule` + `reporting_commitments` |
| 四.6 | CAR 轴自事件日后 T+1 起;三窗 [0,+4]主/[0,+19]/[0,+59] | `window`("T+1起,后5/20/60日";τ=0:=T+1=S2-DEC3 既有锚) + `cleaning` + `verdict_authority` |
| 四.7 | 主窗 ADJ-BMP 唯一判据;朴素t/Corrado/日历法全 NFV | `engine_params.verdict_policy='adj_bmp_main_only'` + `verdict_authority`(field_roles) |
| 四.8 | 效力 llm/prescreen | `verdict_power_note` |
| 四.9 | 清洗/listing/hijack 排除改变估计对象,偏差方向未知 | `bias_statement` |
| 五.4 | 拟入裁定数字须直接漏斗+明确分母 | `reporting_commitments`(七档漏斗+恒等式+分母承诺) |
| 五.5 | 3,661 永久取消硬基线资格 | `event_def` 末句 |
| 六.2 | report 显式 limit_down_selection 分支/真锚/exp8 零回归 | `reporting_commitments`(施工面预登记,本轮不施工) |
| 七.4 | 主漏斗固定顺序(七档) | `event_def` 末段 + `reporting_commitments` |
| 补充令1 | 右删失∧hijack=互斥主原因+正交 audit 标志+重叠计数 NFV | `event_def` + `diagnostic_dimensions.reversal_hijack_audit` |
| 补充令2 | 对账=既有钉批视图+日历轴;不新建 snapshot/manifest | `snapshot_batch_req.note` + 本档 §4 对账实录 |
| 八 | 禁区+预判由人亲拟 | 非 PAP 键;本档 §8 执行实录 |

**裁定未覆盖、草案沿既有冻结常量的键(请终版一并确认)**:`benchmark`(含 pool_hypothesis 字样,
engine 实际只用 market)/`cost` 四值/`holdout`/`sample_gate=30`/`cleaning` 中估计窗
250~91·160·112 与 unified 顺延≤5(spec §5-6 既有冻结口径)——均逐字节沿承 exp8 v3,零自行改动。

## 3. 主事件漏斗(令七.4;权威=StudySnapshot 121 钉批+日历轴)

权威重算实物 = aliyun `/tmp/s13pap/`(脚本 `s13recon.py` sha256 `ffbb512e…3078e`,只读、
零价格收益列、零库写、零新 snapshot/manifest);**双跑逐字节一致**(§4.1)。
漏斗顺序 = 令七.4 互斥主原因:原始最大链→右删失→研究期外→listing 异常→duplicate→
reversal_hijack→最终主事件集。

| 档 | 计数 | 说明 |
|---|---|---|
| 输入行(钉批∩日历) | 15,099,011 | = snap 15,099,014 − 日历外 3 行(§4) |
| 成员行(one_word∧open_at_down_limit) | 18,106 | = 链内 12,066 + len1 段 6,040;与窄闸"一字下"18,106 精确一致 |
| 原始最大链(A,N≥2) | 3,323 | len1 段 6,040 不成链;链长分布∑=3,323 |
| − 右删失 right_censored_no_event_day | 47 | 互斥主原因第一档 |
| − 研究期外 pre2007 / post | 456 / 0 | 2007-01-01≤ev<2024-07-01;post 端 holdout 视图焊死 |
| − listing 异常 | 0 | 三类 fail-closed 全零 |
| − duplicate mapping (ts_code,event_date) | 0 | 全剔口径,实测零 |
| − reversal_hijack | **26** | 逐条 audit 见 §5;不入主集 |
| = **最终主事件集** | **2,794** | |

**程序化断言 = `s13_assert_identities.py` 36/36 ALL_PASS**(交付包内含脚本+输出,输入=双跑
实物 JSON,零重算):总恒等 3,323=47+456+0+0+0+26+2,794;候选事件链 2,820=hijack 26 ⊔
主集 2,794(不交并);**hijack 26 ≤ 反向一字涨停顺延行 63**(且 audit ∑deferred_up=63,
每链≥1);ST 层 1,480+1,314=2,794;recent 层 29+2,765=2,794;board/year/evday 各层恒等;
右删失∧hijack 重叠计数=0(audit 空、正交标志 `reversal_hijack_observed_before_censoring`
零触发;若非零仅入 audit,`NOT_FOR_VERDICT`)。

**比例(分子/分母/漏斗阶段全显式)**:hijack 占比 = 26/2,820(分母=过 listing/duplicate 后
进入 hijack 档的存活候选)= **0.922%**;26/3,323(分母=原始最大链)= 0.782%。ST 占比 =
1,480/2,794(分母=最终主事件集)= **52.97%**。

**对窄闸 2,820 的逐层归因(如实列差,零追数)**:窄闸"A 研究期事件 2,820"= 本漏斗 hijack 档
前的候选存活数(窄闸无 hijack 档);2,820 − hijack 26(ST 14/非 ST 12;main 24/chinext 2;
recent_listing 0)= 2,794,各诊断层同步核销:ST 1,494→1,480、非 ST 1,326→1,314、main
2,620→2,596、chinext 200→198、recent 29→29,右删失 47、pre2007 456 两侧相同。旧 3,661
维持永久取消硬基线资格(令五.5),不逐项归因。
⚠ 工地此前对 2,489/57.5%/30.9%/"差异 30 条"的派生推测已被人作废,不进入本档任何结论;
本节全部数字出自本次同一 snapshot(121)、同一交易日历轴、同一过滤顺序的确定性双跑重算。

## 4. 3 行差异只读对账(令五.2;补充令2)

### 4.1 权威对账记录(指令二)

- StudySnapshot **ID = 121**;digest = `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`
  (manifest 三处同 content 系,mirror 读回)。
- **完整批次向量(manifest content)**:qbase = daily 6 / adj_factor 7 / stock_basic 6 /
  namechange 7 / trade_cal 10 / forecast 1 / holder_sell_predisclose 12 / stk_holdertrade 2;
  taosha = market_return 88 / pool_b1 18 / pool_b1_return 18。实际依赖批次(本研究触及五表)
  = daily 6 / adj_factor 7 / stock_basic 6 / namechange 7 / trade_cal 10,与 current 各表
  max(batch_id) 逐项相等(`vector_equal_current_max` 全 true;不等即停报,未触发)。
- 语义 = 正式 ViewReader:`set_config('shuheng.study_snapshot_id',121)` +
  `explore_reader_prices_snap JOIN explore_reader_calendar_snap USING (trade_date)`;
  current 视图仅作 3 行差异解释性对照,**非 PAP 样本基线**。
- **双跑**:run1 完成 2026-07-21 17:19:14 +0800,run2 完成 17:26:11 +0800(同脚本同参数);
  结果 SHA256 双跑同值 `ecc915b5fc6c95261cfa39a12a50f85f855ba2767013e6a44f10d5aacdea260f`,
  `cmp` 逐字节一致;run1.log==run2.log(`dff36ab3…`);按停止线不追加第三次运行。

### 4.2 3 行差异逐行(指令三)

行级三数:current 15,099,014 = snap(121) 15,099,014;snap∩日历 15,099,011;双向 SQL
EXCEPT(身份=(ts_code,trade_date)):current−钉批 = 3 行,钉批−current = **0** 行;交易
日历轴本身双向差异 = 0。

| ts_code | trade_date | limit_status | open_limit_status | 进入交易日历轴 | 落在研究期 | 链成员/链边界/事件身份 |
|---|---|---|---|---|---|---|
| 000002.SZ | 1992-10-04(周日) | none | none | 否(current/钉批日历均无此日) | 否(<2007) | 非成员;±2 行邻域全 none,不邻接任何一字行→不构成链边界或事件日 |
| 000002.SZ | 1993-01-03(周日) | none | none | 否 | 否(<2007) | 同上 |
| 000007.SZ | 1993-01-03(周日) | none | none | 否 | 否(<2007) | 同上 |

成因 = 老数据源 1992/93 年三根落在交易日历外自然日(周日)的 bar,日历轴内连接剔除。
邻域证据(库内一次最小只读查询,§三闭合范围,SELECT 无价格收益列):三行各自 ±2 行
`limit_status/open_limit_status` 全 `none/none`;两票 1997 前一字行各恰 1 根孤立行
(current 与钉批双侧计数相同,len1 不成链)。

### 4.3 双向集合差异(指令三;全零=本单元内闭合)

| 集合(钉批∩日历 vs current) | only_first | only_second |
|---|---|---|
| A 最大饱和链集合(ts,链首,链尾) | 0 | 0 |
| A 主事件集(ts,event_date) | 0 | 0 |
| B 最大饱和链集合 | 0 | 0 |
| B 主事件集 | 0 | 0 |

**reversal_hijack 集合与右删失集合差异 = 0(推导闭合,前提逐项程序化断言)**:
①差异行仅 3 根、全属 000002.SZ/000007.SZ(行级双向 EXCEPT);②其余全部票两侧行流恒等,
管线逐票确定性→分类逐票相同;③该两票的 3 行非成员、不邻接任何一字行(§4.2 邻域证据)
→不可能改变链边界/事件日/顺延结构,且 A/B 链集合差异已直接计算=0;④hijack audit 26 条
零链属该两票;⑤全部漏斗计数器双侧逐键相等(仅 rows_streamed 差 3):hijack 26=26、
右删失 47=47。⇒ 四类集合差异全部为 0,**勘误裁定(五)在本单元内闭合,无非零项,无上报项**。

## 5. A/B 口径与诊断面(全部 NOT_FOR_VERDICT)

B 口径 = 交易所日历连续(A 成员段按日历相邻切分),与 A 位于**完全相同的过滤阶段**
(同一 funnel 函数镜像,逐档计数存在性+总恒等已程序化断言):

| 档(NFV 对照) | A 口径 | B 口径 |
|---|---|---|
| 最大饱和链 | 3,323 | 3,366 |
| 右删失 | 47 | 50 |
| 研究期外 pre2007/post | 456 / 0 | 463 / 0 |
| listing 异常 | 0 | 0 |
| duplicate(碰撞链剔除/碰撞事件日) | 0 / 0 | 99 / 49 |
| reversal_hijack | 26 | 26 |
| 最终主事件集 | 2,794 | 2,728 |

A vs B 主事件集(钉批内)双向差异 = A 独有 66 / B 独有 0(B 碰撞日 fail-closed 全剔所致,
逐条名单在结果 JSON `event_identity_diffs`);B 总恒等 3,366=50+463+0+0+99+26+2,728。
诊断分布(均 NFV,分母=主事件集 2,794):ST 1,480(52.97%)/非 ST 1,314;main 2,596 /
chinext 198(改革前 193/后 5)/ star 0;recent_listing 29 / seasoned 2,765;年度峰值
2015=418、2018=322、2020=252;共享事件日≥2 票=500 天,top=2007-06-06(107 票)、
2015-07-09(75 票);hijack 年份集中 2015=14(全部链尾 2015-07-07/08,股灾反弹几何)、
2024=4;ST 链起点 vs 事件日不一致 74 条逐条留痕(归层按事件日 PIT)。事件日形态:仍跌停
806 / 涨停 330 / none 1,658;开盘位 open_at_down_limit 1,884(真开板保留)/ up 3 / none 907。

## 6. 攻击 fixture 设计(令七.5;设计,不施工)

覆盖令七.5 全部 12 组并扩充至 18 组;每组=输入几何→预期行为→攻击点。
实现阶段落 `verify_limit_down_rules.py`(纯合成行,不触真实数据)。

| # | 名称 | 输入几何(合成行序) | 预期行为 |
|---|---|---|---|
| F1 | N=1 不成链 / N=2 成链 | 单根 D̄;两根 D̄D̄(D̄=one_word∧open_at_down_limit) | 前者零链(len1 run 计数);后者恰 1 链 len2 |
| F2 | 最大饱和链禁截子链 | D̄×5 连续 | 恰 1 链 len5;len2/3/4 子链计数=0 |
| F3 | 停牌缺 bar 不重置 A 链 | D̄D̄〔缺bar×3〕D̄ | 恰 1 链 len3(行序连续);B 口径镜像拆 2 段(仅诊断) |
| F4 | 真实非一字 bar 必须断链 | D̄D̄,none,D̄D̄ | 恰 2 链各 len2;none 行为前链事件日 |
| F5 | 反向一字涨停触发 hijack 并排除 | D̄D̄,Ū(one_word∧open_at_up_limit),none | 链存在但主集=0;hijack 计数=1;audit 含该链(顺延结构 up=1);none 日不成为主集事件 |
| F6 | 真开板保留 | D̄D̄,X(open_at_down_limit ∧ limit_status='limit_down'≠one_word) | X 为合法事件日,保留主集;不触发 hijack |
| F7 | 重复映射全剔 | D̄D̄,Ū,D̄D̄,none | 链1 顺延穿 Ū 与链2 达同一 none 日=链2 事件日→duplicate:两链全剔逐条留痕;主集=0;不合并不择一 |
| F8 | listing 三类异常 fail-closed | ①无 listing 行 ②首 bar<list_date ③delist≤list 或 bar≥delist_date | 三类各:该票候选全剔,计入 listing_anomaly 档并按类留痕 |
| F9 | ST 切换按事件日归层 | 链起点 is_st=false,事件日 is_st=true | 入 ST 层;st_flag_chain_vs_eventday_diff 计数+1 且逐条留痕;主判决不变 |
| F10 | 研究期上下界 | 事件日=2006-12-29 / 2007-01-01 / 2024-06-28 | 剔(out_of_period_pre2007)/ 保留 / 保留;≥2024-07-01 结构上不可见(holdout 视图焊死)+驱动断言 0 |
| F11 | 科创板单行不成链 | star 板单根 D̄ | len1 run 不成链;star 层零事件如实报告(NO_EVENTS_IN_LAYER) |
| F12 | 诊断层递归零 verdict | 构造含 ST/listing_age/B 对照/hijack audit 的完整 result | 递归扫描全部诊断块:无 verdict/verdict_note/显著性分类字段;NFV 标记在场;顶层 verdict 唯一 |
| F13 | 右删失∧hijack 互斥主原因(补充令1) | D̄D̄,Ū,〔数据终止〕 | 主漏斗记 right_censored_no_event_day=1,hijack 档=0;audit 正交标志 reversal_hijack_observed_before_censoring=true,重叠计数=1 |
| F14 | 纯右删失 | D̄D̄〔数据终止〕 | right_censored=1;正交标志 false/缺省;hijack=0 |
| F15 | 链后停牌跨档开板保留 | D̄D̄〔缺bar×2〕none | 事件日=none 行,保留;susp_gap 诊断标志;不误入顺延计数 |
| F16 | 混合一字顺延结构 | D̄D̄,Ū,D̄,none(第二段 D̄ 为 len1) | 链1 顺延结构 up=1,down=1→hijack 剔除;len1 段不成链;主集=0 |
| F17 | 创业板改革边界(300216 实案镜像) | chinext 链跨 2020-08-24,limit_pct 10%→20% PIT | 链成员判定按当日制度价位;改革日后一字判据用 20% |
| F18 | B 口径 NFV 不改主集 | F3 同几何 | A=1 链入主漏斗;B=拆 2 段仅入 B 对照块;主事件集只认 A;B 碰撞计数不影响主集 |

## 7. 复用与触碰面(令六,只登记)

与窄闸报告一致:新增 `limit_down_rules.py` + exp13 driver + exp13 fixture 三件纯新增;
`report.py` 适配阶段增显式 `limit_down_selection` 分支(标题"exp13 一字跌停开板"/真实
StudySnapshot 锚/缺锚 fail-closed/exp8 逐字节零回归);统计内核零触碰——本单元均未施工。

## 8. 停止线遵守实录(令八)

未写生产代码/未读取收益(对账与邻域证据查询 SELECT 列表均无任何价格收益列,连接
`default_transaction_read_only=on`)/未计算 CAR 或显著性/未冻结/未生成 manifest 或 source
snapshot/未正式运行/未写台账/未代写方向与把握度预判。权威重算恰双跑(run1/run2,§4.1),
逐字节一致后未追加第三次运行、未自行开启新复核项;漏斗恒等断言跑在双跑实物 JSON 上,
零重算。裁决留痕 commit(`133f32a`)先于施工、与交付 commit 分单。完成后停交验点。
