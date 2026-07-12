-- 淘沙 · StudySnapshot 快照锁定(可信度硬化窗口 ②,人批 2026-07-12)· taosha 侧
-- 修法(人令原文即口径): 研究启动时由受权角色(非 taosha_engine)生成一次性不可变 snapshot
--   manifest(qbase 各源批次向量 + taosha 派生批次 pool_b1/pool_return);manifest 带不可变主键
--   + 规范化内容摘要 + created_at;引擎经按 manifest 路由的受限视图读取,不给 taosha_engine 扩
--   任何底表权限;fail-closed: 无 manifest 拒运行,禁止静默回退 *_current。
-- 本迁移: ① study_snapshot manifest 表(append-only 焊死;digest=sha256(content::text) 由触发器
--   权威计算〔jsonb::text 为 PG 规范化序列化〕,忽略调用方传值)② 严格路由函数(GUC 未设/manifest
--   不存在/缺键一律 RAISE,无任何回退)③ 三张 *_snap 路由视图 ④ 授权收敛(工程加固,随验收档上报:
--   引擎收 *_current 与 taosha 底表 SELECT,唯一读径=manifest 路由 *_snap;*_current 保留给运维/app)。
-- 依据: docs/hardening-window-order-2026-07-12.md ②;验收档 taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md
-- apply 身份 = postgres(taosha 库属主,承 001-005)。

BEGIN;

-- ── ① manifest 表(一次性不可变) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.study_snapshot (
  snapshot_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- 不可变主键
  content     jsonb NOT NULL,                                    -- 批次向量 {"qbase":{...},"taosha":{...}}
  digest      text  NOT NULL DEFAULT '',                         -- 触发器权威计算,忽略传值
  created_by  text  NOT NULL DEFAULT current_user,
  created_at  timestamptz NOT NULL DEFAULT now(),
  note        text
);
COMMENT ON TABLE public.study_snapshot IS
  'StudySnapshot manifest(硬化②):一次性不可变批次向量;digest=sha256(content::text,jsonb 规范化);'
  'append-only 触发器焊死;引擎经 GUC shuheng.study_snapshot_id + *_snap 视图按此路由,fail-closed。';

CREATE OR REPLACE FUNCTION public.study_snapshot_biu() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.content->'qbase' IS NULL OR NEW.content->'taosha' IS NULL THEN
    RAISE EXCEPTION 'StudySnapshot: content 须含 qbase 与 taosha 两半批次向量';
  END IF;
  IF NEW.created_by = 'taosha_engine' THEN
    RAISE EXCEPTION 'StudySnapshot: 生成角色不得为 taosha_engine(硬化②,受权角色专责)';
  END IF;
  -- 规范化内容摘要由库权威计算(jsonb::text = PG 确定性序列化),忽略调用方传值
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_study_snapshot_biu ON public.study_snapshot;
CREATE TRIGGER trg_study_snapshot_biu BEFORE INSERT ON public.study_snapshot
  FOR EACH ROW EXECUTE FUNCTION public.study_snapshot_biu();

-- append-only 焊死(承 002 _freeze_appendonly;TRUNCATE 语句级另焊)
DROP TRIGGER IF EXISTS trg_study_snapshot_freeze ON public.study_snapshot;
CREATE TRIGGER trg_study_snapshot_freeze BEFORE UPDATE OR DELETE ON public.study_snapshot
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

CREATE OR REPLACE FUNCTION public._no_truncate() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only 表 %:禁 TRUNCATE', TG_TABLE_NAME;
END $$;

DROP TRIGGER IF EXISTS trg_study_snapshot_no_truncate ON public.study_snapshot;
CREATE TRIGGER trg_study_snapshot_no_truncate BEFORE TRUNCATE ON public.study_snapshot
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

-- ── ② 严格路由函数(fail-closed,无回退) ─────────────────────────────────────
CREATE OR REPLACE FUNCTION public.study_snapshot_batch(p_key text) RETURNS bigint
LANGUAGE plpgsql STABLE AS $$
DECLARE sid bigint; b bigint;
BEGIN
  -- GUC 未设 → current_setting 自然报错 unrecognized configuration parameter(fail-closed)
  sid := current_setting('shuheng.study_snapshot_id')::bigint;
  SELECT (content->'taosha'->>p_key)::bigint INTO b
    FROM public.study_snapshot WHERE snapshot_id = sid;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'StudySnapshot fail-closed: manifest % 不存在', sid;
  END IF;
  IF b IS NULL THEN
    RAISE EXCEPTION 'StudySnapshot fail-closed: manifest % 缺 taosha.% 批次键', sid, p_key;
  END IF;
  RETURN b;
END $$;

-- ── ③ manifest 路由视图(列形状与 *_current 逐一相同,仅路由源=manifest) ────────
CREATE OR REPLACE VIEW public.market_return_snap AS
  SELECT trade_date, ret_eqw, n_stocks
  FROM public.market_eqw_return
  WHERE batch_id = public.study_snapshot_batch('market_return');

CREATE OR REPLACE VIEW public.pool_b1_snap AS
  SELECT trade_date, ts_code
  FROM public.pool_b1_membership
  WHERE batch_id = public.study_snapshot_batch('pool_b1');

CREATE OR REPLACE VIEW public.pool_b1_return_snap AS
  SELECT trade_date, ret_pool_eqw, n_pool_stocks
  FROM public.pool_b1_return
  WHERE batch_id = public.study_snapshot_batch('pool_b1_return');

-- ── ④ 授权(只收不扩) ─────────────────────────────────────────────────────
-- 受权角色 taosha_app: 生成 manifest(INSERT)+ 读
GRANT SELECT, INSERT ON public.study_snapshot TO taosha_app;
GRANT USAGE, SELECT ON SEQUENCE public.study_snapshot_snapshot_id_seq TO taosha_app;
-- 引擎: 读 manifest(路由键与 audit 记账用,非底表数据)+ 三张 snap 视图
GRANT SELECT ON public.study_snapshot TO taosha_engine;
GRANT SELECT ON public.market_return_snap    TO taosha_engine;
GRANT SELECT ON public.pool_b1_snap          TO taosha_engine;
GRANT SELECT ON public.pool_b1_return_snap   TO taosha_engine;
-- fail-closed 收权(加固上报项): 引擎不再可读 *_current(max-batch 现值路由)与 taosha 底表,
-- 唯一读径 = manifest 路由 *_snap;*_current 与底表授权对 taosha_app/运维不变。
REVOKE SELECT ON public.market_return_current   FROM taosha_engine;
REVOKE SELECT ON public.pool_b1_current         FROM taosha_engine;
REVOKE SELECT ON public.pool_b1_return_current  FROM taosha_engine;
REVOKE SELECT ON public.market_eqw_return       FROM taosha_engine;
REVOKE SELECT ON public.pool_b1_membership      FROM taosha_engine;
REVOKE SELECT ON public.pool_b1_return          FROM taosha_engine;

COMMIT;
