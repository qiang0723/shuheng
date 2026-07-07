-- 009 · 引擎只读角色 + 权限物理隔离(Q3 要件②:仿台账焊死范式)
-- apply 身份 = **postgres(超级用户)**——CREATE ROLE / 跨属主 GRANT 需超级用户;views(008)属主 qbase_app。
-- 焊死目标:引擎所用 role `taosha_engine` **仅可 SELECT 三个 explore_reader_* 视图**,对底表
--   (bar_daily_snap/adj_factor_snap/trade_cal_snap/forecast_snap/holdertrade_snap/entity_master/entity_alias)
--   **零权限**。视图属主 qbase_app,默认 security_definer(以属主权限读底表),故引擎经视图取数但无法直查底表。
-- 秘钥纪律:role 建为 LOGIN 但**不在此写密码**(不入 git);密码由 ops 另设(root 600 / psql \password),
--   DSN 写 aliyun `/opt/quant/.env` 的 TAOSHA_ENGINE_DSN(只读)。越权/holdout 验收用 SET ROLE 测(免密)。
-- 幂等:IF NOT EXISTS / 可重复 GRANT。

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='taosha_engine') THEN
    CREATE ROLE taosha_engine LOGIN;   -- 密码 ops 另设,不入 git
  END IF;
END $$;

-- 底线:引擎对底表零权(默认 PUBLIC 无 SELECT;此处显式 REVOKE 兜底,防将来误授)
REVOKE ALL ON public.bar_daily_snap, public.adj_factor_snap, public.trade_cal_snap,
             public.forecast_snap, public.holdertrade_snap,
             public.entity_master, public.entity_alias, public.fact_batch, public.entity_batch
  FROM taosha_engine;

-- 仅授:schema usage + 三视图 SELECT
GRANT USAGE ON SCHEMA public TO taosha_engine;
GRANT SELECT ON public.explore_reader_prices    TO taosha_engine;
GRANT SELECT ON public.explore_reader_calendar  TO taosha_engine;
GRANT SELECT ON public.explore_reader_events    TO taosha_engine;

-- 防未来新表默认可见:撤 PUBLIC 对 audit(若有)——保持最小面(仅确保引擎面干净,不动既有 qbase_app/postgres)
-- (audit schema 由 postgres 属主 + 事件触发器防拆,taosha_engine 无 USAGE,天然不可见,无需额外操作)
