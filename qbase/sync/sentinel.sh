#!/usr/bin/env bash
# 枢衡哨兵 · 每日自检(设计 §2.2 + 哨兵加固补充单)
# root cron 运行,Claude Code 运维账户碰不到。检查:DDL 留痕 / 审计与冻结触发器在岗 /
# qbase_app 无 audit 权 / append-only 行数不降。日报落地本机 + 直发飞书(双通道)。
set -uo pipefail

DB=qbase
LOGDIR=/var/log/shuheng;   mkdir -p "$LOGDIR"
STATEDIR=/var/lib/shuheng; mkdir -p "$STATEDIR"
DAY=$(date +%F)
LOG="$LOGDIR/sentinel-$DAY.log"
BASEF="$STATEDIR/rowcount_baseline.tsv"
HERE=$(cd "$(dirname "$0")" && pwd)
Q(){ sudo -u postgres psql -d "$DB" -tAc "$1" 2>/dev/null; }
ALERTS=()

DDL_TODAY=$(Q "SELECT count(*) FROM audit.ddl_audit WHERE event_time::date=current_date")
DDL_LIST=$(Q "SELECT to_char(event_time,'HH24:MI:SS')||'  '||actor||'  '||command_tag||'  '||coalesce(object_identity,'') FROM audit.ddl_audit WHERE event_time::date=current_date ORDER BY id")
[ "${DDL_TODAY:-0}" -gt 0 ] && ALERTS+=("今日 DDL ${DDL_TODAY} 条,请人工复核")

ET=$(Q "SELECT count(*) FROM pg_event_trigger WHERE evtname IN ('trg_audit_ddl_end','trg_audit_sql_drop') AND evtenabled<>'D'")
[ "${ET:-0}" -lt 2 ] && ALERTS+=("❗DDL 审计事件触发器缺失/停用(在岗 ${ET:-0}/2)")

FT=$(Q "SELECT count(*) FROM pg_trigger WHERE tgname='trg_freeze_selftest' AND NOT tgisinternal")
[ "${FT:-0}" -lt 1 ] && ALERTS+=("❗append-only 冻结触发器 trg_freeze_selftest 缺失")

# Q1 entity 三表冻结触发器(应全 3 在岗)
EFT=$(Q "SELECT count(*) FROM pg_trigger WHERE tgname IN ('trg_freeze_entity_master','trg_freeze_entity_alias','trg_freeze_entity_batch') AND NOT tgisinternal")
[ "${EFT:-0}" -lt 3 ] && ALERTS+=("❗entity append-only 冻结触发器缺失/停用(在岗 ${EFT:-0}/3)")

APPAUD=$(Q "SELECT has_schema_privilege('qbase_app','audit','USAGE')::text")
[ "$APPAUD" = "t" ] && ALERTS+=("❗qbase_app 取得 audit schema 权限")

# append-only 行数不降(棘轮:记住历史最大,任何下降=有人绕过触发器删数)
MONITORED="_sentinel_selftest entity_batch entity_master entity_alias"
ROWLINE=""; NEWBASE=""
for T in $MONITORED; do
  CUR=$(Q "SELECT count(*) FROM public.$T"); CUR=${CUR:-0}
  BASE=""; [ -f "$BASEF" ] && BASE=$(awk -F'\t' -v t="$T" '$1==t{print $2}' "$BASEF")
  if [ -n "${BASE:-}" ] && [ "$CUR" -lt "$BASE" ]; then
    ALERTS+=("❗append-only 行数下降 $T ${BASE}→${CUR}")
  fi
  MAX=$CUR; [ -n "${BASE:-}" ] && [ "$BASE" -gt "$CUR" ] && MAX=$BASE
  NEWBASE+="$T	$MAX"$'\n'
  ROWLINE+="$T=${CUR} "
done
printf '%s' "$NEWBASE" > "$BASEF"

LEVEL="🟢 正常"; [ ${#ALERTS[@]} -gt 0 ] && LEVEL="🔴 需复核"
{
  echo "【枢衡·哨兵日报 $DAY】$LEVEL"
  echo "— 今日 DDL: ${DDL_TODAY:-0} 条"
  [ -n "$DDL_LIST" ] && echo "$DDL_LIST" | sed 's/^/    /'
  echo "— 审计事件触发器: ${ET:-0}/2 在岗 | selftest冻结: ${FT:-0} | entity冻结: ${EFT:-0}/3 | qbase_app→audit权限: ${APPAUD:-?}"
  echo "— append-only 行数: ${ROWLINE}"
  for a in "${ALERTS[@]}"; do echo "  ⚠ $a"; done
} | tee "$LOG"

python3 "$HERE/feishu_notify.py" "$(cat "$LOG")" >>"$LOG" 2>&1 || echo "feishu send FAILED" >>"$LOG"
[ ${#ALERTS[@]} -gt 0 ] && exit 1 || exit 0
