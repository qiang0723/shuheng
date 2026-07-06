# 备份链验收留档 · 2026-07-06

> 施工清单 v0.3 第一日备份链(Q1 建表前义务)。验收实物三件 + 加验"密文可恢复"。
> 执行:2026-07-06 20:11 CST,root@新机。

## 拓扑

```
阿里云(root cron 03:00) backup.sh
  pg_dump qbase(-Fc) + pg_dumpall globals + 观澜轮转(只读拉老机 guanlan.db)
  → tar.gz → GPG-AES256 加密 → /var/backups/shuheng/*.tar.gz.gpg + .sha256
  本地留 14 份(明文 dump 亦留,境内快恢复)
        │  只有密文离境
        ▼
AWS(ubuntu cron 03:30) offsite_pull_aws.sh  ← AWS 主动 rsync 拉取(阿里云不反连)
  /home/ubuntu/shuheng-backups/*.tar.gz.gpg  异地留 30 份 + sha256 校验
```

**§2.1 调和**:离境到 AWS 的**只有 GPG-AES256 密文**,明文行情永不离境内;恢复口令(`/etc/shuheng/backup_gpg.pass`,root 600)不离境。Q2 落 A股数据前再与你确认此口径。

## 实物① · 首次 pg_dump 归档成功

```
=== 枢衡备份 2026-07-06 20:11:58 CST ===
[1] pg_dump qbase   OK  16K
[2] pg_dumpall globals OK
[3] 观澜轮转       OK  36K
[4] GPG-AES256    OK  8.0K
[5] sha256: 93865a0c7c66aa9bce78331077cfbf0d3651cc1437d9e59815e990fa729f4956
=== 结果: ✅成功 ===
```
产物:`/var/backups/shuheng/{qbase,globals,shuheng-*.tar.gz.gpg,*.sha256}` + `guanlan/guanlan-2026-07-06.db`。

## 实物② · 异地(AWS)同步到位

```
2026-07-06 12:13:08 offsite OK: shuheng-2026-07-06.tar.gz.gpg 校验通过,共 1 份
/home/ubuntu/shuheng-backups/shuheng-2026-07-06.tar.gz.gpg  (6.0K)
sha256 -c: shuheng-2026-07-06.tar.gz.gpg: OK   ← AWS 侧独立校验通过
```
(AWS 时钟 UTC=12:13 = 阿里云 CST 20:13,同刻。)

## 实物③ · 观澜轮转首轮产物

`/var/backups/shuheng/guanlan/guanlan-2026-07-06.db`(36K)——首份每日轮转副本,只读拉自老机 `/opt/guanlan/data/guanlan.db`,老平台零改动。观澜自此有每日轮转(此前只有单一 live 文件)。

## 加验 · 密文可真恢复(骗不了人)

境内解密 → 解包 → 恢复,证明备份不是"存了个打不开的壳":
```
解密+解包: globals-2026-07-06.sql  guanlan-2026-07-06.db  qbase-2026-07-06.dump
pg_restore qbase → 恢复后:audit.ddl_audit=17  _sentinel_selftest=2
观澜副本 timing_state=21
```
scratch 库用完即删。

## 留存 / 告警
- 本地 14 份 / 异地 30 份轮转;备份失败 → 飞书告警(§7 告警条目)。
- **待补(第一日剩项)**:到期台账 cron(季度恢复演练提醒等),其中**「轮转备份的恢复」纳入季度演练清单**。

— 待人签收 —
