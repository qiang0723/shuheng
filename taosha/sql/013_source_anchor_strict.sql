-- 淘沙 · source_anchor 严格 schema + manifest 血缘真相容(外审第二轮窄补 #3,2026-07-13)
-- 缺口(外审复审退回,施工前探针坐实):
--   P-A: derived_batch_bi 仅查 IS NOT NULL → source_anchor={} 空锚批次 INSERT 放行;
--   P-B: _batch_lineage_trusted 仅查"是否非 NULL" → 锚 qbase 向量与 manifest 向量全不匹配
--        的批次照样入 manifest(生成放行)——"稳定复现但血缘不一致"。
-- 修法(窄补令原文即口径):
--   ① source_anchor 严格 schema: 拒 {} 及缺失关键字段的锚。关键字段=
--      qbase(非空源批次向量对象,值全为批次号数值)+ source_manifest{snapshot_id, digest(64hex)};
--      pool_b1_return_batch 另须 taosha_parent.pool_b1 == 行内 pool_batch_id。
--   ② 批次 INSERT 时锚须绑定库内真实 manifest: snapshot_id 在 study_snapshot 在位、digest 逐字
--      一致、锚 qbase 向量==该 manifest 的 qbase 半(锚=实际所读已发布快照向量,拒伪锚;
--      attestation 强制在 qbase 读径 fail-closed,taosha 侧核 manifest 实物+digest)。
--   ③ manifest 生成双检升级: 三派生批各解析其锚(行内 source_anchor 优先,历史批走 registry
--      verified 锚),锚过严格 schema 且其 qbase 向量与 NEW.content->'qbase' **逐键相容**
--      (锚中每一源键须在 manifest 向量中在位且批次号相等;manifest 多出的新源键不冲突)
--      ——不相容拒绝生成,~~仅"是否非 NULL"检查~~ 作废。
-- 相容性口径注记: 锚键 ⊆ manifest 键且值全等=派生批所读源与 manifest 宣称源一致;qbase 若
--   刷新既有源批次,旧派生批即与新向量不相容 → 新 manifest 拒生成(fail-closed 方向,须按序
--   再种派生批;流程届时人令排产,本迁移不留后门)。
-- 回滚边界: derived_batch_bi()/study_snapshot_biu() 重放 010 定义;恢复 010 的
--   _batch_lineage_trusted();DROP _anchor_schema_reason()/_batch_lineage_anchor()。
-- apply 身份 = postgres(taosha 库属主,承 001-012)。
-- 依据: docs/postaudit-round2-narrow-order-2026-07-13.md #3;
--   验收档 taosha/docs/postaudit-round2-narrow-acceptance-2026-07-13.md

BEGIN;

-- ── ① 严格 schema 判定(单一来源: 批次触发器与 manifest 双检共用) ────────────────
CREATE OR REPLACE FUNCTION public._anchor_schema_reason(a jsonb) RETURNS text
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE k text; v jsonb; sm jsonb;
BEGIN
  IF a IS NULL THEN RETURN 'source_anchor 为 NULL'; END IF;
  IF jsonb_typeof(a) <> 'object' OR a = '{}'::jsonb THEN
    RETURN '空锚 {} 或非对象';
  END IF;
  IF jsonb_typeof(a->'qbase') IS DISTINCT FROM 'object' OR a->'qbase' = '{}'::jsonb THEN
    RETURN '缺关键字段 qbase(须为非空源批次向量对象)';
  END IF;
  FOR k, v IN SELECT * FROM jsonb_each(a->'qbase') LOOP
    IF jsonb_typeof(v) <> 'number' THEN
      RETURN format('qbase 向量键 %s 非批次号数值', k);
    END IF;
  END LOOP;
  sm := a->'source_manifest';
  IF jsonb_typeof(sm) IS DISTINCT FROM 'object' THEN
    RETURN '缺关键字段 source_manifest{snapshot_id, digest}';
  END IF;
  IF jsonb_typeof(sm->'snapshot_id') IS DISTINCT FROM 'number' THEN
    RETURN 'source_manifest.snapshot_id 缺失或非数值';
  END IF;
  IF coalesce(sm->>'digest', '') !~ '^[0-9a-f]{64}$' THEN
    RETURN 'source_manifest.digest 缺失或非 64 位小写 hex';
  END IF;
  RETURN NULL;   -- 合法
END $$;
COMMENT ON FUNCTION public._anchor_schema_reason(jsonb) IS
  'source_anchor 严格 schema 判定(窄补#3): 合法→NULL,非法→原因文本。拒 {}/缺 qbase/'
  '缺 source_manifest/批次号非数值/digest 非 64hex。';

-- ── ② 派生批次 BEFORE INSERT: 严格 schema + 绑定库内真实 manifest(承 010 强制非空) ──
CREATE OR REPLACE FUNCTION public.derived_batch_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE reason text; sid bigint; m_digest text; m_qbase jsonb; p bigint;
BEGIN
  IF NEW.source_anchor IS NULL THEN
    RAISE EXCEPTION '修法#3: 新派生批次须锚定源(source_anchor=已发布快照的 qbase 向量+source_manifest),从 ingest 起强制(表 %)', TG_TABLE_NAME;
  END IF;
  reason := public._anchor_schema_reason(NEW.source_anchor);
  IF reason IS NOT NULL THEN
    RAISE EXCEPTION '修法#3(窄补): source_anchor 严格 schema 不过——%(表 %;拒 {} 及缺关键字段的锚)',
      reason, TG_TABLE_NAME;
  END IF;
  sid := (NEW.source_anchor->'source_manifest'->>'snapshot_id')::bigint;
  SELECT digest, content->'qbase' INTO m_digest, m_qbase
  FROM public.study_snapshot WHERE snapshot_id = sid;
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#3(窄补): source_anchor 绑定的 manifest % 不存在(seed 须绑定已发布 snapshot,禁 current/max 现值为锚)', sid;
  END IF;
  IF m_digest IS DISTINCT FROM (NEW.source_anchor->'source_manifest'->>'digest') THEN
    RAISE EXCEPTION '修法#3(窄补): source_anchor.source_manifest.digest 与 manifest % 库内 digest 不一致(拒伪锚)', sid;
  END IF;
  IF m_qbase IS DISTINCT FROM (NEW.source_anchor->'qbase') THEN
    RAISE EXCEPTION '修法#3(窄补): source_anchor.qbase 向量与所绑定 manifest % 的 qbase 半不一致(锚必须=实际所读已发布快照向量)', sid;
  END IF;
  IF TG_TABLE_NAME = 'pool_b1_return_batch' THEN
    p := (NEW.source_anchor->'taosha_parent'->>'pool_b1')::bigint;
    IF p IS NULL OR p <> NEW.pool_batch_id THEN
      RAISE EXCEPTION '修法#3(窄补): pool_b1_return 批锚须含 taosha_parent.pool_b1 且==行内 pool_batch_id(锚 % / 行 %)',
        coalesce(p::text, '<缺>'), NEW.pool_batch_id;
    END IF;
  END IF;
  RETURN NEW;
END $$;
COMMENT ON FUNCTION public.derived_batch_bi() IS
  '派生批次 BEFORE INSERT(010 强制非空 + 013 窄补): source_anchor 严格 schema(拒 {}/缺关键
  字段)+绑定库内真实 manifest(snapshot_id 在位/digest 逐字一致/qbase 向量==manifest qbase 半)
  +pool_b1_return 父池批锚行一致。作废(013): 010 的仅 NOT NULL 判定。';

