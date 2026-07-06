-- 003 · 哨兵自检夹具(apply 身份 = qbase_app)
-- 一张 append-only 演示表 + 冻结触发器,专供"防拆实测"(DROP TRIGGER)与行数不降检查。
-- 非 Q1 业务表;Q1 起真实 append-only 快照表落地后,哨兵检查项扩展到它们。

CREATE TABLE IF NOT EXISTS public._sentinel_selftest (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  note          text,
  observed_time timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION public._freeze_selftest() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only: % 被拒(_sentinel_selftest 只增不改不删)', TG_OP; END; $$;

DROP TRIGGER IF EXISTS trg_freeze_selftest ON public._sentinel_selftest;
CREATE TRIGGER trg_freeze_selftest BEFORE UPDATE OR DELETE ON public._sentinel_selftest
  FOR EACH ROW EXECUTE FUNCTION public._freeze_selftest();
