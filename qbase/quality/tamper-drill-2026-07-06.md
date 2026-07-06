# 哨兵防拆实测记录 · 2026-07-06

> 《哨兵加固补充单》验收:用 Claude Code 运维账户(`qbase_app`,非超级用户)真实执行 DROP TRIGGER,
> 验证 ddl_audit 留痕 + 飞书告警触达 + 拆装无法掩盖,验完恢复。**附实物,非结论。**

## 结构前提(实测确认)

- `audit.ddl_audit` 属主 = **postgres**;两个事件触发器 `trg_audit_ddl_end`(ddl_command_end)、`trg_audit_sql_drop`(sql_drop)在岗。
- `qbase_app` 对 `audit` schema `has_schema_privilege = false`——结构上碰不到审计。
- 审计函数 `audit.log_ddl()` = SECURITY DEFINER(postgres 属主):即便触发 DDL 的角色对 audit 无权,也强制留痕。

## 诚实记录:第一次跑暴露一个 bug(已修)

首次实测 DROP **报错回滚**(`record "r" has no field "in_extension"`)——`pg_event_trigger_dropped_objects()` 无 `in_extension` 列(那是 `ddl_commands()` 的)。后果:拆不成、也没留痕。修复 = 各分支只 SELECT 自身存在的列(commit `7676789`)。**这正是"附实物不附结论"的价值——若报"防拆已验",就是假的。** 下为修复后干净实测。

## 实测链条(修复后,2026-07-06 19:37 CST)

| 步 | 动作 | 结果(实物) |
|---|---|---|
| [1] 拆 | `qbase_app` 执行 `DROP TRIGGER trg_freeze_selftest` | psql 返回 `DROP TRIGGER`;冻结触发器**确实消失** |
| [2] 留痕 | 查 ddl_audit 新增行 | `id=16 \| actor=qbase_app \| DROP TRIGGER \| trg_freeze_selftest on public._sentinel_selftest` |
| [3] 掩盖 | `qbase_app` 尝试销痕 | `DELETE audit.ddl_audit` → **permission denied for schema audit**;`DROP EVENT TRIGGER` → **must be owner** |
| [4] 告警 | 跑哨兵 | 🔴 需复核:「冻结触发器缺失」+「今日 DDL 16 条」;**飞书返回 `StatusMessage:success`**;exit=1 |
| [5] 恢复 | `qbase_app` 重建 trigger | 冻结触发器回岗 |
| [6] 恢复留痕 | 查 ddl_audit | `id=17 \| actor=qbase_app \| CREATE TRIGGER \| trg_freeze_selftest ...`(恢复动作同样留痕) |

## 结论(结构性质,非承诺)

拆焊点这个动作:**做得成,但藏不住,且触即告警**。Claude Code 账户无法删审计、无法停事件触发器、无法在不留痕的情况下改数。哨兵每日 08:30 root cron(碰不到)复检并直发飞书;当日 DDL 非空即标「人工复核」——建设期 DDL 多属正常,由人过目;冻结期 DDL 罕见,非空即高度可疑。

留档另见 `/var/log/shuheng/sentinel-2026-07-06.log`(落地本机)+ 飞书(直发人)。— 待人签收 —
