# 枢衡 quant · STATE(会话无关权威状态)

> 状态持久化纪律(仓根 CLAUDE.md,v1.5)载体。**开工第一动作读此文件;阶段完成/收工必更新。**
> 本文件 + 数据库实物 = 真身;会话记忆是草稿。**断链恢复第一动作 = 查库 + 读本文件。**
> 改判纪律:口径/指针改判须在此**显式作废旧条目(内容+原因)**,不留新旧并存。

最后更新:2026-07-07(v1.5 批复生效 + 我侧三件激活后收工)

## 当前切片

**Q2 行情主线 ✅ 全部收口**。v1.5 A–G 全批生效。三题拍板(2026-07-07):走A先补切片1→验收→切片2;切片2用合成fixture不建mock视图、reader按explore_reader契约写死Q3零改造接入;十一条核对单于切片1验收后随切片2开工令给出、入 taosha/docs/。
**切片1 台账 = 终验就绪·待人终签(2026-07-07):** DB `taosha`(属主postgres,role `taosha_app` 非属主→禁不掉触发器)。表 `experiment`(§4+data_class/crowding_prior)。焊死触发器全自测过+重建后复检仍拒。**三裁已落地**(裁1 #3=literature+platform记note;裁2 closed编码+状态机注记;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填)。**登记终态五条齐(exp_id1-6):** radar_heat/holder_sell#3/forecast_drift/rv_resonance frozen + drawdown_rebuy #2closed+#2b frozen(family_trial自增1→2);#2b元数据量价/高。**pap_json↔§6 逐字核对 diff归零(12/12字段MATCH,verify_pap_vs_spec.py)**。入备份链。验收文档 `taosha/docs/slice1-ledger-acceptance-2026-07-07.md`。commit `d381af6→(本次)`。**待人终签→切片2(开工令+十一条核对单)。**

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
- **切片1 三裁已落地(2026-07-07,✅ 待终签)**:裁1 #3 source_type=literature+platform记note(已补登);裁2 closed编码批准+状态机注记入验收文档;裁3 创始四条元数据NULL、#2b=量价/高、此后新登记强制填(ledger焊)。仅剩人终签。
