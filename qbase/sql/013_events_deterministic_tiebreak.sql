-- 013 · 事件视图 DISTINCT ON tie-break 确定性钉死(硬化窗口中人拍 A,2026-07-12)
-- 缺陷(硬化② 验收实测发现): explore_reader_events/_snap 的 DISTINCT ON (ts_code,first_ann_date)
--   ORDER BY ... ann_date ASC NULLS LAST 在最早 ann_date 并列多行时(全批 11,689 对)选行随执行
--   计划漂移——19 对可翻转事件存在性(实测漂 3 行: 105,584↔105,587),62 对可翻转层归属。
-- 人拍 A(2026-07-12): **工程钉死次级键**——排序追加代理键 id ASC(采集落库序,append-only 批内
--   永恒)。不宣称语义: 不是"选更好的行",是"任意但永远同一行";钉死效应在硬化③ 全量 diff 中
--   与 ST 修复分开归因;#4 已闭卷结果不动,缺陷走 ⑤ addendum 附注(c)(随附注(b) 一并补录)。
-- 本迁移: 两视图(008 现行 + 012 snap)同一口径同改;列名/序/类型逐一不变(CREATE OR REPLACE)。
-- 依据: docs/hardening-window-order-2026-07-12.md ②③ + 人拍留痕(验收档 hardening-item2 §缺陷);
-- apply 身份 = qbase_app(视图属主链承 008/010/012)。

BEGIN;

-- ══ explore_reader_events(008 版,max-batch 现值路由)══
CREATE OR REPLACE VIEW public.explore_reader_events AS
WITH orig AS (   -- 每 (票,first_ann_date) 取原始披露行;tie-break 钉死: ann_date 并列 → id ASC(人拍A)
  SELECT DISTINCT ON (f.ts_code, f.first_ann_date)
         f.ts_code, f.first_ann_date, f.type, f.batch_id
  FROM public.forecast_snap f
  WHERE f.batch_id = (SELECT max(batch_id) FROM public.fact_batch WHERE source='tushare:forecast')
    AND f.first_ann_date IS NOT NULL          -- 缺锚剔除(C3)
    AND f.first_ann_date < DATE '2024-07-01'  -- holdout 焊死
    AND f.ts_code !~ '\.BJ$'                   -- 北交所排除
  ORDER BY f.ts_code, f.first_ann_date, f.ann_date ASC NULLS LAST, f.id ASC   -- id=代理键,任意但钉死
)
SELECT
  o.ts_code,
  o.ts_code || ':' || to_char(o.first_ann_date,'YYYYMMDD') AS event_id,
  o.first_ann_date,
  CASE
    WHEN o.type IN ('预增','略增','续盈')       THEN 'good'
    WHEN o.type IN ('预减','略减','首亏','续亏') THEN 'bad'
    WHEN o.type = '扭亏'                         THEN 'turnaround'
    ELSE 'out_of_layer'
  END AS event_type_layer,
  'batch' || o.batch_id AS snapshot_batch
FROM orig o
WHERE o.type IN ('预增','略增','续盈','预减','略减','首亏','续亏','扭亏');

-- ══ explore_reader_events_snap(012 版,manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_events_snap AS
WITH orig AS (   -- 同一 tie-break 口径(两视图不允许分叉)
  SELECT DISTINCT ON (f.ts_code, f.first_ann_date)
         f.ts_code, f.first_ann_date, f.type, f.batch_id
  FROM public.forecast_snap f
  WHERE f.batch_id = public.study_snap_batch('forecast')
    AND f.first_ann_date IS NOT NULL
    AND f.first_ann_date < DATE '2024-07-01'
    AND f.ts_code !~ '\.BJ$'
  ORDER BY f.ts_code, f.first_ann_date, f.ann_date ASC NULLS LAST, f.id ASC   -- id=代理键,任意但钉死
)
SELECT
  o.ts_code,
  o.ts_code || ':' || to_char(o.first_ann_date,'YYYYMMDD') AS event_id,
  o.first_ann_date,
  CASE
    WHEN o.type IN ('预增','略增','续盈')       THEN 'good'
    WHEN o.type IN ('预减','略减','首亏','续亏') THEN 'bad'
    WHEN o.type = '扭亏'                         THEN 'turnaround'
    ELSE 'out_of_layer'
  END AS event_type_layer,
  'batch' || o.batch_id AS snapshot_batch
FROM orig o
WHERE o.type IN ('预增','略增','续盈','预减','略减','首亏','续亏','扭亏');

COMMIT;
