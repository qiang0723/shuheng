# exp20(earnings_revision)PAP 草案 + 逐项裁决映射 + 待人拍清单(2026-07-18 深夜)

- **令源**:`taosha/docs/earnings-revision-pap-order-2026-07-18.md`(人令原文即口径,留痕 commit `7f86caa`)。
- **本单元性质**:仅 PAP 草案。零代码/零收益·CAR·显著性读取/零台账写入/零冻结/零 manifest/零运行。台账 exp20 现状(只读核):registered / source_type=llm / verdict_power=prescreen / pap_json=登记占位(细化待排产)——本草案即该细化,**未写库**。
- **草案地位**:非冻结文本。所有标注〔待人拍 §3-N〕的键为**显式未决**,以人批终版为准;人批准后另出 canonical JSON 文件并按 §1.11 绑定规则计算 digest,冻结句由人内嵌预判。

## 1. PAP 草案(pap_json v1-draft,逐键)

```json
{
  "pap_schema_version": 2,
  "analysis_type": "event",
  "event_def": "业绩预告修正公告事件(既裁2026-07-17+判决形态裁定2026-07-18方案1):样本源=qbase forecast_snap 中 first_ann_date≠ann_date 的行=修正公告候选(登记令原文口径)。来源链键=(ts_code,end_date,first_ann_date);市场事件键=(ts_code,ann_date),每键唯一。同日逐字段重复行仅在L2确定性折叠,L1原始行不动。修正方向基准B=同链内事件日前最近一次公开披露(可为首披或前一修正),不取链首次披露。fail-closed全集(逐条留痕不猜不补):孤儿修正(链无首披行)/ann_date<first_ann_date/同期多链归属不明/基准或当前数值不可判/同日方向冲突/600856.SH单位疑点(既裁单票留痕项)。同日多链同方向→折叠为单事件〔待人确认 §3-9〕。不使用type文字作方向回退。flat(方向判定相等)不进入方向判决,仅计数报告。不设修正幅度门。方向判定字段与比较规则=〔待人拍 §3-3〕。研究期 2013-01-01≤ann_date<2024-07-01(2012前首披链结构性缺失);事件轴自公告日后T+1开始。窄闸参考数(候选12,569/基准B可判5,225)仅为规则实现对账参考,不是预写样本量;正式n_events_total由事件生成器在研究期+flat排除+全部fail-closed后重新确定并逐层对账差异(令四)。",
  "signed_ar": {
    "formula": "signed_AR(i,τ) = direction_sign(i) × raw_AR(i,τ);direction_sign: up=+1, down=−1",
    "application_level": "符号变换施加于事件级、逐τ的raw_AR,先于一切聚合与检验:AAR/CAAR求均、截面方差、BMP标准化、ADJ-BMP聚集修正全部消费signed_AR;禁止仅对最终CAAR或报告展示值改符号(令一)",
    "estimand": "E[signed_CAR]=价格沿修正方向的平均异常反应(估计对象仅限清洗存活样本);正signed效应=价格沿修正方向反应,负signed效应=价格逆修正方向反应",
    "single_verdict": "合并signed事件集只产生一个主窗ADJ-BMP顶层verdict,不因方向诊断层分拆α"
  },
  "diagnostic_dimensions": {
    "axes": { "direction": ["up", "down"] },
    "direction_fail_closed": "主事件集所有事件的direction层键必须严格∈{up,down};空值、flat、unknown及任何白名单外值在进入CAR计算及顶层verdict调用前fail-closed拒绝运行;白名单与axes.direction逐项一致对账(令二;结构沿exp8 listing_age_fail_closed先例)",
    "display_basis": "raw AR〔人建议raw,待终确认 §3-6〕:诊断层报告up/down各层事件数/存活数/逐因逐年剔除/raw CAAR与raw ADJ-BMP数值,保留实际方向与强度;主检验的signed数值不在诊断层重复渲染",
    "note": "up/down为结构化NOT_FOR_VERDICT诊断轴:零verdict、零显著性分类字段,计算路径结构上不调用判决函数,不改变顶层判决;不引入上修/下修双检验、多重比较或总判决规则(令二);flat事件不在轴内,仅入计数报告块",
    "zero_survivor_status": {
      "NO_EVENTS_IN_LAYER": "该层事件总数=0",
      "UNESTIMABLE_BY_FROZEN_COVERAGE": "有事件、零存活,剔因全属冻结覆盖/历史门槛",
      "UNESTIMABLE_AFTER_FROZEN_CLEANING": "零存活由清洗/顺延超限或多因混合造成;附逐因逐年剔除分解"
    }
  },
  "window": "〔待人拍 §3-4:主窗/次级窗/稳健窗及选择依据须独立成立,不得引exp8的5/20/60为既裁先例〕",
  "pool": { "universe": "〔待人拍 §3-5:研究池未冻结〕", "source": "qbase explore_reader_forecast(_snap)〔适配阶段按§5白名单先例新建视图对,holdout焊死〕+ explore_reader_prices(_snap) + explore_reader_listing(_snap) + explore_reader_calendar(_snap)" },
  "benchmark": "〔待人拍 §3-5:基准口径未冻结;与pool同批裁定〕",
  "cleaning": "A股清洗(spec §5 冻结口径为默认基线):估计期=事件日前250至前91交易日(160日),窗内有效交易日<112(70%)剔;停牌=轴内缺bar或flag。事件日T须为真实交易行,T缺行/停牌→fail-closed剔除event_day_anomaly单独留痕。τ0=自T+1起首个可交易日,顺延政策=〔待人拍 §3-8〕。ST处置=〔待人拍 §3-7〕。CAR轴起点=T+1(既裁:事件轴自公告日后T+1开始)",
  "cost": { "commission": 0.00025, "stamp_tax_sell": 0.001, "slippage_oneway": 0.001, "limit_up_board_untradeable": true },
  "verdict_authority": "唯一判决=顶层主窗ADJ-BMP(对signed事件集);辅助方法(朴素t/Corrado秩/日历时间法)反向或反显著不得改变判决,分歧只入verdict_note如实报告;主窗字段级角色元数据field_roles:adj_bmp_car=VERDICT_AUTHORITY,其余统计=NOT_FOR_VERDICT,taus/n=CONTEXT,未分类新字段fail-closed;次级窗/稳健窗/direction诊断轴均为结构化NOT_FOR_VERDICT报告项。单侧/双侧门槛及显著反向verdict对应规则=〔待人拍 §3-1/§3-2;硬约束:不得把统计显著但方向相反解读为支持原假设〕",
  "bias_statement": "大量不可判与fail-closed剔除造成样本选择,偏差方向未知;估计对象仅限2013年后可形成合法修正链且数值可判的存活样本,不得外推为全体业绩预告修正事件的效应。",
  "verdict_power_note": "exp20=llm/prescreen效力,不得写成full证据(既裁重申);报告强制水印(铁律①)",
  "engine_params": "〔草案参数语义,终名以适配阶段实现+fixture为准:benchmark_mode=§3-5/diagnostic_dims=[direction]/direction_signed_main=true/direction_display=raw(§3-6)/nfv_structured=true/postpone_policy=§3-8/st_policy=§3-7/strata_enabled=false/verdict_policy=§3-1;driver施工时逐字消费,不留运行时选择;偏差声明唯一权威=本PAP bias_statement键〕",
  "sample_gate": 30,
  "holdout": { "holdout_start": "2024-07-01", "once_per_hypothesis": true, "use_requires_human_approval": true },
  "pap_digest_binding": "沿exp8 v3先例逐字:canonical串=实质键(顶层剔除_前缀运行时键)词典序+紧凑分隔符+UTF-8序列化;digest=sha256(canonical串+末尾单换行)=冻结PAP文件SHA256=引擎重算唯一权威;调用方digest只作逐字断言fail-closed;result记绑定三元组{pap_sha256,key='bias_statement',text原文};报告来源锚直接显示实际digest",
  "snapshot_batch_req": "result须记StudySnapshot manifest ID+digest(硬化②);manifest于冻结后另行生成;source=qbase forecast_snap+daily/adj_factor/stock_basic/namechange/trade_cal(+基准侧taosha派生批,视§3-5裁定),全部经StudySnapshot manifest路由",
  "reporting_commitments": "①正式n_events_total与窄闸参考数(12,569/5,225)逐层对账,差异逐因归因入audit;②剔除分解逐年逐因;fail-closed六类(孤儿/时序违例/多链归属/数值不可判/同日方向冲突/600856.SH)逐类计数、600856.SH单独留痕;③flat事件计数报告(不入方向判决不入主样本);④direction轴逐层报告事件数/存活数/逐因逐年剔除/raw CAAR/raw ADJ-BMP,零存活层按真实原因命名且块必须在场;⑤事件年度分布及聚集折算N(ρ̄→N_eff)如实报告不调参;⑥报告直接消费本PAP bias_statement并渲染来源锚;禁则清单四项沿P1-4先例fixture零命中验收"
}
```

