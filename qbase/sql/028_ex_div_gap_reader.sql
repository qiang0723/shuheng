-- 028 · exp14 ex_div_gap 冻结前数据对账：dividend / adj_factor 最小事实列面。
-- 人令：taosha/docs/ex-div-gap-datarecon-order-2026-08-09.md。
-- L1忠实：不判实施阶段、送转阈值、版本折叠、因子变化或事件资格；判断全部留在taosha L2。

BEGIN;

CREATE OR REPLACE VIEW public.explore_reader_ex_div_gap AS
SELECT d.ts_code,d.end_date,d.ann_date,d.div_proc,d.stk_div,
       d.stk_bo_rate,d.stk_co_rate,d.record_date,d.ex_date,
       d.imp_ann_date,d.update_flag,'batch'||d.batch_id AS snapshot_batch
FROM public.dividend_snap d
WHERE d.batch_id=(SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:dividend')
  AND d.ex_date<DATE '2024-07-01'
  AND d.ts_code ~ '\.(SH|SZ)$';

CREATE OR REPLACE VIEW public.explore_reader_ex_div_gap_snap AS
SELECT d.ts_code,d.end_date,d.ann_date,d.div_proc,d.stk_div,
       d.stk_bo_rate,d.stk_co_rate,d.record_date,d.ex_date,
       d.imp_ann_date,d.update_flag,'batch'||d.batch_id AS snapshot_batch
FROM public.dividend_snap d
WHERE d.batch_id=public.study_snap_batch('dividend')
  AND d.ex_date<DATE '2024-07-01'
  AND d.ts_code ~ '\.(SH|SZ)$';

CREATE OR REPLACE VIEW public.explore_reader_ex_div_factor AS
SELECT a.ts_code,a.trade_date,a.adj_factor,'batch'||a.batch_id AS snapshot_batch
FROM public.adj_factor_snap a
WHERE a.batch_id=(SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:adj_factor')
  AND a.trade_date<DATE '2024-07-01'
  AND a.ts_code ~ '\.(SH|SZ)$';

CREATE OR REPLACE VIEW public.explore_reader_ex_div_factor_snap AS
SELECT a.ts_code,a.trade_date,a.adj_factor,'batch'||a.batch_id AS snapshot_batch
FROM public.adj_factor_snap a
WHERE a.batch_id=public.study_snap_batch('adj_factor')
  AND a.trade_date<DATE '2024-07-01'
  AND a.ts_code ~ '\.(SH|SZ)$';

COMMENT ON VIEW public.explore_reader_ex_div_gap IS
  'exp14专属dividend最新批忠实投影；holdout=ex_date<2024-07-01；事件判断属taosha L2。';
COMMENT ON VIEW public.explore_reader_ex_div_gap_snap IS
  'exp14专属dividend StudySnapshot钉批忠实投影；holdout同current。';
COMMENT ON VIEW public.explore_reader_ex_div_factor IS
  'exp14专属adj_factor最新批最小事实列面；不判因子变化。';
COMMENT ON VIEW public.explore_reader_ex_div_factor_snap IS
  'exp14专属adj_factor StudySnapshot钉批最小事实列面；不判因子变化。';

GRANT SELECT ON public.explore_reader_ex_div_gap TO taosha_engine;
GRANT SELECT ON public.explore_reader_ex_div_gap_snap TO taosha_engine;
GRANT SELECT ON public.explore_reader_ex_div_factor TO taosha_engine;
GRANT SELECT ON public.explore_reader_ex_div_factor_snap TO taosha_engine;
COMMIT;
