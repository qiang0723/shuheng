-- 027 · exp23 buyback_announce 数据闭合：repurchase L1事实表 + current/snap最小视图。
-- 人令：taosha/docs/buyback-announce-dataclose-order-2026-08-07.md。
-- L1只忠实存官方九字段，不判首次披露、方案身份、用途或事件资格。

BEGIN;

CREATE TABLE IF NOT EXISTS public.repurchase_snap (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id        bigint NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code         text,
  ann_date        date,
  end_date        date,
  proc            text,
  exp_date        date,
  vol             numeric,
  amount          numeric,
  high_limit      numeric,
  low_limit       numeric,
  valid_time      timestamptz NOT NULL,
  observed_time   timestamptz NOT NULL DEFAULT now()
  -- 无业务键 UNIQUE：源端多行/重复/生命周期忠实保留，L1仅去完全相同行。
);

CREATE INDEX IF NOT EXISTS ix_repurchase_snap_batch
  ON public.repurchase_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_repurchase_snap_event
  ON public.repurchase_snap(ts_code,ann_date);

COMMENT ON TABLE public.repurchase_snap IS
  '回购事实快照·exp23数据闭合：源=Tushare repurchase；全历史月窗采集；append-only；'
  'L1不判首次披露、方案身份、用途或事件资格。';

DROP TRIGGER IF EXISTS trg_freeze_repurchase_snap ON public.repurchase_snap;
CREATE TRIGGER trg_freeze_repurchase_snap
  BEFORE UPDATE OR DELETE ON public.repurchase_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_no_truncate_repurchase_snap ON public.repurchase_snap;
CREATE TRIGGER trg_no_truncate_repurchase_snap
  BEFORE TRUNCATE ON public.repurchase_snap
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

CREATE OR REPLACE VIEW public.explore_reader_repurchase AS
SELECT r.ts_code,r.ann_date,r.end_date,r.proc,r.exp_date,r.vol,r.amount,
       r.high_limit,r.low_limit,'batch'||r.batch_id AS snapshot_batch
FROM public.repurchase_snap r
WHERE r.batch_id=(SELECT max(batch_id) FROM public.fact_batch
                  WHERE source='tushare:repurchase')
  AND r.ann_date<DATE '2024-07-01'
  AND r.ts_code !~ '\.BJ$';

CREATE OR REPLACE VIEW public.explore_reader_repurchase_snap AS
SELECT r.ts_code,r.ann_date,r.end_date,r.proc,r.exp_date,r.vol,r.amount,
       r.high_limit,r.low_limit,'batch'||r.batch_id AS snapshot_batch
FROM public.repurchase_snap r
WHERE r.batch_id=public.study_snap_batch('repurchase')
  AND r.ann_date<DATE '2024-07-01'
  AND r.ts_code !~ '\.BJ$';

COMMENT ON VIEW public.explore_reader_repurchase IS
  '源=tushare:repurchase最新批；holdout焊死；最小忠实列面，事件与用途判断属taosha L2。';
COMMENT ON VIEW public.explore_reader_repurchase_snap IS
  '源=StudySnapshot qbase.repurchase钉批；holdout焊死；最小忠实列面。';

GRANT SELECT ON public.explore_reader_repurchase TO taosha_engine;
GRANT SELECT ON public.explore_reader_repurchase_snap TO taosha_engine;

COMMIT;
