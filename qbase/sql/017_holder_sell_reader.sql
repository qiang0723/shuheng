-- 017 · holder_sell 只读研究视图 + PIT 上市窗视图(§5 最小适配器四项之①②③,人批 2026-07-16)
-- 范围(排产令 §5 白名单): holder_sell_predisclose_snap 只读研究视图 / holdout 视图层焊死 /
--   taosha engine 最小 SELECT 授权。事件判别(六类/首次/关联/去重)不在视图内——qbase=L1 忠实归一
--   零判断,规则属 L2 适配器(taosha/compute/holder_sell_rules.py)。
-- 视图对(现值 + _snap manifest 路由)同口径,承 008/012/013 范式:
--   · holdout 焊死: 京时公告日 < DATE '2024-07-01'(qbase 铁律5,线在视图不在应用代码);
--   · 北交所排除 ts_code !~ '\.BJ$'(与 explore_reader_events 面同口径;当前批 12 实测 0 行,防御性);
--   · 忠实列传递,不过滤"坏"数据(未解析字段照出,消费方自处);
--   · ann_date_bj = 京时日历日(时区归一=归一层职责;PAP T+1 日级口径的事件日锚)。
-- explore_reader_listing(_snap): entity_master PIT 上市窗(ts_code/list_status/list_date/delist_date),
--   供 L2 跨代码同 announcement_id 归属裁定(人令 2026-07-16 窄闸③:禁输入顺序保留首行);忠实主档,无 holdout
--   (静态主体档,PIT 由 list/delist 日期表达)。
-- lineage: 源=holder_sell_predisclose_snap(cninfo:holder_sell_predisclose)/entity_master(tushare:stock_basic);
--   批次=现值 max / study_snap_batch 路由;口径=本头注。
-- apply 身份 = qbase_app(视图属主链承 008/010/012/013;属主自授 engine SELECT)。

BEGIN;

-- ══ 视图 4:explore_reader_holder_sell(现值 max-batch 路由)══
CREATE OR REPLACE VIEW public.explore_reader_holder_sell AS
SELECT
  h.ts_code,
  h.stock_code,
  h.announcement_id,
  h.title,
  h.holder_name,
  h.reduce_ratio_max_pct,
  h.reduce_period_start,
  h.reduce_period_end,
  h.valid_time,
  (h.valid_time AT TIME ZONE 'Asia/Shanghai')::date AS ann_date_bj,
  'batch' || h.batch_id AS snapshot_batch
FROM public.holder_sell_predisclose_snap h
WHERE h.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'cninfo:holder_sell_predisclose')
  AND (h.valid_time AT TIME ZONE 'Asia/Shanghai')::date < DATE '2024-07-01'
  AND h.ts_code !~ '\.BJ$';

-- ══ 视图 4s:explore_reader_holder_sell_snap(manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_holder_sell_snap AS
SELECT
  h.ts_code,
  h.stock_code,
  h.announcement_id,
  h.title,
  h.holder_name,
  h.reduce_ratio_max_pct,
  h.reduce_period_start,
  h.reduce_period_end,
  h.valid_time,
  (h.valid_time AT TIME ZONE 'Asia/Shanghai')::date AS ann_date_bj,
  'batch' || h.batch_id AS snapshot_batch
FROM public.holder_sell_predisclose_snap h
WHERE h.batch_id = public.study_snap_batch('holder_sell_predisclose')
  AND (h.valid_time AT TIME ZONE 'Asia/Shanghai')::date < DATE '2024-07-01'
  AND h.ts_code !~ '\.BJ$';

-- ══ 视图 5:explore_reader_listing(现值 max-batch 路由;PIT 上市窗)══
CREATE OR REPLACE VIEW public.explore_reader_listing AS
SELECT
  e.ts_code,
  e.list_status,
  e.list_date,
  e.delist_date,
  'batch' || e.batch_id AS snapshot_batch
FROM public.entity_master e
WHERE e.batch_id = (SELECT max(batch_id) FROM public.entity_batch
                    WHERE source = 'tushare:stock_basic');

-- ══ 视图 5s:explore_reader_listing_snap(manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_listing_snap AS
SELECT
  e.ts_code,
  e.list_status,
  e.list_date,
  e.delist_date,
  'batch' || e.batch_id AS snapshot_batch
FROM public.entity_master e
WHERE e.batch_id = public.study_snap_batch('stock_basic');

-- ══ 最小 SELECT 授权(§5 白名单③;底表零权维持 009 焊死)══
GRANT SELECT ON public.explore_reader_holder_sell      TO taosha_engine;
GRANT SELECT ON public.explore_reader_holder_sell_snap TO taosha_engine;
GRANT SELECT ON public.explore_reader_listing          TO taosha_engine;
GRANT SELECT ON public.explore_reader_listing_snap     TO taosha_engine;

COMMIT;
