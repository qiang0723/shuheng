-- 008 · Q3 explore_reader 归一视图族 + 引擎只读角色(切片3 硬前置)
-- 人裁(2026-07-07):视图**只吐真实 bar + 归一列**,停牌由引擎按 trade_cal 断档判定(不铺 None 网格)。
-- 铁律7:facts 只存事实,归一是视图的活。本族把原始 OHLCV/因子/日历/实体归一为淘沙 reader 契约形状。
-- holdout 焊死:视图 DDL 内 `WHERE trade_date < '2024-07-01'`(spec 冻结值,非应用层过滤)。
-- 换源约束:视图集中管理;老机退役换本地源只改视图不动消费方(本回已是本地表,提前满足)。
-- 幂等:CREATE OR REPLACE。apply 身份 = qbase_app(属主 postgres 建角色部分见文末,需超级用户段)。

-- ── 最新批次锚(实物为准,避免硬编码 batch_id)──────────────────────────────────
--   entity_master=stock_basic 最新;bar/adj/cal=各 tushare 源最新;forecast=最新。

-- ══ 视图 1:explore_reader_calendar(权威交易日轴,供引擎按 trade_cal 断档判停牌)══
-- 契约补充(Q3 新增,供切片3 引擎建交易日轴):SSE 交易日(is_open=1),holdout 焊死。
CREATE OR REPLACE VIEW public.explore_reader_calendar AS
SELECT c.cal_date AS trade_date,
       c.pretrade_date
FROM public.trade_cal_snap c
WHERE c.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:trade_cal')
  AND c.is_open = 1
  AND c.cal_date < DATE '2024-07-01';    -- holdout 焊死

-- ══ 视图 2:explore_reader_prices(逐 [证券×真实交易日] 价格行 + 归一列)══
-- 契约 PRICE_COLUMNS=(ts_code,trade_date,close,is_suspended,limit_status,board,is_st,industry)。
-- close=**后复权**(原始 close×adj_factor,D3 收益口径);limit_status 用**原始** close/pre_close 判
-- (涨跌停限于原始价,后复权会破坏绝对价);is_suspended=**false**(真实 bar 无停牌行,停牌=缺行,引擎按
-- calendar 断档判——见 008 验收〔契约核对发现〕);board=ts_code 前缀;is_st=PIT 名称含 ST;industry=entity_master。
CREATE OR REPLACE VIEW public.explore_reader_prices AS
WITH em AS (   -- 实体维(最新 stock_basic 批:industry + 上市/退市界)
  SELECT ts_code, industry, list_date, delist_date
  FROM public.entity_master
  WHERE batch_id = (SELECT max(batch_id) FROM public.entity_batch WHERE source='tushare:stock_basic')
),
base AS (
  SELECT b.ts_code,
         b.trade_date,
         b.close      AS raw_close,       -- 原始收盘(limit 判定基准)
         b.pre_close  AS raw_pre_close,   -- 原始昨收(涨跌停基准)
         b.open AS o, b.high AS h, b.low AS l,
         (b.close * a.adj_factor)::numeric AS adj_close,   -- 后复权收盘(D3,供收益)
         em.industry,
         -- board:ts_code 前缀(与 reader.contract.BOARDS 对齐)
         CASE
           WHEN b.ts_code ~ '\.BJ$'            THEN 'bse'
           WHEN b.ts_code ~ '^688'             THEN 'star'
           WHEN b.ts_code ~ '^(300|301)'       THEN 'chinext'
           ELSE 'main'
         END AS board,
         -- is_st:PIT 名称含 ST(entity_alias 忠实存全的 namechange,闭区间 [start,end])
         EXISTS (
           SELECT 1 FROM public.entity_alias ea
           WHERE ea.ts_code = b.ts_code
             AND ea.alias_type = 'name'
             AND ea.alias LIKE '%ST%'
             AND ea.start_date <= b.trade_date
             AND (ea.end_date IS NULL OR b.trade_date <= ea.end_date)
         ) AS is_st
  FROM public.bar_daily_snap b
  JOIN public.adj_factor_snap a
    ON a.ts_code = b.ts_code AND a.trade_date = b.trade_date
   AND a.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:adj_factor')
  LEFT JOIN em ON em.ts_code = b.ts_code
  WHERE b.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:daily')
    AND b.trade_date < DATE '2024-07-01'   -- holdout 焊死
),
lim AS (
  SELECT base.*,
         -- 涨跌停限幅(小数):ST 优先;创业板 2020-08-24 regime;北交 30% 兜底
         CASE
           WHEN is_st                         THEN 0.05
           WHEN board = 'main'                THEN 0.10
           WHEN board = 'chinext'             THEN CASE WHEN trade_date < DATE '2020-08-24' THEN 0.10 ELSE 0.20 END
           WHEN board = 'star'                THEN 0.20
           ELSE 0.30
         END AS limit_pct
  FROM base
)
SELECT
  ts_code,
  trade_date,
  adj_close AS close,                     -- 契约 close = 后复权
  false     AS is_suspended,              -- 真实 bar 恒 false(停牌=缺行,引擎按 calendar 断档)
  -- limit_status:分价位取整(round 到分),原始价判定;一字板=全日一价且封停
  CASE
    WHEN raw_pre_close IS NULL OR raw_pre_close = 0 THEN 'none'
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 + limit_pct), 2) THEN 'one_word'   -- 一字涨停
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 - limit_pct), 2) THEN 'one_word'   -- 一字跌停
    WHEN raw_close = round(raw_pre_close * (1 + limit_pct), 2)     THEN 'limit_up'
    WHEN raw_close = round(raw_pre_close * (1 - limit_pct), 2)     THEN 'limit_down'
    ELSE 'none'
  END AS limit_status,
  board,
  is_st,
  industry
