# 切片3 · 步3 验收:全市场等权日收益预计算落库(2026-07-08)

**结论:通过。** taosha L2 落 `market_batch`#1 + `market_eqw_return` **8186 行**,双算闸机器精度、
holdout 硬闸过、append-only 防拆对属主亦生效。这是切片3 真实库接入的第一块(步3),供步4 ViewReader /
步7 #4 全市场假设读取全市场等权基准(regressor)。

## 1. 交付物
- 迁移 `taosha/sql/002_market_return.sql`(commit `98df86d`/`e843a55`,postgres 属主 apply):
  - `market_batch`(溯源:source/hypothesis/compounding/frozen_digest/holdout/view_rows/out_rows/min·max_date/pull_time/note)
  - `market_eqw_return(batch_id, trade_date, ret_eqw, n_stocks)`(口径写死表/列注释)
  - append-only 触发器 `_freeze_appendonly`(UPDATE/DELETE 一律 RAISE)
  - `market_return_current` 视图(路由 max batch,引擎读表不现算)
  - 授权只收不扩:`taosha_app` INSERT/SELECT;`taosha_engine` SELECT(读基准,步4 消费)
- 预算件 `taosha/ingest/seed_market_return.py`:读 qbase 视图、复用冻结 `compute/returns.py`、双算闸、硬闸、落库。

## 2. 口径(与 002 表注逐字对应,骗不了人)
- **ret_eqw[d] = 全市场等权【连续/对数】日收益** = 当日【有 present bar 且有前序 present bar】的票,
  其 `log(后复权 close_d / close_前序present)` 的**简单等权平均**。收益核 = 冻结 `returns.py`
  `log_rates_from_prices(Close, multi_day)`(estudy2 `rates.cpp` 复刻);视图无 null 价行(停牌=缺行),
  故"相邻 present 行比值"恒等于 multi_day 跨缺口收益——恢复日拿 catch-up 收益、落恢复日。
- **n_stocks[d](诊断列)= 分母** = 上述参与票数;停牌缺行不进分母;IPO 首个 bar 无前序价不进;
  早年薄截面照算不修(此列作诊断)。
- **轴 = explore_reader_calendar(SSE 交易日,约束②)**:源 = `explore_reader_prices ∩ explore_reader_calendar`。
  基准按定义 = 每 SSE 交易日等权收益,须落日历轴(= 引擎消费轴 = 约束② 轴)。
- **宇宙 = 沪深**(北交所 .BJ 已在 qbase 视图层排除,本表继承);**holdout = trade_date < 2024-07-01**(视图 WHERE 焊死,继承)。
- **冻结口径指纹**:`frozen_config.audit_digest()` = `b88a43ef7bd8…`(落 batch.frozen_digest,固定"跑的是哪套冻结口径")。

## 3. off-calendar 数据发现(诚实归因,已处置)
--dry 揭露:`explore_reader_prices` 有 **8189** 个 distinct 交易日,而 `explore_reader_calendar` 只有 **8187**。
多出 **2 天 = 1992-10-04 与 1993-01-03**(共 **3 个主板 bar / 3 只票**)。核 SSE `trade_cal_snap`:
两日 **is_open=0(周日)**——早年 tushare 日线里的非交易日 bar 噪声,官方日历正确排除。
- **处置**:市场基准落日历轴(源 ∩ calendar),结构性剔除这 3 个 off-calendar bar(batch.note 记 `off-calendar剔除=3`);
  受影响票的收益自然跨到前一日历交易日(returns.py 跨缺口)。**这是对已冻结约束②日历轴的实现,非新造口径。**
- **量级**:两日均在 1992–93,早 holdout(2024)/业绩预告事件三十年,对任何真实研究影响 = 零。
- **登记**:qbase 侧"日线含非交易日 bar"属数据质量携带项(与约束②相关),供步4/步7 及 qbase caveats 参考。

## 4. 双算闸(骗不了人:两独立实现须吻合)
- Python(冻结 `returns.py` 逐票聚合)= 落库权威;SQL 窗口 `avg(ln(close/lag(close)))`(镜像同一日历轴 JOIN)独立复算。
- 结果:**`max|Δret| = 6.523e-16`(机器精度)**,**`n_stocks` 不一致 = 0 天**。不过即中止不落库(本次过)。

## 5. 硬闸(holdout 泄漏防护)
- `max(trade_date) = 2024-06-28 < 2024-07-01`(holdout)✓
- `out_rows = 8186` = 8187 日历交易日 − 1(首日 1990-12-19 全为首 bar 无前序,无收益)✓
  **绝非全日历 8797**(8797 = 1990→2026 全交易日;若落 8797 = holdout 泄漏事故)。
- 视图 raw=15,099,014 / 日历轴 input=15,099,011(off-calendar 剔除=3),范围 1990-12-19..2024-06-28。

## 6. append-only 防拆实测(属主 postgres 身份,触发器须对所有人含属主生效)
| 操作 | 结果 |
|---|---|
| `UPDATE market_eqw_return` | 被拒 ✓(`禁 UPDATE`)|
| `DELETE market_eqw_return` | 被拒 ✓(`禁 DELETE`)|
| `UPDATE market_batch` | 被拒 ✓ |
| `DELETE market_batch` | 被拒 ✓ |
| 防拆后行数 | data=8186 / batch=1 不变 ✓ |

## 7. 诊断:n_stocks 年度分布 + ret_eqw 抽样
| 年 | 天数 | avg n_stocks | min | max |
|---|---|---|---|---|
|1990| 8 | 4 | 1 | 5 |
|1991| 255 | 10 | 3 | 13 |
|2000| 239 | 963 | 875 | 1040 |
|2015| 244 | 2334 | 1339 | 2535 |
|2024| 117 | 5098 | 5052 | 5114 |

早年薄截面(1990 单日最少 1 只)、逐年增至满市场 ~5100。ret_eqw 抽样:1990-12-20=+0.0489(n=3,早年小样噪声)/
2015-06-15=−0.0193(n=2314)/2024-06-28=+0.0043(n=5088),量级 ±0.0x,合理。

## 8. 剩余(切片3 真实库接入)
- **步4**:建 `reader/view.py` ViewReader(读 explore_reader 三视图 + market_return_current,role `taosha_engine`,
  DSN 配 aliyun `.env` 600 不进 git,已预批);权限只收不扩。
- **步7**:跑 #4 market 单跑 = 第一份真实体检报告。

落库身份:读 `QBASE_APP_DSN`(视图 holdout/.BJ/后复权 结构性保证,与账号无关);写 `TAOSHA_APP_DSN`(只 INSERT)。
运行:aliyun `/opt/venvs/qbase-ingest/bin/python -m taosha.ingest.seed_market_return`(PYTHONPATH=/opt/quant)。
