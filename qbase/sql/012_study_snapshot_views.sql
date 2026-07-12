-- 012 · StudySnapshot 批次向量路由视图(可信度硬化窗口 ②,人批 2026-07-12)· qbase 侧
-- 引擎读径改为 *_snap 三视图:批次路由不再取 max(batch_id) 现值,改由会话 GUC
--   `shuheng.study_batches`(JSON 批次向量,源=taosha.study_snapshot manifest,引擎连接时注入)。
-- fail-closed: GUC 未设 → current_setting 自然报错;向量缺键 → RAISE;无任何静默回退。
-- 授权收敛: taosha_engine 收 explore_reader_*(max-batch 现值路由)SELECT,只授三张 *_snap
--   (qbase_app 等采集/落库侧对 explore_reader_* 的读取不受影响)。
-- 视图体 = 008(calendar/events)/010(prices 含后复权 open)现行定义**逐字复制**,仅四处
--   max(batch_id) 子查询替换为 study_snap_batch('键');holdout `<2024-07-01` 与北交所 `!~'\.BJ$'`
--   焊法逐字保留。lineage: 源/口径同 008/010,批次=manifest 指定。
-- 依据: docs/hardening-window-order-2026-07-12.md ②;验收档 taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md
-- apply 身份 = qbase_app(视图属主链承 008/010)。

BEGIN;

-- ── 严格路由函数(fail-closed) ────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.study_snap_batch(p_key text) RETURNS bigint
LANGUAGE plpgsql STABLE AS $$
DECLARE payload jsonb; b bigint;
BEGIN
  -- GUC 未设 → current_setting 自然报错 unrecognized configuration parameter(fail-closed)
  payload := current_setting('shuheng.study_batches')::jsonb;
  b := (payload ->> p_key)::bigint;
  IF b IS NULL THEN
    RAISE EXCEPTION 'StudySnapshot fail-closed: 批次向量缺键 %(GUC shuheng.study_batches)', p_key;
  END IF;
  RETURN b;
END $$;

-- ══ 视图 1s:explore_reader_calendar_snap(=008 视图1,批次改 manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_calendar_snap AS
SELECT c.cal_date AS trade_date,
       c.pretrade_date
FROM public.trade_cal_snap c
WHERE c.batch_id = public.study_snap_batch('trade_cal')
  AND c.is_open = 1
  AND c.cal_date < DATE '2024-07-01';    -- holdout 焊死(同 008)

-- ══ 视图 2s:explore_reader_prices_snap(=010 视图2 含后复权 open,批次改 manifest 路由)══
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
  adj_close AS close,                     -- 契约 close = 后复权(列名/序/类型与 explore_reader_prices 逐一相同)
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
  adj_open AS "open"                      -- 010 末列:后复权开盘
FROM lim;

-- ══ 视图 3s:explore_reader_events_snap(=008 视图3,批次改 manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_events_snap AS
WITH orig AS (   -- 每 (票,first_ann_date) 取原始披露行(ann_date 最早;同 008)
  SELECT DISTINCT ON (f.ts_code, f.first_ann_date)
         f.ts_code, f.first_ann_date, f.type, f.batch_id
  FROM public.forecast_snap f
  WHERE f.batch_id = public.study_snap_batch('forecast')
    AND f.first_ann_date IS NOT NULL          -- 缺锚剔除(C3)
    AND f.first_ann_date < DATE '2024-07-01'  -- holdout 焊死
    AND f.ts_code !~ '\.BJ$'                   -- 北交所排除
  ORDER BY f.ts_code, f.first_ann_date, f.ann_date ASC NULLS LAST
)
SELECT
  o.ts_code,
  o.ts_code || ':' || to_char(o.first_ann_date,'YYYYMMDD') AS event_id,
  o.first_ann_date,
  CASE
    WHEN o.type IN ('预增','略增','续盈')       THEN 'good'
    WHEN o.type IN ('预减','略减','首亏','续亏') THEN 'bad'
    WHEN o.type = '扭亏'                         THEN 'turnaround'
    ELSE 'out_of_layer'
  END AS event_type_layer,
  'batch' || o.batch_id AS snapshot_batch
FROM orig o
WHERE o.type IN ('预增','略增','续盈','预减','略减','首亏','续亏','扭亏');

-- ── 授权(只收不扩;引擎唯一读径 = *_snap) ──────────────────────────────────
GRANT SELECT ON public.explore_reader_calendar_snap TO taosha_engine;
GRANT SELECT ON public.explore_reader_prices_snap   TO taosha_engine;
GRANT SELECT ON public.explore_reader_events_snap   TO taosha_engine;
REVOKE SELECT ON public.explore_reader_calendar FROM taosha_engine;
REVOKE SELECT ON public.explore_reader_prices   FROM taosha_engine;
REVOKE SELECT ON public.explore_reader_events   FROM taosha_engine;

COMMIT;
