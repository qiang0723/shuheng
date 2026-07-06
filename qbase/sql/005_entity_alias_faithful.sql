-- 005 · entity_alias 落库口径:忠实存全(人批 2026-07-06;apply 身份 = qbase_app)
-- 背景:tushare namechange 源系统性脏 —— 全宇宙 5861 只中 1059 只(18%)存在同自然键
--   (ts_code,name,start_date)碰撞:①end 空(陈旧"仍当前")vs 填(真实结束日)并存(1801 键);
--   ②U/W 未盈利后缀同日并存;③tushare 自身错别字(如 退市印记 vs 印纪退)同日两名;
--   ④极少数两个不同非空 end(15 键)。这些是源事实的脏,不是待裁的真异常。
-- 决定(人批):L1 = 忠实底料,zero-judgment。放宽唯一约束到"整行不重复",tushare 每条 distinct
--   行都落;"哪个 end 真 / 哪个名 canonical"这类归一判断集中到 Q3 v_entity_alias 视图(可 PAP 改)。
--   符合 qbase 铁律7(表只存事实、忠实归一交给视图)。004 的窄约束在此放宽,采集脚本仅做整行去重。
-- 幂等:可重复 apply。append-only 焊死触发器不受影响(ALTER 不触发行级 U/D 触发器)。

-- 去掉 004 的窄自然键约束(Postgres 自动命名)
ALTER TABLE public.entity_alias
  DROP CONSTRAINT IF EXISTS entity_alias_batch_id_ts_code_alias_type_alias_start_date_key;

-- 换成全字段唯一(NULLS NOT DISTINCT,PG15+;PG18.4 支持):
-- 语义 = "同一 batch 内不得有逐字节完全相同的两行",与采集脚本整行去重同一不变量,做 DB 侧兜底。
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.entity_alias'::regclass
      AND conname = 'entity_alias_faithful_key'
  ) THEN
    ALTER TABLE public.entity_alias
      ADD CONSTRAINT entity_alias_faithful_key
      UNIQUE NULLS NOT DISTINCT
        (batch_id, ts_code, alias_type, alias, start_date, end_date, ann_date);
  END IF;
END $$;
