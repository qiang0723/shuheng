# 收割会第二轮登记档(2026-07-12,财务类轮巡 + human 题 2 条)

> 人令原文留痕 + 台账落库回执。9 条入台账 `status=registered`(不冻结、不排产、不占引擎;
> PAP 细化与冻结在各自排产时另行)。执行=单连接单事务一次 COMMIT,`ledger.register` 既有通路
> + exp15 对偶注记回写(registered 态 pap 未冻结,触发器放行)。

## 1. 人令原文(逐字)

> 收割会第二轮登记令(2026-07-12,财务类轮巡+human 题 2 条,人已筛全收)
> 9 条假设入台账,状态=registered(不冻结、不排产、不占引擎)。登记要件同首批:待冻结参数在 event_def 文本内显式标注不静默取值;数据盲声明入各条 contamination_note;财务类统一约束写进每条 event_def:事件日锚=实际披露日(f_ann_date/公告日),绝不用报告期末 end_date。
> LLM 题 7 条(source=llm / verdict_power=prescreen / data_class=财务 / 数据盲声明="出题仅依据制度事实与文献机制,未接触任何相关回测或收益数据"):
>
> earnings_flash_gap · 已发业绩预告的公司,业绩快报披露日实际数对预告区间的偏离(超上沿/落下沿,分层)=事件。方向:同偏离方向。crowding=低。注:与 forecast_drift 不同族——彼测预告日,此测快报日的修正增量。
> audit_qualified · 年报被出具非标审计意见(保留/无法表示/否定)公告日=事件。方向:负。crowding=低。
> dividend_surprise · 年度每股分红较上年变动 ≥50%(阈值待冻结,增/减分层)的预案公告日=事件。方向:增正减负。crowding=中。
> earnings_revision · 对已发业绩预告再发修正公告=事件(修正方向分层)。方向:同修正方向。crowding=低。注:数据零备货——forecast_snap 中 first_ann_date≠ann_date 行即样本源。
> goodwill_impair · 年报/预告首次披露大额商誉减值(减值额/净资产 ≥5%,待冻结)=事件。方向:人未定(短窗负/中窗"出清"存疑)。crowding=中。
> delist_warning_financial · 因连续亏损/净资产为负被实施退市风险警示公告日=事件。方向:负。crowding=低。注:与 st_imposition 对偶,族关系待架构窗口排产时终核。
> buyback_announce · 股份回购预案公告日=事件(注销式/库存式分层)。方向:正。crowding=中高。
>
> human 题 2 条(source=human,足额判决效力路径):
>
> sox_spillover · 美股费城半导体指数(SOX)单日涨跌幅 ≥±3% → 次日 A 股半导体链=事件,方向:同向。data_class=宏观/跨市场。注:数据前置=美股指数日线最小采集件(KB 级,不建美股腿),排产时触发,登记不阻塞。
> preannounced_exhaustion · 强预喜(预增且幅度上沿 ≥50%,待冻结)且公告前 20 日相对行业指数超额 ≥10%(待冻结)=条件事件;检验形态=预跑组 vs 未预跑组的公告后反应差(短窗 0,+5 与中窗 0,+20)。方向:条件层负(预跑组弱于未预跑组)。data_class=财务×量价交叉。观察来源:2026-07 中报预期季人的盘面目击(数据盲,非回测),入 contamination_note。族关系(forecast_drift 条件变体 vs 独立 family)排产时架构窗口终核。
>
> 回执要求:登记行数 + 台账健康看板(总数应为 25/50、全市场族数、五类分布更新、轮巡指针→分析师预期〔下周,该类前置=时间戳口径核查:修正时点是否=研报发布日,口径不明不登记〕)。

## 2. 登记稿口径(工程侧)

- **财务锚约束附着范围**:统一约束句逐字附入 7 条财务 event_def 及 preannounced_exhaustion
  (事件=公告条件,锚适用);**sox_spillover 不附**(事件锚=美股指数日→次日,无披露日概念,
  约束不适用——工程判断,登记于此)。
- **human 2 条 crowding_prior 登记令未载 → 人补拍(2026-07-12)**:sox_spillover=**高**、
  preannounced_exhaustion=**中**(pap 内 crowding_note 留痕)。
- 对偶回写:exp15 st_imposition pap.dual 追加 delist_warning_financial(族关系待架构窗口
  排产时终核);registered 态 pap 未冻结,UPDATE 触发器放行。
- 其余同首批:必备键显式"待冻结"占位不静默取值;第二轮**未标全市场口径**(与首批不同),
  pool=待冻结(sox 例外:A股半导体链,事件定义载);preannounced 的 window 载登记令检验形态
  原文(短窗 0,+5 与中窗 0,+20,冻结时定稿)。

## 3. 落库回执(库查实物,2026-07-12)

| exp_id | family#trial | source/data_class | vp | crowding | 注记 |
|---|---|---|---|---|---|
| 17 | earnings_flash_gap#1 | llm/财务 | prescreen | 低 | 非 forecast_drift 同族(快报修正增量) |
| 18 | audit_qualified#1 | llm/财务 | prescreen | 低 | — |
| 19 | dividend_surprise#1 | llm/财务 | prescreen | 中 | 增/减分层 |
| 20 | earnings_revision#1 | llm/财务 | prescreen | 低 | 数据零备货(forecast_snap first_ann≠ann) |
| 21 | goodwill_impair#1 | llm/财务 | prescreen | 中 | 方向人未定 |
| 22 | delist_warning_financial#1 | llm/财务 | prescreen | 低 | 对偶 st_imposition(族关系排产终核) |
| 23 | buyback_announce#1 | llm/财务 | prescreen | 中高 | 注销式/库存式分层 |
| 24 | sox_spillover#1 | human/宏观/跨市场 | **full** | 高(人拍) | 数据前置=美股指数日线最小采集件,排产时触发 |
| 25 | preannounced_exhaustion#1 | human/财务×量价交叉 | **full** | 中(人拍) | 盘面目击来源入 contamination_note;族关系排产终核 |

全部 `status=registered` / `family_trial=1`;exp15 pap.dual 已回写双向对偶。

## 4. 台账健康看板(更新)

- **总行数 = 25**(令载 25/50 之 25;50=预算基数原样回执)。
- **状态五类分布**:registered **18** / frozen **3** / running **0** / done **3** / closed **1**。
- **distinct family = 24**(drawdown_rebuy 一族两行)。
- **全市场口径族**:仍 **12**(首批 9 + drawdown_rebuy trial2 + holder_sell + forecast_drift)——
  第二轮 9 条登记令未标全市场口径,pool 待冻结不计入(sox=半导体链)。
- **data_class 分布**:量价 10 / 财务 7 / 宏观跨市场 1 / 财务×量价交叉 1 / synthetic 1 / NULL 5
  (创始存量,裁3 豁免不回填)。source 分布:llm 17 / human 4 / platform 2 / literature 2。
- **轮巡指针 → 分析师预期(下周)**:该类前置=**时间戳口径核查(修正时点是否=研报发布日;
  口径不明不登记)**——登记在案,届时先核后登。

## 5. 状态

登记完成继续待命(下一假设单仍按既定两前置:①#3 采集收敛验收 ②收割会后人拍排产)。
#3 采集守护照守。
