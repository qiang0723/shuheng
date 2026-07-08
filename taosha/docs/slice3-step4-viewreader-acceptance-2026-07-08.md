# 切片3 · 步4 验收:真实 ViewReader + 引擎接线(2026-07-08)

**结论:通过。** 建成 `reader/view.py` ViewReader(契约实现之二,role `taosha_engine` 只读物理隔离),
runner 两接缝(calendar 轴 + 读市场基准表)对合成域**逐字节零回归**,引擎身份三组断言(越权/holdout/.BJ)
全绿。ViewReader 站在焊死的地上,供步7 跑 #4 第一份真实体检报告。

## 1. 交付物
- `reader/view.py`:ViewReader(prices/prices_by_security/events/calendar/market_return),同 SyntheticReader 签名。
- `engine/runner.py` 两接缝(人批 2026-07-08,STATE 线80 授权;约束③ 逐字节零回归证明)。
- taosha_engine DSN 配置(aliyun `.env` 600,不进 git)。commit `6a04af6`(ViewReader+接缝)。

## 2. 步4-A:taosha_engine DSN 配置(操作报告,密钥不现身)
- 服务器端(aliyun):`openssl rand -hex 24` 生成密码(URL 安全)→ `ALTER ROLE taosha_engine PASSWORD`
  (scram-sha-256 哈希存储)→ 追加 `TAOSHA_ENGINE_QBASE_DSN`(dbname=qbase)+ `TAOSHA_ENGINE_TAOSHA_DSN`
  (dbname=taosha)入 `/opt/quant/.env`。**密码全程走 shell 变量,未打进对话/代码/git**(秘钥纪律)。
- `.env` 权限 600 root:root、gitignored(git check-ignore 命中、未跟踪)。auth=pg_hba `host 127.0.0.1 scram-sha-256`。

## 3. 步4-B:引擎身份三组断言(以 taosha_engine,非 DBA;ViewReader 站焊死地上的前提)
| 组 | 断言 | 结果 |
|---|---|---|
| Group1 越权 | 直查 qbase 底表 bar_daily_snap/adj_factor_snap/trade_cal_snap/forecast_snap/entity_master/entity_alias | **6 底表全 permission denied** ✓ |
| Group2 holdout 泄漏 | 三视图 trade_date/first_ann_date ≥ 2024-07-01 | prices/calendar/events 全 **0** ✓ |
| Group3 .BJ 排除 | prices/events `ts_code ~ '\.BJ$'` | 全 **0** ✓ |
| Group4 taosha 侧 | market_eqw_return/market_return_current 可读(8186);experiment/market_batch | 市场基准可读 ✓;experiment+market_batch **denied** ✓(最小权,engine 不见批溯源)|

登录可用(current_user=taosha_engine @ qbase 与 taosha)。**此前为 DBA 侧验,本次为引擎身份实测。**

## 4. 步4-C:ViewReader 设计与真库冒烟
- **数据源**:qbase `explore_reader` 三视图(role taosha_engine)+ taosha `market_return_current`。
- **事件票取数(非全宇宙)**:先读 events 定样本 ts_code,再按样本 `WHERE ts_code = ANY(...)` 拉 prices(不载全 15M)。
- **轴 ∩ explore_reader_calendar(约束② + 个股侧 standing 裁定 2026-07-08)**:prices JOIN calendar——bar 落非交易日
  结构性剔除、收益跨到前一日历交易日(returns.py 跨缺口)。
- **纵深防御**:holdout/.BJ/后复权 由视图定义结构性保证;reader 侧 `contract.enforce_*` 再挡一道。
- **真库冒烟(aliyun)**:events=105584 / 样本证券=**5356** / calendar=8187日(1990-12-19..2024-06-28)/
  market 非空=**8186**(=日历−1,首日 None)。小样本 prices_by_security(000001.SZ 7897行/银行、
  600519.SH 5466行/白酒、000004.SZ 7752行):全部升序、holdout(<2024-07-01)、落日历日(∩calendar 生效)、
  close 正 float、is_suspended 全 False(视图只出真实 bar)。全断言过。

## 5. runner 两接缝 + 约束③ 逐字节零回归(安全证明)
| 接缝 | 改动 | 合成域 | 真实域 |
|---|---|---|---|
| ① 轴 | `all_dates = [c.trade_date for c in reader.calendar()]`(替 `sorted({by_sec union})`)| SyntheticReader.calendar()=by_sec 并集 → all_dates 逐一致 | explore_reader_calendar 8187 日历日(约束②:缺行=停牌须在完整日历轴数)|
| ② 市场基准 | market 模式:`reader.market_return()` 若有则读表,否则 `equal_weight_market`(现算)| SyntheticReader 无 market_return → 现算(路径不变)| ViewReader 读 market_return_current(引擎读表不现算)|

**证明**:合成端到端 `run_ashare_study` result_json **sha256 前后完全相同**(`ba52959400b5…`)——两接缝对合成域零影响。

## 6. 真实数据携带项(登记,供步7;不阻塞步4)
- **industry='nan'**:如 000004.SZ,industry 字段为字面串 `'nan'`(entity_master 快照 NaN 串化)。口径④ ρ̄ 行业分组会出一个 'nan' 桶;属口径④"行业非 PIT、二阶影响"携带项延伸,步7 报告注记。
- **clean_event 空价行崩风险**:runner `clean_event` 首行取 `rows[0]`,对"有 forecast 事件但无价行"的票会 IndexError。真实 #4 全样本(5356 票,events()=105584 全事件)跑前需**硬化(空 rows 前置剔除为 no_price)或事件↔样本一致性过滤**。步7 开跑前处置,登记为步7 前置。

## 7. 剩余:步7(第一份真实体检报告)
- 跑 #4 market 单跑:ViewReader() 默认(sample=全事件票)→ runner.run_study(benchmark_mode='market')→ report。
- 前置:①处置 §6 clean_event 空价行风险;②#4 的 pap 冻结登记(台账 experiment,#4 业绩预告);③规模(全事件票 prices ~千万行加载)评估。
- 引擎读全市场等权基准=步3 market_return_current(读表不现算)。
