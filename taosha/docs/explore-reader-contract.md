# 《explore_reader 列契约(淘沙侧要求)》(切片2 定,供 Q3 零改造照建)

> 状态:淘沙引擎(切片2)对 qbase `explore_reader` 视图族的**列级接口契约**。
> 由来:spec v0.2 只钉了 `explore_reader = 唯一数据入口、holdout 焊 WHERE`,**未给列级定义**——
> 那视图是 Q3 交付的真身。切片2 reader 必须"按契约写死、Q3 零改造接入"(开工令②),
> 故此处**先定契约、Q3 照建**。改判须走配置审计(与 STATE `S2-DEC3` 邻,item 10 纪律)。
> 本契约=**接口形状**;切片2 用 `SyntheticReader` 对合成 fixture 满足同一形状,不建 mock 视图。

## 0. 铁则(结构性,不靠自觉)

- **holdout 物理隔离**:两视图 WHERE 均焊 `trade_date < '2024-07-01'`(`first_ann_date < '2024-07-01'`)。
  探索代码结构上**拿不到** holdout 区数据(taosha CLAUDE.md 铁律②;holdout 动用须人批、走另路)。
- **禁零填充**:停牌/无交易日 `close` 置 **NULL**(NA),视图不得以 0 或前值填充(item 5;NA 语义下沉到 returns.py)。
- **只读**:reader 账号仅 SELECT;唯一写入对象=淘沙台账(边界铁则)。

## 1. `explore_reader_prices`(逐 [证券 × 交易日] 价格与市场微结构)

| 列 | 类型 | 语义 | 消费方 |
|---|---|---|---|
| `ts_code` | text | 证券唯一键(entity_master.ts_code) | 分组键 |
| `trade_date` | date | 交易日(仅 `< 2024-07-01`) | 对齐轴 |
| `close` | numeric NULL | 收盘价;**停牌/无交易=NULL**(禁零填充) | returns.py 对数收益 |
| `is_suspended` | bool | 该日停牌(item 7 事件落停牌期剔除依据) | cleaning 停牌剔除 |
| `limit_status` | text | `none`/`limit_up`/`limit_down`/`one_word`(一字板);A股清洗一字板标注+顺延 | cleaning 涨跌停/一字板 |
| `board` | text | `main`(主板)/`chinext`(创业板)/`star`(科创板)/`bse`(北交所) | item 8 板块分层 |
| `is_st` | bool | 当日 ST/*ST(spec §5:ST 剔除) | cleaning ST 剔除 |
| `industry` | text | tushare industry(口径④ ρ̄ 行业分组键) | abnormal_tests ρ̄ |

- 一行 = 一个证券在一个交易日的观测。全宇宙(供全市场等权基准) + 事件证券共用此视图。
- `board`/`is_st`/`industry` 为**当前快照**(非 PIT);ρ̄ 二阶近似注记已在案(口径④),`board` regime 边界由引擎按 `trade_date` 判(下 §3)。

## 2. `explore_reader_events`(逐 [证券 × 事件] 事件锚)

| 列 | 类型 | 语义 | 消费方 |
|---|---|---|---|
| `ts_code` | text | 事件证券 | 关联 prices |
| `event_id` | text | 事件唯一键(可复现) | 结果溯源 |
| `first_ann_date` | date | **事件日锚 = first_ann_date,无 fallback**(#4;C3 关闭,严禁回退 ann_date) | cleaning τ 轴 |
| `event_type_layer` | text | #4 三层映射结果:`预喜`/`预亏`/`扭亏`/`层外`(附录C 冻结) | pool 过滤 |
| `snapshot_batch` | text | 数据快照批次号(pap_json.snapshot_batch_req 校验、结果可复现) | result_json |

- 事件日锚 `first_ann_date` 与 prices 的 `trade_date` 同粒度(交易日);盘后披露前视规避 → 可交易时点 = 事件日 T+1(见 §3 τ 轴)。
- holdout:`first_ann_date < '2024-07-01'` 焊在视图 WHERE(事件锚落 holdout 区的事件结构上取不到)。

## 3. τ 轴与派生量(引擎侧,不在视图)

- **τ=0 := 首个可交易日 = T+1**(S2-DEC3;事件日 T 盘后披露→规避→观测自 T+1)。主窗 `[0,+2]=T+1..T+3`、稳健窗 `[0,+5]=T+1..T+6`。
- **市场基准(regressor)= 引擎从 prices 全宇宙/池按冻结基准等权算**(口径②:池内=雷达股池等权/全市场=全市场等权),**非视图列**——避免把判断口径下沉到数据层。
- **估计窗覆盖**:事件日前 250 至前 91 交易日(160 日)内 `close` 非 NULL 的有效交易日数 → `frozen_config.coverage_ok`(≥112)。
- **板块 regime 边界(2020-08-24)**:创业板涨跌幅 ±10%→±20% 制度切换,由引擎按 `trade_date` 相对 2020-08-24 判涨跌停阈值(前段 10%/后段 20%),见 `frozen_ashare`。

## 4. 切片2 满足方式(SyntheticReader,不建 mock 视图)

- `taosha/reader/synthetic.py` 读 A股合成 fixture(prices.csv + events.csv),产出与 §1/§2 **同列同序**的行迭代器;
  holdout 过滤同样以 `trade_date < 2024-07-01` 结构性施加(fixture 不含 holdout 区事件,验收在合成域)。
- Q3 交付真 `explore_reader` 视图时:reader 只换数据源(视图替 fixture),**接口签名不变** → 零改造。
