# 硬化窗口行政闭卷档(2026-07-15)

依据:2026-07-15 排产令 §1(`docs/holder-sell-scheduling-order-2026-07-15.md`,留痕 commit `f3acc50`)。
性质:**只收凭证,不扩大技术复核**。技术面终结论(五项 #1–#5 全闭)见外部复核终结论留痕 `828cf7a` 及验收档 `taosha/docs/postaudit-round3-narrow-acceptance-2026-07-13.md` §10/§11/§12。

## 1. 删除回报(令定八要素)

| 要素 | 凭证 |
|---|---|
| 执行时间 | 秘扫+SHA256:2026-07-15 12:26–12:31 CST;DROP 两库:**2026-07-15 12:35:49 CST**;rm r3disc:**2026-07-15 12:36:06 CST** |
| 执行身份 | 阿里云 root(SSH `aliyun-new`),DROP 经 `sudo -u postgres psql` |
| 归档清单 | 12 件证据 + SHA256SUMS + README = `docs/evidence/r3disc-2026-07-13/`(evidence.json / evidence2.json / mret_seed{,2}.log / pret_seed{,2}.log / orchestrate{,2}.{py,log} / orchestrate{,2}_stdout.log);秘密扫描全模式**零命中**;stdout 双写件与主日志 sha 逐字节同,照实归档 |
| Git commit | 归档 = `f305ba5`(6 件)+ `b9d6009`(8 份 .log 被 `.gitignore:20 *.log` 拦截后 `git add -f` 补入);均已 push GitHub |
| 异机核验 | ①源机(aliyun)sha256 ↔ AWS 拉取件 12/12 全等;②push 后 aliyun `git pull`(ff 至 `b9d6009`)拉取件 `sha256sum -c SHA256SUMS` **12/12 OK** + 与 `/root/r3disc/` 原件 `cmp` **12/12 SAME**——双向闭环后方执行删除 |
| 两库不存在 | 删除前 `pg_database` 9 库(含 qbase_iso 12GB / taosha_iso 801MB,合计 13,828,320,638 字节);删除后 7 库,`qbase_iso`、`taosha_iso` 均不在列(水印批 11–14 随库销毁) |
| 磁盘回收量 | `/` 分区 free 42,015,244,288 → 55,843,667,968 字节 = **回收 13,828,423,680 字节(≈12.88 GiB)**,与两库合计吻合;另 `/root/r3disc/` 7,266,645 字节(证据原件+隔离 git 树,已先归档)随目录删除 |
| 生产未变化 | 删除前后各查一次,全等:qbase `fact_batch` = 批 1–10(trade_cal 批={5,8,9,10});taosha `market_batch` max=**39**;`pool_b1_return_batch` max=**5**;`/opt/quant` HEAD=`b9d6009` porcelain **0**。生产库零写入、生产代码零改动 |

`/root/r3disc/` 整体删除,不保留重复隔离 git 树(与 GitHub 仓同源,证据链代码锚 `8b538e4` 可随时检出)和本地证据副本;删除后 `ls` 确认不存在、无残留进程。

## 2. #1-b 代理规则正式追认

按令,#1-b(next_open 顺延判定之开盘时点代理规则)冻结文本**正式追认**,文本锚定为:

> **`docs/postaudit-round3-narrow-order-2026-07-13.md` 末节原文**(R-open-1 开盘 print 存在 + R-open-2 开盘价不在跌停位;代理非真实成交验证,能力边界声明随 result/报告发布)。

自此 #1-b 不再是待批项;该文本即冻结口径,后续修改须走人批。

## 3. 关窗宣告

- 硬化窗口(2026-07-12 开窗,含五项修法+三轮窄补+判别力补测 v1/v2)**技术面+行政面全部闭卷,窗口关闭**。
- 冻结令(除 #3 采集外不新起施工跑批)随关窗解除;工地按 2026-07-15 排产令切换到结果生产(holder_sell 检验排产)。
- 本档为凭证收口,不重开技术复核;收尾期间未发现需重开窗口的问题。
