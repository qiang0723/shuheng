-- qbase · StudySnapshot 权威镜像 + 发布凭证(外审五项修法 #2,人终签 2026-07-13)
-- 攻击路径(外审坐实): 012 的 study_snap_batch() 读 GUC shuheng.study_batches——
--   引擎连接自报的完整批次向量 JSON,库侧零权威对照(跨库不能直查 taosha manifest),
--   伪造向量即可穿透全部 _snap 视图。
-- 修法(人令原文即口径): 权威映射必须落库、受权角色写入、引擎零写权——
--   ① 受权角色创建 taosha manifest(既有 006 流程);
--   ② 在 qbase 写入相同 snapshot_id/content/digest 的不可变镜像(本表,digest 库算忽略传值);
--   ③ 受权角色校验两库内容与 digest 一致后,另行 INSERT append-only 的 publication
--     attestation(不是修改镜像行状态字段);
--   路由视图只接受存在有效 attestation 的 snapshot_id;引擎只传 snapshot_id,不得自报
--   任何批次向量或 token;任一步中断的半成品不可消费、留审计不改不删;
--   两库 canonical digest 算法一致(= sha256(content::text jsonb 规范化, UTF8) hex,
--   与 taosha 006 study_snapshot_biu 逐字同式)并以实测向量验证。
-- 存量回填(我方确认点①,随终签批复): 迁移后由受权角色对既有 manifest#1/#2 执行
--   publish 回填镜像+attestation(publisher=taosha/experiment/snapshot.py --publish),
--   否则一切既有 snapshot 读取 fail-closed——回填本身即审计记录。
-- 回滚边界: study_snap_batch() 重放 012 定义(恢复 GUC 向量路由=有意降级,须人批);
--   mirror/publication 两表为 append-only 审计实物,回滚保留不删。
-- apply 身份 = postgres(表/触发器属主=postgres,qbase_app 仅获 INSERT/SELECT——
--   写入者不能拆焊死;承 001 audit 防拆纪律)。
-- 依据: docs/postaudit-five-order-2026-07-13.md #2;
--   验收档 taosha/docs/postaudit-item2-snapshot-mirror-acceptance-2026-07-13.md

BEGIN;

-- ── 辅助(qbase 侧此前无语句级 TRUNCATE 拒) ─────────────────────────────────
CREATE OR REPLACE FUNCTION public._no_truncate() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only 表 %:禁 TRUNCATE', TG_TABLE_NAME;
END $$;

-- ── ① 权威镜像表(不可变;digest 库算忽略传值=与 taosha 同式规范化) ──────────────
CREATE TABLE IF NOT EXISTS public.study_snapshot_mirror (
  snapshot_id bigint PRIMARY KEY,                 -- == taosha study_snapshot.snapshot_id
  content     jsonb NOT NULL,                     -- 完整 manifest 两半向量(与 taosha 行逐字节同构)
  digest      text  NOT NULL DEFAULT '',          -- 触发器权威计算,忽略传值
  created_by  text  NOT NULL DEFAULT current_user,
  created_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.study_snapshot_mirror IS
  'StudySnapshot 权威镜像(修法#2): taosha manifest 的 qbase 侧不可变落库副本;'
  'digest=sha256(content::text,jsonb 规范化)库算(两库同式);受权角色写入,引擎只读;'
  '仅有镜像而无 publication attestation 的行=半成品,不可消费,留审计不改不删。';

CREATE OR REPLACE FUNCTION public.study_snapshot_mirror_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.content->'qbase' IS NULL OR NEW.content->'taosha' IS NULL THEN
    RAISE EXCEPTION '修法#2: 镜像 content 须含 qbase 与 taosha 两半批次向量';
  END IF;
  IF current_user = 'taosha_engine' THEN
    RAISE EXCEPTION '修法#2: 引擎不得写镜像(受权角色专责)';
  END IF;
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_study_snapshot_mirror_bi ON public.study_snapshot_mirror;
CREATE TRIGGER trg_study_snapshot_mirror_bi BEFORE INSERT ON public.study_snapshot_mirror
  FOR EACH ROW EXECUTE FUNCTION public.study_snapshot_mirror_bi();
DROP TRIGGER IF EXISTS trg_study_snapshot_mirror_freeze ON public.study_snapshot_mirror;
CREATE TRIGGER trg_study_snapshot_mirror_freeze
  BEFORE UPDATE OR DELETE ON public.study_snapshot_mirror
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
DROP TRIGGER IF EXISTS trg_study_snapshot_mirror_no_truncate ON public.study_snapshot_mirror;
CREATE TRIGGER trg_study_snapshot_mirror_no_truncate
  BEFORE TRUNCATE ON public.study_snapshot_mirror
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

-- ── ② 发布凭证(append-only;两库一致性在 INSERT 时焊死,不走 UPDATE 状态位) ─────
CREATE TABLE IF NOT EXISTS public.study_snapshot_publication (
  publication_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  snapshot_id     bigint NOT NULL REFERENCES public.study_snapshot_mirror(snapshot_id),
  attested_digest text   NOT NULL,   -- 受权角色自 taosha manifest 读得的 digest(跨库一致性证词)
  attested_by     text   NOT NULL DEFAULT current_user,
  attested_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.study_snapshot_publication IS
  'StudySnapshot 发布凭证(修法#2): 受权角色校验两库内容/digest 一致后另行 INSERT;'
  '路由只认有凭证的 snapshot_id;attested_digest 必须==镜像库算 digest(触发器焊死)。';

CREATE OR REPLACE FUNCTION public.study_snapshot_publication_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE d text;
BEGIN
  IF current_user = 'taosha_engine' THEN
    RAISE EXCEPTION '修法#2: 引擎不得写发布凭证(受权角色专责)';
  END IF;
  SELECT digest INTO d FROM public.study_snapshot_mirror WHERE snapshot_id = NEW.snapshot_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#2: snapshot % 无镜像,不可发布(先落镜像)', NEW.snapshot_id;
  END IF;
  IF NEW.attested_digest <> d THEN
    RAISE EXCEPTION '修法#2: 两库 digest 不一致(taosha 证词 % / qbase 镜像库算 %),拒发布',
      NEW.attested_digest, d;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_study_snapshot_publication_bi ON public.study_snapshot_publication;
CREATE TRIGGER trg_study_snapshot_publication_bi
  BEFORE INSERT ON public.study_snapshot_publication
  FOR EACH ROW EXECUTE FUNCTION public.study_snapshot_publication_bi();
DROP TRIGGER IF EXISTS trg_study_snapshot_publication_freeze ON public.study_snapshot_publication;
CREATE TRIGGER trg_study_snapshot_publication_freeze
  BEFORE UPDATE OR DELETE ON public.study_snapshot_publication
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
DROP TRIGGER IF EXISTS trg_study_snapshot_publication_no_truncate ON public.study_snapshot_publication;
CREATE TRIGGER trg_study_snapshot_publication_no_truncate
  BEFORE TRUNCATE ON public.study_snapshot_publication
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

-- ── ③ 路由函数收权: 引擎只传 snapshot_id;只认有有效凭证的镜像 ────────────────────
CREATE OR REPLACE FUNCTION public.study_snap_batch(p_key text) RETURNS bigint
LANGUAGE plpgsql STABLE AS $$
DECLARE sid bigint; b bigint;
BEGIN
  -- GUC 未设 → current_setting 自然报错(fail-closed)。
  -- 作废(014): 012 的 GUC shuheng.study_batches 自报向量路由——引擎自报即可伪造。
  sid := current_setting('shuheng.study_snapshot_id')::bigint;
  SELECT (m.content->'qbase'->>p_key)::bigint INTO b
  FROM public.study_snapshot_mirror m
  WHERE m.snapshot_id = sid
    AND EXISTS (SELECT 1 FROM public.study_snapshot_publication p
                WHERE p.snapshot_id = m.snapshot_id AND p.attested_digest = m.digest);
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#2 fail-closed: snapshot % 无有效发布凭证(镜像缺失或未 attested),拒路由', sid;
  END IF;
  IF b IS NULL THEN
    RAISE EXCEPTION '修法#2 fail-closed: snapshot % 镜像 qbase 向量缺键 %', sid, p_key;
  END IF;
  RETURN b;
END $$;

-- ── 授权: 受权角色写(qbase_app,发布程序身份);引擎两表仅 SELECT,零写权 ─────────
GRANT INSERT, SELECT ON public.study_snapshot_mirror      TO qbase_app;
GRANT INSERT, SELECT ON public.study_snapshot_publication TO qbase_app;
GRANT USAGE, SELECT ON SEQUENCE public.study_snapshot_publication_publication_id_seq TO qbase_app;
GRANT SELECT ON public.study_snapshot_mirror      TO taosha_engine;
GRANT SELECT ON public.study_snapshot_publication TO taosha_engine;

COMMIT;
