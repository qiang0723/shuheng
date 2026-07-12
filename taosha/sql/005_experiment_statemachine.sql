-- 淘沙台账 · 状态机焊死(可信度硬化窗口 ①,人批 2026-07-12)
-- 修法(人令原文即口径): result 仅可随 running→done 首写;frozen_at 仅可随 registered→frozen 写;
--   done_at 仅可随迁移写 —— 字段变更绑定唯一合法迁移。
-- 人拍A(2026-07-12,closed 关闭原因载体): close 停写 result_json,新增 closure_reason 列
--   (仅可随 registered/frozen→closed 迁移一次性写);exp2 历史行(closed 且 result_json 有值)
--   原样保留不动,触发器只辖此后变更。
-- 出生焊死(工程加固,随验收档上报架构窗口): INSERT 出生态仅允许 registered/frozen;
--   result_json/done_at/closure_reason 出生必空 —— 堵"出生即 done 带 result"绕道,
--   使 result 首写在结构上唯一地发生于 running→done 迁移。
-- 依据: docs/hardening-window-order-2026-07-12.md ①;验收档 taosha/docs/hardening-item1-statemachine-acceptance-2026-07-12.md

BEGIN;

ALTER TABLE experiment ADD COLUMN IF NOT EXISTS closure_reason text;
COMMENT ON COLUMN experiment.closure_reason IS
  '关闭原因(硬化① 人拍A):仅可随 registered/frozen→closed 迁移一次性写入;result_json 自此纯装研究结果';

-- ── BEFORE INSERT: family_trial 自增 + llm→prescreen + 出生态焊死 ─────────────
CREATE OR REPLACE FUNCTION experiment_biu() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  -- family_trial 触发器自增(忽略调用方传值,焊死"改参=新行、family 继承计数+1")
  SELECT COALESCE(MAX(family_trial), 0) + 1 INTO NEW.family_trial
    FROM experiment WHERE family = NEW.family;

  -- 铁律①: source_type=llm → verdict_power 必须 prescreen
  IF NEW.source_type = 'llm' AND NEW.verdict_power <> 'prescreen' THEN
    RAISE EXCEPTION '铁律①违反: source_type=llm 强制 verdict_power=prescreen(得到 %)', NEW.verdict_power;
  END IF;

  -- 硬化①出生焊死: 出生态白名单(running/done/closed 只能经迁移到达)
  IF NEW.status NOT IN ('registered', 'frozen') THEN
    RAISE EXCEPTION '硬化①: INSERT 出生态仅允许 registered/frozen(得到 %)', NEW.status;
  END IF;

  -- 硬化①出生焊死: 迁移绑定字段出生必空
  IF NEW.result_json IS NOT NULL OR NEW.done_at IS NOT NULL OR NEW.closure_reason IS NOT NULL THEN
    RAISE EXCEPTION '硬化①: result_json/done_at/closure_reason 不得随 INSERT 写入(result 仅可随 running→done 首写)';
  END IF;

  -- 冻结态一致性: frozen 出生须带 frozen_at;registered 出生不得带 frozen_at
  IF NEW.status = 'frozen' AND NEW.frozen_at IS NULL THEN
    RAISE EXCEPTION '登记冻结态须同时置 frozen_at';
  END IF;
  IF NEW.status = 'registered' AND NEW.frozen_at IS NOT NULL THEN
    RAISE EXCEPTION '硬化①: registered 出生不得带 frozen_at(frozen_at 仅可随 registered→frozen 迁移写)';
  END IF;
  RETURN NEW;
END $$;

