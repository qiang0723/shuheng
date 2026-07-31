-- 025 · exp18 audit_qualified 数据前置：年报审计意见事实表 + 最小只读视图对。
-- 人令：taosha/docs/audit-qualified-dataclose-order-2026-07-31.md。
-- L1 边界：忠实存 Tushare fina_audit 返回；不判定意见类别、首次披露、修订或事件资格。
-- 双时戳：valid_time=ann_date（缺失才回退批次 as-of）；observed_time=本批实际采集时刻。
-- holdout：ann_date < 2024-07-01 在 current / snap 两只消费视图中焊死。
-- apply 身份=qbase_app；幂等；底表不授 taosha_engine。

BEGIN;

CREATE TABLE IF NOT EXISTS public.fina_audit_snap (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id       bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code        text        NOT NULL,
  ann_date       date,
  end_date       date,
  audit_result   text,
  audit_fees     numeric,
  audit_agency   text,
  audit_sign     text,
  valid_time     timestamptz NOT NULL,
  observed_time  timestamptz NOT NULL DEFAULT now()
  -- 无批内 UNIQUE：同票同期可能有源重复或源端当前态异常；L1忠实存，采集侧仅做整行去重。
);

CREATE INDEX IF NOT EXISTS ix_fina_audit_snap_batch
  ON public.fina_audit_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_fina_audit_snap_ts_period
  ON public.fina_audit_snap(ts_code, end_date);
CREATE INDEX IF NOT EXISTS ix_fina_audit_snap_event
  ON public.fina_audit_snap(ts_code, ann_date, end_date);

COMMENT ON TABLE public.fina_audit_snap IS
  '年报审计意见事实快照·exp18数据前置：源=Tushare fina_audit；按证券全量获取；append-only；'
  'L1忠实存源字段，不判意见类别、首次披露、修订或事件资格。';

CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_fina_audit_snap ON public.fina_audit_snap;
CREATE TRIGGER trg_freeze_fina_audit_snap
  BEFORE UPDATE OR DELETE ON public.fina_audit_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

CREATE OR REPLACE VIEW public.explore_reader_fina_audit AS
SELECT a.ts_code, a.ann_date, a.end_date, a.audit_result,
       a.audit_fees, a.audit_agency, a.audit_sign,
       'batch' || a.batch_id AS snapshot_batch
FROM public.fina_audit_snap a
WHERE a.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source='tushare:fina_audit')
  AND a.ann_date < DATE '2024-07-01'
  AND a.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_fina_audit_snap AS
SELECT a.ts_code, a.ann_date, a.end_date, a.audit_result,
       a.audit_fees, a.audit_agency, a.audit_sign,
       'batch' || a.batch_id AS snapshot_batch
FROM public.fina_audit_snap a
WHERE a.batch_id = public.study_snap_batch('fina_audit')
  AND a.ann_date < DATE '2024-07-01'
  AND a.ts_code !~ '\.BJ$';

COMMENT ON VIEW public.explore_reader_fina_audit IS
  '源=tushare:fina_audit最新批；holdout=ann_date<2024-07-01；最小忠实列面，事件判定属taosha L2。';
COMMENT ON VIEW public.explore_reader_fina_audit_snap IS
  '源=StudySnapshot qbase.fina_audit钉批；holdout=ann_date<2024-07-01；最小忠实列面。';

GRANT SELECT ON public.explore_reader_fina_audit      TO taosha_engine;
GRANT SELECT ON public.explore_reader_fina_audit_snap TO taosha_engine;

COMMIT;
