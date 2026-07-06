-- 002 · 角色 · Claude Code 运维账户 qbase_app
-- 有 public schema DDL 权(建表/触发器/migration),但对 audit schema 零权限——
-- 结构上做不到"先废审计再动手"。密码不入 git:部署时 ALTER ROLE ... PASSWORD 从 .env 注入。
-- role_explore/role_holdout/role_service 待 Q3 视图族落地后另建(此处不预建)。

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='qbase_app') THEN
    CREATE ROLE qbase_app LOGIN;   -- 密码部署时注入
  END IF;
END $$;

GRANT CONNECT ON DATABASE qbase TO qbase_app;
GRANT USAGE, CREATE ON SCHEMA public TO qbase_app;

-- audit 对 qbase_app 一律封死(防拆前提)
REVOKE ALL ON SCHEMA audit FROM qbase_app;
REVOKE ALL ON ALL TABLES    IN SCHEMA audit FROM qbase_app;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA audit FROM qbase_app;
