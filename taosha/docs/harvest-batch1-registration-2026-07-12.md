# 收割会首批登记档(2026-07-12)

> 人令原文留痕 + 台账落库回执。9 条假设入台账 `status=registered`(不冻结、不排产、不占引擎;
> PAP 细化与冻结在各自排产时另行)。执行=单连接单事务一次 COMMIT,`ledger.register` 既有通路。

## 1. 人令原文(逐字)

> 收割会首批登记令(2026-07-12 首次会产出,人已筛全收)
> 9 条假设入台账,状态=registered(不冻结、不排产、不占引擎;PAP 细化与冻结在各自排产时另行)。共同字段:source=llm / verdict_power=prescreen / data_class=量价 / 数据盲声明="出题仅依据制度事实与文献机制,未接触任何相关回测或收益数据"(入各条 contamination_note)。逐条:
>
> limit_open · 连续一字涨停(N 板,N≥2,参数待冻结)后首个非一字交易日=事件。方向:人未定(冻结时随密封定)。crowding=高。对偶:limit_down_open。
> suspension_return · 停牌 ≥20 交易日后复牌日=事件。方向:复牌短窗与停牌期间行业指数变动同向补价。crowding=高。注:2018 停复牌改革为 regime 边界,检验时分层。
> volume_drought_break · 成交额缩至自身 60 日均值 30% 以下持续 ≥5 日后,首个放量(>60 日均值)且收阳日=事件(阈值 30%/5 日/放量倍数标注待冻结)。方向:正。crowding=高。
> high_pullback · 创 250 日新高后 10 日内回落 3–5% 且未破 20 日线,条件齐备日=事件(参数待冻结)。方向:正。crowding=高。注:与 drawdown_rebuy 机制方向相反、不同 family,登记注明非同族依据。
> st_removal · 撤销 ST/风险警示公告日=事件。方向:正。crowding=中低。对偶:st_imposition。数据:is_st PIT 现成。
> limit_down_open · 连续一字跌停(N≥2,待冻结)后首个非一字日=事件。方向:人未定。crowding=低。对偶:limit_open。
> ex_div_gap · 高送转除权日(送转合计 ≥0.5,待冻结)=事件。方向:正(名义价格幻觉)。crowding=中。注:高送转监管各轮收紧为 regime 分层维度。
> st_imposition · 被实施 ST/风险警示公告日=事件。方向:负(制度性强制卖压)。crowding=低。对偶:st_removal。
> yearend_strength · 12 月末 10 个交易日跑赢全市场等权 ≥5% 之票,次年 1 月首个交易日=事件(阈值待冻结)。方向:人未定。
>
> 登记要件:"待冻结"参数在事件定义文本内显式标注不静默取值;对偶关系写入双方注记;9 条均标全市场口径。回执:行数+台账健康看板(总数应为 16/50、全市场族数、五类分布)。

## 2. 登记稿口径(工程侧,骗不了人)

- `event_def` = 人令逐字(含"待冻结"显式标注,不静默取值);`direction`/对偶(`dual`)/regime 注记/
  非同族依据(`family_note`)/数据注记(`data_note`)照原文入 pap_json 对应键(对偶双方均写)。
- pap 必备 8 键中 `window`/`cost`/`cleaning`/`snapshot_batch_req` = **显式"待冻结(排产时…)"占位**,
  不预取任何数值;`pool.universe`=全市场、`benchmark.market_hypothesis`=全市场等权(登记令"9 条均标
  全市场口径")、`holdout`=平台结构块(2024-07-01,动用须人批)。
- 共同字段照令:source_type=llm(触发器强制 verdict_power=prescreen)/ data_class=量价 /
  contamination_note=数据盲声明原文 + 收割会来源注记;crowding_prior 逐条照令。

## 3. 落库回执(库查实物,2026-07-12)

| exp_id | family#trial | title | crowding | 对偶/注记 |
|---|---|---|---|---|
| 8 | limit_open#1 | 连续一字涨停开板 | 高 | 对偶 limit_down_open |
| 9 | suspension_return#1 | 长期停牌复牌 | 高 | 2018 停复牌改革 regime 分层 |
| 10 | volume_drought_break#1 | 缩量干涸后放量收阳 | 高 | — |
| 11 | high_pullback#1 | 250日新高后小幅回落不破20日线 | 高 | 非 drawdown_rebuy 同族(机制方向相反) |
| 12 | st_removal#1 | 撤销ST/风险警示 | 中低 | 对偶 st_imposition;is_st PIT 现成 |
| 13 | limit_down_open#1 | 连续一字跌停开板 | 低 | 对偶 limit_open |
| 14 | ex_div_gap#1 | 高送转除权 | 中 | 高送转监管收紧 regime 分层 |
| 15 | st_imposition#1 | 实施ST/风险警示 | 低 | 对偶 st_removal |
| 16 | yearend_strength#1 | 12月末强势股次年1月首日 | 中 | — |

全部 `status=registered` / `family_trial=1` / `verdict_power=prescreen`(触发器放行确认)。

## 4. 台账健康看板

- **总行数 = 16**(令载 16/50 之 16;50=令中预算基数,台账无此字段,原样回执)。
- **状态五类分布**(状态机五态):registered **9** / frozen **3**(radar_heat#1、holder_sell#1、
  rv_resonance#1)/ running **0** / done **3**(exp3 #2b、exp5 #4、exp7 SMOKE)/ closed **1**(exp2)。
- **distinct family = 15**(drawdown_rebuy 一族两行 trial1/2)。
- **全市场口径族**:字符串匹配 `pap.pool.universe 含"全市场"` 命中 13 族,其中 synthetic_smoke 为
  合成域非真实假设 → **真实假设全市场口径族 = 12**(新 9 + drawdown_rebuy〔trial2 b1 全市场流动性池〕
  + holder_sell + forecast_drift〔全A股〕)。非全市场:radar_heat(雷达信号覆盖股池)、
  rv_resonance(观象全池);drawdown_rebuy trial1(closed)为雷达股池旧版。
- **新 9 条 crowding 分布**:高 4 / 中 2 / 中低 1 / 低 2。

## 5. 状态

登记完成即待命(下一条假设单暂缓,等:①#3 采集收敛后数据验收;②检验排产由人在收割会后拍)。
#3 采集守护照守。
