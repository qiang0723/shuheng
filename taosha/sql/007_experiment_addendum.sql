-- 淘沙 · experiment_addendum 审计附属表(可信度硬化窗口 ⑤,人批 2026-07-12)
-- 修法(人令原文即口径): Experiment 审计附属对象,append-only;**不改终态载荷**,
--   原 result_json 一字不动。字段: exp_id / 原 result sha256 / 问题类别 / 附注正文 /
--   是否影响 verdict / created_at / 审批来源指针;同款触发器焊死(禁 UPDATE/DELETE)。
-- 依据: docs/hardening-window-order-2026-07-12.md ⑤;验收档 taosha/docs/hardening-item5-addendum-acceptance-2026-07-12.md
-- apply 身份 = postgres(taosha 库属主,承 001-006)。

BEGIN;

CREATE TABLE IF NOT EXISTS public.experiment_addendum (
  addendum_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  exp_id          bigint NOT NULL REFERENCES public.experiment(exp_id),
  result_sha256   text,                          -- 原 result_json 的 sha256(jsonb::text 规范化;无 result 的态可 NULL)
  category        text   NOT NULL,               -- 问题类别(如 strategy_version_qualification / cleaning_defect)
  body            text   NOT NULL,               -- 附注正文(人批口径原文,不改写)
  affects_verdict boolean NOT NULL,              -- 是否影响 verdict(判定本身由人批,此处忠实登记)
  approval_ref    text   NOT NULL,               -- 审批来源指针(施工单/裁决留痕文档路径+条款)
  created_by      text   NOT NULL DEFAULT current_user,
  created_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.experiment_addendum IS
  'Experiment 审计附属对象(硬化⑤): 对已闭卷 result 的事后附注(定性/缺陷登记),append-only;'
  '原 result_json 一字不动,verdict 不因附注改变;result_sha256 锚定附注所指版本。';

-- append-only 焊死(同款: UPDATE/DELETE 行级拒 + TRUNCATE 语句级拒,承 002/_no_truncate 006)
DROP TRIGGER IF EXISTS trg_experiment_addendum_freeze ON public.experiment_addendum;
CREATE TRIGGER trg_experiment_addendum_freeze BEFORE UPDATE OR DELETE ON public.experiment_addendum
  FOR EACH ROW EXECUTE FUNCTION public._freeze_appendonly();

DROP TRIGGER IF EXISTS trg_experiment_addendum_no_truncate ON public.experiment_addendum;
CREATE TRIGGER trg_experiment_addendum_no_truncate BEFORE TRUNCATE ON public.experiment_addendum
  FOR EACH STATEMENT EXECUTE FUNCTION public._no_truncate();

CREATE INDEX IF NOT EXISTS idx_experiment_addendum_exp ON public.experiment_addendum(exp_id);

-- 授权(只收不扩): taosha_app 记附注+读;引擎只读(报告可引附注,不可写)
GRANT SELECT, INSERT ON public.experiment_addendum TO taosha_app;
GRANT USAGE, SELECT ON SEQUENCE public.experiment_addendum_addendum_id_seq TO taosha_app;
GRANT SELECT ON public.experiment_addendum TO taosha_engine;

COMMIT;