-- ── ③ 锚解析(行内优先,历史批走 registry verified;不可证→NULL) ─────────────────
CREATE OR REPLACE FUNCTION public._batch_lineage_anchor(p_table text, p_batch bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE a jsonb;
BEGIN
  IF p_table NOT IN ('market_batch', 'pool_b1_batch', 'pool_b1_return_batch') THEN
    RETURN NULL;
  END IF;
  EXECUTE format('SELECT source_anchor FROM public.%I WHERE batch_id = $1', p_table)
    INTO a USING p_batch;
  IF a IS NOT NULL THEN RETURN a; END IF;
  SELECT source_anchor INTO a FROM public.batch_lineage_registry
  WHERE batch_table = p_table AND batch_id = p_batch AND lineage_status = 'verified';
  RETURN a;   -- 批不存在/未登记/legacy-unverified → NULL(血缘不可证)
END $$;

-- ── ④ manifest 生成双检升级: 承 006/010 全检 + 锚 schema + qbase 向量逐键相容 ──────
CREATE OR REPLACE FUNCTION public.study_snapshot_biu() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE b_mr bigint; b_p bigint; b_pr bigint; parent bigint;
        t record; a jsonb; reason text; k text; v jsonb; mv jsonb;
BEGIN
  -- ── 承 006 原检 ──
  IF NEW.content->'qbase' IS NULL OR NEW.content->'taosha' IS NULL THEN
    RAISE EXCEPTION 'StudySnapshot: content 须含 qbase 与 taosha 两半批次向量';
  END IF;
  IF NEW.created_by = 'taosha_engine' THEN
    RAISE EXCEPTION 'StudySnapshot: 生成角色不得为 taosha_engine(硬化②,受权角色专责)';
  END IF;

  -- ── 承 010: taosha 三键完备(fail-closed 在源头) ──
  b_mr := (NEW.content->'taosha'->>'market_return')::bigint;
  b_p  := (NEW.content->'taosha'->>'pool_b1')::bigint;
  b_pr := (NEW.content->'taosha'->>'pool_b1_return')::bigint;
  IF b_mr IS NULL OR b_p IS NULL OR b_pr IS NULL THEN
    RAISE EXCEPTION '修法#3: taosha 批次向量须含 market_return/pool_b1/pool_b1_return 三键';
  END IF;

  -- ── 承 010 修法#3a: 血缘相容强制项: pool_b1_return 批的父池批 == manifest.pool_b1 ──
  SELECT pool_batch_id INTO parent FROM pool_b1_return_batch WHERE batch_id = b_pr;
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#3: pool_b1_return 批 % 不存在', b_pr;
  END IF;
  IF parent <> b_p THEN
    RAISE EXCEPTION '修法#3: 血缘不相容——pool_b1_return 批 % 派生自池批 %,manifest.pool_b1=%(拒生成)',
      b_pr, parent, b_p;
  END IF;

  -- ── 修法#3b(013 窄补): 锚可证+schema 合法+qbase 向量逐键相容(作废仅非 NULL 判定) ──
  FOR t IN SELECT * FROM (VALUES ('market_batch', b_mr, 'market_return'),
                                 ('pool_b1_batch', b_p, 'pool_b1'),
                                 ('pool_b1_return_batch', b_pr, 'pool_b1_return'))
           AS x(tbl, bid, key) LOOP
    a := public._batch_lineage_anchor(t.tbl, t.bid);
    IF a IS NULL THEN
      RAISE EXCEPTION '修法#3: % 批 % 血缘不可证(未登记/legacy-unverified/无源锚),不允许生成正式研究 manifest',
        t.key, t.bid;
    END IF;
    reason := public._anchor_schema_reason(a);
    IF reason IS NOT NULL THEN
      RAISE EXCEPTION '修法#3(窄补): % 批 % 源锚非法——%(空锚/缺关键字段的锚不得入 manifest)',
        t.key, t.bid, reason;
    END IF;
    FOR k, v IN SELECT * FROM jsonb_each(a->'qbase') LOOP
      mv := NEW.content->'qbase'->k;
      IF mv IS NULL THEN
        RAISE EXCEPTION '修法#3(窄补): 血缘不相容——% 批 % 锚含 qbase 源 %,manifest qbase 向量缺此键(拒生成)',
          t.key, t.bid, k;
      END IF;
      IF mv IS DISTINCT FROM v THEN
        RAISE EXCEPTION '修法#3(窄补): 血缘不相容——% 批 % 的 qbase 源 % 锚=% ≠ manifest=%(拒生成;非仅非NULL检查)',
          t.key, t.bid, k, v, mv;
      END IF;
    END LOOP;
  END LOOP;

  -- 规范化内容摘要由库权威计算(承 006,jsonb::text = PG 确定性序列化),忽略调用方传值
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;
COMMENT ON FUNCTION public.study_snapshot_biu() IS
  'StudySnapshot BEFORE INSERT(006 硬化② + 010 修法#3 + 013 窄补): 两半向量+非引擎角色'
  '+digest 库算+血缘相容(pool 父批)+三派生批锚 schema 合法且 qbase 向量与 manifest 逐键相容。'
  '作废(013): 010 的 _batch_lineage_trusted 仅非 NULL 判定。';

DROP FUNCTION IF EXISTS public._batch_lineage_trusted(text, bigint);

-- ── ⑤ 前置断言: 存量 4 历史批 registry 锚过严格 schema 且与 manifest#1 向量逐键相容 ──
--    (不过=历史锚实物与本修法冲突,须人裁,迁移中止不带病上线)
DO $$
DECLARE r record; reason text; k text; v jsonb; mv jsonb; m1 jsonb;
BEGIN
  SELECT content->'qbase' INTO m1 FROM study_snapshot WHERE snapshot_id = 1;
  IF m1 IS NULL THEN
    RAISE EXCEPTION '窄补#3 前置断言失败: manifest#1 缺失';
  END IF;
  FOR r IN SELECT batch_table, batch_id, source_anchor FROM batch_lineage_registry
           WHERE lineage_status = 'verified' LOOP
    reason := public._anchor_schema_reason(r.source_anchor);
    IF reason IS NOT NULL THEN
      RAISE EXCEPTION '窄补#3 前置断言失败: registry(%,%) 锚不过严格 schema——%',
        r.batch_table, r.batch_id, reason;
    END IF;
    FOR k, v IN SELECT * FROM jsonb_each(r.source_anchor->'qbase') LOOP
      mv := m1->k;
      IF mv IS NULL OR mv IS DISTINCT FROM v THEN
        RAISE EXCEPTION '窄补#3 前置断言失败: registry(%,%) 锚源 % 与 manifest#1 不相容(%≠%)',
          r.batch_table, r.batch_id, k, v, coalesce(mv::text, '<缺>');
      END IF;
    END LOOP;
  END LOOP;
END $$;

COMMIT;
