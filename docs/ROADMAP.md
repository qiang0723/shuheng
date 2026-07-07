# 枢衡 · Roadmap(验收点进度镜像)

> 权威 = 本目录《施工清单 v0.3》《设计方案 v0.2》与《淘沙 spec v0.2 冻结版》。
> 本文件只做**进度镜像**,不新增范围;与权威冲突以权威为准。串行推进,每个验收点**人验收后**才进下一个。切片3 过 = **建设冻结**。

图例:✅ 完成 · 🟡 进行中 · ⬜ 未开始 · 🔒 等人批/等前置

## 里程碑序列

| 阶段 | 验收点 | 状态 | 备注 |
|---|---|---|---|
| **第一日** | 骨架 / 单向通道 / 恢复演练 / 焊死 / 备份链 / 到期台账 | ✅ | **全部落成并签收**:git+GitHub 中枢、bootstrap、恢复演练、前置查询、焊死+防拆实测、备份链(GPG 异地+密文恢复验证)、到期台账 cron。四份 quality 留档已签收 |
| **Q1** | Entity Master 最小版(ts_code 锚 + 别名;stock_basic/namechange 种子) | ✅ | **已签收(2026-07-07)**:master 5861(含退市 D=334)/ alias 20005(忠实存全)。namechange 源系统性脏,人批「忠实存全、归一留 Q3 视图」口径(005 放宽约束)。10 项核查 + 三项补证(对账差一 T00018.SH / 巨潮预留位 / #1858 实证)全过。留档 `quality/q1-entity-master-2026-07-06.md`;口径与挂账见 `quality/caveats-and-ledger.md` |
| **Q2** | 公共事实回填 PIT(forecast+holdertrade 全市场史 append-only + 巨潮采集件);三层核对协议验收 | 🟡 | **行情主线 ✅ 收口(2026-07-07)**:forecast_snap 138458 / holdertrade_snap 179843(源=tushare 分片全量,锚 batch=6 含退市);V1–V5 全过、C3 关闭、#4 三层映射冻结(`taosha/docs/taosha-spec-appendix-C.md`,污染标注)。留档 `quality/q2-facts-backfill-2026-07-07.md`。**巨潮腿**:`cninfo.py` 采集件已借入(确权+sha256)+ 覆盖自查(**人裁档位二**,减持须 PIT 读取)。范围裁定:仅 `forecast`+`stk_holdertrade` 两张("四件套"作废)。**待办**(`quality/caveats-and-ledger.md`):L1 巨潮码填充、L3 减持 PDF 解析增补(钉死3字段,**v1.5 已入清单,切片2验收后动工**)、L4 category 抽验、L2 映射基数核实;C1 T00018.SH 默认不捞 |
| **Q3** | 归一视图最小版(v_signal_radar / v_judgment_rv / explore_reader 族,holdout 焊 WHERE)+ 三角色权限隔离 | ⬜ | 验收 = 淘沙 reader 取到数 & 实测取不到 holdout 区。**换源约束见下 ⬇** |
| **Q3a** | LLM 截止日登记表(五列,人工种子) | ⬜ | |
| **Q4** | 六对象 schema 纸面稿 | 🔒 | 等人批;Q1–Q3 不等它 |
| **淘沙·切片1** | 台账 sql+ledger+pap+触发器;五条登记冻结、UPDATE 被拒实测 | ⬜ | |
| **淘沙·切片2** | 引擎(ADJ-BMP/秩/日历组合 + A股清洗 + 报告);合成数据跑通且 **estudy2 对数一致** | ⬜ | estudy2 装配中 |
| **淘沙·切片3** | 假设 #4 端到端 = 修正案三**总验收** | 🔒 | **⚠ 密封预判钩子**;前置 = 人密封预判已封存 → **建设冻结** |

## 未来绑定约束(背景,不是现在的任务)

- **Q3 换源能力(人补记 2026-07-05)**:项目合并日老阿里云退役,marketdata 及四平台自产数据全量迁入新机。故 Q3 归一视图**实现方式**必须预留"换源":视图定义**集中管理**,将来把数据源从"老库外部连接(FDW/dblink 只读)"切到"本机本地表"时,**只改视图定义、不动任何消费方代码**。现在不做任何迁移动作。

## 当前位置

**Q2 行情主线 ✅ 全部收口(2026-07-07)**:密封预判已封存(门已开)。回填 forecast_snap 138458 / holdertrade_snap 179843(tushare 分片全量,含退市宇宙);V1–V5 验收全过(源口径≠老机 md / 去重零残留 / 退市 324-334 / first_ann 非空 99.93% 证 #4 锚 first_ann_date / PIT 快照链)。C3(91 行 null-first_ann)驳回重挂后关闭:#4 锚 first_ann_date 无 fallback,type→#4 三层映射人批冻结(附录C,污染标注),35 行实层缺锚排除、按年份分解。留档 `quality/q2-facts-backfill-2026-07-07.md`。
**巨潮腿(并行、不阻塞切片2)**:`cninfo.py` 已借入(源 `github.com/quant-newman/radar`,确权+sha256 逐字等价),覆盖自查=人裁**档位二**,减持 PDF 解析件立为增补项 L3(**v1.5 已入清单,切片2验收后动工**)。
**下一步 = 待人令**:淘沙切片2(引擎/estudy2)或 巨潮件采集(L1 填充 + 减持采集)。挂账 L1/L2/L3/L4 + C1 在册。逐节点日志见 `CONSTRUCTION-LOG.md`。
