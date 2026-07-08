-- 002 · 淘沙 L2 · 全市场等权日收益预计算(切片3 步3)
-- 依据: ops/STATE.md〈切片3施工清单〉步3(市场收益预计算落库,统计口径产物归 L2);
--   compute/frozen_config.py 口径①=continuous(对数收益);engine/benchmark 裁定=#4 跑 market
--   (全市场等权)单跑;北交所排除口径(qbase 视图层已排,本表继承);holdout<2024-07-01(视图焊死,继承)。
-- 铁律(taosha CLAUDE.md §2/§3 + 承 qbase 006 append-only 范式):
--   ① append-only:禁 UPDATE/DELETE(触发器焊死),修数=新 batch;引擎读表不现算、路由 max batch。
--   ② 唯一写入=淘沙库;本表为 L2 统计口径产物(全市场等权基准),非上游事实。
--   ③ 口径写死表/列注释(骗不了人),运行时不可漂移。
-- 口径(与 seed_market_return.py 落库核逐字对应):
--   ret_eqw = 全市场等权【连续/对数】日收益
--           = 当日【有 present bar 且有前序 present bar】的票,其 log(后复权 close_d / close_前序present)
--             的【简单等权平均】。close=后复权(视图 explore_reader_prices);
--           停牌=缺行(视图无 null 行)→"相邻 present 行比值"恒等于 compute/returns.py multi_day
--             (estudy2 rates.cpp 复刻)的跨缺口收益:恢复日拿 catch-up 收益、落恢复日。
--   n_stocks(诊断列)= 分母 = 当日【有 present bar 且有前序 present bar】的票数;
--           停牌缺行不进分母;IPO 首个 bar 无前序价故不进;早年薄截面照算不修(此列作诊断)。
--   轴=explore_reader_calendar(SSE 交易日,约束②):源=explore_reader_prices ∩ explore_reader_calendar,
--     早年非交易日 bar(周日,trade_cal is_open=0,如 1992-10-04/1993-01-03)结构性排除、收益跨到前一日历交易日。
--   宇宙=沪深(北交所 .BJ 已在 qbase 视图层排除);holdout=trade_date < 2024-07-01(视图 WHERE 焊死,本表继承)。
-- apply 身份 = postgres(属主;taosha_app 无 schema CREATE 权)。幂等(IF NOT EXISTS / OR REPLACE)。

BEGIN;

-- ── 批次 + 溯源(每次预算=一个 market_batch)──────────────────────────────────
CREATE TABLE IF NOT EXISTS public.market_batch (
  batch_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source        text        NOT NULL,   -- 'qbase:explore_reader_prices'(经视图:继承 holdout+.BJ排除+后复权)
  hypothesis    text        NOT NULL,   -- 'market'(全市场等权基准;frozen_config regressor market_hypothesis)
  compounding   text        NOT NULL,   -- frozen_config 口径①: 'continuous'(对数收益)
  frozen_digest text        NOT NULL,   -- frozen_config.audit_digest():固定"跑的是哪套冻结口径"
  holdout_start date        NOT NULL,   -- 2024-07-01(继承视图焊死;落库后必满足 max_date < 此值)
  view_rows     bigint      NOT NULL,   -- 扫描视图行数(证据)
  out_rows      bigint      NOT NULL,   -- 落库行数(应≈8187、绝非全日历 8797;首日无前序→约 8186)
  min_date      date        NOT NULL,
  max_date      date        NOT NULL,   -- 泄漏断言:必 < holdout_start
  pull_time     timestamptz NOT NULL,   -- 预算批次时刻(UTC;observed 源头,不冒充实时)
  note          text                    -- 口径说明 / 双算闸结果 / 剔除与边界证据
);

-- ── 全市场等权日收益(数据)──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.market_eqw_return (
  batch_id   bigint  NOT NULL REFERENCES public.market_batch(batch_id),
  trade_date date    NOT NULL,
  ret_eqw    double precision NOT NULL,   -- 见表注:全市场等权连续(对数)日收益
  n_stocks   integer NOT NULL,            -- 见列注:当日等权参与票数(诊断列)
  PRIMARY KEY (batch_id, trade_date)
);
CREATE INDEX IF NOT EXISTS ix_market_eqw_return_date ON public.market_eqw_return(trade_date);

COMMENT ON TABLE public.market_eqw_return IS
  '全市场等权连续(对数)日收益预计算(切片3步3)。ret_eqw=当日有present bar且有前序present bar的票 '
  'log(后复权close_d/close_前序present)的等权平均;分母(n_stocks)=当日有present bar且有前序present bar的票'
  '(停牌缺行不进分母);轴=explore_reader_calendar SSE交易日(约束②,早年非交易日bar已排除);'
  '宇宙=沪深(北交所视图层已排);holdout<2024-07-01;append-only(修数=新batch),'
  '引擎路由max batch(见 market_return_current 视图)读表不现算。';
COMMENT ON COLUMN public.market_eqw_return.ret_eqw IS
  '等权连续(对数)日收益。收益核=compute/returns.py(estudy2 rates.cpp复刻)multi_day在无null视图序列上的'
  '等价:停牌缺行→跨缺口收益落恢复日。';
COMMENT ON COLUMN public.market_eqw_return.n_stocks IS
  '当日等权参与票数(诊断列,不作剔除依据)。=分母:当日有present bar且有前序present bar的票数;'
  '停牌缺行不进分母;IPO首个bar无前序价不进;早年薄截面照算不修。';

-- ── append-only 焊死:UPDATE/DELETE 一律拒(承 qbase 006 _freeze_appendonly;taosha 本库自建 OR REPLACE 幂等自足)──
CREATE OR REPLACE FUNCTION public._freeze_appendonly() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only 表 %:禁 %(修数=新 batch,不改不删)', TG_TABLE_NAME, TG_OP;
END $$;

DROP TRIGGER IF EXISTS trg_market_batch_freeze ON public.market_batch;
CREATE TRIGGER trg_market_batch_freeze BEFORE UPDATE OR DELETE ON public.market_batch
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_market_eqw_return_freeze ON public.market_eqw_return;
CREATE TRIGGER trg_market_eqw_return_freeze BEFORE UPDATE OR DELETE ON public.market_eqw_return
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

-- ── 引擎读:latest batch 路由视图(承 Q3 max-batch 路由范式;引擎读表不现算)──────
CREATE OR REPLACE VIEW public.market_return_current AS
  SELECT trade_date, ret_eqw, n_stocks
  FROM public.market_eqw_return
  WHERE batch_id = (SELECT max(batch_id) FROM public.market_batch);

-- ── 授权(只收不扩):落库 taosha_app 只 INSERT/SELECT(无 UPDATE/DELETE,触发器再焊一道);
--     引擎 taosha_engine 只 SELECT(读全市场等权基准,步4 ViewReader 消费)──────────
GRANT SELECT, INSERT ON public.market_batch      TO taosha_app;
GRANT SELECT, INSERT ON public.market_eqw_return TO taosha_app;
GRANT USAGE, SELECT ON SEQUENCE public.market_batch_batch_id_seq TO taosha_app;
GRANT SELECT ON public.market_eqw_return    TO taosha_engine;
GRANT SELECT ON public.market_return_current TO taosha_engine;

COMMIT;
