-- 006 · Q2 公共事实回填(PIT):forecast(业绩预告)+ stk_holdertrade(股东增减持)
-- 全市场史(含退市)落 append-only 快照表;每次拉取=一个新 batch + 自打 observed_time,禁 upsert。
-- 同 004 范式(004 注释已预告 forecast_snap/holdertrade_snap 同范式):双时戳 + 冻结触发器焊死。
-- 铁律(qbase CLAUDE.md):只读上游永不回写 / 双时戳(valid=事件时,observed=批次拉取时刻,不冒充实时)
--   / append-only 只增不改不删(修数=新 batch)/ 含退市 / lineage 必填 / 忠实存全(不打质量分、不过滤)。
-- 忠实存全教训(承 005):不加会拒合法历史行的唯一约束;整行去重在采集侧做,DB 侧仅
--   UNIQUE NULLS NOT DISTINCT 全业务键元组做**批内**纯双投递防重,同键 distinct 行照落。
-- 回改侦测:跨 batch 按业务键 diff(forecast 锚 first_ann_date;holdertrade 锚 ann_date+holder+窗口),
--   本 DDL 只建承载表与查询索引;侦测逻辑(三层核对协议之③)另件,首批无可 diff。
-- 幂等:可重复 apply(IF NOT EXISTS / OR REPLACE)。apply 身份 = qbase_app。
-- 明确不做:不建消费视图/角色(Q3);不预建巨潮采集(并行另件);不算任何指标/信号(L2 的活)。

-- ── 批次 + lineage(多源共用:source 区分)────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.fact_batch (
  batch_id   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source     text        NOT NULL,   -- 'tushare:forecast' / 'tushare:stk_holdertrade'
  asof_date  date        NOT NULL,   -- PIT as-of(拉取日;当期快照口径)
  pull_time  timestamptz NOT NULL,   -- observed_time 源头(采集时刻,UTC)
  note       text                    -- 口径说明 / 分片计数 / 缺失率与截断证据
);

-- ── forecast_snap:业绩预告全市场史(含退市)─────────────────────────────────
-- tushare `forecast` 口径字段;数值忠实照落(min/max 区间、单位=万元由源定,不换算不判断)。
CREATE TABLE IF NOT EXISTS public.forecast_snap (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id        bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code         text        NOT NULL,       -- 锚(tushare 口径)
  ann_date        date,                        -- 本次公告日(披露 = 事件时来源)
  end_date        date,                        -- 报告期
  type            text,                        -- 预告类型(预增/预减/扭亏/首亏/…)
  p_change_min    numeric,                     -- 净利润变动幅度下限(%)
  p_change_max    numeric,                     -- 净利润变动幅度上限(%)
  net_profit_min  numeric,                     -- 预告净利润下限(万元)
  net_profit_max  numeric,                     -- 预告净利润上限(万元)
  last_parent_net numeric,                     -- 上年同期归母净利润(万元)
  first_ann_date  date,                        -- 首次公告日(回改侦测锚:批间同键 first_ann 变动=回改)
  summary         text,                        -- 业绩预告摘要
  change_reason   text,                        -- 业绩变动原因
  valid_time      timestamptz NOT NULL,        -- 事件时:ann_date;缺则 first_ann_date;再缺 batch as-of
  observed_time   timestamptz NOT NULL DEFAULT now(),
  -- 批内纯双投递防重(NULLS NOT DISTINCT:NULL 视为相等,故同键 NULL 双发也拦);
  -- 同键但字段有别的 distinct 行(如同期多次修正预告)不撞约束,照落——忠实存全。
  UNIQUE NULLS NOT DISTINCT
    (batch_id, ts_code, ann_date, end_date, type, p_change_min, p_change_max,
     net_profit_min, net_profit_max, last_parent_net, first_ann_date, summary, change_reason)
);
CREATE INDEX IF NOT EXISTS ix_forecast_snap_ts    ON public.forecast_snap(ts_code);
CREATE INDEX IF NOT EXISTS ix_forecast_snap_batch ON public.forecast_snap(batch_id);
-- 回改 diff:按业务键跨 batch 对齐(ts_code+报告期+首次公告)
CREATE INDEX IF NOT EXISTS ix_forecast_snap_key   ON public.forecast_snap(ts_code, end_date, first_ann_date);

-- ── holdertrade_snap:股东增减持全市场史(含退市)──────────────────────────────
-- tushare `stk_holdertrade` 口径字段;方向 in_de(IN 增持 / DE 减持)、数量比例忠实照落。
CREATE TABLE IF NOT EXISTS public.holdertrade_snap (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id      bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code       text        NOT NULL,          -- 锚
  ann_date      date,                          -- 公告日(披露 = 事件时来源)
  holder_name   text,                          -- 股东名称
  holder_type   text,                          -- 股东类型(G高管/P个人/C公司)
  in_de         text,                          -- 增减持方向(IN/DE)
  change_vol    numeric,                       -- 变动数量(股)
  change_ratio  numeric,                       -- 占流通比例(%)
  after_share   numeric,                       -- 变动后持股(股)
  after_ratio   numeric,                       -- 变动后占流通比例(%)
  avg_price     numeric,                       -- 平均价格
  total_share   numeric,                       -- 持股总数(股)
  begin_date    date,                          -- 增减持开始日
  close_date    date,                          -- 增减持结束日
  valid_time    timestamptz NOT NULL,          -- 事件时:ann_date;缺则 batch as-of
  observed_time timestamptz NOT NULL DEFAULT now(),
  UNIQUE NULLS NOT DISTINCT
    (batch_id, ts_code, ann_date, holder_name, holder_type, in_de, change_vol,
     change_ratio, after_share, after_ratio, avg_price, total_share, begin_date, close_date)
);
CREATE INDEX IF NOT EXISTS ix_holdertrade_snap_ts    ON public.holdertrade_snap(ts_code);
CREATE INDEX IF NOT EXISTS ix_holdertrade_snap_batch ON public.holdertrade_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_holdertrade_snap_key   ON public.holdertrade_snap(ts_code, ann_date, holder_name);

-- ── append-only 焊死:UPDATE/DELETE 一律拒(与 004 共用 _freeze_appendonly)──────
-- 004 已建该函数;此处 OR REPLACE 重声明保 006 自足可独立 apply(同体幂等)。
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新增 batch)', TG_OP, TG_TABLE_NAME;
END; $$;

DROP TRIGGER IF EXISTS trg_freeze_fact_batch ON public.fact_batch;
CREATE TRIGGER trg_freeze_fact_batch BEFORE UPDATE OR DELETE ON public.fact_batch
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_forecast_snap ON public.forecast_snap;
CREATE TRIGGER trg_freeze_forecast_snap BEFORE UPDATE OR DELETE ON public.forecast_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_freeze_holdertrade_snap ON public.holdertrade_snap;
CREATE TRIGGER trg_freeze_holdertrade_snap BEFORE UPDATE OR DELETE ON public.holdertrade_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
