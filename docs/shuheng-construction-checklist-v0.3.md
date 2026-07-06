# 枢衡(quant/ monorepo)· 初始化与 qbase 首批施工清单 v0.3

> 替换 v0.2。变更:新架构正式命名**枢衡**;双云拓扑定案(人拍 2026-07-05)。Q1–Q4 内容承 v0.2 不变。

## 0. 拓扑(定案)

| 机器 | 角色 | 承载 |
|---|---|---|
| **阿里云机(数据与批算)** | 枢衡本体 | qbase 库、淘沙引擎运行时、巨潮/tushare 采集、假设台账、每日备份;老库只读直连(同云内网) |
| **AWS 机(服务与施工)** | 工地+出口 | Claude Code 常驻、LLM API、git 代码仓、对外服务部署与域名绑定(海外免备案)、将来美股腿 |

**三条跨云铁则:**
1. **写权限只在阿里云**:AWS(服务与 Claude Code)对 qbase 一律只读;淘沙台账写入只发生在阿里云。
2. **代码单向下行,数据不上行**:AWS 改码 → git push → 阿里云拉取部署;禁止直改阿里云生产代码。
3. **服务读"结果副本"**:台账/体检报告/记分等小体积产出,批算后从阿里云单向同步只读副本至 AWS 供服务读;大表(行情/回填)永不同步。阿里云数据库不对公网开放,仅对 AWS 固定 IP/隧道开只读账号。加密备份互为异地副本(阿里云→AWS)。

**注**:淘沙极简版无 Web UI(spec 绝不做清单),现阶段 AWS 无服务可部署属正常,勿为填充而造仪表盘(红灯律)。

## 第一日 · 初始化

**阿里云机:**
1. Ubuntu + PostgreSQL + **R + estudy2**;quant/ 拉取部署位;老库只读账号(radar/research_view/marketdata,SELECT only,同云内网);坩埚/观澜经备份文件副本。
2. 备份链:qbase+台账当日入每日备份(pg_dump+加密同步 AWS 异地);人的 ledger CSV 确认在覆盖内。
3. **恢复演练(一石三鸟)**:四平台备份全部真实恢复+抽查行数,留档人签收;副本非第二真相源。
4. 到期台账 cron:07-10 持仓复盘/10-06 雷达窗/10-25 checkpoint/每月红灯律/墓地回看/密封开启。只提醒不建议。

**AWS 机:**
5. git 仓建立(quant/ monorepo:qbase/、taosha/,零 import 只经表交换);Claude Code 环境;.env 秘钥纪律(tushare token、各 DSN 只住 .env 不进 git)。
6. 至阿里云的只读隧道/白名单;**不持有任何写凭据**。

## qbase 首批(阿里云机执行,串行,每步人验收)

**Q1 · Entity Master 最小版**:ts_code 锚+别名表;种子 tushare stock_basic/namechange;注意 namechange 静默缺失缺陷(issue #1858),分片后全量核行数。

**Q2 · 公共事实回填(PIT 工程)**:forecast+stk_holdertrade 全市场史(含退市)落 append-only 快照表(每次拉取=新批次+自打 observed_time,禁 upsert);**巨潮预披露采集件=雷达 cninfo 代码复制落位**(copy 不 import,雷达本体零改动),落 announcementId+announcementTime(毫秒)+adjunctUrl;常驻跨快照 diff 侦测回改。**验收=三层核对协议**(存在性分层抽样/时间戳偏差量化/回改侦测跑通)。**自动升级阈值**:ann_date 系统性晚1日→事件时点前移;回改率>1%→强制当时快照;缺失率>2%→巨潮升主源。

**Q3 · 归一视图最小版**:v_signal_radar / v_judgment_rv(decision_card→Judgment)/ explore_reader 族(WHERE trade_date < '2024-07-01' 焊死);每视图 lineage 三字段。验收=淘沙 reader 取到数据且实测取不到 holdout 区。

**Q3a · LLM 截止日登记表**:五列(model/version/knowledge_cutoff/enabled_date/note),人工种子。

**Q4 · 六对象 schema 纸面稿**:总架构窗口起草人批;Q1–Q3 不等 Q4。

## 总验收

淘沙切片3(#4 端到端,阿里云机跑)= 修正案三达成。

## 明令不做

不迁移老平台躯壳/不动老机配置/AWS 不持写凭据/不建 FDW 之外重型同步/不为 AWS 造前端。
