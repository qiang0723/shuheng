-- 007 · 行情回填(PIT):日线 bar_daily + 复权因子 adj_factor + 交易日历 trade_cal
-- 承 Q3 换源约束的**人拍变更**(2026-07-07):原 ROADMAP 定"Q3 视图经 FDW 只读老库、现在不迁移";
--   人裁改走 B=回填 marketdata 进 qbase 本地表(marketdata=梯队4"市面可重拉"公共事实,可借阅,
--   区别于 radar/research_view/crucible 判断数据的不借阅)。源=**tushare**(与 Q2 同源、不碰老平台)。
-- 全市场史(含退市)落 append-only 快照;每源每次拉=新 fact_batch + observed_time,禁 upsert。同 006 范式。
-- 铁律(qbase CLAUDE.md):只存事实零判断零加工 / 双时戳(valid=行情时,observed=批次拉取时刻)
--   / append-only 只增不改不删(修数/复权重述=新 batch)/ 含退市 / lineage 必填 / 忠实存全不打质量分。
-- **归一是视图的活(铁律7),不在此**:后复权收盘(=close×adj_factor,D3)、is_suspended(交易日无 bar)、
--   limit_status(close vs pre_close vs 板块限幅)、board(ts_code 前缀)、is_st(PIT 名称含 ST)、
--   industry(entity_master)——全部留给 Q3 explore_reader 视图算,facts 只忠实存原始 OHLCV/因子/日历。
-- 无 UNIQUE:承 006 philosophy——append-only 多 batch(复权因子会被除权除息重述、同键跨批多行合法),
--   设 UNIQUE(ts_code,trade_date) 会拒合法历史行;纯双投递防重由采集侧整行去重(见 seed_marketdata.py)。
-- 幂等:可重复 apply(IF NOT EXISTS / OR REPLACE)。apply 身份 = qbase_app。
-- 明确不做:不建消费视图/角色(Q3 视图另件 008);不算收益/复权/信号(视图与引擎的活)。

-- ── 批次 + lineage 复用 006 的 public.fact_batch(source 区分:tushare:daily/adj_factor/trade_cal)──

-- ── bar_daily_snap:日线全市场史(含退市)· tushare `daily` 口径,原始未复权 ───────────────
CREATE TABLE IF NOT EXISTS public.bar_daily_snap (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code       text        NOT NULL,          -- 锚(tushare 口径)
  trade_date    date        NOT NULL,          -- 行情日(= valid_time 来源)
  open          numeric,                        -- 开盘价(未复权,元)
  high          numeric,                        -- 最高价(未复权)
  low           numeric,                        -- 最低价(未复权)
  close         numeric,                        -- 收盘价(未复权;后复权=×adj_factor,留视图)
  pre_close     numeric,                        -- 昨收(未复权;涨跌停判定基准)
  change        numeric,                        -- 涨跌额
  pct_chg       numeric,                        -- 涨跌幅(%,未复权口径)
  vol           numeric,                        -- 成交量(手)
  amount        numeric,                        -- 成交额(千元)
  valid_time    timestamptz NOT NULL,           -- 事件时:trade_date
  observed_time timestamptz NOT NULL DEFAULT now()
  -- 无 UNIQUE:同 006(append-only 多 batch;去重在采集层整行去重)。
);
CREATE INDEX IF NOT EXISTS ix_bar_daily_snap_ts    ON public.bar_daily_snap(ts_code);
CREATE INDEX IF NOT EXISTS ix_bar_daily_snap_batch ON public.bar_daily_snap(batch_id);
-- 视图 JOIN 主路径:按(票,日)取最新 batch 的 bar
CREATE INDEX IF NOT EXISTS ix_bar_daily_snap_key   ON public.bar_daily_snap(ts_code, trade_date);

-- ── adj_factor_snap:复权因子全市场史 · tushare `adj_factor` ───────────────────────────
-- 后复权 close = 原始 close × adj_factor(D3 收益口径=后复权收盘)。因子随除权除息被重述→新 batch。
CREATE TABLE IF NOT EXISTS public.adj_factor_snap (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code       text        NOT NULL,
  trade_date    date        NOT NULL,
  adj_factor    numeric,                        -- 复权因子(忠实照落,不归一)
  valid_time    timestamptz NOT NULL,           -- trade_date
  observed_time timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_adj_factor_snap_ts    ON public.adj_factor_snap(ts_code);
CREATE INDEX IF NOT EXISTS ix_adj_factor_snap_batch ON public.adj_factor_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_adj_factor_snap_key   ON public.adj_factor_snap(ts_code, trade_date);

-- ── trade_cal_snap:交易日历 · tushare `trade_cal`(SSE,全市场同历)──────────────────────
-- is_suspended 判定的日历栅格:某交易日(is_open=1)某活票(list≤d≤delist)无 bar ⇒ 停牌(视图算)。
CREATE TABLE IF NOT EXISTS public.trade_cal_snap (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  exchange      text        NOT NULL,           -- 交易所(SSE)
  cal_date      date        NOT NULL,           -- 日历日
  is_open       smallint,                       -- 1=交易日 0=休市
  pretrade_date date,                            -- 上一交易日
  valid_time    timestamptz NOT NULL,           -- cal_date
  observed_time timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_trade_cal_snap_batch ON public.trade_cal_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_trade_cal_snap_key   ON public.trade_cal_snap(exchange, cal_date);

-- ── append-only 焊死:UPDATE/DELETE 一律拒(复用 004/006 的 _freeze_appendonly)────────────
-- 006 已建该函数;OR REPLACE 重声明保 007 自足可独立 apply(同体幂等)。
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_bar_daily_snap ON public.bar_daily_snap;
CREATE TRIGGER trg_freeze_bar_daily_snap BEFORE UPDATE OR DELETE ON public.bar_daily_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_adj_factor_snap ON public.adj_factor_snap;
CREATE TRIGGER trg_freeze_adj_factor_snap BEFORE UPDATE OR DELETE ON public.adj_factor_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_trade_cal_snap ON public.trade_cal_snap;
CREATE TRIGGER trg_freeze_trade_cal_snap BEFORE UPDATE OR DELETE ON public.trade_cal_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