## 2. 逐项裁决映射(人令条款 → 草案落点)

| # | 人令条款 | 草案落点 | 备注 |
|---|---------|---------|------|
| 一.1 | 方案1 signed AR,up=+1/down=−1,事件级逐τ | `signed_ar.formula` | 逐字 |
| 一.2 | 符号变换先于AAR/CAAR/BMP/ADJ-BMP聚合与检验 | `signed_ar.application_level` | 禁只改展示值,逐字 |
| 一.3 | 正/负signed效应语义 | `signed_ar.estimand` | 逐字 |
| 一.4 | 单一主窗ADJ-BMP顶层verdict,不分拆α | `signed_ar.single_verdict` | 逐字 |
| 一.5 | 单双侧+显著反向解释=待人确认,不得静默决定 | `verdict_authority`〔待拍§3-1/2〕 | 硬约束"显著反向≠支持原假设"已写入 |
| 二.1 | up/down白名单+空值/flat/unknown进CAR前fail-closed | `diagnostic_dimensions.direction_fail_closed` | 沿exp8 listing_age_fail_closed结构 |
| 二.2 | 可报告数值集(事件数/存活/逐因逐年/raw CAAR/ADJ-BMP) | `reporting_commitments`④+`display_basis` | |
| 二.3 | raw vs signed展示须明确;人建议raw | `display_basis`=raw〔确认§3-6〕 | 草案按人建议取raw |
| 二.4 | 诊断层零verdict/零显著性分类/不调判决函数/不改顶层 | `diagnostic_dimensions.note` | 攻击fixture在适配阶段验收 |
| 二.5 | 不引入双检验/多重比较/总判决 | `diagnostic_dimensions.note`+`signed_ar.single_verdict` | |
| 三.1 | 基准B=事件日前最近一次公开披露 | `event_def` | |
| 三.2 | 链键/事件键 | `event_def` | |
| 三.3 | 同日重复仅L2折叠,L1不动 | `event_def` | |
| 三.4 | fail-closed五类+600856.SH | `event_def` fail-closed全集+`reporting_commitments`② | |
| 三.5 | 不用type回退/flat仅计数/无幅度门 | `event_def` | |
| 三.6 | 研究期2013-01-01≤ann_date<2024-07-01,T+1起轴 | `event_def`+`cleaning` | |
| 三.7 | 效力llm/prescreen不得写full | `verdict_power_note` | 台账行已核=llm/prescreen |
| 四 | 12,569/5,225仅对账参考,正式数量重新确定+逐层对账 | `event_def`末句+`reporting_commitments`① | 不预写进结果 |
| 五 | bias statement人给定内容 | `bias_statement` | 照令转写 |
| 五 | digest绑定/sample_gate/StudySnapshot/报告承诺 | `pap_digest_binding`/`sample_gate`/`snapshot_batch_req`/`reporting_commitments` | 沿exp8 v3先例 |
| 六 | 本单元零码零跑零冻结 | 本档头部声明 | 已遵守 |

