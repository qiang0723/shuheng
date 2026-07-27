-- 020 · exp24 数据前置闭合(人令 2026-07-27 二,裁定 A4/B1/C2):
--   SOX 指数日线最小表 + 申万半导体 L2(801081.SI)历史成分最小表 + 两只最新批读取视图。
-- 范围红线(令文):限 SOX 与 801081.SI,不建通用美股或跨市场平台;单指数单成分表,不扩列族。
-- 同 007 范式:append-only(_freeze_appendonly 焊死)+ 双时戳 + fact_batch lineage;
--   归一是视图的活(铁律7),表只忠实照落源字段,零判断零加工;触发判定(±3%/Decimal)是
--   淘沙研究侧的活,不在 qbase 算。
-- lineage(铁律6,三字段):
--   sox_daily_snap:源=Nasdaq GIW 站点内部端点 POST indexes.nasdaq.com/Index/HistoryData
--     (人裁 A4 主锚;非官方授权API,原始响应+SHA 仅存内部证据包,不入库);接入=fact_batch.pull_time
--     (source='nasdaq_giw:sox_daily');口径=美东交易日 EOD 指数值(SOX 数据行自证交易日)。
--   sw_member_snap:源=tushare index_member_all(人裁 C2,不走老机);接入=fact_batch.pull_time
--     (source='tushare:sw_member');口径=申万现行(2021版)体系回溯+历史进出日期=半PIT(人裁 B1,
--     如实披露不包装)。
-- 幂等:可重复 apply(IF NOT EXISTS / OR REPLACE)。apply 身份 = qbase_app。

-- ── sox_daily_snap:SOX 指数日线(单指数;采集范围=人令:首个研究事件前一 SOX 交易日起,
--    至能完整判定 event_date<2024-07-01 止;端点推定留痕于采集件与交付档,不因 A 股估计窗扩大)──
CREATE TABLE IF NOT EXISTS public.sox_daily_snap (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  trade_date    date        NOT NULL,   -- 美东交易日(源 TimeStamp 之 UTC 日期部;数据行自证交易日)
  close         numeric,                -- 指数收盘值(源字段 Value;忠实照落全精度)
  high          numeric,                -- 源字段 High
  low           numeric,                -- 源字段 Low
  net_change    numeric,                -- 源字段 NetChange(仅照落;±3% 触发以 close 序列自算为准,PAP 草案口径)
  currency      text,                   -- 源字段 Currency(USD)
  valid_time    timestamptz NOT NULL,   -- 事件时=该美东交易日 16:00 America/New_York 收盘(UTC 入库,DST 如实)
  observed_time timestamptz NOT NULL DEFAULT now()
  -- 无 UNIQUE:承 006/007 philosophy(append-only 多 batch 合法;防重=采集侧整行去重)。
);
CREATE INDEX IF NOT EXISTS ix_sox_daily_snap_batch ON public.sox_daily_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_sox_daily_snap_key   ON public.sox_daily_snap(trade_date);
COMMENT ON TABLE public.sox_daily_snap IS
  'SOX(费城半导体指数)日线快照·exp24 数据前置(020,人裁A4):源=Nasdaq GIW 站点内部端点(主锚,'
  '非官方授权API);美东交易日 EOD;append-only;原始响应+SHA 仅存内部证据包不入库;'
  '范围=人令 2026-07-27 二(研究映射窗,不因 A 股估计窗扩大);单指数,不扩美股腿。';

-- ── sw_member_snap:申万半导体 L2 成分(单指数;含已剔除成员=含退市语义,防幸存者偏差)────
CREATE TABLE IF NOT EXISTS public.sw_member_snap (
  id            bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  index_code    text        NOT NULL,   -- 固定 801081.SI(L2;范围红线)
  ts_code       text        NOT NULL,   -- 成员证券(tushare 口径锚)
  name          text,                   -- 源快照名(忠实照落,PIT 名以 namechange 归一视图为准)
  l1_code       text, l1_name text,     -- 801080.SI 电子(源字段照落)
  l3_code       text, l3_name text,     -- 七个 L3 子行业(源字段照落)
  in_date       date,                   -- 纳入日(半PIT:现行体系回溯的历史进出日期,人裁B1)
  out_date      date,                   -- 剔除日(NULL=现役)
  is_new        text,                   -- 源字段 Y/N 忠实照落
  valid_time    timestamptz NOT NULL,   -- 事件时=in_date
  observed_time timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sw_member_snap_batch ON public.sw_member_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_sw_member_snap_key   ON public.sw_member_snap(index_code, ts_code, in_date);
COMMENT ON TABLE public.sw_member_snap IS
  '申万半导体 L2(801081.SI)历史成分快照·exp24 数据前置(020,人裁B1/C2):源=tushare '
  'index_member_all(重采,不走老机);半PIT 语义=申万现行(2021版)体系回溯+历史进出日期,'
  '如实披露不包装;append-only;单指数,不扩行业族。';

-- ── append-only 焊死(复用 004/006/007 的 _freeze_appendonly;OR REPLACE 保自足)──────────
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_sox_daily_snap ON public.sox_daily_snap;
CREATE TRIGGER trg_freeze_sox_daily_snap
  BEFORE UPDATE OR DELETE ON public.sox_daily_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_sw_member_snap ON public.sw_member_snap;
CREATE TRIGGER trg_freeze_sw_member_snap
  BEFORE UPDATE OR DELETE ON public.sw_member_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

-- ── 最小读取视图(最新批;承 008 max(batch_id) 范式;lineage 注释即三字段)────────────────
CREATE OR REPLACE VIEW public.sox_daily AS
SELECT s.trade_date, s.close, s.high, s.low, s.net_change, s.currency, s.batch_id
FROM public.sox_daily_snap s
WHERE s.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='nasdaq_giw:sox_daily');
COMMENT ON VIEW public.sox_daily IS
  '源=nasdaq_giw:sox_daily 最新批;接入时间=该批 fact_batch.pull_time;口径=美东交易日 EOD 指数值。';

CREATE OR REPLACE VIEW public.sw_member AS
SELECT m.index_code, m.ts_code, m.name, m.l3_code, m.l3_name,
       m.in_date, m.out_date, m.is_new, m.batch_id
FROM public.sw_member_snap m
WHERE m.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:sw_member');
COMMENT ON VIEW public.sw_member IS
  '源=tushare:sw_member 最新批;接入时间=该批 fact_batch.pull_time;口径=申万现行体系回溯+'
  '历史进出日期(半PIT,人裁B1 如实披露);成员资格判定(区间/事件日)是消费方的活。';
