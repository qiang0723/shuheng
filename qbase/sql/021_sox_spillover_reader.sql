-- 021 · exp24 SOX spillover 只读研究视图对。
-- L1 只忠实路由批13/14；±3%、跨市场映射、D4 与成员展开均在 taosha L2。
-- snapshot247 只作数据前置锚；正式运行须由 exp24 自有 StudySnapshot 路由。

BEGIN;

CREATE OR REPLACE VIEW public.explore_reader_sox_daily AS
SELECT s.trade_date, s.close, s.currency, 'batch' || s.batch_id AS snapshot_batch
FROM public.sox_daily_snap s
WHERE s.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'nasdaq_giw:sox_daily')
  AND s.trade_date < DATE '2024-07-01';

CREATE OR REPLACE VIEW public.explore_reader_sox_daily_snap AS
SELECT s.trade_date, s.close, s.currency, 'batch' || s.batch_id AS snapshot_batch
FROM public.sox_daily_snap s
WHERE s.batch_id = public.study_snap_batch('sox_daily')
  AND s.trade_date < DATE '2024-07-01';

CREATE OR REPLACE VIEW public.explore_reader_sw_member AS
SELECT m.index_code, m.ts_code, m.in_date, m.out_date,
       'batch' || m.batch_id AS snapshot_batch
FROM public.sw_member_snap m
WHERE m.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'tushare:sw_member')
  AND m.index_code = '801081.SI';

CREATE OR REPLACE VIEW public.explore_reader_sw_member_snap AS
SELECT m.index_code, m.ts_code, m.in_date, m.out_date,
       'batch' || m.batch_id AS snapshot_batch
FROM public.sw_member_snap m
WHERE m.batch_id = public.study_snap_batch('sw_member')
  AND m.index_code = '801081.SI';

GRANT SELECT ON public.explore_reader_sox_daily      TO taosha_engine;
GRANT SELECT ON public.explore_reader_sox_daily_snap TO taosha_engine;
GRANT SELECT ON public.explore_reader_sw_member      TO taosha_engine;
GRANT SELECT ON public.explore_reader_sw_member_snap TO taosha_engine;

COMMIT;
