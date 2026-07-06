#!/usr/bin/env bash
# 异地拉取 · AWS ubuntu cron
# AWS(工地)主动从阿里云拉加密备份;阿里云从不反连 AWS —— 保持"代码下行/数据不上行"的不对称。
# 只取密文(.gpg)+ 校验文件;明文永不离境内。
set -uo pipefail
DEST=/home/ubuntu/shuheng-backups
mkdir -p "$DEST"
SRC=aliyun-new:/var/backups/shuheng

rsync -q -e ssh "$SRC/shuheng-"*.tar.gz.gpg "$DEST/" 2>/dev/null || true
rsync -q -e ssh "$SRC/shuheng-"*.sha256      "$DEST/" 2>/dev/null || true

cd "$DEST"
LATEST=$(ls -1t shuheng-*.tar.gz.gpg 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  STAMP="${LATEST%.tar.gz.gpg}.sha256"
  if [ -f "$STAMP" ] && sha256sum -c "$STAMP" >/dev/null 2>&1; then
    echo "$(date +%F\ %T) offsite OK: $LATEST 校验通过,共 $(ls -1 shuheng-*.tar.gz.gpg|wc -l) 份"
  else
    echo "$(date +%F\ %T) ❌ 校验失败: $LATEST"; exit 1
  fi
else
  echo "$(date +%F\ %T) ❌ 无备份可拉"; exit 1
fi
# 异地保留 30 份
ls -1t shuheng-*.tar.gz.gpg 2>/dev/null | tail -n +31 | xargs -r rm -f
