-- 淘沙 · experiment_addendum result_sha256 库侧锚定(外审五项修法 #5,人终签 2026-07-13)
-- 攻击路径(外审坐实): 007 的 result_sha256 是裸 text 列,库侧零校验——锚定全靠应用层
--   前置断言,任意占位串(如自检曾用的 'probe')可原样入库,附注所指 result 版本可伪造。
-- 修法(人令原文即口径): hash 由数据库从对应 result_json 自动计算,不留"忽略或拒绝"二选一——
--   ①调用方不传 → 库自动计算填写;②显式传入 → 必须与库算值一致,否则拒;
--   ③对应 experiment 无 result_json → 拒绝创建 result-bound 附注(不传则留 NULL=非 result-bound,
--     承 007 注释"无 result 的态可 NULL");④格式约束 = 64 位小写十六进制;⑤既有正确附注行原样保留。
-- 实现取 BEFORE INSERT 触发器而非表 CHECK(我方确认点③,随终签批复):
--   自动计算填写本身需要触发器改 NEW 值;且不做追溯校验(append-only 表既有行不重验,原样保留)。
-- digest 口径(承 007 注释既有约定,唯一): sha256(result_json::text jsonb 规范化, UTF8) hex 小写。
-- 前置断言焊进迁移: 存量行锚与库算 digest 必须全等,任一不等迁移即中止(fail-closed apply;
--   施工前已实测 4 行全等 addendum_id∈{1,4,5,6},id 2/3/7 为回滚探针 identity 空洞、无实行)。
-- 回滚边界: DROP TRIGGER trg_experiment_addendum_bi + DROP FUNCTION experiment_addendum_bi();
--   表结构/数据零触碰。
-- apply 身份 = postgres(taosha 库属主,承 001-008)。
-- 依据: docs/postaudit-five-order-2026-07-13.md #5;
--   验收档 taosha/docs/postaudit-item5-addendum-sha-acceptance-2026-07-13.md

BEGIN;

-- ── 前置断言(fail-closed): 存量非空锚必须与库算 digest 逐行全等 ────────────────
DO $$
DECLARE bad bigint;
BEGIN
  SELECT count(*) INTO bad
  FROM experiment_addendum a JOIN experiment e USING (exp_id)
  WHERE a.result_sha256 IS NOT NULL
    AND a.result_sha256 IS DISTINCT FROM
        encode(sha256(convert_to(e.result_json::text, 'UTF8')), 'hex');
  IF bad > 0 THEN
    RAISE EXCEPTION '修法#5 前置断言失败: % 行存量锚与库算 digest 不等,迁移中止(须停工上报,不得静默两套口径)', bad;
  END IF;
END $$;

-- ── BEFORE INSERT: 库侧权威计算/校验 ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION experiment_addendum_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE computed text;
BEGIN
  SELECT CASE WHEN e.result_json IS NULL THEN NULL
              ELSE encode(sha256(convert_to(e.result_json::text, 'UTF8')), 'hex') END
    INTO computed
  FROM experiment e WHERE e.exp_id = NEW.exp_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION '修法#5: exp % 不存在,附注无所指', NEW.exp_id;
  END IF;

  IF NEW.result_sha256 IS NULL THEN
    -- ①不传 → 库自动计算填写(exp 无 result_json 时 computed=NULL=非 result-bound 附注,合法)
    NEW.result_sha256 := computed;
  ELSE
    -- ④格式约束先行: 64 位小写十六进制
    IF NEW.result_sha256 !~ '^[0-9a-f]{64}$' THEN
      RAISE EXCEPTION '修法#5: result_sha256 须为 64 位小写十六进制(得到 %)', NEW.result_sha256;
    END IF;
    -- ③无 result_json → 拒绝 result-bound
    IF computed IS NULL THEN
      RAISE EXCEPTION '修法#5: exp % 无 result_json,拒绝创建 result-bound 附注(不传 result_sha256 可记非绑定附注)', NEW.exp_id;
    END IF;
    -- ②显式传入必须与库算一致
    IF NEW.result_sha256 <> computed THEN
      RAISE EXCEPTION '修法#5: result_sha256 与库算 digest 不一致(传入 % / 库算 %)', NEW.result_sha256, computed;
    END IF;
  END IF;
  RETURN NEW;
END $$;

COMMENT ON FUNCTION experiment_addendum_bi() IS
  'addendum BEFORE INSERT 库侧锚定(修法#5): result_sha256 库算权威——不传自动填,'
  '传入必须一致,格式 64hex 小写,无 result_json 拒 result-bound。'
  '作废(009): 007 时期"锚定靠应用层前置断言"的口径。';

DROP TRIGGER IF EXISTS trg_experiment_addendum_bi ON public.experiment_addendum;
CREATE TRIGGER trg_experiment_addendum_bi BEFORE INSERT ON public.experiment_addendum
  FOR EACH ROW EXECUTE FUNCTION experiment_addendum_bi();

COMMIT;
