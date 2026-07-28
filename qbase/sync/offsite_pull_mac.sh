#!/usr/bin/env bash
# 异地拉取 · Mac Pro(launchd,迁移改判 2026-07-28:接替 offsite_pull_aws.sh)
# Mac 主动从阿里云拉加密备份;阿里云从不反连 —— 保持"代码下行/数据不上行"的不对称。
# 只取密文(.gpg)+ 校验文件;明文永不出库机。
# 拉取窗口(人裁 2026-07-28 改判:~~源端现存全部~~→最近 3 天):与异地留存 3 份对齐;
#   旧口径缺陷=源端 5 份>本地 3 份,每日重拉本地已轮转删除的 2 份旧密文(~2.8G)再删,且首拉须拉全部 5 份。
# 补拉:窗口内(≤2 天)漏跑可自愈;⚠连续漏跑 >2 天产生窗口外缺份 —— 阿里云本地留 5 份,
#   长时间关机后手动 rsync 指定日期补(rsync -e ssh "$SRC/shuheng-YYYY-MM-DD."* "$DEST/")。
set -uo pipefail
DEST="${SHUHENG_BACKUP_DEST:-$HOME/shuheng-backups}"
SRC="${SHUHENG_BACKUP_SRC:-root@47.103.32.81:/var/backups/shuheng}"
mkdir -p "$DEST"

# SHUHENG_PULL_WINDOW_DAYS:默认 3;首拉赶时间可设 1(只拉今日 ~1.4G),缺的两日由次日 launchd 按默认窗口自动补。
WINDOW="${SHUHENG_PULL_WINDOW_DAYS:-3}"
for ((d = 0; d < WINDOW; d++)); do
  DAY=$(date -v-"${d}"d +%F)   # macOS date;本脚本仅跑 Mac(launchd)
  rsync -q -e ssh "$SRC/shuheng-$DAY.tar.gz.gpg" "$DEST/" 2>/dev/null || true
  rsync -q -e ssh "$SRC/shuheng-$DAY.sha256"     "$DEST/" 2>/dev/null || true
done

cd "$DEST"
sha256_check() {  # macOS 无 sha256sum,回落 shasum
  if command -v sha256sum >/dev/null 2>&1; then sha256sum -c "$1"; else shasum -a 256 -c "$1"; fi
}
LATEST=$(ls -1t shuheng-*.tar.gz.gpg 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  STAMP="${LATEST%.tar.gz.gpg}.sha256"
  if [ -f "$STAMP" ] && sha256_check "$STAMP" >/dev/null 2>&1; then
    echo "$(date +%F\ %T) offsite OK: $LATEST 校验通过,共 $(ls -1 shuheng-*.tar.gz.gpg|wc -l) 份"
  else
    echo "$(date +%F\ %T) ❌ 校验失败: $LATEST"; exit 1
  fi
else
  echo "$(date +%F\ %T) ❌ 无备份可拉"; exit 1
fi
# 异地保留 3 份(人裁 2026-07-28 深夜改判:~~30 份~~→3 份;更早恢复点仅剩阿里云本地 5 份)
ls -1t shuheng-*.tar.gz.gpg 2>/dev/null | tail -n +4 | xargs rm -f
for s in shuheng-*.sha256; do [ -f "${s%.sha256}.tar.gz.gpg" ] || rm -f "$s"; done