## 3. 待人拍参数清单(冻结前必须逐项人拍,施工侧不代决)

1. **主检验单侧 or 双侧**。甲=双侧(既有引擎门槛,α=0.05族内递减)——signed框架下双侧同时覆盖"沿方向显著"与"逆方向显著"两种可判读结果;乙=单侧(正向)——检验目标更贴"沿修正方向反应"的原假设,但逆向大效应只能落NOT_SIG。**推荐甲**(与既有引擎一致,零新统计机构,且逆向显著是高信息量证伪读数)。
2. **ADJ-BMP过阈但signed效应为负时的顶层verdict对应**(与第1项联动)。甲(配双侧)=verdict三态:SIG_ALIGNED(显著且signed为正=支持方向假设)/SIG_REVERSED(显著且signed为负=证伪且逆向,明文不得写作支持)/NOT_SIG;乙(配单侧)=二态SIG/NOT_SIG,逆向信息只入verdict_note+NFV。**推荐甲**;无论哪案,"显著但方向相反≠支持原假设"按令写死在verdict_authority。
3. **方向判定字段与比较规则**(基准B之"数值",决定up/down/flat/不可判)。甲=net_profit_min/max区间中点比较(当前vs基准;中点差>0=up/<0=down/=0=flat;两字段全缺=不可判fail-closed);乙=区间分离序(min_new>max_old=up/max_new<min_old=down/区间重叠=不可判)——更保守但预计大量重叠不可判;丙=p_change_min/max中点。**推荐甲**;⚠留痕:07-17窄闸产出5,225的实现脚本未持久归档,人拍定规则后按§4对账,与5,225的差异逐层归因,对不上即停报人。
4. **exp20自身三窗及依据**(不得引exp8 5/20/60为先例)。甲=主[0,+4]/次级[0,+19]/稳健[0,+59]——依据:修正公告属点状信息事件,主检验聚焦披露后一周内即时定价最干净;盈余漂移(PEAD式延续)属延伸观察,归次级/稳健NFV窗;乙=主[0,+9]/次级[0,+29]/稳健[0,+59]——依据:修正多披露于盘后且业绩期公告密集,吸收或更慢。**推荐甲**(主窗越短离多重比较与混杂越远;数值上与exp8重合系独立依据下的巧合,冻结文本写自身依据)。
5. **研究池与基准口径**(当前未冻结)。甲=全A排北交所+全市场等权基准(benchmark_mode=market;先例=exp4/exp8均market单跑,taosha market_eqw_return派生批现成,pool对exp20无冻结定义);乙=雷达股池等权(pool_b1)——池口径对本假设无既裁定义,采用即须另行冻结适用性论证。**推荐甲**。
6. **direction诊断层展示口径确认**:人令建议raw AR,草案已按raw落键——请终确认(raw保留上修/下修实际方向与强度;signed数值仅在主检验)。
7. **ST处置**:甲=spec§5默认剔除(st_policy=reject;exp8之keep系该实验单点例外,不自动继承);乙=保留+ST诊断轴(需另加轴)。**推荐甲**(回归默认,少一条例外)。
8. **τ0顺延政策**:甲=unified(T+1起停牌/一字板统一顺延计数,≤5保留、6日剔除;exp8 C1回修后口径,更精细);乙=legacy(既有默认路径)。**推荐甲**,但exp8的unified系该实验裁定,对exp20采用须人明示。
9. **同日多链同方向折叠为单事件**:事件键=(ts_code,ann_date)唯一+同日方向冲突fail-closed为既裁;同日多链**同方向**折叠为一事件是其自然推论,草案已如此写——请确认(否则该情形需另裁)。
10. **估计窗/覆盖门槛/sample_gate沿spec§5默认**(250~91/160日/112门/gate30):草案按默认基线落键——如对修正公告场景需调整请明示,否则视为沿用。

## 4. 后续顺序(令六固定,照录)

PAP草案交人复核 → 人批准最终PAP并在冻结句内嵌预判 → 最小适配器与攻击fixture(含explore_reader_forecast视图对新建+§3-3规则实现与5,225对账+signed路径与direction fail-closed攻击测试) → StudySnapshot绑定 → 单次正式运行 → 取证 → 外审 → persist。
