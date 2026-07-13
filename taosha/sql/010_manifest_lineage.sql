-- 淘沙 · manifest 批次血缘一致性(外审五项修法 #3,人终签 2026-07-13)
-- 攻击路径(外审坐实): snapshot.collect_content() 取各批次表 max(batch_id) 拼向量,
--   manifest 生成处无交叉校验——可产出内部不相容的 manifest(如 pool_b1_return 批派生自
--   池批 A 而 manifest.pool_b1=B),派生批次亦无源锚定,血缘断链不可审计。
-- 修法(人令原文即口径): 验收标准=血缘相容性,非所有批次号相等——
--   ① 至少强制 pool_b1_return.pool_batch_id == manifest.pool_b1;
--   ② 派生批次须锚定其 qbase 源向量或源 manifest digest(从 ingest 起强制写入);
--   ③ 历史批次: 不加 NOT NULL(现有 snapshot 不失效)、不批量补猜(不造伪血缘);
--     唯一路径=可由既有审计实物证明者入独立 append-only lineage registry 附审批来源,
--     无法证明者标 legacy-unverified、不允许其生成新的正式研究 manifest。
-- 历史批次证据(查库实测 2026-07-13,非补猜): qbase 九批全部 pull_time=2026-07-07,
--   此后零新批(append-only 时间戳可重构)→ 四个 taosha 派生批(market 1,2 / pool_b1 1 /
--   pool_b1_return 1,建于 07-08..07-12)运行时 qbase max-batch 向量 == manifest#1 的
--   qbase 半边(digest 2a8a271f…);pool_b1_return 1 的父池批=行内 pool_batch_id=1(FK 实物)。
--   故四批全部 verified 入 registry,锚由库内 SELECT 构造(零字面拼写)。
-- 回滚边界: DROP 三张批次表 BEFORE INSERT 触发器与 derived_batch_bi()、
--   _batch_lineage_trusted(),study_snapshot_biu() 重放 006 定义;registry 表为
--   append-only 审计实物,回滚时保留不删(留档无害);source_anchor 列保留(nullable,无行为)。
-- apply 身份 = postgres(taosha 库属主,承 001-009)。
-- 依据: docs/postaudit-five-order-2026-07-13.md #3;
--   验收档 taosha/docs/postaudit-item3-manifest-lineage-acceptance-2026-07-13.md

BEGIN;

-- ── ① lineage registry(append-only;历史批次登记专用,写权=属主高权限路径专责) ──
CREATE TABLE IF NOT EXISTS public.batch_lineage_registry (
  lineage_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_table    text   NOT NULL CHECK (batch_table IN
                   ('market_batch', 'pool_b1_batch', 'pool_b1_return_batch')),
  batch_id       bigint NOT NULL,
  lineage_status text   NOT NULL CHECK (lineage_status IN ('verified', 'legacy-unverified')),
  source_anchor  jsonb,                -- verified 须非空: qbase 源向量 / 源 manifest digest / taosha 父批
  evidence_ref   text   NOT NULL,     -- 审计实物指针(验收档路径/库内可重构规则)
  approval_ref   text   NOT NULL,     -- 审批来源(施工单条款)
  created_by     text   NOT NULL DEFAULT current_user,
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (batch_table, batch_id),
  CHECK (lineage_status <> 'verified' OR source_anchor IS NOT NULL)
);
COMMENT ON TABLE public.batch_lineage_registry IS
  '派生批次血缘登记(修法#3): 历史批次唯一合法登记路径,append-only;verified=审计实物可证'
  '(锚必填),legacy-unverified=不可证(禁止生成新正式研究 manifest);迁移后新批次'
  '不经此表——血缘在批次行 source_anchor 列随 ingest 强制写入。';

DROP TRIGGER IF EXISTS trg_batch_lineage_registry_freeze ON public.batch_lineage_registry;
CREATE TRIGGER trg_batch_lineage_registry_freeze
  BEFORE UPDATE OR DELETE ON public.batch_lineage_registry
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
DROP TRIGGER IF EXISTS trg_batch_lineage_registry_no_truncate ON public.batch_lineage_registry;
CREATE TRIGGER trg_batch_lineage_registry_no_truncate
  BEFORE TRUNCATE ON public.batch_lineage_registry
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

-- 只读授权(登记=属主专责;taosha_app/引擎均无写权——外审#1 同款登记表纪律)
GRANT SELECT ON public.batch_lineage_registry TO taosha_app;
GRANT SELECT ON public.batch_lineage_registry TO taosha_engine;

-- ── ② 派生批次表 source_anchor 列(nullable=历史行不失效)+ 前向强制 ─────────────
ALTER TABLE public.market_batch         ADD COLUMN IF NOT EXISTS source_anchor jsonb;
ALTER TABLE public.pool_b1_batch        ADD COLUMN IF NOT EXISTS source_anchor jsonb;
ALTER TABLE public.pool_b1_return_batch ADD COLUMN IF NOT EXISTS source_anchor jsonb;
COMMENT ON COLUMN public.market_batch.source_anchor IS
  '源锚定(修法#3): qbase 源向量或源 manifest digest;迁移后新批 BEFORE INSERT 强制非空,'
  '历史行 NULL(血缘见 batch_lineage_registry)';

CREATE OR REPLACE FUNCTION public.derived_batch_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.source_anchor IS NULL THEN
    RAISE EXCEPTION '修法#3: 新派生批次须锚定源(source_anchor=qbase 源向量或源 manifest digest),从 ingest 起强制(表 %)', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_market_batch_bi ON public.market_batch;
CREATE TRIGGER trg_market_batch_bi BEFORE INSERT ON public.market_batch
  FOR EACH ROW EXECUTE FUNCTION public.derived_batch_bi();
DROP TRIGGER IF EXISTS trg_pool_b1_batch_bi ON public.pool_b1_batch;
CREATE TRIGGER trg_pool_b1_batch_bi BEFORE INSERT ON public.pool_b1_batch
  FOR EACH ROW EXECUTE FUNCTION public.derived_batch_bi();
DROP TRIGGER IF EXISTS trg_pool_b1_return_batch_bi ON public.pool_b1_return_batch;
CREATE TRIGGER trg_pool_b1_return_batch_bi BEFORE INSERT ON public.pool_b1_return_batch
  FOR EACH ROW EXECUTE FUNCTION public.derived_batch_bi();

-- ── ③ 历史批次物化登记(verified;锚由库内 SELECT 构造,零字面补猜) ──────────────
-- 前置断言: manifest#1 在位且 digest 与在案值一致(锚的根)
DO $$
DECLARE d text;
BEGIN
  SELECT digest INTO d FROM study_snapshot WHERE snapshot_id = 1;
  IF d IS NULL OR d NOT LIKE '2a8a271f%' THEN
    RAISE EXCEPTION '修法#3 前置断言失败: manifest#1 缺失或 digest 非在案值(得到 %),迁移中止', d;
  END IF;
END $$;

INSERT INTO public.batch_lineage_registry
  (batch_table, batch_id, lineage_status, source_anchor, evidence_ref, approval_ref)
SELECT v.tbl, v.bid, 'verified',
       jsonb_build_object(
         'qbase', s.content->'qbase',
         'source_manifest', jsonb_build_object('snapshot_id', s.snapshot_id, 'digest', s.digest),
         'basis', 'qbase 九批全部 pull_time=2026-07-07 且此后零新批(append-only 时间戳重构)'
       ) || CASE WHEN v.tbl = 'pool_b1_return_batch'
                 THEN jsonb_build_object('taosha_parent', jsonb_build_object('pool_b1',
                        (SELECT pool_batch_id FROM pool_b1_return_batch WHERE batch_id = v.bid)))
                 ELSE '{}'::jsonb END,
       v.ev,
       'docs/postaudit-five-order-2026-07-13.md #3(人终签 2026-07-13)'
FROM (VALUES
  ('market_batch', 1::bigint,
   'taosha/docs/slice3-step3-market-return-acceptance-2026-07-08.md(人签收 a7639f1)'),
  ('market_batch', 2::bigint,
   'taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md(并发写探针批,②验收)'),
  ('pool_b1_batch', 1::bigint,
   'taosha/docs/slice3-step2-drawdown-eventver-acceptance-2026-07-09.md(b1池 batch=1,2,948,735 成员行)'),
  ('pool_b1_return_batch', 1::bigint,
   'taosha/docs/slice3-step2-drawdown-eventver-acceptance-2026-07-09.md(--verify 硬项;行内 pool_batch_id=1 FK 实物)')
) AS v(tbl, bid, ev)
CROSS JOIN (SELECT snapshot_id, digest, content FROM study_snapshot WHERE snapshot_id = 1) s;

-- ── ④ manifest 生成双检: 血缘相容 + 血缘可信(fail-closed) ────────────────────
CREATE OR REPLACE FUNCTION public._batch_lineage_trusted(p_table text, p_batch bigint)
RETURNS boolean LANGUAGE plpgsql STABLE AS $$
DECLARE ok boolean;
BEGIN
  IF p_table NOT IN ('market_batch', 'pool_b1_batch', 'pool_b1_return_batch') THEN
    RETURN false;
  END IF;
  SELECT EXISTS (SELECT 1 FROM batch_lineage_registry
                 WHERE batch_table = p_table AND batch_id = p_batch
                   AND lineage_status = 'verified') INTO ok;
  IF ok THEN RETURN true; END IF;
  EXECUTE format('SELECT EXISTS (SELECT 1 FROM public.%I WHERE batch_id = $1 '
                 'AND source_anchor IS NOT NULL)', p_table) INTO ok USING p_batch;
  RETURN ok;
END $$;

CREATE OR REPLACE FUNCTION public.study_snapshot_biu() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE b_mr bigint; b_p bigint; b_pr bigint; parent bigint;
BEGIN
  -- ── 承 006 原检 ──
  IF NEW.content->'qbase' IS NULL OR NEW.content->'taosha' IS NULL THEN
    RAISE EXCEPTION 'StudySnapshot: content 须含 qbase 与 taosha 两半批次向量';
  END IF;
  IF NEW.created_by = 'taosha_engine' THEN
    RAISE EXCEPTION 'StudySnapshot: 生成角色不得为 taosha_engine(硬化②,受权角色专责)';
  END IF;

  -- ── 修法#3: taosha 三键完备(fail-closed 在源头) ──
  b_mr := (NEW.content->'taosha'->>'market_return')::bigint;
  b_p  := (NEW.content->'taosha'->>'pool_b1')::bigint;
  b_pr := (NEW.content->'taosha'->>'pool_b1_return')::bigint;
  IF b_mr IS NULL OR b_p IS NULL OR b_pr IS NULL THEN
    RAISE EXCEPTION '修法#3: taosha 批次向量须含 market_return/pool_b1/pool_b1_return 三键';
  END IF;

  -- ── 修法#3a: 血缘相容(至少强制项): pool_b1_return 批的父池批 == manifest.pool_b1 ──
  SELECT pool_batch_id INTO parent FROM pool_b1_return_batch WHERE batch_id = b_pr;
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#3: pool_b1_return 批 % 不存在', b_pr;
  END IF;
  IF parent <> b_p THEN
    RAISE EXCEPTION '修法#3: 血缘不相容——pool_b1_return 批 % 派生自池批 %,manifest.pool_b1=%(拒生成)',
      b_pr, parent, b_p;
  END IF;

  -- ── 修法#3b: 血缘可信: 三派生批各须 registry verified 或行内 source_anchor 非空 ──
  IF NOT public._batch_lineage_trusted('market_batch', b_mr) THEN
    RAISE EXCEPTION '修法#3: market_return 批 % 血缘不可证(未登记/legacy-unverified/无源锚),不允许生成正式研究 manifest', b_mr;
  END IF;
  IF NOT public._batch_lineage_trusted('pool_b1_batch', b_p) THEN
    RAISE EXCEPTION '修法#3: pool_b1 批 % 血缘不可证,不允许生成正式研究 manifest', b_p;
  END IF;
  IF NOT public._batch_lineage_trusted('pool_b1_return_batch', b_pr) THEN
    RAISE EXCEPTION '修法#3: pool_b1_return 批 % 血缘不可证,不允许生成正式研究 manifest', b_pr;
  END IF;

  -- 规范化内容摘要由库权威计算(承 006,jsonb::text = PG 确定性序列化),忽略调用方传值
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;

COMMENT ON FUNCTION public.study_snapshot_biu() IS
  'StudySnapshot BEFORE INSERT(006 硬化② + 010 修法#3): 两半向量+非引擎角色+digest 库算'
  '+血缘相容(pool_b1_return.pool_batch_id==pool_b1)+血缘可信(registry verified 或 source_anchor)。'
  '作废(010): 006 时期"manifest 生成无血缘交叉校验"的状态。';

COMMIT;
