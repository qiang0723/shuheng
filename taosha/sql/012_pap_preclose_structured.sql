-- 淘沙 · PAP preclose_to_tail 时间字段结构化(外审第二轮窄补 #1,2026-07-13)
-- 缺口(外审复审退回): 011 的 _pap_freeze_gate 对 preclose_to_tail 停留在"字符串非空
--   +LIKE close_confirmed"判定——decision_cutoff 晚于 fill_window 起点的反向时间窗口
--   可冻结(施工前探针 P-C 坐实: cutoff=15:00 / start=14:55 冻结放行)。
-- 修法(窄补令原文即口径): preclose_to_tail 改为结构化、可解析的时间字段,代码层强制断言
--   decision_cutoff < fill_window_start,不能停留在字符串非空判断。
--   结构: decision_cutoff='HH:MM';fill_window={"start":"HH:MM","end":"HH:MM"} 且 start<end;
--   decision_price_source/fill_price_rule/slippage_rule 仍为人选定非空文本(代码零默认)。
--   ~~011 的"字符串非空+LIKE close_confirmed"判定~~ 作废(HH:MM 结构化正则天然排除自由文本)。
--   与 python 层①(pap.validate_strategy_execution)同则;既有 frozen 行不受扰(gate 仅辖
--   registered→frozen 迁移)。close_to_next_open 分支一字不动。
-- 回滚边界: _pap_freeze_gate 重放 011 定义;DROP _hhmm_minutes()。
-- apply 身份 = postgres(taosha 库属主,承 001-011)。
-- 依据: docs/postaudit-round2-narrow-order-2026-07-13.md #1;
--   验收档 taosha/docs/postaudit-round2-narrow-acceptance-2026-07-13.md

BEGIN;

-- ── 结构化时间解析('HH:MM' → 当日分钟数;非法结构 → NULL,调用方拒) ─────────────
CREATE OR REPLACE FUNCTION public._hhmm_minutes(t text) RETURNS int
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
  IF t IS NULL OR t !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$' THEN
    RETURN NULL;
  END IF;
  RETURN split_part(t, ':', 1)::int * 60 + split_part(t, ':', 2)::int;
END $$;

-- ── _pap_freeze_gate: 承 011 全文,preclose_to_tail 分支改结构化时间判定 ──────────
CREATE OR REPLACE FUNCTION public._pap_freeze_gate(p_exp bigint, p_pap jsonb) RETURNS void
LANGUAGE plpgsql STABLE AS $$
DECLARE legacy boolean; at text; se jsonb; prof text; k text; d int; f int;
        w_start int; w_end int;
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
    -- 窄补(2026-07-13): 结构化可解析时间字段+强制断言;~~字符串非空+LIKE close_confirmed~~ 作废
    FOREACH k IN ARRAY ARRAY['decision_price_source','fill_price_rule','slippage_rule'] LOOP
      IF coalesce(btrim(se->>k), '') = '' THEN
        RAISE EXCEPTION '修法#1: preclose_to_tail 缺必填结构字段 %(截止时点与代理价规则由人在冻结前选定,代码不得自行默认)', k;
      END IF;
    END LOOP;
    d := public._hhmm_minutes(se->>'decision_cutoff');
    IF d IS NULL THEN
      RAISE EXCEPTION '修法#1(窄补): preclose_to_tail decision_cutoff 须为结构化时间 HH:MM(得到 %;不接受自由文本)',
        coalesce(se->>'decision_cutoff', '<缺>');
    END IF;
    IF jsonb_typeof(se->'fill_window') IS DISTINCT FROM 'object' THEN
      RAISE EXCEPTION '修法#1(窄补): preclose_to_tail fill_window 须为结构化 {start,end}(得到 %)',
        coalesce(se->>'fill_window', '<缺>');
    END IF;
    w_start := public._hhmm_minutes(se->'fill_window'->>'start');
    w_end   := public._hhmm_minutes(se->'fill_window'->>'end');
    IF w_start IS NULL OR w_end IS NULL THEN
      RAISE EXCEPTION '修法#1(窄补): preclose_to_tail fill_window.start/end 须为 HH:MM(得到 start=% end=%)',
        coalesce(se->'fill_window'->>'start', '<缺>'), coalesce(se->'fill_window'->>'end', '<缺>');
    END IF;
    IF NOT (d < w_start) THEN
      RAISE EXCEPTION '修法#1(窄补): 强制断言 decision_cutoff < fill_window.start 不成立(% >= %):决策必须严格早于成交窗口,拒冻结',
        se->>'decision_cutoff', se->'fill_window'->>'start';
    END IF;
    IF NOT (w_start < w_end) THEN
      RAISE EXCEPTION '修法#1(窄补): fill_window.start 须严格早于 end(% >= %)',
        se->'fill_window'->>'start', se->'fill_window'->>'end';
    END IF;
  ELSE
    RAISE EXCEPTION '修法#1: execution_profile 白名单外: %(合法={close_to_next_open, preclose_to_tail})', coalesce(prof, '<缺>');
  END IF;
END $$;

COMMENT ON FUNCTION public._pap_freeze_gate(bigint, jsonb) IS
  'PAP 冻结硬门(011 修法#1 + 012 窄补): legacy registry 白名单/新 schema 全量校验/执行模式白名单/'
  '信息时序禁组合/preclose_to_tail 结构化时间字段(HH:MM)+强制断言 decision_cutoff<fill_window.start。'
  '作废(012): 011 的"字符串非空+LIKE close_confirmed"判定。';

COMMIT;
