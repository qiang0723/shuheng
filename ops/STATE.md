# 枢衡 quant · STATE(会话无关权威状态)

> 状态持久化纪律(仓根 CLAUDE.md,v1.5)载体。**开工第一动作读此文件;阶段完成/收工必更新。**
> 本文件 + 数据库实物 = 真身;会话记忆是草稿。**断链恢复第一动作 = 查库 + 读本文件。**
> 改判纪律:口径/指针改判须在此**显式作废旧条目(内容+原因)**,不留新旧并存。

最后更新:2026-07-07(v1.5 批复生效 + 我侧三件激活后收工)

## 当前切片

**Q2 行情主线 ✅ 全部收口**(回填 + V1–V5 + C3 关闭 + #4 映射冻结)。v1.5 A–G 全批生效。
**下一步 = 切片 2 开工令(人单独下达),此前不动工。** 巨潮件采集/L1 填充亦待人令。

## 已裁决口径与指针

- **Q2 范围** = `forecast` + `stk_holdertrade` 两张(tushare 源);~~"行情四件套"~~ **作废**(文档打架已裁 2026-07-07)。
- **库指针(aliyun-new qbase,实物为准)**:`forecast_snap`=138458(batch#1)/ `holdertrade_snap`=179843(batch#2)/ `entity_master`=5861(含退市 D=334)/ `entity_alias`=20005(忠实存全)。锚 entity_master batch=6。
- **#4 事件日锚** = `first_ann_date`,**无 fallback 分支**(~~回退 ann_date~~ 已撤销/严禁,2026-07-07 驳回)。
- **#4 type→三层映射(冻结)** = `taosha/docs/taosha-spec-appendix-C.md`:预喜{预增,略增,续盈}/预亏{预减,略减,首亏,续亏}/扭亏独立/层外{不确定,其他}。污染标注:LLM拟定·人批冻结·未触样本收益数据。
- **C3 关闭**:91 行 null-first_ann = 56 行'其他'(层外非#4)+ 35 行实层**排除**(缺锚不可定位,按年份分解入附录C)。
- **#3 = 档位二**:减持须 PIT 读取(含≥总股本1%门槛),不得 holdertrade 事后反筛。→ **L3 减持 PDF 解析增补件**(范围钉死:仅减持预披露类、仅抽 股东名/拟减持比例上限/减持期间 3 字段、失败行标注、不做通用框架);**v1.5 已入清单,切片 2 验收后动工**。
- **巨潮采集件** = `github.com/quant-newman/radar` 的 `src/radar/cninfo.py`(sha256 `7875485ceeb23f496bac6bf4550d0a7776e3af3603445df8b11dfd53670a4fde`),已借入 `qbase/ingest/cninfo.py`(逐字 copy)。本刀只抓公告列表元数据、不解析 PDF 正文。
- **切片 2 对数参照** = estudy2 **0.10.0 版本钉死**(附录D):GitHub 归档源装、源码快照入仓;未决 issue #12/#16;分歧逐笔归因先核参照未决 issue、CAR 聚合分歧附手算。
- **holdout 线** = 2024-07-01(焊在视图 WHERE)。
- **机器**:`aliyun-new`(部署 `/opt/quant` + qbase 库,我有 root)/ `aliyun-old`(老平台**只读**,ProxyJump,坩埚判断数据任何情况不读)/ 老 aws `43.213.181.243`(巨潮源**备份**,`john-test.pem`,只借采集件·数据不碰)。部署 = `git push origin main && ssh aliyun-new 'cd /opt/quant && git pull --ff-only'`。

## 运行中后台任务

- **无运行中任务**。`seed_facts.py` Q2 回填已完成并 COMMIT;守望 `b097j3l62` 已触发结束。
- **root cron(aliyun-new)**:哨兵 08:30 / 备份 03:00 / 到期提醒 09:00。查验 = `ssh aliyun-new 'crontab -l'` + 各日志;飞书秘钥 `/etc/shuheng/sentinel.env`。

## 待答点(挂账,见 qbase/quality/caveats-and-ledger.md)

- **L1**:巨潮 secCode/orgId 填充验收(行数 + secCode↔orgId 对射抽查)——巨潮件采集时。
- **L2**:alias 映射约束基数——反向唯一取 batch scoped 是有意容跨批复用还是应收紧全局?待 Q2 真数据核实基数后定死(现不焊)。
- **L4**:`cninfo.py` `category=""` 是否稳定返回减持预披露公告——实采抽验。
- **C1**:tushare 对 2007 前退市不完备(T00018.SH),默认不捞、挂老机退役迁移单(≈2027 H1)。
