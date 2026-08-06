-- 026 · exp19 dividend_surprise 数据闭合：dividend L1事实表 + current/snap最小只读视图。
-- 人令：taosha/docs/dividend-surprise-dataclose-order-2026-08-06.md。
-- L1忠实：不判初始预案、不折叠阶段/版本、不计算年度变化；holdout仅在消费视图焊死。

BEGIN;

CREATE TABLE IF NOT EXISTS public.dividend_snap (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id          bigint NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code           text NOT NULL,
  end_date          date,
  ann_date          date,
  div_proc          text,
  stk_div           numeric,
  stk_bo_rate       numeric,
  stk_co_rate       numeric,
  cash_div          numeric,
  cash_div_tax      numeric,
  record_date       date,
  ex_date           date,
  pay_date          date,
  div_listdate      date,
  imp_ann_date      date,
  base_date         date,
  base_share        numeric,
  update_flag       text,
  valid_time        timestamptz NOT NULL,
  observed_time     timestamptz NOT NULL DEFAULT now()
  -- 无业务键 UNIQUE：源可含多阶段、多版本、多公告日；L1只去完全相同行。
);

CREATE INDEX IF NOT EXISTS ix_dividend_snap_batch
  ON public.dividend_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_dividend_snap_ts_period
  ON public.dividend_snap(ts_code,end_date);
CREATE INDEX IF NOT EXISTS ix_dividend_snap_event
  ON public.dividend_snap(ts_code,ann_date,end_date);

COMMENT ON TABLE public.dividend_snap IS
  '分红送股事实快照·exp19数据闭合：源=Tushare dividend；逐证券全历史；append-only；'
  'L1不判阶段/版本/事件资格，实施值严禁在消费层回填初始预案。';

CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_dividend_snap ON public.dividend_snap;
CREATE TRIGGER trg_freeze_dividend_snap
  BEFORE UPDATE OR DELETE ON public.dividend_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_no_truncate_dividend_snap ON public.dividend_snap;
CREATE TRIGGER trg_no_truncate_dividend_snap
  BEFORE TRUNCATE ON public.dividend_snap
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

CREATE OR REPLACE VIEW public.explore_reader_dividend AS
SELECT d.ts_code,d.end_date,d.ann_date,d.div_proc,d.cash_div_tax,
       d.base_date,d.base_share,d.update_flag,'batch'||d.batch_id AS snapshot_batch
FROM public.dividend_snap d
WHERE d.batch_id=(SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:dividend')
  AND d.ann_date<DATE '2024-07-01'
  AND d.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_dividend_snap AS
SELECT d.ts_code,d.end_date,d.ann_date,d.div_proc,d.cash_div_tax,
       d.base_date,d.base_share,d.update_flag,'batch'||d.batch_id AS snapshot_batch
FROM public.dividend_snap d
WHERE d.batch_id=public.study_snap_batch('dividend')
  AND d.ann_date<DATE '2024-07-01'
  AND d.ts_code !~ '\.BJ$';

COMMENT ON VIEW public.explore_reader_dividend IS
  '源=tushare:dividend最新批；holdout=ann_date<2024-07-01；最小忠实列面，事件判断属taosha L2。';
COMMENT ON VIEW public.explore_reader_dividend_snap IS
  '源=StudySnapshot qbase.dividend钉批；holdout=ann_date<2024-07-01；最小忠实列面。';

GRANT SELECT ON public.explore_reader_dividend TO taosha_engine;
GRANT SELECT ON public.explore_reader_dividend_snap TO taosha_engine;

COMMIT;
