-- 010 · explore_reader_prices 增列后复权 open(切片3 步7 选项2:可交易口径进场价)
-- 缘由:pap exp_id=5 冻结可交易口径"T+1 开盘进"(cost.limit_up_board_untradeable),引擎需进场价。
--       原 008 视图只吐 close(D3 后复权),不含 open → 本迁移增后复权 open。
-- 焊接纪律(与 008 同):holdout `< 2024-07-01`、北交所 `!~ '\.BJ$'` 焊在 DDL(非应用层);
--       后复权 = 原始 open × adj_factor(与 close 同口径 D3);停牌=缺行(视图不铺 None 网格)。
-- ⚠ Postgres CREATE OR REPLACE VIEW 只允许在**列尾**新增列 → open 追加为最末列(industry 之后),
--    与 reader.contract.PRICE_COLUMNS 同序。既有列名/序/类型逐一不变 → 消费方零改造、授权保留
--    (CREATE OR REPLACE 不 DROP,taosha_engine 的 SELECT 授权不失)。
-- 幂等:CREATE OR REPLACE。apply 身份 = qbase_app(视图属主链见 008)。
-- 本迁移**只**改 explore_reader_prices;calendar/events 视图不动。

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
  adj_open AS "open"                      -- 010 新增:后复权开盘(契约末列;quoted 避 keyword 歧义)
FROM lim;
