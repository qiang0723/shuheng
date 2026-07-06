-- 001 · DDL 审计(哨兵加固补充单 §1)——防拆核心
-- 属主 = postgres(超级用户 / root 侧)。Claude Code 运维账户 qbase_app 对 audit 零权限。
-- 拆装任何触发器/表都经 event trigger 强制留痕,security definer 保证即便触发者无权也照写。
-- 幂等:可重复 apply。

CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION postgres;
REVOKE ALL ON SCHEMA audit FROM PUBLIC;

CREATE TABLE IF NOT EXISTS audit.ddl_audit (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_time      timestamptz NOT NULL DEFAULT now(),
  actor           text NOT NULL,          -- session_user:真实登录角色(security definer 不改它)
  command_tag     text,
  object_type     text,
  object_identity text,
  in_extension    boolean
);
REVOKE ALL ON audit.ddl_audit FROM PUBLIC;

CREATE OR REPLACE FUNCTION audit.log_ddl() RETURNS event_trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = audit, pg_temp AS $$
DECLARE r record;
BEGIN
  IF TG_EVENT = 'sql_drop' THEN
    FOR r IN SELECT * FROM pg_event_trigger_dropped_objects() LOOP
      INSERT INTO audit.ddl_audit(actor,command_tag,object_type,object_identity,in_extension)
      VALUES (session_user, TG_TAG, r.object_type, r.object_identity, r.in_extension);
    END LOOP;
  ELSE
    FOR r IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
      INSERT INTO audit.ddl_audit(actor,command_tag,object_type,object_identity,in_extension)
      VALUES (session_user, TG_TAG, r.object_type, r.object_identity, r.in_extension);
    END LOOP;
  END IF;
END; $$;
ALTER FUNCTION audit.log_ddl() OWNER TO postgres;

DROP EVENT TRIGGER IF EXISTS trg_audit_ddl_end;
CREATE EVENT TRIGGER trg_audit_ddl_end  ON ddl_command_end EXECUTE FUNCTION audit.log_ddl();
DROP EVENT TRIGGER IF EXISTS trg_audit_sql_drop;
CREATE EVENT TRIGGER trg_audit_sql_drop ON sql_drop        EXECUTE FUNCTION audit.log_ddl();
