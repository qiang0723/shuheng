-- 淘沙台账 · 出生态收窄为仅 registered(外审五项修法 #4,人终签 2026-07-13)
-- 攻击路径(外审坐实): 005 出生白名单含 frozen 且要求配套 frozen_at ——
--   taosha_app 可 INSERT 出生即 frozen 行,绕过 registered→frozen 的人冻结仪式
--   (冻结 = 人对 PAP 的终审动作,不得由登记方在出生时自我宣告)。
-- 修法(人令原文即口径): 常规 INSERT 路径只允许生成 status='registered';
--   历史导入需求走独立高权限迁移程序(superuser 专项迁移脚本 + 留痕),不复用
--   taosha_app 常规写路径 —— 本次无历史导入需求,该程序不预建,需求出现时另行人批。
-- 影响面: 仓内唯一登记路径 ledger.register() 不写 status(默认 registered)、
--   freeze() 走 UPDATE 迁移 —— 合法路径零影响(正向控制见自检 F1-F10b)。
-- 回滚边界: 本迁移仅 CREATE OR REPLACE experiment_biu();回滚 = 重放 005 中同名
--   函数定义(触发器绑定不变)。台账数据零触碰。
-- 依据: docs/postaudit-five-order-2026-07-13.md #4;
--   验收档 taosha/docs/postaudit-item4-birth-registered-acceptance-2026-07-13.md

BEGIN;

-- ── BEFORE INSERT: family_trial 自增 + llm→prescreen + 出生态焊死(收窄版) ────
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

  -- 修法#4: 出生态唯一合法值 registered(frozen/running/done/closed 只能经迁移到达;
  --   历史导入走独立高权限迁移程序,不走本触发器辖下的常规写路径)
  IF NEW.status <> 'registered' THEN
    RAISE EXCEPTION '修法#4: INSERT 出生态仅允许 registered(得到 %;frozen 只能经 registered→frozen 迁移到达)', NEW.status;
  END IF;

  -- 硬化①出生焊死(保留): 迁移绑定字段出生必空
  IF NEW.result_json IS NOT NULL OR NEW.done_at IS NOT NULL OR NEW.closure_reason IS NOT NULL THEN
    RAISE EXCEPTION '硬化①: result_json/done_at/closure_reason 不得随 INSERT 写入(result 仅可随 running→done 首写)';
  END IF;

  -- 修法#4: frozen_at 出生必空(仅可随 registered→frozen 迁移写;
  --   吸收并收紧 005 的"registered 出生不得带 frozen_at"——如今对一切出生态成立)
  IF NEW.frozen_at IS NOT NULL THEN
    RAISE EXCEPTION '修法#4: frozen_at 不得随 INSERT 写入(仅可随 registered→frozen 迁移一次性写)';
  END IF;

  RETURN NEW;
END $$;

COMMENT ON FUNCTION experiment_biu() IS
  '台账 BEFORE INSERT 焊死(005 硬化① + 008 修法#4): 出生态仅 registered;'
  'frozen_at/result_json/done_at/closure_reason 出生必空;family_trial 触发器自增;铁律①。'
  '作废(008): 005 的"出生态白名单 registered/frozen"——frozen 出生 = 绕过人冻结仪式的旁路。';

COMMIT;
