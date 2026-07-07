-- 淘沙台账 · experiment(六对象 Experiment 契约)· 切片1
-- 依据: spec v0.2 冻结版 §4 表 + §2 铁律触发器落法;v1.5 新增 data_class/crowding_prior 元数据字段。
-- 铁则: append-only(禁 DELETE/TRUNCATE)、pap_json 冻结后不可改、status 单向推进、result 一次性写入、
--       family_trial 触发器自增、source_type=llm 强制 verdict_power=prescreen。焊死用触发器,不靠自觉。
-- 双时戳: registered_at=observed(系统记录), frozen_at=valid(PAP 冻结生效)。

BEGIN;

CREATE TABLE IF NOT EXISTS experiment (
  exp_id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  family         text   NOT NULL,
  family_trial   int    NOT NULL,                      -- 触发器自增,插入值被覆盖
  title          text   NOT NULL,
  source_type    text   NOT NULL CHECK (source_type IN ('human','platform','literature','llm')),
  verdict_power  text   NOT NULL CHECK (verdict_power IN ('full','prescreen')),
  contamination_note text,
  pap_json       jsonb  NOT NULL,                       -- 事件定义/窗口/池/基准/成本/holdout/清洗/快照批次要求
  status         text   NOT NULL DEFAULT 'registered'
                        CHECK (status IN ('registered','frozen','running','done','closed')),
  -- v1.5 元数据(新登记填写,不作筛选依据):
  data_class     text,
  crowding_prior text,
  registered_at  timestamptz NOT NULL DEFAULT now(),    -- observed
  frozen_at      timestamptz,                           -- valid(冻结生效)
  result_json    jsonb,                                 -- CAR/检验统计量/样本数/校正门槛/快照批次/verdict
  done_at        timestamptz,
  UNIQUE (family, family_trial)                          -- 配合触发器自增,挡并发竞态
);

CREATE INDEX IF NOT EXISTS idx_experiment_family ON experiment(family);
CREATE INDEX IF NOT EXISTS idx_experiment_status ON experiment(status);

-- ── BEFORE INSERT: family_trial 自增 + llm→prescreen 强制 ───────────────────
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

  -- 冻结态一致性: status=frozen 必须已有 frozen_at 与 pap_json
  IF NEW.status = 'frozen' AND NEW.frozen_at IS NULL THEN
    RAISE EXCEPTION '登记冻结态须同时置 frozen_at';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_experiment_biu ON experiment;
CREATE TRIGGER trg_experiment_biu BEFORE INSERT ON experiment
  FOR EACH ROW EXECUTE FUNCTION experiment_biu();

-- ── BEFORE UPDATE: 不可变列锁 + status 单向推进 + 一次性写入 ─────────────────
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

  -- 铁律④: pap_json 冻结后一律 RAISE
  IF OLD.frozen_at IS NOT NULL AND NEW.pap_json IS DISTINCT FROM OLD.pap_json THEN
    RAISE EXCEPTION '铁律④违反: pap_json 冻结后不可改(改参=INSERT 新行)';
  END IF;

  -- frozen_at 一次性写入(NULL→值);已冻结不可再改
  IF OLD.frozen_at IS NOT NULL AND NEW.frozen_at IS DISTINCT FROM OLD.frozen_at THEN
    RAISE EXCEPTION 'frozen_at 一次性写入,不可改';
  END IF;

  -- result_json 一次性写入
  IF OLD.result_json IS NOT NULL AND NEW.result_json IS DISTINCT FROM OLD.result_json THEN
    RAISE EXCEPTION 'result_json 一次性写入,不可覆写';
  END IF;

  -- done_at 一次性写入
  IF OLD.done_at IS NOT NULL AND NEW.done_at IS DISTINCT FROM OLD.done_at THEN
    RAISE EXCEPTION 'done_at 一次性写入,不可改';
  END IF;

  -- status 单向推进(合法迁移白名单)
  IF NEW.status <> OLD.status THEN
    IF NOT ( (OLD.status='registered' AND NEW.status IN ('frozen','closed'))
          OR (OLD.status='frozen'     AND NEW.status IN ('running','closed'))
          OR (OLD.status='running'    AND NEW.status='done') ) THEN
      RAISE EXCEPTION 'status 非法迁移: % → %', OLD.status, NEW.status;
    END IF;
    -- 进入 frozen 必须同步置 frozen_at
    IF NEW.status='frozen' AND NEW.frozen_at IS NULL THEN
      RAISE EXCEPTION '推进到 frozen 须同步置 frozen_at';
    END IF;
    -- 进入 done 必须同步置 result_json + done_at
    IF NEW.status='done' AND (NEW.result_json IS NULL OR NEW.done_at IS NULL) THEN
      RAISE EXCEPTION '推进到 done 须同步置 result_json 与 done_at';
    END IF;
  END IF;

  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_experiment_bu ON experiment;
CREATE TRIGGER trg_experiment_bu BEFORE UPDATE ON experiment
  FOR EACH ROW EXECUTE FUNCTION experiment_bu();

-- ── 禁 DELETE / TRUNCATE(append-only) ──────────────────────────────────────
CREATE OR REPLACE FUNCTION experiment_no_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'experiment 台账 append-only: 禁 DELETE';
END $$;

DROP TRIGGER IF EXISTS trg_experiment_no_delete ON experiment;
CREATE TRIGGER trg_experiment_no_delete BEFORE DELETE ON experiment
  FOR EACH ROW EXECUTE FUNCTION experiment_no_delete();

CREATE OR REPLACE FUNCTION experiment_no_truncate() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'experiment 台账 append-only: 禁 TRUNCATE';
END $$;

DROP TRIGGER IF EXISTS trg_experiment_no_truncate ON experiment;
CREATE TRIGGER trg_experiment_no_truncate BEFORE TRUNCATE ON experiment
  FOR EACH STATEMENT EXECUTE FUNCTION experiment_no_truncate();

COMMIT;
