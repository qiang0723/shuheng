-- 淘沙 · 014 派生批锚=实际依赖键集合 + 源级快照(外审第三轮窄补 #3,2026-07-13,人终签)
-- 依据: docs/postaudit-round3-narrow-order-2026-07-13.md #3-a/#3-b(F 条留痕 67150fb)。
--
-- 缺口(外部第二独立视角复核退回,实物坐实):
--   #3-a: 013 derived_batch_bi 要求锚 qbase 向量 == 所绑 manifest qbase 半**全等**(013:83),
--         且三 seed 把整个 qbase 向量写入锚 → 与派生批无依赖的源(forecast/stk_holdertrade)
--         刷新也会使批次"不相容"——违反已明确判据(验收重点=血缘相容性,非全批次号相等)。
--   #3-b: 合法再种路径**循环死锁**(013:18 自认"刷新源→新 manifest 拒生成"为 fail-closed 方向,
--         但 seed 又必须绑定已发布快照,发布=生成 manifest 又被拒)→ 设计断裂,本轮必须解决。
--
-- 修法:
--   ① _derived_qbase_deps(tbl): 各派生批 → 实际 qbase 依赖键集合(SQL 权威镜像;python 侧
--      snapshot.DERIVED_BATCH_QBASE_DEPS 同表,自检逐键交叉断言)。依据=各 seed 实际读径:
--        market_batch         = {adj_factor, daily, namechange, stock_basic, trade_cal}
--                               (explore_reader_prices_snap 内联四源 + calendar_snap)
--        pool_b1_batch        = {daily, stock_basic, trade_cal}
--                               (bar_daily_snap.amount 原始额不复权 + entity_master 上市界 + 轴)
--        pool_b1_return_batch = {adj_factor, daily, namechange, stock_basic, trade_cal}
--                               (同 market 读径;taosha 父池批走 taosha_parent 锚,非 qbase 键)
--   ② derived_batch_bi 升级: 锚 qbase 键集合 == 依赖集合**不多不少**(多键=过锚重罚无辜源、
--      少键=依赖不可证,均拒),且逐键与所绑 manifest qbase 半相等(manifest 可含更多键);
--      ~~013 全向量全等~~ 作废。承 013: 严格 schema/manifest 在位/digest 逐字/pool 父批锚行一致。
--   ③ study_snapshot_biu 分域: content 含 taosha 键 = **研究 manifest**(承 006/010/013 全检:
--      两半向量+三键完备+pool 父批相容+三派生批锚 schema+逐键相容);content 仅 qbase 半 =
--      **源级快照**(#3-b 合法再种链第一环: 只检 qbase 半非空+REQUIRED 六键+非引擎角色+库算
--      digest,不检派生批——它就是给"源刷新后、派生批再种前"这个窗口用的)。
--      消费面 fail-closed 已在位: 引擎 ViewReader 对缺 taosha 半的快照直接拒(view.py,实测);
--      qbase study_snap_batch() 读 content->'qbase'->>key 对两类快照同式(零改动)。
--   合法再种链(#3-b): 刷新源批 → --create-source 源级快照(发布=镜像+attestation 同机制)
--      → 三 seed --source-snapshot-id 绑之再种 → --create 研究 manifest(最新派生批锚相容→放行)。
--
-- 正向控制不弱化: 研究 manifest 的全部 013 检查逐字保留;源级快照不可被引擎当研究 manifest
--   消费(ViewReader fail-closed);派生批锚仍须绑定库内真实已发布快照(digest 逐字)。
-- 回滚边界: derived_batch_bi()/study_snapshot_biu() 重放 013 定义;DROP _derived_qbase_deps()。
-- apply 身份 = postgres(taosha 库属主,承 001-013)。
-- 前置断言: 存量 4 registry verified 锚(历史批,全向量式)不受本迁移影响(它们非新 INSERT;
--   manifest 双检对其仍走逐键相容=向量键 ⊆ manifest 且值等,manifest#1/#2 实测相容,迁移中
--   DO 块复验不过即中止)。

BEGIN;

-- ── ① 依赖键映射(SQL 权威;python snapshot.DERIVED_BATCH_QBASE_DEPS 为镜像) ─────────
CREATE OR REPLACE FUNCTION public._derived_qbase_deps(p_table text) RETURNS text[]
LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE p_table
    WHEN 'market_batch'         THEN ARRAY['adj_factor','daily','namechange','stock_basic','trade_cal']
    WHEN 'pool_b1_batch'        THEN ARRAY['daily','stock_basic','trade_cal']
    WHEN 'pool_b1_return_batch' THEN ARRAY['adj_factor','daily','namechange','stock_basic','trade_cal']
    ELSE NULL
  END
$$;
COMMENT ON FUNCTION public._derived_qbase_deps(text) IS
  '窄补第三轮 #3-a: 派生批次表 → 实际 qbase 依赖键集合(不多不少;依据=seed 实际读径,'
  '验收档 postaudit-round3;forecast/stk_holdertrade 与三派生批无依赖,不入锚)。';

-- ── ② 派生批次 BEFORE INSERT: 锚=依赖键集合不多不少 + 逐键与所绑 manifest 相等 ──────
CREATE OR REPLACE FUNCTION public.derived_batch_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE reason text; sid bigint; m_digest text; m_qbase jsonb; p bigint;
        deps text[]; anchor_keys text[]; k text; v jsonb; mv jsonb;
BEGIN
  IF NEW.source_anchor IS NULL THEN
    RAISE EXCEPTION '修法#3: 新派生批次须锚定源(source_anchor=依赖键向量+source_manifest),从 ingest 起强制(表 %)', TG_TABLE_NAME;
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
  -- 窄补第三轮 #3-a: 锚 qbase 键集合 == 实际依赖键集合(不多不少;~~013 全向量全等~~作废)
  deps := public._derived_qbase_deps(TG_TABLE_NAME);
  IF deps IS NULL THEN
    RAISE EXCEPTION '窄补#3-a: 表 % 无依赖键映射(不默认不猜)', TG_TABLE_NAME;
  END IF;
  SELECT array_agg(key ORDER BY key) INTO anchor_keys
  FROM jsonb_object_keys(NEW.source_anchor->'qbase') AS key;
  IF anchor_keys IS DISTINCT FROM (SELECT array_agg(x ORDER BY x) FROM unnest(deps) x) THEN
    RAISE EXCEPTION '窄补#3-a: % 锚 qbase 键集合 % ≠ 实际依赖键集合 %(不多不少;多键=过锚,少键=依赖不可证)',
      TG_TABLE_NAME, anchor_keys, deps;
  END IF;
  FOR k, v IN SELECT * FROM jsonb_each(NEW.source_anchor->'qbase') LOOP
    mv := m_qbase->k;
    IF mv IS NULL OR mv IS DISTINCT FROM v THEN
      RAISE EXCEPTION '窄补#3-a: % 锚依赖键 %=% 与所绑定快照 % 的向量值 % 不一致(锚必须=实际所读已发布快照之依赖键值)',
        TG_TABLE_NAME, k, v, sid, coalesce(mv::text, '<缺>');
    END IF;
  END LOOP;
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
  '派生批次 BEFORE INSERT(010 强制非空 + 013 严格 schema/绑定真实 manifest + 014 窄补第三轮:'
  '锚 qbase 键集合==实际依赖键集合不多不少、逐键与所绑快照相等〔快照可含更多键〕)。'
  '作废(014): 013 的锚==manifest qbase 半全向量全等。';

-- ── ③ StudySnapshot BEFORE INSERT: 研究 manifest / 源级快照分域(#3-b) ───────────────
CREATE OR REPLACE FUNCTION public.study_snapshot_biu() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE b_mr bigint; b_p bigint; b_pr bigint; parent bigint;
        t record; a jsonb; reason text; k text; v jsonb; mv jsonb; req text;
BEGIN
  IF NEW.created_by = 'taosha_engine' THEN
    RAISE EXCEPTION 'StudySnapshot: 生成角色不得为 taosha_engine(硬化②,受权角色专责)';
  END IF;
  IF NEW.content->'qbase' IS NULL OR jsonb_typeof(NEW.content->'qbase') <> 'object'
     OR NEW.content->'qbase' = '{}'::jsonb THEN
    RAISE EXCEPTION 'StudySnapshot: content 须含非空 qbase 批次向量';
  END IF;

  IF NEW.content ? 'taosha' THEN
    -- ══ 研究 manifest 域: 013 全检逐字保留 ══
    b_mr := (NEW.content->'taosha'->>'market_return')::bigint;
    b_p  := (NEW.content->'taosha'->>'pool_b1')::bigint;
    b_pr := (NEW.content->'taosha'->>'pool_b1_return')::bigint;
    IF b_mr IS NULL OR b_p IS NULL OR b_pr IS NULL THEN
      RAISE EXCEPTION '修法#3: taosha 批次向量须含 market_return/pool_b1/pool_b1_return 三键';
    END IF;
    SELECT pool_batch_id INTO parent FROM pool_b1_return_batch WHERE batch_id = b_pr;
    IF NOT FOUND THEN
      RAISE EXCEPTION '修法#3: pool_b1_return 批 % 不存在', b_pr;
    END IF;
    IF parent <> b_p THEN
      RAISE EXCEPTION '修法#3: 血缘不相容——pool_b1_return 批 % 派生自池批 %,manifest.pool_b1=%(拒生成)',
        b_pr, parent, b_p;
    END IF;
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
  ELSE
    -- ══ 源级快照域(窄补第三轮 #3-b): 仅 qbase 半;REQUIRED 六键完备(fail-closed 在源头)══
    -- 用途=合法再种链第一环(源刷新后、派生批再种前);不检派生批相容(那正是它要打断的死锁);
    -- 引擎消费面 fail-closed(ViewReader 拒缺 taosha 半)= 源级快照不可当研究 manifest 用。
    FOREACH req IN ARRAY ARRAY['stock_basic','namechange','trade_cal','daily','adj_factor','forecast'] LOOP
      IF NEW.content->'qbase'->req IS NULL THEN
        RAISE EXCEPTION '窄补#3-b: 源级快照 qbase 向量缺必需键 %(先补齐源批次)', req;
      END IF;
    END LOOP;
  END IF;

  -- 规范化内容摘要由库权威计算(承 006,jsonb::text = PG 确定性序列化),忽略调用方传值
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;
COMMENT ON FUNCTION public.study_snapshot_biu() IS
  'StudySnapshot BEFORE INSERT(006 硬化② + 010/013 修法#3 + 014 窄补第三轮): 分域——'
  '含 taosha 半=研究 manifest(013 全检逐字保留: 三键完备+pool 父批相容+三派生批锚 schema'
  '+qbase 向量逐键相容);仅 qbase 半=源级快照(#3-b 合法再种链第一环,REQUIRED 六键+非引擎'
  '角色+库算 digest;引擎消费面 ViewReader fail-closed 拒缺 taosha 半)。';

-- ── ⑤ 前置断言: 存量 4 registry verified 锚仍与 manifest#1 逐键相容(承 013,复验不过即中止)──
DO $$
DECLARE r record; reason text; k text; v jsonb; mv jsonb; m1 jsonb; n_reg int;
BEGIN
  SELECT content->'qbase' INTO m1 FROM study_snapshot WHERE snapshot_id = 1;
  IF m1 IS NULL THEN
    RAISE EXCEPTION '窄补第三轮 前置断言失败: manifest#1 缺失';
  END IF;
  SELECT count(*) INTO n_reg FROM batch_lineage_registry WHERE lineage_status = 'verified';
  IF n_reg <> 4 THEN
    RAISE EXCEPTION '窄补第三轮 前置断言失败: registry verified 应 4 行,实 %(库实况变动须人裁)', n_reg;
  END IF;
  FOR r IN SELECT batch_table, batch_id, source_anchor FROM batch_lineage_registry
           WHERE lineage_status = 'verified' LOOP
    reason := public._anchor_schema_reason(r.source_anchor);
    IF reason IS NOT NULL THEN
      RAISE EXCEPTION '窄补第三轮 前置断言失败: registry(%,%) 锚不过严格 schema——%',
        r.batch_table, r.batch_id, reason;
    END IF;
    FOR k, v IN SELECT * FROM jsonb_each(r.source_anchor->'qbase') LOOP
      mv := m1->k;
      IF mv IS NULL OR mv IS DISTINCT FROM v THEN
        RAISE EXCEPTION '窄补第三轮 前置断言失败: registry(%,%) 锚源 % 与 manifest#1 不相容(%≠%)',
          r.batch_table, r.batch_id, k, v, coalesce(mv::text, '<缺>');
      END IF;
    END LOOP;
  END LOOP;
END $$;

COMMIT;
