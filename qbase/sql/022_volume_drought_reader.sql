-- 022 · exp10 volume_drought_break 成交额事件只读视图对。
-- qbase 只忠实路由事件识别所需 raw amount/open/close；60日均量、连续低量、
-- armed/终局与所有 fail-closed 规则均留在 taosha L2。
-- holdout 与北交所排除在视图层焊死；current=max daily 批，_snap=StudySnapshot 路由。

BEGIN;

CREATE OR REPLACE VIEW public.explore_reader_volume_drought AS
SELECT b.ts_code, b.trade_date, b.open, b.close, b.amount,
       'batch' || b.batch_id AS snapshot_batch
FROM public.bar_daily_snap b
WHERE b.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'tushare:daily')
  AND b.trade_date < DATE '2024-07-01'
  AND b.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_volume_drought_snap AS
SELECT b.ts_code, b.trade_date, b.open, b.close, b.amount,
       'batch' || b.batch_id AS snapshot_batch
FROM public.bar_daily_snap b
WHERE b.batch_id = public.study_snap_batch('daily')
  AND b.trade_date < DATE '2024-07-01'
  AND b.ts_code !~ '\.BJ$';

GRANT SELECT ON public.explore_reader_volume_drought      TO taosha_engine;
GRANT SELECT ON public.explore_reader_volume_drought_snap TO taosha_engine;

COMMIT;