FROM lim;

-- ══ 视图 3:explore_reader_events(事件锚:业绩预告漂移 #5/#4 系)══
-- 契约 EVENT_COLUMNS=(ts_code,event_id,first_ann_date,event_type_layer,snapshot_batch)。
-- 事件日锚=first_ann_date(无 fallback,#4 裁定);event_type_layer=type→附录C 三层映射(预喜/预亏/扭亏);
-- 层外(不确定/其他)与缺锚(first_ann_date 空)剔除(C3)。holdout first_ann_date<2024-07-01。
-- ⚠ #3 减持事件源=L3 减持预披露 PDF(档位二 PIT),尚未落库→本视图暂只出 forecast 系事件;#3 待 L3 落库补。
-- 去重要点:一事件 = 一 (ts_code, first_ann_date)。forecast_snap 一票一报告期常有原始+多次修正
-- 多行、且共享同一 first_ann_date(事件锚不变)→ 直接 SELECT 会撞 event_id。PIT 正解:取**原始披露**
-- (ann_date 最早=首次)那一行的 type 作事件类型;修正是漂移更新、非新事件。层映射/holdout 在去重后。
CREATE OR REPLACE VIEW public.explore_reader_events AS
WITH orig AS (   -- 每 (票,first_ann_date) 取原始披露行(ann_date 最早)
  SELECT DISTINCT ON (f.ts_code, f.first_ann_date)
         f.ts_code, f.first_ann_date, f.type, f.batch_id
  FROM public.forecast_snap f
  WHERE f.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:forecast')
    AND f.first_ann_date IS NOT NULL          -- 缺锚剔除(C3:不可定位事件日)
    AND f.first_ann_date < DATE '2024-07-01'  -- holdout 焊死
  ORDER BY f.ts_code, f.first_ann_date, f.ann_date ASC NULLS LAST   -- 最早 ann_date=原始披露
)
SELECT
  o.ts_code,
  o.ts_code || ':' || to_char(o.first_ann_date,'YYYYMMDD') AS event_id,
  o.first_ann_date,
  CASE
    WHEN o.type IN ('预增','略增','续盈')       THEN 'good'      -- 预喜
    WHEN o.type IN ('预减','略减','首亏','续亏') THEN 'bad'       -- 预亏
    WHEN o.type = '扭亏'                         THEN 'turnaround'-- 扭亏独立
    ELSE 'out_of_layer'                                           -- 不确定/其他(层外)
  END AS event_type_layer,
  'batch' || o.batch_id AS snapshot_batch
FROM orig o
WHERE o.type IN ('预增','略增','续盈','预减','略减','首亏','续亏','扭亏');  -- 层外(其他/不确定)不出
