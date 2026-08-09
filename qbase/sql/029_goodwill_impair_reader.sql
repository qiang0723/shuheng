-- 029 · exp21 goodwill_impair 数据闭合：资产负债表 PIT L1 + current/snap最小视图。
-- 人令：taosha/docs/goodwill-impair-dataclose-order-2026-08-09.md。
-- L1只忠实保留源报表版本与两种权益，不判事件、分母资格或商誉减值金额。

BEGIN;

CREATE TABLE IF NOT EXISTS public.balancesheet_pit_snap (
  id                              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id                        bigint NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code                         text,
  ann_date                        date,
  f_ann_date                      date,
  end_date                        date,
  report_type                     text,
  comp_type                       text,
  update_flag                     text,
  goodwill                        numeric,
  total_hldr_eqy_exc_min_int      numeric,
  total_hldr_eqy_inc_min_int      numeric,
  valid_time                      timestamptz NOT NULL,
  observed_time                   timestamptz NOT NULL DEFAULT now()
  -- 无业务键 UNIQUE：多版本/调整前后/同日多报表忠实保留，L1仅去完全相同行。
);

CREATE INDEX IF NOT EXISTS ix_balancesheet_pit_batch
  ON public.balancesheet_pit_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_balancesheet_pit_key
  ON public.balancesheet_pit_snap(ts_code,end_date,f_ann_date,report_type,update_flag);

COMMENT ON TABLE public.balancesheet_pit_snap IS
  '资产负债表PIT事实·exp21数据闭合：源=Tushare balancesheet_vip；append-only；'
  'goodwill仅余额、两种权益仅分母候选；L1不判商誉减值、版本或事件资格。';

DROP TRIGGER IF EXISTS trg_freeze_balancesheet_pit_snap ON public.balancesheet_pit_snap;
CREATE TRIGGER trg_freeze_balancesheet_pit_snap
  BEFORE UPDATE OR DELETE ON public.balancesheet_pit_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_no_truncate_balancesheet_pit_snap ON public.balancesheet_pit_snap;
CREATE TRIGGER trg_no_truncate_balancesheet_pit_snap
  BEFORE TRUNCATE ON public.balancesheet_pit_snap
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

CREATE OR REPLACE VIEW public.explore_reader_balancesheet_pit AS
SELECT b.ts_code,b.ann_date,b.f_ann_date,b.end_date,b.report_type,b.comp_type,
       b.update_flag,b.goodwill,b.total_hldr_eqy_exc_min_int,
       b.total_hldr_eqy_inc_min_int,'batch'||b.batch_id AS snapshot_batch
FROM public.balancesheet_pit_snap b
WHERE b.batch_id=(SELECT max(batch_id) FROM public.fact_batch
                  WHERE source='tushare:balancesheet')
  AND COALESCE(b.f_ann_date,b.ann_date)<DATE '2024-07-01'
  AND b.ts_code ~ '\.(SH|SZ)$';

CREATE OR REPLACE VIEW public.explore_reader_balancesheet_pit_snap AS
SELECT b.ts_code,b.ann_date,b.f_ann_date,b.end_date,b.report_type,b.comp_type,
       b.update_flag,b.goodwill,b.total_hldr_eqy_exc_min_int,
       b.total_hldr_eqy_inc_min_int,'batch'||b.batch_id AS snapshot_batch
FROM public.balancesheet_pit_snap b
WHERE b.batch_id=public.study_snap_batch('balancesheet')
  AND COALESCE(b.f_ann_date,b.ann_date)<DATE '2024-07-01'
  AND b.ts_code ~ '\.(SH|SZ)$';

COMMENT ON VIEW public.explore_reader_balancesheet_pit IS
  '源=tushare:balancesheet最新批；实际公告时点holdout；最小忠实列面，事件判断属taosha L2。';
COMMENT ON VIEW public.explore_reader_balancesheet_pit_snap IS
  '源=StudySnapshot qbase.balancesheet钉批；实际公告时点holdout；最小忠实列面。';

GRANT SELECT ON public.explore_reader_balancesheet_pit TO taosha_engine;
GRANT SELECT ON public.explore_reader_balancesheet_pit_snap TO taosha_engine;

COMMIT;
