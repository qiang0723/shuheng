-- 011 · 减持预披露事件表(#3 = holder_sell = exp_id 4;生产采集承载)
-- 缘由:#3 事件锚 = 减持计划**首次预披露**公告日(PIT),tushare holdertrade_snap(事后增减持)不含
--   预披露事件、且非 PIT。本表承载巨潮 cninfo 采集 + L3 三字段解析(股东名/拟减持比例上限/减持期间)。
-- 范式同 006:双时戳(valid_time=公告时点/observed_time=采集时点,NOT NULL)+ append-only 焊死
--   (_freeze_appendonly 共用)+ fact_batch lineage;忠实存全、失败如实标注(parse_fail)。
-- 事件粒度(人裁 2026-07-08):一司多次预披露 = **逐次独立事件**,自然键 = announcement_id(去重锚)。
-- title 判据放宽已过 pilot 标注集回归(人裁①);排除词命中逐条留痕(title_reason,人裁②)。
-- 幂等:IF NOT EXISTS。apply 身份 = qbase_app。北交所排除在消费视图(切片3),底表忠实存全。

CREATE TABLE IF NOT EXISTS public.holder_sell_predisclose_snap (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id        bigint      NOT NULL REFERENCES public.fact_batch(batch_id),
  ts_code         text        NOT NULL,       -- 带后缀(entity_master 锚;由 stock_code 前缀派生)
  stock_code      text        NOT NULL,       -- 巨潮无后缀原始码
  announcement_id text,                        -- 巨潮公告ID(逐次独立事件自然键;dedup 锚)
  title           text        NOT NULL,        -- 公告标题(title 判据依据)
  announcement_type text,                      -- 原始 type 码列表(L4:码不稳,仅存证不作筛)
  source_url      text,                        -- PDF 链接(解析源)
  -- L3 三字段(解析失败留 NULL + parse_fail 标注,不猜不填)
  holder_name          text,                   -- 拟减持股东名
  reduce_ratio_max_pct numeric,                -- 拟减持比例上限(%);#3 门槛"≥总股本1%"按此逐次判
  reduce_period_start  date,                   -- 减持期间起(绝对式)
  reduce_period_end    date,                   -- 减持期间止(绝对式)
  reduce_period_text   text,                   -- 期间原文(绝对=起~止 / 相对=披露之日起…原文)
  reduce_period_kind   text,                   -- absolute | relative | NULL
  parse_fail      text[],                      -- 空=三字段全中;非空=如实标注缺项
  title_reason    text,                        -- classify_title 理由(留痕;命中即 'pass')
  valid_time      timestamptz NOT NULL,        -- 事件时:公告时点(announcementTime UTC)=首次预披露锚
  observed_time   timestamptz NOT NULL DEFAULT now()   -- 采集时点
  -- 无批内 UNIQUE:同 006 理由(事件快照无批内唯一不变量;去重 scope=采集层 by announcement_id)。
);
CREATE INDEX IF NOT EXISTS ix_holder_sell_pre_ts    ON public.holder_sell_predisclose_snap(ts_code);
CREATE INDEX IF NOT EXISTS ix_holder_sell_pre_batch ON public.holder_sell_predisclose_snap(batch_id);
CREATE INDEX IF NOT EXISTS ix_holder_sell_pre_ann   ON public.holder_sell_predisclose_snap(announcement_id);
CREATE INDEX IF NOT EXISTS ix_holder_sell_pre_vt    ON public.holder_sell_predisclose_snap(ts_code, valid_time);

-- append-only 焊死(共用 _freeze_appendonly;006 已建该函数)
DROP TRIGGER IF EXISTS trg_freeze_holder_sell_pre ON public.holder_sell_predisclose_snap;
CREATE TRIGGER trg_freeze_holder_sell_pre BEFORE UPDATE OR DELETE ON public.holder_sell_predisclose_snap
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();
