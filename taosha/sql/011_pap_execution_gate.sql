-- 淘沙 · 新策略 PAP 可执行离场硬门 · 库侧两件(外审五项修法 #1,人终签 2026-07-13)
-- 攻击路径(外审): 无 schema 版本与 analysis_type,策略版含否靠文本推断;策略执行时序
--   (决策 vs 成交)无结构化约束——close_confirmed+same_close 类不可执行口径可再入新 PAP;
--   legacy 白名单若靠调用方传字段/registered_at 判断则可伪造。
-- 修法(人令原文即口径,三层 fail-closed 之层②+registry):
--   ① pap_legacy_registry = 迁移时刻物化的只读 append-only 登记表(唯一 legacy 判据);
--     收录范围=当时已存在、缺新 schema 字段的**全部**实验(含 frozen/done/closed,注明
--     物化时 status——我方确认点②,随终签批复);taosha_app 与引擎均无写权;
--     迁移完成后新增实验不可能进入(append-only+零写权+物化一次性)。
--   ② registered→frozen 迁移触发器调 _pap_freeze_gate():legacy 无 schema=事件版白名单放行
--     (策略驱动一律拒在层③);legacy 升级 schema(registered 态人批补元数据)仍只许
--     analysis_type=event;非 legacy 须全量 schema 校验——执行模式白名单
--     {close_to_next_open, preclose_to_tail}、信息时序禁组合(决策必须严格早于成交窗口,
--     close_confirmed+same_close 直接拒)、preclose 必填字段人选定代码零默认。
-- 回滚边界: experiment_bu() 重放 005+008 定义(去 gate 调用);DROP _pap_freeze_gate();
--   registry 为 append-only 审计实物,回滚保留不删。
-- apply 身份 = postgres(taosha 库属主,承 001-010)。
-- 依据: docs/postaudit-five-order-2026-07-13.md #1;
--   验收档 taosha/docs/postaudit-item1-pap-execution-gate-acceptance-2026-07-13.md

BEGIN;

-- ── ① legacy registry(物化一次性;唯一 legacy 判据) ─────────────────────────────
CREATE TABLE IF NOT EXISTS public.pap_legacy_registry (
  exp_id              bigint PRIMARY KEY REFERENCES public.experiment(exp_id),
  status_at_migration text   NOT NULL,     -- 物化时刻台账 status(确认点②: 全 status 普查)
  registered_at       timestamptz,
  note                text   NOT NULL,
  created_by          text   NOT NULL DEFAULT current_user,
  created_at          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.pap_legacy_registry IS
  'legacy-event 白名单(修法#1): 011 迁移时刻物化的存量缺 schema 实验普查,append-only 只读;'
  '唯一判据(不认调用方传 legacy 字段/可伪造 registered_at);legacy 只允许事件版冻结与运行,'
  '策略驱动一律拒;升级 schema 仅 registered 态经人确认补元数据且仍限 analysis_type=event。';

DROP TRIGGER IF EXISTS trg_pap_legacy_registry_freeze ON public.pap_legacy_registry;
CREATE TRIGGER trg_pap_legacy_registry_freeze
  BEFORE UPDATE OR DELETE ON public.pap_legacy_registry
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
DROP TRIGGER IF EXISTS trg_pap_legacy_registry_no_truncate ON public.pap_legacy_registry;
CREATE TRIGGER trg_pap_legacy_registry_no_truncate
  BEFORE TRUNCATE ON public.pap_legacy_registry
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

-- 只读授权(零写权: 写只在本迁移物化一次)
GRANT SELECT ON public.pap_legacy_registry TO taosha_app;
GRANT SELECT ON public.pap_legacy_registry TO taosha_engine;

-- 物化: 当时已存在、缺 pap_schema_version 的全部实验(预期=台账全 25 行,断言核数)
INSERT INTO public.pap_legacy_registry (exp_id, status_at_migration, registered_at, note)
SELECT exp_id, status, registered_at,
       'legacy-event 白名单物化(修法#1,2026-07-13): 迁移时刻缺 pap_schema_version;'
       '只允许事件版冻结与运行,策略驱动一律拒'
FROM public.experiment
WHERE NOT (pap_json ? 'pap_schema_version')
ON CONFLICT (exp_id) DO NOTHING;

DO $$
DECLARE n_reg bigint; n_exp bigint;
BEGIN
  SELECT count(*) INTO n_reg FROM pap_legacy_registry;
  SELECT count(*) INTO n_exp FROM experiment;
  IF n_reg <> 25 OR n_exp <> 25 THEN
    RAISE EXCEPTION '修法#1 物化断言失败: registry=% / experiment=%(预期 25/25 点时普查),迁移中止',
      n_reg, n_exp;
  END IF;
END $$;

-- ── ② 冻结硬门(层②) ────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public._pap_freeze_gate(p_exp bigint, p_pap jsonb) RETURNS void
LANGUAGE plpgsql STABLE AS $$
DECLARE legacy boolean; at text; se jsonb; prof text; k text; d int; f int;
BEGIN
  SELECT EXISTS (SELECT 1 FROM pap_legacy_registry WHERE exp_id = p_exp) INTO legacy;

  IF legacy AND NOT (p_pap ? 'pap_schema_version') THEN
    RETURN;   -- legacy 事件版白名单放行(策略拒在驱动层③;pap 无策略结构可言)
  END IF;
  IF legacy AND (p_pap ? 'pap_schema_version') THEN
    -- 升级路径(registered 态人批补元数据): 仍只许事件版
    IF p_pap->>'analysis_type' IS DISTINCT FROM 'event' THEN
      RAISE EXCEPTION '修法#1: legacy 实验只允许事件版冻结与运行(升级 schema 后 analysis_type 须=event;策略须 INSERT 新实验行)';
    END IF;
  END IF;
  IF NOT legacy AND NOT (p_pap ? 'pap_schema_version') THEN
    RAISE EXCEPTION '修法#1: 新 PAP 须含 pap_schema_version(legacy 唯一判据=pap_legacy_registry 物化表,不认调用方自称/registered_at)';
  END IF;

  IF (p_pap->>'pap_schema_version') <> '2' THEN
    RAISE EXCEPTION '修法#1: pap_schema_version 须为 2(得到 %)', p_pap->>'pap_schema_version';
  END IF;
  at := p_pap->>'analysis_type';
  IF at IS NULL OR at NOT IN ('event', 'strategy', 'event_and_strategy') THEN
    RAISE EXCEPTION '修法#1: analysis_type 须为 event|strategy|event_and_strategy(得到 %;不得靠文本推断)', coalesce(at, '<缺>');
  END IF;
  IF at = 'event' THEN
    RETURN;   -- 纯事件假设不要求 strategy_execution
  END IF;

  se := p_pap->'strategy_execution';
  IF se IS NULL OR jsonb_typeof(se) <> 'object' THEN
    RAISE EXCEPTION '修法#1: analysis_type 含 strategy 须结构化 strategy_execution(执行模式白名单)';
  END IF;
  -- 信息时序禁组合(先于白名单判): 决策时点必须严格早于成交窗口
  d := CASE se->>'decision_time' WHEN 'preclose_cutoff' THEN 10 WHEN 'close_confirmed' THEN 30
       ELSE NULL END;
  f := CASE se->>'fill_time' WHEN 'tail_window' THEN 20 WHEN 'same_close' THEN 30
       WHEN 'close' THEN 30 WHEN 'next_open' THEN 40 ELSE NULL END;
  IF d IS NOT NULL AND f IS NOT NULL AND d >= f THEN
    RAISE EXCEPTION '修法#1: 禁止组合(信息时序): 决策时点(%)必须严格早于成交窗口(%)——close_confirmed+same_close 等直接拒绝',
      se->>'decision_time', se->>'fill_time';
  END IF;
  prof := se->>'execution_profile';
  IF prof = 'close_to_next_open' THEN
    IF se->>'decision_time' IS DISTINCT FROM 'close_confirmed'
       OR se->>'fill_time'   IS DISTINCT FROM 'next_open'
       OR se->>'fill_price'  IS DISTINCT FROM 'next_adjusted_open'
       OR se->>'slippage_rule' IS DISTINCT FROM 'frozen_cost' THEN
      RAISE EXCEPTION '修法#1: close_to_next_open 四字段须逐字冻结值(decision_time=close_confirmed/fill_time=next_open/fill_price=next_adjusted_open/slippage_rule=frozen_cost)';
    END IF;
  ELSIF prof = 'preclose_to_tail' THEN
    FOREACH k IN ARRAY ARRAY['decision_cutoff','decision_price_source','fill_window','fill_price_rule','slippage_rule'] LOOP
      IF coalesce(btrim(se->>k), '') = '' THEN
        RAISE EXCEPTION '修法#1: preclose_to_tail 缺必填结构字段 %(截止时点与代理价规则由人在冻结前选定,代码不得自行默认)', k;
      END IF;
    END LOOP;
    IF se->>'decision_cutoff' LIKE '%close_confirmed%' THEN
      RAISE EXCEPTION '修法#1: preclose_to_tail 决策必须发生在成交之前(decision_cutoff 不得为 close_confirmed)';
    END IF;
  ELSE
    RAISE EXCEPTION '修法#1: execution_profile 白名单外: %(合法={close_to_next_open, preclose_to_tail})', coalesce(prof, '<缺>');
  END IF;
END $$;

-- ── experiment_bu: 承 005(全文)+ 008(出生焊死在 biu,不在此)+ 本 gate 调用 ────
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

  -- 修法#1 层②(外审 2026-07-13): registered→frozen 冻结硬门
  IF OLD.status = 'registered' AND NEW.status = 'frozen' THEN
    PERFORM public._pap_freeze_gate(OLD.exp_id, NEW.pap_json);
  END IF;

  RETURN NEW;
END $$;

COMMENT ON FUNCTION experiment_bu() IS
  '台账 BEFORE UPDATE(005 硬化① + 011 修法#1): 字段变更绑定唯一合法迁移 + 冻结硬门'
  '_pap_freeze_gate(legacy registry 白名单/新 schema 全量校验/执行模式白名单/信息时序禁组合)。';

COMMIT;