-- ── BEFORE UPDATE: 字段变更绑定唯一合法迁移(反向+正向双控核心) ───────────────
CREATE OR REPLACE FUNCTION experiment_bu() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  -- 永久不可变列
  IF NEW.family <> OLD.family OR NEW.family_trial <> OLD.family_trial
     OR NEW.title <> OLD.title OR NEW.source_type <> OLD.source_type
     OR NEW.verdict_power <> OLD.verdict_power
     OR NEW.registered_at <> OLD.registered_at THEN
    RAISE EXCEPTION '不可变列被改(family/family_trial/title/source_type/verdict_power/registered_at)';
  END IF;

  -- status 单向推进(合法迁移白名单;先判,后续字段绑定引用)
  IF NEW.status <> OLD.status THEN
    IF NOT ( (OLD.status='registered' AND NEW.status IN ('frozen','closed'))
          OR (OLD.status='frozen'     AND NEW.status IN ('running','closed'))
          OR (OLD.status='running'    AND NEW.status='done') ) THEN
      RAISE EXCEPTION 'status 非法迁移: % → %', OLD.status, NEW.status;
    END IF;
  END IF;

  -- 铁律④: pap_json 仅 registered 态(未冻结)可完善
  IF NEW.pap_json IS DISTINCT FROM OLD.pap_json THEN
    IF OLD.frozen_at IS NOT NULL OR OLD.status <> 'registered' THEN
      RAISE EXCEPTION '铁律④违反: pap_json 冻结后/离开 registered 态不可改(改参=INSERT 新行)';
    END IF;
  END IF;

  -- 硬化①: frozen_at 仅可随 registered→frozen 迁移一次性写入
  IF NEW.frozen_at IS DISTINCT FROM OLD.frozen_at THEN
    IF NOT (OLD.frozen_at IS NULL AND OLD.status='registered' AND NEW.status='frozen') THEN
      RAISE EXCEPTION '硬化①: frozen_at 仅可随 registered→frozen 迁移一次性写入';
    END IF;
  END IF;

  -- 硬化①: result_json 仅可随 running→done 迁移一次性首写
  IF NEW.result_json IS DISTINCT FROM OLD.result_json THEN
    IF NOT (OLD.result_json IS NULL AND OLD.status='running' AND NEW.status='done') THEN
      RAISE EXCEPTION '硬化①: result_json 仅可随 running→done 迁移一次性首写';
    END IF;
  END IF;

  -- 硬化①: done_at 仅可随迁移写(running→done 或 registered/frozen→closed),一次性
  IF NEW.done_at IS DISTINCT FROM OLD.done_at THEN
    IF NOT (OLD.done_at IS NULL AND
            ( (OLD.status='running' AND NEW.status='done')
           OR (OLD.status IN ('registered','frozen') AND NEW.status='closed') )) THEN
      RAISE EXCEPTION '硬化①: done_at 仅可随 running→done 或 →closed 迁移一次性写入';
    END IF;
  END IF;

  -- 硬化①(人拍A): closure_reason 仅可随 registered/frozen→closed 迁移一次性写入
  IF NEW.closure_reason IS DISTINCT FROM OLD.closure_reason THEN
    IF NOT (OLD.closure_reason IS NULL
            AND OLD.status IN ('registered','frozen') AND NEW.status='closed') THEN
      RAISE EXCEPTION '硬化①: closure_reason 仅可随 registered/frozen→closed 迁移一次性写入';
    END IF;
  END IF;

  -- 迁移完备性: 进入目标态必须同置绑定字段
  IF NEW.status <> OLD.status THEN
    IF NEW.status='frozen' AND NEW.frozen_at IS NULL THEN
      RAISE EXCEPTION '推进到 frozen 须同步置 frozen_at';
    END IF;
    IF NEW.status='done' AND (NEW.result_json IS NULL OR NEW.done_at IS NULL) THEN
      RAISE EXCEPTION '推进到 done 须同步置 result_json 与 done_at';
    END IF;
    IF NEW.status='closed' AND (NEW.closure_reason IS NULL OR NEW.done_at IS NULL) THEN
      RAISE EXCEPTION '推进到 closed 须同步置 closure_reason 与 done_at(人拍A: 关闭原因入 closure_reason)';
    END IF;
  END IF;

  RETURN NEW;
END $$;

COMMIT;
