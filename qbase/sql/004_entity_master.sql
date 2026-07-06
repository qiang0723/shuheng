-- 004 · Q1 Entity Master 最小版(apply 身份 = qbase_app)
-- ts_code 锚 + 别名史。append-only 快照制:每次种子=一个新 batch,当期态取最新 batch。
-- 与 _sentinel_selftest、Q2 forecast_snap/holdertrade_snap 同范式(双时戳 + 冻结触发器焊死)。
-- 铁律:只读上游永不回写 / 双时戳 / append-only / 含退市 / lineage 必填 / 忠实归一(不打质量分)。
-- 幂等:可重复 apply(表/触发器 IF NOT EXISTS / OR REPLACE)。
-- 明确不做:不预建巨潮采集逻辑(alias_type 只留通用位);不建消费视图/角色(Q3);不扩公司/概念图谱。

-- ── 批次 + lineage(三字段:source / asof_date=批次时间 / note=口径)──────────────
CREATE TABLE IF NOT EXISTS public.entity_batch (
  batch_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source        text        NOT NULL,         -- 'tushare:stock_basic' / 'tushare:namechange'
  asof_date     date        NOT NULL,         -- PIT as-of(拉取日;当期快照口径)
  pull_time     timestamptz NOT NULL,         -- observed_time 源头(采集时刻,UTC)
  note          text                          -- 口径说明 / 分片计数证据
);

-- ── entity_master:ts_code 锚,全市场含退市(list_status D 退市 / P 暂停 / L 上市)──
CREATE TABLE IF NOT EXISTS public.entity_master (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.entity_batch(batch_id),
  ts_code       text        NOT NULL,         -- 锚(tushare 口径,如 000001.SZ)
  symbol        text,
  name          text,                         -- 该 batch 观测时的当期名
  area          text,
  industry      text,
  market        text,
  exchange      text,
  list_status   char(1),                      -- L 上市 / D 退市 / P 暂停上市
  list_date     date,
  delist_date   date,
  valid_time    timestamptz NOT NULL,         -- 事件时:快照 as-of(= batch pull_time)
  observed_time timestamptz NOT NULL DEFAULT now(),
  UNIQUE(batch_id, ts_code)
);
CREATE INDEX IF NOT EXISTS ix_entity_master_ts   ON public.entity_master(ts_code);
CREATE INDEX IF NOT EXISTS ix_entity_master_batch ON public.entity_master(batch_id);

-- ── entity_alias:别名史。Q1 只落 namechange 历史名(alias_type='name')──────────
-- alias_type 为通用位:Q2 起可加 'cninfo_seccode'/'cninfo_orgid' 无需改表(§4.1 别名表设计意图)。
CREATE TABLE IF NOT EXISTS public.entity_alias (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.entity_batch(batch_id),
  ts_code       text        NOT NULL,         -- 锚
  alias_type    text        NOT NULL,         -- Q1: 'name'
  alias         text        NOT NULL,         -- 名称(Q2 起亦可为代码值)
  start_date    date,                         -- namechange 启用日
  end_date      date,                         -- namechange 停用日(NULL=至今)
  ann_date      date,                         -- 公告日
  valid_time    timestamptz NOT NULL,         -- 事件时:名称启用日(start_date);缺则 batch as-of
  observed_time timestamptz NOT NULL DEFAULT now(),
  UNIQUE(batch_id, ts_code, alias_type, alias, start_date)
);
CREATE INDEX IF NOT EXISTS ix_entity_alias_ts ON public.entity_alias(ts_code);

-- ── append-only 焊死:UPDATE/DELETE 一律拒(只增不改不删,修数=新 batch)────────
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_entity_master ON public.entity_master;
CREATE TRIGGER trg_freeze_entity_master BEFORE UPDATE OR DELETE ON public.entity_master
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_entity_alias ON public.entity_alias;
CREATE TRIGGER trg_freeze_entity_alias BEFORE UPDATE OR DELETE ON public.entity_alias
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_entity_batch ON public.entity_batch;
CREATE TRIGGER trg_freeze_entity_batch BEFORE UPDATE OR DELETE ON public.entity_batch
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
