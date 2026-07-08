-- 003 · 淘沙 L2 · b1 全市场流动性池成员 PIT 预计算(切片3 #2b = exp_id 3)
-- 依据: 附录 F / pap exp3 pool + 2026-07-08 人裁排产令①(contamination_note 在案);
--   compute/liquidity_pool.py 口径:trailing-20d 成交额均值 PIT 逐事件评估日排名(禁全期均值=前视着力点)、
--   上市满120交易日宇宙、前20%入池、停牌稳健(窗内非空均值)。
-- 铁律(承 002 market_return 范式):
--   ① append-only(触发器焊死),修数=新 batch;引擎读表不现算全市场 amount、路由 max batch。
--   ② 唯一写入=淘沙库;本表=L2 口径产物(池成员),非上游事实(amount 源=qbase bar_daily_snap,只读)。
--   ③ 口径写死表/列注释,运行时不可漂移;frozen_digest=liquidity_pool.audit 固定跑的是哪套口径。
--   ④ 北交所排除 + holdout<2024-07-01 继承 qbase 口径(源票取自非 .BJ、评估日 < holdout)。
-- apply 身份 = postgres(属主;taosha_app 无 schema CREATE 权)。幂等(IF NOT EXISTS)。

BEGIN;

-- ── 批次 + 溯源(每次预算=一个 pool_b1_batch)────────────────────────────────
CREATE TABLE IF NOT EXISTS public.pool_b1_batch (
  batch_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source         text        NOT NULL,   -- 'qbase:bar_daily_snap.amount(非.BJ)'
  frozen_digest  text        NOT NULL,   -- liquidity_pool.audit_digest():固定池口径(N20/120/20%)
  amount_window  int         NOT NULL,   -- 20(trailing 交易日)
  listing_min    int         NOT NULL,   -- 120(上市满交易日)
  top_fraction   double precision NOT NULL,  -- 0.20
  holdout_start  date        NOT NULL,   -- 2024-07-01(评估日必 < 此值)
  min_date       date        NOT NULL,
  max_date       date        NOT NULL,   -- 泄漏断言:必 < holdout_start
  n_dates        bigint      NOT NULL,   -- 覆盖评估日数
  out_rows       bigint      NOT NULL,   -- 落库(date×member)行数
  avg_pool_size  double precision NOT NULL,  -- 各期平均池规模(快照留档)
  pull_time      timestamptz NOT NULL,
  note           text                    -- 口径/快照/边界证据
);

-- ── 池成员(数据):逐 [评估日 × 成员票] ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.pool_b1_membership (
  batch_id   bigint  NOT NULL REFERENCES public.pool_b1_batch(batch_id),
  trade_date date    NOT NULL,           -- 评估日(PIT:成员由 [d-19,d] 成交额定)
  ts_code    text    NOT NULL,           -- 带后缀(沪深;非 .BJ)
  PRIMARY KEY (batch_id, trade_date, ts_code)
);
CREATE INDEX IF NOT EXISTS ix_pool_b1_membership_dt ON public.pool_b1_membership(trade_date, ts_code);

COMMENT ON TABLE public.pool_b1_membership IS
  'b1 全市场流动性池成员 PIT 预计算(#2b/exp3)。成员=评估日 d 上市满120交易日宇宙中,按 trailing-20 '
  '交易日成交额均值(PIT,禁全期均值)降序取前20%(ceil,同额 ts_code 稳定序)。停牌稳健(窗内非空均值);'
  '宇宙沪深(非.BJ);评估日<2024-07-01(holdout)。append-only(修数=新batch),引擎路由max batch '
  '(pool_b1_current 视图)读表不现算全市场 amount。口径=liquidity_pool.py(frozen_digest 见 batch)。';

-- ── max batch 路由视图(引擎 in_pool 查此)──────────────────────────────────
CREATE OR REPLACE VIEW public.pool_b1_current AS
SELECT trade_date, ts_code
FROM public.pool_b1_membership
WHERE batch_id = (SELECT max(batch_id) FROM public.pool_b1_batch);

-- ── append-only 焊死(UPDATE/DELETE 一律拒;修数=新 batch)────────────────────
CREATE OR REPLACE FUNCTION public._freeze_pool_b1() RETURNS trigger
LANGUAGE plpgsql AS $fn$
BEGIN
  RAISE EXCEPTION 'append-only: % 被拒(% 只增不改不删,修数=新 batch)', TG_OP, TG_TABLE_NAME;
END $fn$;

DROP TRIGGER IF EXISTS trg_freeze_pool_b1_batch ON public.pool_b1_batch;
CREATE TRIGGER trg_freeze_pool_b1_batch BEFORE UPDATE OR DELETE ON public.pool_b1_batch
  FOR EACH ROW EXECUTE FUNCTION public._freeze_pool_b1();

DROP TRIGGER IF EXISTS trg_freeze_pool_b1_membership ON public.pool_b1_membership;
CREATE TRIGGER trg_freeze_pool_b1_membership BEFORE UPDATE OR DELETE ON public.pool_b1_membership
  FOR EACH ROW EXECUTE FUNCTION public._freeze_pool_b1();

-- ── 授权(最小权;承 002 范式)────────────────────────────────────────────────
--   taosha_app:写入(loader,append-only 触发器仅拒 UPDATE/DELETE、放行 INSERT);
--   taosha_engine:只读 in_pool 路由视图 + 底表(引擎 PIT 池过滤 + 池等权基准)。
GRANT INSERT, SELECT ON public.pool_b1_batch      TO taosha_app;
GRANT INSERT, SELECT ON public.pool_b1_membership TO taosha_app;
GRANT SELECT ON public.pool_b1_membership TO taosha_engine;
GRANT SELECT ON public.pool_b1_current    TO taosha_engine;

COMMIT;
