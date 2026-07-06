#!/usr/bin/env bash
# 枢衡每日备份 · 阿里云 root cron
# pg_dump(qbase)+globals(角色) + 观澜副本(只读拉老机) → 打包 → GPG-AES256 加密。
# 本地留明文(境内,快恢复);离境到 AWS 的只有 .gpg 密文 —— 与设计 §2.1「A股数据不出境」调和。
# 秘钥:GPG 口令在 /etc/shuheng/backup_gpg.pass(root 600,不进 git)。
set -uo pipefail

BDIR=/var/backups/shuheng
GDIR=$BDIR/guanlan
LOGDIR=/var/log/shuheng
PASS=/etc/shuheng/backup_gpg.pass

# ── 行情类表出境排除位(§2.1 预裁 2026-07-06)────────────────────────────
# 人预裁:自产数据(台账/快照)+ 公共公告事实(预告/减持,巨潮公开)密文出境异地 = 允许。
# 行情大表将来迁入本机后,其备份"是否出境"届时另裁,默认倾向境内跨区 OSS 替代出境。
# 届时把行情表名填入下列清单,离境打包按此裁剪(境内全量、离境剔除)。现为空、不实现。
OFFSITE_EXCLUDE_TABLES=""   # 例(勿填,现无):md.bar_daily_raw md.adj_factor md.daily_basic
# ────────────────────────────────────────────────────────────────────────

mkdir -p "$BDIR" "$GDIR" "$LOGDIR"
DAY=$(date +%F)
LOG="$LOGDIR/backup-$DAY.log"
HERE=$(cd "$(dirname "$0")" && pwd)
FAIL=0
notify(){ python3 "$HERE/feishu_notify.py" "$1" >/dev/null 2>&1 || true; }

{
  echo "=== 枢衡备份 $DAY $(date +%T\ %Z) ==="
  # 1. qbase(自产真身)
  if sudo -u postgres pg_dump -Fc qbase > "$BDIR/qbase-$DAY.dump"; then
    echo "[1] pg_dump qbase   OK  $(du -h "$BDIR/qbase-$DAY.dump"|cut -f1)"
  else echo "[1] ❌ pg_dump qbase FAILED"; FAIL=1; fi
  # 2. 全局角色(qbase_app 等,per-db dump 不含)
  if sudo -u postgres pg_dumpall --globals-only > "$BDIR/globals-$DAY.sql"; then
    echo "[2] pg_dumpall globals OK"
  else echo "[2] ❌ globals FAILED"; FAIL=1; fi
  # 3. 观澜每日轮转(只读拉老机 10.0.0.196,不动老平台)
  if scp -q -i ~/.ssh/id_ed25519 -o BatchMode=yes root@10.0.0.196:/opt/guanlan/data/guanlan.db "$GDIR/guanlan-$DAY.db"; then
    echo "[3] 观澜轮转       OK  $(du -h "$GDIR/guanlan-$DAY.db"|cut -f1)"
  else echo "[3] ❌ 观澜拉取 FAILED"; FAIL=1; fi
  # 4. 打包 + GPG 加密(离境只带密文)
  BUNDLE="$BDIR/shuheng-$DAY.tar.gz"
  tar -czf "$BUNDLE" -C "$BDIR" "qbase-$DAY.dump" "globals-$DAY.sql" -C "$GDIR" "guanlan-$DAY.db"
  if gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-file "$PASS" -o "$BUNDLE.gpg" "$BUNDLE"; then
    rm -f "$BUNDLE"; echo "[4] GPG-AES256    OK  $(du -h "$BUNDLE.gpg"|cut -f1)"
  else echo "[4] ❌ 加密 FAILED"; FAIL=1; fi
  # 5. 校验和(basename,供 AWS 侧 -c 校验)
  ( cd "$BDIR" && sha256sum "shuheng-$DAY.tar.gz.gpg" > "shuheng-$DAY.sha256" && echo "[5] sha256: $(cut -d' ' -f1 "shuheng-$DAY.sha256")" )
  # 6. 本地留存 14 份
  for pat in "shuheng-*.tar.gz.gpg" "qbase-*.dump" "globals-*.sql"; do
    ls -1t $BDIR/$pat 2>/dev/null | tail -n +15 | xargs -r rm -f; done
  ls -1t "$GDIR"/guanlan-*.db 2>/dev/null | tail -n +15 | xargs -r rm -f
  echo "=== 结果: $([ $FAIL -eq 0 ] && echo ✅成功 || echo ❌有失败) ==="
} | tee "$LOG"

[ $FAIL -ne 0 ] && notify "【枢衡·备份】🔴 $DAY 备份失败,详见 $LOG"
exit $FAIL
