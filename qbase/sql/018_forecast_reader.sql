-- 018 · forecast 只读研究视图对(exp20 业绩预告修正,冻结令 2026-07-18 深夜六 令三①)
-- 范围(令三白名单): explore_reader_forecast(_snap) 只读视图对 / holdout 视图层焊死 /
--   taosha engine 最小 SELECT 授权。事件判别(修正链/基准B/方向/fail-closed 六类)不在视图内——
--   qbase=L1 忠实归一零判断,规则属 L2 适配器(taosha/compute/earnings_revision_rules.py)。
-- 视图对(现值 + _snap manifest 路由)同口径,承 008/012/013/017 范式:
--   · holdout 焊死: ann_date < DATE '2024-07-01'(qbase 铁律5,线在视图不在应用代码;
--     锚=ann_date——修正链基准B只回看更早公告,holdout 后行结构上不可见即可保链完整);
--   · 北交所排除 ts_code !~ '\.BJ$'(与 explore_reader_events 面同口径);
--   · **最小列面**=冻结 PAP v2(digest e1d18dc1…7fd5)方向规则消费面:链键(ts_code,end_date,
--     first_ann_date)+事件锚 ann_date+判定字段 p_change_min/p_change_max。net_profit_min/max、
--     type 等字段冻结口径明令禁用("不改用net_profit,不使用type文字回退")→ 不出列,
--     结构上防误用(最小列面≠过滤行;行忠实传递,含数值不可判行,fail-closed 属 L2);
--   · 研究期下限(2013-01-01)属 L2 事件规则,不焊视图(L1 忠实,链基准可回看 2013 前公告)。
-- lineage: 源=forecast_snap(tushare:forecast)/批次=现值 max / study_snap_batch('forecast') 路由
--   (键已在源级快照向量,snapshot 74 实测 forecast:1)/口径=本头注。
-- apply 身份 = qbase_app(视图属主链承 008/010/012/013/017;属主自授 engine SELECT)。

BEGIN;

-- ══ 视图 6:explore_reader_forecast(现值 max-batch 路由)══
CREATE OR REPLACE VIEW public.explore_reader_forecast AS
SELECT
  f.ts_code,
  f.ann_date,
  f.end_date,
  f.first_ann_date,
  f.p_change_min,
  f.p_change_max,
  'batch' || f.batch_id AS snapshot_batch
FROM public.forecast_snap f
WHERE f.batch_id = (SELECT max(batch_id) FROM public.fact_batch
                    WHERE source = 'tushare:forecast')
  AND f.ann_date < DATE '2024-07-01'
  AND f.ts_code !~ '\.BJ$';

-- ══ 视图 6s:explore_reader_forecast_snap(manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_forecast_snap AS
SELECT
  f.ts_code,
  f.ann_date,
  f.end_date,
  f.first_ann_date,
  f.p_change_min,
  f.p_change_max,
  'batch' || f.batch_id AS snapshot_batch
FROM public.forecast_snap f
WHERE f.batch_id = public.study_snap_batch('forecast')
  AND f.ann_date < DATE '2024-07-01'
  AND f.ts_code !~ '\.BJ$';

-- ══ 最小 SELECT 授权(令三白名单;底表零权维持 009 焊死)══
GRANT SELECT ON public.explore_reader_forecast      TO taosha_engine;
GRANT SELECT ON public.explore_reader_forecast_snap TO taosha_engine;

COMMIT;
