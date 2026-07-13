-- 015 · explore_reader_prices / explore_reader_prices_snap 增列 open_limit_status
--       (外审第三轮窄补 #1-b,2026-07-13,人终签;docs/postaudit-round3-narrow-order-2026-07-13.md)
-- 缘由:next_open 离场"开盘可成交"判定不得使用日终信息(limit_status 为日终收盘口径)。
--       新列 = **开盘时点**涨跌停位标记:原始 open 是否恰在 round(原始前收×(1±limit_pct),2)
--       价位——开盘时点(集合竞价撮合后)即可得,PIT 干净。limit_pct 复用两视图既有口径
--       (主板10%/ST5%/创业板2020-08-24后20%/科创板20%,原始价分位取整;口径唯一,逐字同式)。
-- 能力边界(人令,如实标注):本列是**日线代理规则**输入——opening print 存在/开盘价不在
--       跌停位 ≠ 我方委托单能排队成交;不得宣称"已验证真实可成交"。消费方(taosha
--       compute.holding_path._sellable_at_open)与报告端同式标注。
-- 值域:'none' / 'open_at_up_limit' / 'open_at_down_limit'(open 缺或前收缺 → 'none',
--       opening print 缺失由消费方按 open IS NULL 判,R-open-1)。
-- 焊接纪律(与 008/010/012 同):holdout `< 2024-07-01`、北交所 `!~ '\.BJ$'` 焊在 DDL;
--       批次路由两视图各自保留(current=max(batch_id) / _snap=study_snap_batch manifest 路由)。
-- ⚠ Postgres CREATE OR REPLACE VIEW 只允许在**列尾**新增列 → open_limit_status 追加为最末列
--    (open 之后),与 reader.contract.PRICE_COLUMNS 同序。既有列名/序/类型逐一不变 →
--    消费方零改造、授权保留(CREATE OR REPLACE 不 DROP,taosha_engine 对 _snap 的 SELECT 不失)。
-- 幂等:CREATE OR REPLACE。apply 身份 = qbase_app(视图属主链承 008/010/012)。
-- 本迁移**只**改 prices 两视图;calendar/events(current 与 _snap)不动。范围=窄补#1-b,无他。

BEGIN;

-- ══ 视图 1:explore_reader_prices(current,max-batch 路由;=010 体 + 末列 open_limit_status)══
CREATE OR REPLACE VIEW public.explore_reader_prices AS
WITH em AS (   -- 实体维(最新 stock_basic 批:industry + 上市/退市界)
  SELECT ts_code, industry, list_date, delist_date
  FROM public.entity_master
  WHERE batch_id = (SELECT max(batch_id) FROM public.entity_batch WHERE source='tushare:stock_basic')
),
name_seg AS (   -- namechange PIT 段(同 008:折叠脏孪生 + LEAD 划界,免疫 446 票污染)
  SELECT ts_code, start_date,
         bool_or(alias LIKE '%ST%') AS seg_has_st,
         bool_or(alias LIKE '%退')  AS seg_delist_clean,
         LEAD(start_date) OVER (PARTITION BY ts_code ORDER BY start_date) AS next_start
  FROM public.entity_alias
  WHERE alias_type = 'name'
    AND batch_id = (SELECT max(batch_id) FROM public.entity_batch WHERE source='tushare:namechange')
  GROUP BY ts_code, start_date
),
base AS (
  SELECT b.ts_code,
         b.trade_date,
         b.close      AS raw_close,
         b.pre_close  AS raw_pre_close,
         b.open AS o, b.high AS h, b.low AS l,
         (b.close * a.adj_factor)::numeric AS adj_close,      -- 后复权收盘(D3)
         (b.open  * a.adj_factor)::numeric AS adj_open,       -- 后复权开盘(010 增;与 close 同 D3 口径)
         em.industry,
         CASE
           WHEN b.ts_code ~ '\.BJ$'            THEN 'bse'
           WHEN b.ts_code ~ '^688'             THEN 'star'
           WHEN b.ts_code ~ '^(300|301)'       THEN 'chinext'
           ELSE 'main'
         END AS board,
         CASE
           WHEN seg.seg_delist_clean THEN false
           WHEN seg.seg_has_st       THEN true
           ELSE false
         END AS is_st
  FROM public.bar_daily_snap b
  JOIN public.adj_factor_snap a
    ON a.ts_code = b.ts_code AND a.trade_date = b.trade_date
   AND a.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:adj_factor')
  LEFT JOIN em ON em.ts_code = b.ts_code
  LEFT JOIN name_seg seg
    ON seg.ts_code = b.ts_code
   AND seg.start_date <= b.trade_date
   AND (seg.next_start IS NULL OR b.trade_date < seg.next_start)
  WHERE b.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:daily')
    AND b.trade_date < DATE '2024-07-01'   -- holdout 焊死
    AND b.ts_code !~ '\.BJ$'               -- 北交所排除(体系原则,同 holdout DDL 焊法)
),
lim AS (
  SELECT base.*,
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
  adj_close AS close,                     -- 契约 close = 后复权(既有列,序不变)
  false     AS is_suspended,
  CASE
    WHEN raw_pre_close IS NULL OR raw_pre_close = 0 THEN 'none'
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 + limit_pct), 2) THEN 'one_word'
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 - limit_pct), 2) THEN 'one_word'
    WHEN raw_close = round(raw_pre_close * (1 + limit_pct), 2)     THEN 'limit_up'
    WHEN raw_close = round(raw_pre_close * (1 - limit_pct), 2)     THEN 'limit_down'
    ELSE 'none'
  END AS limit_status,
  board,
  is_st,
  industry,
  adj_open AS "open",                     -- 010 列:后复权开盘
  CASE                                    -- 015 末列:开盘时点涨跌停位标记(窄补第三轮 #1-b)
    WHEN o IS NULL OR raw_pre_close IS NULL OR raw_pre_close = 0        THEN 'none'
    WHEN o = round(raw_pre_close * (1 - limit_pct), 2)                  THEN 'open_at_down_limit'
    WHEN o = round(raw_pre_close * (1 + limit_pct), 2)                  THEN 'open_at_up_limit'
    ELSE 'none'
  END AS open_limit_status
FROM lim;

-- ══ 视图 2:explore_reader_prices_snap(manifest 路由;=012 体 + 末列 open_limit_status)══
CREATE OR REPLACE VIEW public.explore_reader_prices_snap AS
WITH em AS (   -- 实体维(stock_basic 批=manifest:industry + 上市/退市界)
  SELECT ts_code, industry, list_date, delist_date
  FROM public.entity_master
  WHERE batch_id = public.study_snap_batch('stock_basic')
),
name_seg AS (   -- namechange PIT 段(同 008:折叠脏孪生 + LEAD 划界,免疫 446 票污染)
  SELECT ts_code, start_date,
         bool_or(alias LIKE '%ST%') AS seg_has_st,
         bool_or(alias LIKE '%退')  AS seg_delist_clean,
         LEAD(start_date) OVER (PARTITION BY ts_code ORDER BY start_date) AS next_start
  FROM public.entity_alias
  WHERE alias_type = 'name'
    AND batch_id = public.study_snap_batch('namechange')
  GROUP BY ts_code, start_date
),
base AS (
  SELECT b.ts_code,
         b.trade_date,
         b.close      AS raw_close,
         b.pre_close  AS raw_pre_close,
         b.open AS o, b.high AS h, b.low AS l,
         (b.close * a.adj_factor)::numeric AS adj_close,      -- 后复权收盘(D3)
         (b.open  * a.adj_factor)::numeric AS adj_open,       -- 后复权开盘(010;与 close 同 D3 口径)
         em.industry,
         CASE
           WHEN b.ts_code ~ '\.BJ$'            THEN 'bse'
           WHEN b.ts_code ~ '^688'             THEN 'star'
           WHEN b.ts_code ~ '^(300|301)'       THEN 'chinext'
           ELSE 'main'
         END AS board,
         CASE
           WHEN seg.seg_delist_clean THEN false
           WHEN seg.seg_has_st       THEN true
           ELSE false
         END AS is_st
  FROM public.bar_daily_snap b
  JOIN public.adj_factor_snap a
    ON a.ts_code = b.ts_code AND a.trade_date = b.trade_date
   AND a.batch_id = public.study_snap_batch('adj_factor')
  LEFT JOIN em ON em.ts_code = b.ts_code
  LEFT JOIN name_seg seg
    ON seg.ts_code = b.ts_code
   AND seg.start_date <= b.trade_date
   AND (seg.next_start IS NULL OR b.trade_date < seg.next_start)
  WHERE b.batch_id = public.study_snap_batch('daily')
    AND b.trade_date < DATE '2024-07-01'   -- holdout 焊死(同 008/010)
    AND b.ts_code !~ '\.BJ$'               -- 北交所排除(同 008/010 DDL 焊法)
),
lim AS (
  SELECT base.*,
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
  adj_close AS close,                     -- 契约 close = 后复权(列名/序/类型与 current 视图逐一相同)
  false     AS is_suspended,
  CASE
    WHEN raw_pre_close IS NULL OR raw_pre_close = 0 THEN 'none'
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 + limit_pct), 2) THEN 'one_word'
    WHEN o = h AND h = l AND l = raw_close
         AND raw_close = round(raw_pre_close * (1 - limit_pct), 2) THEN 'one_word'
    WHEN raw_close = round(raw_pre_close * (1 + limit_pct), 2)     THEN 'limit_up'
    WHEN raw_close = round(raw_pre_close * (1 - limit_pct), 2)     THEN 'limit_down'
    ELSE 'none'
  END AS limit_status,
  board,
  is_st,
  industry,
  adj_open AS "open",                     -- 010 列:后复权开盘
  CASE                                    -- 015 末列:开盘时点涨跌停位标记(窄补第三轮 #1-b,同式)
    WHEN o IS NULL OR raw_pre_close IS NULL OR raw_pre_close = 0        THEN 'none'
    WHEN o = round(raw_pre_close * (1 - limit_pct), 2)                  THEN 'open_at_down_limit'
    WHEN o = round(raw_pre_close * (1 + limit_pct), 2)                  THEN 'open_at_up_limit'
    ELSE 'none'
  END AS open_limit_status
FROM lim;

COMMIT;
