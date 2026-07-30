-- 023 · exp17 earnings_flash_gap 数据前置：业绩快报事实表 + 只读研究视图对。
-- 人令：taosha/docs/earnings-flash-gap-dataclose-order-2026-07-30.md。
-- L1 边界：忠实存 Tushare express_vip 返回；不判定初始/修订、不选预告版本、不算方向。
-- 双时戳：valid_time=ann_date（缺失才回退批次 as-of）；observed_time=本批实际采集时刻。
-- holdout：ann_date < 2024-07-01 在 current / snap 两只消费视图中焊死。
-- apply 身份=qbase_app；幂等；底表不授 taosha_engine。

BEGIN;

CREATE TABLE IF NOT EXISTS public.express_snap (
  id                          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id                    bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code                     text        NOT NULL,
  ann_date                    date,
  end_date                    date,
  revenue                     numeric,
  operate_profit              numeric,
  total_profit                numeric,
  n_income                    numeric,
  total_assets                numeric,
  total_hldr_eqy_exc_min_int  numeric,
  diluted_eps                 numeric,
  diluted_roe                 numeric,
  yoy_net_profit              numeric,
  bps                         numeric,
  yoy_sales                   numeric,
  yoy_op                      numeric,
  yoy_tp                      numeric,
  yoy_dedu_np                 numeric,
  yoy_eps                     numeric,
  yoy_roe                     numeric,
  growth_assets               numeric,
  yoy_equity                  numeric,
  growth_bps                  numeric,
  or_last_year                numeric,
  op_last_year                numeric,
  tp_last_year                numeric,
  np_last_year                numeric,
  eps_last_year               numeric,
  open_net_assets             numeric,
  open_bps                    numeric,
  perf_summary                text,
  is_audit                    integer,
  remark                      text,
  update_flag                 text,
  valid_time                  timestamptz NOT NULL,
  observed_time               timestamptz NOT NULL DEFAULT now()
  -- 无批内 UNIQUE：同票同期可有初始/修订/源重复；L1 忠实存，采集侧只去整行双投递。
);

CREATE INDEX IF NOT EXISTS ix_express_snap_batch
  ON public.express_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_express_snap_ts_period
  ON public.express_snap(ts_code, end_date);
CREATE INDEX IF NOT EXISTS ix_express_snap_event
  ON public.express_snap(ts_code, ann_date, end_date);

COMMENT ON TABLE public.express_snap IS
  '业绩快报事实快照·exp17数据前置：源=Tushare express_vip；按报告期季度分片；append-only；'
  '源字段忠实照落，update_flag语义与异常组处置由taosha L2裁定。';

CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_express_snap ON public.express_snap;
CREATE TRIGGER trg_freeze_express_snap
  BEFORE UPDATE OR DELETE ON public.express_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

CREATE OR REPLACE VIEW public.explore_reader_express AS
SELECT e.ts_code, e.ann_date, e.end_date, e.n_income, e.update_flag,
       'batch' || e.batch_id AS snapshot_batch
FROM public.express_snap e
WHERE e.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source='tushare:express')
  AND e.ann_date < DATE '2024-07-01'
  AND e.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_express_snap AS
SELECT e.ts_code, e.ann_date, e.end_date, e.n_income, e.update_flag,
       'batch' || e.batch_id AS snapshot_batch
FROM public.express_snap e
WHERE e.batch_id = public.study_snap_batch('express')
  AND e.ann_date < DATE '2024-07-01'
  AND e.ts_code !~ '\.BJ$';

COMMENT ON VIEW public.explore_reader_express IS
  '源=tushare:express最新批；holdout=ann_date<2024-07-01；最小列面，事件判定属taosha L2。';
COMMENT ON VIEW public.explore_reader_express_snap IS
  '源=StudySnapshot qbase.express钉批；holdout=ann_date<2024-07-01；最小列面。';

GRANT SELECT ON public.explore_reader_express      TO taosha_engine;
GRANT SELECT ON public.explore_reader_express_snap TO taosha_engine;

COMMIT;
