-- 024 · exp17 earnings_flash_gap 专属 forecast 利润区间只读视图对。
-- 人裁补充：taosha/docs/earnings-flash-gap-freeze-adapt-addendum-2026-07-30.md。
-- L1 只投影事实字段；A1/B1/C1、区间完整性与方向判定全部留在 taosha L2。

BEGIN;

CREATE OR REPLACE VIEW public.explore_reader_forecast_profit AS
SELECT f.ts_code, f.ann_date, f.end_date,
       f.net_profit_min, f.net_profit_max,
       'batch' || f.batch_id AS snapshot_batch
FROM public.forecast_snap f
WHERE f.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'tushare:forecast')
  AND f.ann_date < DATE '2024-07-01'
  AND f.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_forecast_profit_snap AS
SELECT f.ts_code, f.ann_date, f.end_date,
       f.net_profit_min, f.net_profit_max,
       'batch' || f.batch_id AS snapshot_batch
FROM public.forecast_snap f
WHERE f.batch_id = public.study_snap_batch('forecast')
  AND f.ann_date < DATE '2024-07-01'
  AND f.ts_code !~ '\.BJ$';

COMMENT ON VIEW public.explore_reader_forecast_profit IS
  'exp17 专属 forecast 利润区间现值视图；holdout/排北焊死；事件判断属 taosha L2。';
COMMENT ON VIEW public.explore_reader_forecast_profit_snap IS
  'exp17 专属 forecast 利润区间 StudySnapshot 视图；最小列面；事件判断属 taosha L2。';

GRANT SELECT ON public.explore_reader_forecast_profit      TO taosha_engine;
GRANT SELECT ON public.explore_reader_forecast_profit_snap TO taosha_engine;

COMMIT;
