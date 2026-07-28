# 备份链验收留档 · 2026-07-06

> 施工清单 v0.3 第一日备份链(Q1 建表前义务)。验收实物三件 + 加验"密文可恢复"。
> 执行:2026-07-06 20:11 CST,root@新机。

> **⚠ 改判(2026-07-28,人裁):本地留存 14 份 → 5 份**。原因=本地明文+密文合计 39G,占 100G 系统盘大头(64%);本地定位为境内快恢复,5 份足够,更早恢复点走 AWS 异地密文。~~**异地 AWS 30 份不动,仍为最后防线。**~~(此句被当日深夜二次改判覆盖,见下条)下文正文中"本地留 14 份"字样为 07-06 验收时点原文,以本条为准。落地=backup.sh `tail -n +15`→`tail -n +6`(含观澜轮转同改)。
>
> **⚠ 二次改判(2026-07-28 深夜,人裁,迁移施工单改判记 #9):异地接收点=Mac Pro(AWS 工作机当日删除),异地留存 ~~30 份~~→3 份;AWS 现存 27G/30 份历史不迁、随删机消失**。原因=迁移拉取过慢;代价已向人陈述(每份均为全量快照,旧份唯一价值=更早恢复点;此后全系统恢复深度=阿里云本地 5 天+Mac 异地 3 天,07-24 前状态永久不可回溯),人知情裁定不留。落地=`qbase/sync/offsite_pull_mac.sh` `tail -n +31`→`tail -n +4`。下文拓扑图中"AWS…异地留 30 份"为验收时点原文,以本条为准。
>
> **⚠ 三次改判(2026-07-28 深夜二,人裁,迁移施工单改判记 #10):Mac 拉取窗口=~~源端现存全部密文~~→只拉最近 3 天**(与留存 3 份对齐;消除源端 5 份>本地 3 份导致的每日重拉 ~2.8G,首拉免拉旧份)。代价=补拉自愈窗口 4 天→2 天,窗口外缺份手动补(阿里云本地 5 份仍在)。留存份数口径(本地 5/异地 3)不变。
>
> **✅ 收口(2026-07-28 傍晚):异地接收点自此=Mac Pro,承接验收达成(迁移施工单改判记 #7 当日替代口径)**=①Mac 手动拉取 OK,今日密文 SHA 与阿里云权威值 `4c658b7a…8dce` 逐字一致;②launchd `com.shuheng.offsite-pull` 已 load(状态 0,plist 已指 Mac 实际仓路径 `~/Desktop/shuheng/shuheng/qbase/sync/offsite_pull_mac.sh`);③Mac 端 gnupg 解密今日密文列档实证(qbase/taosha dump+globals.sql;口令已离机至 Mac `~/.shuheng/backup_gpg.pass` 600)。**AWS 工作机 offsite_pull_aws.sh cron 已停用(crontab 已空)**;下文拓扑图与正文中 AWS 侧描述全部为历史留档。残余=次日 04:00 launchd 首次自动实跑未实地观察(改判记 #7 已陈述,人接受;失败时阿里云本地 5 份兜底)。

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
