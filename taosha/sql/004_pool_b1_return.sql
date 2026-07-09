-- 004 · 淘沙 L2 · b1 池等权日收益 PIT 活基准预计算(切片3 #2b = exp_id 3 · 步②)
-- 依据: pap exp3 benchmark.pool_hypothesis='雷达股池等权' + 2026-07-09 步②预置①(人):
--   基准=b1 池等权 PIT 活基准——基准成分逐日=当日池快照(pool_b1_current[d]);
--   验收硬项=任抽一日基准成分集合==当日池快照(seed_pool_b1_return --verify)。禁读静态 market_return。
-- 口径(与 seed_pool_b1_return.py 落库核逐字对应,骗不了人):
--   ret_pool_eqw[d] = 当日池快照成员(pool_b1_current 于评估日 d)中【有 present bar 且有前序 present bar】
--     的票 log(后复权 close_d/close_前序present) 的【简单等权平均】(收益核=冻结 returns.py multi_day/Close,
--     estudy2 rates.cpp 复刻;停牌缺行→跨缺口收益落恢复日,禁零填充)。
--   n_pool_stocks[d](诊断列)= 分母 = 上述【当日池快照内且有效收益】的票数;停牌缺行不进分母、
--     池快照内当日无 present bar 的票不进(⊆ 当日池快照);当期池空/无有效收益 → 该日无行(不落 None)。
-- 铁律(承 002/003 范式):
--   ① append-only(触发器焊死),修数=新 batch;引擎路由 max batch(pool_b1_return_current 视图)读表不现算。
--   ② 唯一写入=淘沙库;本表=L2 口径产物(池等权基准),非上游事实(价源=qbase 归一视图,只读)。
--   ③ 口径写死表/列注释,运行时不可漂移;frozen_digest=frozen_config.audit(收益核口径);
--      pool_batch_id=派生所依据的 pool_b1_batch(血缘:基准成分来自哪批池快照)。
--   ④ 北交所排除 + holdout<2024-07-01 继承(价源=非.BJ 视图、评估日 < holdout;落库后断言 max_date<holdout)。
-- apply 身份 = postgres(属主;taosha_app 无 schema CREATE 权)。幂等(IF NOT EXISTS / OR REPLACE)。

BEGIN;

-- ── 批次 + 溯源(每次预算=一个 pool_b1_return_batch)──────────────────────────
CREATE TABLE IF NOT EXISTS public.pool_b1_return_batch (
  batch_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source         text        NOT NULL,   -- 'qbase:explore_reader_prices∩calendar × taosha:pool_b1_current'
  pool_batch_id  bigint      NOT NULL REFERENCES public.pool_b1_batch(batch_id),  -- 血缘:成分来自哪批池
  compounding    text        NOT NULL,   -- frozen_config 口径①: 'continuous'(对数收益)
  frozen_digest  text        NOT NULL,   -- frozen_config.audit_digest():固定收益核口径
  holdout_start  date        NOT NULL,   -- 2024-07-01(评估日必 < 此值)
  view_rows      bigint      NOT NULL,   -- 扫描价视图行数(证据)
  out_rows       bigint      NOT NULL,   -- 落库行数(有池等权收益的评估日数)
  min_date       date        NOT NULL,
  max_date       date        NOT NULL,   -- 泄漏断言:必 < holdout_start
  avg_n_stocks   double precision NOT NULL,  -- 各期平均有效分母(池快照内有效收益票数)
  pull_time      timestamptz NOT NULL,
  note           text                    -- 口径 / 双算闸结果 / 验收硬项 / 边界证据
);

-- ── b1 池等权日收益(数据)────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.pool_b1_return (
  batch_id      bigint  NOT NULL REFERENCES public.pool_b1_return_batch(batch_id),
  trade_date    date    NOT NULL,           -- 评估日(基准成分=当日池快照 pool_b1_current[d])
  ret_pool_eqw  double precision NOT NULL,  -- 见表注:池等权连续(对数)日收益
  n_pool_stocks integer NOT NULL,           -- 见列注:当日等权参与票数(诊断列,⊆当日池快照)
  PRIMARY KEY (batch_id, trade_date)
);
CREATE INDEX IF NOT EXISTS ix_pool_b1_return_date ON public.pool_b1_return(trade_date);

COMMENT ON TABLE public.pool_b1_return IS
  'b1 池等权连续(对数)日收益 PIT 活基准(#2b/exp3 步②)。ret_pool_eqw=当日池快照(pool_b1_current[d])'
  '成员中有present bar且有前序present bar的票 log(后复权close_d/close_前序present)的等权平均;'
  '分母(n_pool_stocks)=上述票数(⊆当日池快照;停牌缺行不进);收益核=冻结returns.py(rates.cpp复刻)'
  '跨缺口收益落恢复日;宇宙沪深(北交所视图层已排);holdout<2024-07-01。基准成分逐日=当日池快照'
  '(验收硬项:seed_pool_b1_return --verify 任抽一日成分==pool_b1_current[d]);禁读静态market_return。'
  'append-only(修数=新batch),引擎路由max batch(pool_b1_return_current视图)读表不现算。';
COMMENT ON COLUMN public.pool_b1_return.n_pool_stocks IS
  '当日等权参与票数(诊断列,不作剔除依据)。=分母:当日池快照内有present bar且有前序present bar的票数;'
  '停牌缺行不进;池快照内当日无bar的票不进;早年薄截面照算不修。';

-- ── max batch 路由视图(引擎 pool_return 查此)──────────────────────────────────
CREATE OR REPLACE VIEW public.pool_b1_return_current AS
  SELECT trade_date, ret_pool_eqw, n_pool_stocks
  FROM public.pool_b1_return
  WHERE batch_id = (SELECT max(batch_id) FROM public.pool_b1_return_batch);

-- ── append-only 焊死(UPDATE/DELETE 一律拒;修数=新 batch;承 002 _freeze_appendonly)──
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only 表 %:禁 %(修数=新 batch,不改不删)', TG_TABLE_NAME, TG_OP;
END $$;

DROP TRIGGER IF EXISTS trg_pool_b1_return_batch_freeze ON public.pool_b1_return_batch;
CREATE TRIGGER trg_pool_b1_return_batch_freeze BEFORE UPDATE OR DELETE ON public.pool_b1_return_batch
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_pool_b1_return_freeze ON public.pool_b1_return;
CREATE TRIGGER trg_pool_b1_return_freeze BEFORE UPDATE OR DELETE ON public.pool_b1_return
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

-- ── 授权(只收不扩;承 002/003 范式)────────────────────────────────────────────
--   taosha_app:写入(seed,append-only 触发器仅拒 UPDATE/DELETE、放行 INSERT);
--   taosha_engine:只读 pool_return 路由视图(引擎 SIM regressor rm=池等权 PIT)。
GRANT SELECT, INSERT ON public.pool_b1_return_batch TO taosha_app;
GRANT SELECT, INSERT ON public.pool_b1_return       TO taosha_app;
GRANT USAGE, SELECT ON SEQUENCE public.pool_b1_return_batch_batch_id_seq TO taosha_app;
GRANT SELECT ON public.pool_b1_return         TO taosha_engine;
GRANT SELECT ON public.pool_b1_return_current TO taosha_engine;

COMMIT;
