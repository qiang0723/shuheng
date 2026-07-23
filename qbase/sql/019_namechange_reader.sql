-- 019 · namechange 只读研究视图对(exp12 ST/风险警示完整撤销,冻结令 2026-07-23 三节"只读视图接入")
-- 范围(令三授权面): explore_reader_namechange(_snap) 只读视图对 / holdout 视图层焊死 /
--   taosha engine 最小 SELECT 授权。事件判别(段位折叠/状态谓词/完整撤销/fail-closed 六类)
--   不在视图内——qbase=L1 忠实归一零判断,规则属 L2 适配器(taosha/compute/st_removal_rules.py)。
-- 视图对(现值 + _snap manifest 路由)同口径,承 008/012/017/018 范式:
--   · holdout 焊死: (ann_date IS NULL OR ann_date < DATE '2024-07-01')(qbase 铁律5,线在视图;
--     锚=ann_date——冻结 PAP(digest 62a387a2…4353)事件锚唯一=ann_date;ann 为 NULL 的行忠实
--     传递(锚缺失=L2 fail-closed 剔除留痕,全部为 2010 年及以前段=覆盖边界,无 holdout 泄漏面);
--     ann≥holdout 的段结构上不可见);
--   · 北交所排除 ts_code !~ '\.BJ$'(冻结 PAP pool.universe"排除北交所,视图DDL焊死");
--   · **最小列面**=冻结 PAP event_def 名称段位法消费面:ts_code+alias(名称谓词)+start_date
--     (段折叠键+生效日校验)+ann_date(唯一事件锚)。end_date 冻结口径明令不信任
--     ("不信任行级 end_date,段边界=LEAD(start_date)")→ 不出列,结构上防误用;
--     孪生行(同 ts_code,start_date 多行)忠实传递不折叠,折叠属 L2(is_st PIT 修法同源);
--   · 研究期下限(2011-01-01)属 L2 事件规则,不焊视图(L1 忠实;锚缺失/期外剔除全在 L2 留痕)。
-- lineage: 源=entity_alias(tushare:namechange,append-only 焊死)/批次=现值 max(entity_batch)
--   或 study_snap_batch('namechange') 路由(键已在批次向量,snap121 实测 namechange:7)/口径=本头注。
-- apply 身份 = qbase_app(视图属主链承 008/010/012/013/017/018;属主自授 engine SELECT)。

BEGIN;

-- ══ 视图 7:explore_reader_namechange(现值 max-batch 路由)══
CREATE OR REPLACE VIEW public.explore_reader_namechange AS
SELECT
  n.ts_code,
  n.alias,
  n.start_date,
  n.ann_date,
  'batch' || n.batch_id AS snapshot_batch
FROM public.entity_alias n
WHERE n.alias_type = 'name'
  AND n.batch_id = (SELECT max(batch_id) FROM public.entity_batch
                    WHERE source = 'tushare:namechange')
  AND (n.ann_date IS NULL OR n.ann_date < DATE '2024-07-01')
  AND n.ts_code !~ '\.BJ$';

-- ══ 视图 7s:explore_reader_namechange_snap(manifest 路由)══
CREATE OR REPLACE VIEW public.explore_reader_namechange_snap AS
SELECT
  n.ts_code,
  n.alias,
  n.start_date,
  n.ann_date,
  'batch' || n.batch_id AS snapshot_batch
FROM public.entity_alias n
WHERE n.alias_type = 'name'
  AND n.batch_id = public.study_snap_batch('namechange')
  AND (n.ann_date IS NULL OR n.ann_date < DATE '2024-07-01')
  AND n.ts_code !~ '\.BJ$';

-- ══ 最小 SELECT 授权(令三授权面;底表零权维持 009 焊死)══
GRANT SELECT ON public.explore_reader_namechange      TO taosha_engine;
GRANT SELECT ON public.explore_reader_namechange_snap TO taosha_engine;

COMMIT;
