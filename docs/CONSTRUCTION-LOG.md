# 枢衡 · 施工记录(工程日志)

> 逐节点**追加**,不改旧条目。每条:做了什么 / 证据 / 关键发现 / 待人拍板 / 下一步。
> 配合 `ROADMAP.md`(验收点进度)阅读。

---

## 节点 2026-07-06 · 第一日初始化

### 做了
- **AWS 工地**:`git init` `quant/` monorepo(main 分支),`.gitignore` 焊死 `.env`(实测 `git check-ignore .env` 通过、`.env` 不入暂存),`.env.example` 模板,README 架构铁则。commit `87acc55`(骨架)、`041c723`(第一日交付);`status` clean。
- **新阿里云**(`aliyun-new` = 47.103.32.81 / 内网 10.0.0.197):加 2G swap;装 PostgreSQL **18.4**(active)、R **4.5.2**;`estudy2` 从 CRAN 存档装配中。
- **恢复演练**:四平台备份走**内网**(老 10.0.0.196 → 新 10.0.0.197)真实恢复 + 逐表数行,全部通过。留档 `qbase/quality/recovery-drill-2026-07-06.md`。坩埚/观澜仅数行,未读内容。
- **两个前置查询**:留档 `qbase/quality/precondition-queries-2026-07-06.md`。

### 关键发现
- **行情三问全 YES**:老 `marketdata`(`md` schema)全市场 5,863 只、含退市(335 只退市中 333 只有行情)、`adj_factor`+`trade_calendar` 齐,史至 1990-12-19。→ §9「日线回填子项」**不需激活**。
- **雷达股池 = append 历史,但深度仅 6 周**(2026-05-20 起)且**全在 holdout 线(2024-07-01)之后**;探索区零雷达数据 → 假设 #1/#2 探索区无样本。
- 新老机 PG 均 18.4;新机实测 **2c/7.2G/100G**(设计写 4c16G/200G)。

### 待人拍板(截至本节点)
- **A** 恢复演练签收 · **B** 哨兵告警通道(Gmail 应用密码 / 钉钉 webhook)· **C** 雷达 #1/#2 走向(建议③先跑 #4 立柱)· **D** #2「雷达股池」口径(entities 宇宙 vs heat_signal 触发集)。
- 信息类:人 ledger CSV 落点(老 `research_view.ledger` 空表,疑走 CSV);观澜是否加每日备份轮转。

### 下一步
等人示意进 **Q1**(Entity Master 最小版)。

---

## 节点 2026-07-06(下午)· 焊死结构 + 防拆实测(人批 A/B 提前拉起)

### 做了
- **GitHub 认领 + 部署管线**:GitHub `qiang0723/shuheng` 定为代码库(待授权推送,见待办);已建 AWS→阿里云 bare-repo 部署管线(`/opt/quant.git` + post-receive checkout → `/opt/quant`),`git status` 干净。
- **飞书告警链路**:webhook + 签名秘钥入阿里云 `/etc/shuheng/sentinel.env`(root 600,不进 git);连通测试 `StatusMessage:success`。
- **焊死结构**(commit `6733bf8`+`7676789`):建 `qbase` 库;`audit.ddl_audit` + security-definer 事件触发器(postgres 属主);`qbase_app` 运维角色(DDL 权、对 audit 零权);`_sentinel_selftest` append-only 夹具 + 冻结触发器;`sentinel.sh`+`feishu_notify.py`;root cron 每日 08:30。
- **防拆实测**:`qbase_app` 真拆 `DROP TRIGGER` → ddl_audit 留痕 → 销痕被拒 → 哨兵 🔴 飞书触达 → 恢复。留档 `qbase/quality/tamper-drill-2026-07-06.md`。
- **雷达股池事实报告**(C):`qbase/quality/radar-pool-facts-2026-07-06.md`——`entities` 仅当前快照无历史,佐证协议 (b)。
- **文档**:设计 §2.1 补记「数据域归属原则」(commit `71b3c1a`)。

### 诚实记录
防拆实测**首跑暴露审计函数 bug**(sql_drop 分支误引 `in_extension`,致 DROP 报错回滚且不留痕),已修(`7676789`)后重跑干净。附实物制度当场兑现价值。

### 待人拍板 / 待办
- **GitHub 推送授权**:加我公钥为 deploy key(写)或给 PAT;**并确认仓库设为 private**(项目机密性)。
- 剩余第一日项:备份链(每日 pg_dump + 异地同步 AWS)、观澜每日备份轮转(D 已批)。
- A 恢复演练 + 防拆实测两份实物待签收。

---

## 节点 2026-07-06(晚)· 备份链(Q1 前义务)

### 做了(A 已签收,证据规格立为惯例)
- **备份链**(commit `8b654de`):`backup.sh`(pg_dump qbase + globals + 观澜轮转 → GPG-AES256)root cron 03:00;`offsite_pull_aws.sh` AWS 主动拉密文 cron 03:30;明文留境内、只密文离境(调和 §2.1)。
- **三件验收实物 + 加验**:①首次归档 ✅成功 ②AWS 异地 sha256 校验通过 ③观澜轮转首份 `guanlan-2026-07-06.db` ④境内 restore-verify(解密→pg_restore→audit=17/selftest=2/观澜=21)。留档 `qbase/quality/backup-chain-2026-07-06.md`。
- GPG 恢复口令在阿里云 `/etc/shuheng/backup_gpg.pass`(root 600),已交人离线保存。

### 待办 / 记录
- **#2/#2b 协议(b)**:切片1 台账落地时执行——原 #2 置关闭、result_json 记「数据前提不成立(池表覆盖式无成员历史)」、族 drawdown_rebuy 计数 +1;#2b 待人冻结参数后才登记,在此前不实现任何池逻辑。
- **Q3 换源约束**(人补记):老库退役日数据迁入新机,归一视图须集中管理、换源只改视图不动消费方。见 ROADMAP。
- **第一日剩项**:到期台账 cron(季度恢复演练等提醒;「观澜轮转备份的恢复」纳入季度演练)。
- 备份链验收实物待签收。之后开 Q1。

---

## 节点 2026-07-06(收官)· 第一日完成

### 做了
- **口令事故整改**(人纠正):GPG 口令曾被打进对话,违反秘钥纪律。已轮换新口令(仅写 `/etc/shuheng/backup_gpg.pass` root 600,**不回显**),重跑备份用新口令覆盖旧密文(本地+AWS 异地均顶掉),新密文恢复验证通过。**立铁规**:交人离线保存的秘钥一律"写服务器文件、人自取",不进对话/代码/git。
- **§2.1 密文出境预裁**(人裁,Q2 免再问):自产数据+公共公告事实密文出境=允许,现行拓扑维持;行情大表将来迁入后其备份是否出境届时另裁(默认倾向境内跨区 OSS)。已在 `backup.sh` 加"行情出境排除位"(注释+空清单,不实现)。
- **到期台账 cron**(第一日第4项,收官,commit `627303f`):`reminders.py`+`due_dates.conf`,只提醒不建议,root cron 每日 09:00;实测命中「持仓复盘 2026-07-10 还有4天」并发飞书成功。

### 第一日状态:✅ 全部完成并签收
git+GitHub 中枢 · bootstrap(PG18.4/R4.5.2/estudy2 0.9.3)· 恢复演练 · 两前置查询 · 焊死+防拆实测 · 备份链(GPG 异地+密文恢复验证)· 到期台账 cron。三 root cron 在岗:哨兵 08:30 / 备份 03:00 / 提醒 09:00。五份 quality 留档(recovery/tamper/precondition/radar-pool/backup-chain)+ A、备份链已签收。

### 下一步(等人开跑)
**Q1 · Entity Master 最小版**(ts_code 锚 + 别名;stock_basic/namechange 种子;注意 namechange 静默缺失 #1858)。
携带约束:切片1 时执行 #2/#2b 协议(b);Q3 换源能力;Q2 前 A股数据落库再点人确认出境口径 + 密封预判钩子。

---

## 节点 2026-07-06(夜)· Q1 起步:机器就位,卡 tushare token

### 做了(代码 commit `0c9020f`+`d1d5f62`,已 push+部署,阿里云 `git status` 干净)
- **DDL**(`qbase/sql/004_entity_master.sql`,身份 qbase_app apply):`entity_batch`(批次+lineage 三字段)/ `entity_master`(ts_code 锚,含退市 L/D/P,双时戳,唯一 (batch,ts_code))/ `entity_alias`(namechange 历史名,`alias_type` 留通用位供 Q2 巨潮码)。三表 UPDATE/DELETE 冻结触发器焊死,幂等。**已 apply 到 qbase**。
- **采集脚本**(`qbase/ingest/seed_entity.py`):stock_basic L/D/P 三态全宇宙(含退市)+ namechange **分 ts_code 分片**抗 #1858,并与整表单拉计数对照(delta 记入 batch.note = "分片后全量核行数"证据);.env 读 token/DSN(不回显);COPY 落库 + 落库后核行数断言。语法通过。
- **运行环境**:阿里云仓库树外 `/opt/venvs/qbase-ingest` 装 tushare 1.4.29 / psycopg 3.3.4 / pandas 3.0.3(python3.14 兼容验过)。
- **哨兵扩展**(`sentinel.sh`):新增 entity 三表冻结触发器在岗检查(EFT 3/3)+ append-only 行数棘轮(记历史最大,任何下降=有人绕过触发器删数)。受控测试(去飞书)通过。

### 证据
- append-only 焊死实测:qbase_app 对 entity_batch 行 `UPDATE`/`DELETE` 双双被拒("append-only: … 被拒");夹具行用 postgres 超级权清理、触发器复位、batch=0 归零。
- DDL 审计:建三表全程进 `audit.ddl_audit`(哨兵当日报 🔴 待人工复核=本职,明日归 0)。

### 卡点(等人)
- **`/opt/quant/.env` 无 `TUSHARE_TOKEN`** → 种子跑不了。请人 ssh 自行 `echo 'TUSHARE_TOKEN=…' >> /opt/quant/.env`(只落 .env,不进对话/git)。加完开跑种子(namechange 分片 ~5800 只,限频约十几分钟)→ 出 quality 留档 → 人验收。
- 口径待人确认(不阻塞):Q1 种子 = tushare 实时最新全量快照 as-of=今日;参考主数据非回测行情,不触发密封预判钩子。

### 下一步
人写入 token → 后台跑 `seed_entity.py` → 核行数 + 退市在册 + namechange 完整性出 `qbase/quality/` 留档 → ROADMAP Q1 标 ✅ 待签收。

---

## 节点 2026-07-07(凌晨)· Q1 种子落库完成,待签收

### 卡点解除 + 落库
- token 已由人写入 `/opt/quant/.env`。首次跑种子:拉取全成功,但落库 COPY 撞 `entity_alias` 唯一约束整批回滚(单事务,无脏数据)。
- 根因诊断(全宇宙扫描):tushare namechange **源系统性脏**——raw 34330 行 / 纯双投递 14325 / distinct 20005;其中 1804 个 `(ts_code,name,start_date)` 自然键碰撞、涉及 1059 只(18%)。主形态 = 同一段命名 **end 空("仍当前"陈旧快照)vs 填(真实结束日)并存**(1801 键);另有 U/W 未盈利后缀、tushare 错别字同日两名(74 组同 start 异名)、15 个两非空 end。原脚本"把同键异 end 当罕见真异常、撞约束报错"的前提被证伪(是常态脏,非异常)。

### 人拍板(动归一口径,按规矩请示)
问题 + 两选项给人:①忠实存全,归一留 Q3 视图 ②入库即归一,种子里判断。**人选 ①**。理由:qbase 铁律7(表只存事实零判断、归一是视图的活);"挑哪个 end 真/哪个名 canonical"是纯判断,写进采集脚本会污染 L1,且 U/W 后缀+错别字需逐类定规则,脆弱。

### 做了(commit `7c51ffc`,已 push+部署,阿里云 git status 干净)
- **迁移 005**(`005_entity_alias_faithful.sql`,qbase_app apply):`entity_alias` 唯一约束由 `(batch,ts_code,alias_type,alias,start_date)` 放宽为 `UNIQUE NULLS NOT DISTINCT (…,end_date,ann_date)`(全字段元组);语义 = 同批内无逐字节相同两行,与脚本整行去重同一不变量。幂等。焊死触发器不受影响。
- **采集脚本**:口径注释三处改(旧"真异常撞约束"→"忠实存全、归一留 Q3 视图");batch note 记新口径。仅整行去重,同键 distinct 行照落。
- **重跑种子**:entity_master=5861(唯一 ts_code 5861,含退市 D=334)、entity_alias=20005,核行数一致 ✅。

### 证据(留档 `quality/q1-entity-master-2026-07-06.md`,10 项回读全过)
- 忠实存全实测:`000004.SZ *ST国华 20250430` end 空+20260622 两行都在;`002143.SZ 20191018` 印纪退+退市印记(tushare 错别字)两名都在;同自然键碰撞键 1804 忠实保留。
- 双时戳无 NULL;valid_time=start_date 当日;三表焊死触发器 3/3 在岗。
- #1858 证据:整拉 10000 vs 分片 distinct 20005,多出 10005,证分片抗截断有效。
- 如实记录:alias 唯一 ts_code 5860(1 只无改名史,忠实不补造);apply 005 进 ddl_audit,哨兵当日 🔴 待人工复核(本职,明日归 0)。

### 下一步(等人签收)
人验收 Q1 留档 → ROADMAP 标 ✅ → 进 **Q2**(公共事实回填 PIT)。⚠ Q2 是第一次碰真实市场历史行情,**开跑前必须先喊人封存密封预判**(回测口径+可交易口径两个数);巨潮 cninfo 采集件需借阅(问人要 GitHub)。

---

## 节点 2026-07-07 · Q1 签收 ✅ + 三项补证 + 口径/挂账台账

### 人签收 Q1(附三项补证要求,已补)
- **证据①对账差一落名字**:`md.security`(5862/D335) vs `entity_master`(5861/D334) 对称差=**恰一只 `T00018.SH`**(上港集箱,退市 2006-10-20,D 态)——同解总数与 D 数两处 off-by-one。补原文:`comm -13`(tushare∖md)为空、`comm -23` 仅 T00018;tushare 现行接口直查 T00018 三态全返 0 行(对照 600193.SH D 态返 1 行证接口无误)。归因=tushare 对 2007 前退市码口径收缩,非我方丢数。
- **证据②巨潮映射位**:`entity_alias.alias_type` 仅 `name`(20005),Q1 未落巨潮码;映射位预留于 `(alias_type,alias)` 多态对(004 §4.1),Q2 采集件填充。
- **证据③#1858 实证**:分片 20005(NULL-ann 14966/75%)vs 一次性拉 10000(NULL-ann 6502);差 10005 中 NULL-ann 占 8464(85%)——被截断丢的绝大多数是无公告日老改名行,分片全保住 → 生存偏差未混入。
- 签收前置确认:留档原缺"反向差集原文+tushare 直查 T00018 原文",**已补进 `q1-entity-master-2026-07-06.md` 证据①**。

### 留档指令三条(边界内执行)
- **指令1(口径注记)** → 新建 `quality/caveats-and-ledger.md` 登 C1:tushare 含退市宇宙对 2007 前退市不完备(T00018.SH),Q2 可捞回,**登记为可选项、默认不捞,待人拍**。
- **指令2(挂账)** → 登 L1:巨潮 secCode/orgId 填充为 Q2 验收项(填充行数 + secCode↔orgId 对射抽查)。
- **指令3(alias 唯一约束自查)→ 技术订正,报人待拍**:直接加 `UNIQUE (alias_type, alias)` **错**,会砸忠实存全——name 行天然重复(跨 batch、同批多段、同键多行)。订正=Q2 落地时加 **partial 约束 scoped 到巨潮码行**(正向 `(batch_id,ts_code,alias_type)` + 反向 `(batch_id,alias_type,alias)`,均 `WHERE alias_type IN ('cninfo_seccode','cninfo_orgid')`),name 行不加;非唯一 `(alias_type,alias)` 查询索引可选。登为 L2 🟡 待人确认。

### 状态
Q1 ✅ 已签收。下一步 = **Q2**(公共事实回填 PIT),🔒 未开跑。⚠ 开跑前必先喊人封存密封预判。挂账 L2 订正待人拍。

---

## 节点 2026-07-07 · Q1 最终签收 + Q2 开跑令(待封存预判)

### Q1 最终签收 ✅
- 两份原始输出补齐(反向差集 `comm -13` 空文 + tushare 现行接口直查 T00018.SH 三态全 0 行,含阳性对照 600193.SH 返 1 行)。人评"阳性对照做法很好"。
- 指令③复盘:人方承认"未核表语义即下约束方向"给错,我方拦截正确,orgId N:1 基数分析采纳。

### L2 裁定(人)
- **认方向,不焊**:四行约束表作为**设计意向登记**,全部待 Q2 真数据核实基数后再定。
- 人加 **Q2 待答确认点**:反向唯一取 `batch_id` scoped 是有意容纳跨批码复用,还是应收紧全局?——用巨潮真数据答。已登台账 L2。
- C1(T00018.SH 捞回)维持默认不捞、待拍。

### Q2 开跑令(人)
- **开跑门 = 人封存密封预判后通知**(封存动作人方完成即通知);我不擅自开跑。
- **开跑顺序**:行情四件套优先;巨潮采集件并行、**不阻塞切片2**。
- 巨潮 cninfo 采集件 **GitHub 借阅已批准**(开跑时需人给仓库指针)。

### 状态
Q1 ✅ 收口。Q2 🔒 待人封存密封预判通知后开跑。台账 `quality/caveats-and-ledger.md`:C1/L1/L2 在册。

---

## 节点 2026-07-07 · Q2 行情主线执行 + 收口

### 前置修正(人纠会话认知)
- **密封预判已封存**(architecture 仓 commit 在案),门已开。
- **Q2 范围 = 施工清单原义 `forecast` + `stk_holdertrade` 两张**;"行情四件套"表述**作废**(文档打架已裁)。
- **巨潮借阅源 = GitHub 雷达仓 `github.com/quant-newman/radar` 的 `src/radar/cninfo.py`**(此前误挂的 IP 43.213.181.243 作废为备份源)。
- 铁律实践:**库是唯一真身,查库不信会话记忆**——查得 006 已 apply、`seed_facts.py` 回填在跑(单腿分别 COMMIT,故跑完前 0 行属正常);本会话不重跑 seed,等 COMMIT 后接验收。

### 行情回填(库实证)
- `forecast_snap`=**138458**(batch#1,源拉 147938 去双发 9480);`holdertrade_snap`=**179843**(batch#2,源拉 182831 去 2988)。脚本自检行数一致。源=tushare 分 ts_code 分片全量,锚 entity_master batch=6(含退市 5861)。

### V1–V5 验收(全过,留档 `quality/q2-facts-backfill-2026-07-07.md`)
- V1 源=tushare 全宇宙 ≠ 老机 md(量级差 2 个数量级,不默认等价);V2 去重零残留(total==distinct_biz);V3 退市覆盖 324/334 防幸存偏差;V4 first_ann 非空 99.93%、9.65% 经修正→#4 锚 first_ann_date 必要(R3);V5 PIT 快照链 600053.SH 修正 4 次 first_ann 恒定;valid_time(逐行披露时点)↔first_ann_date(跨行事件锚)同粒度对齐留档。

### 巨潮腿
- 采集件 `cninfo.py` **借入** `qbase/ingest/`:源仓确权(我方私有 org,本体 HEAD==origin HEAD,提交人=人本人)、sha256 `7875485c…` 逐字等价、176 行零内部 import;雷达本体未动。留档核对报告 + `quality/q2-cninfo-coverage-2026-07-07.md`。
- **覆盖自查=部分覆盖**:本刀只抓公告列表元数据(不解析 PDF 正文)。**人裁档位二**:#3 减持预披露含"≥总股本1%"门槛须 PIT 读取、不得 holdertrade 事后反筛→PDF 解析件为真需求,立增补项(L3,钉死 3 字段股东名/比例上限/期间,切片2后随 v1.5,此前不动工)。`category=""` 稳定性→L4 实采抽验。

### C3(forecast 91 行 null-first_ann)处置:驳回重挂 → 关闭
- 首版误设"回退 ann_date"fallback,**人驳回**(违裁定原文:任何情况不得 ann_date fallback)。撤销。**#4 锚=first_ann_date,无 fallback 分支。**
- 核验 type 值域(10 值)对 #4 三层:发现 91 行**非全'其他'**(仅 56 层外;另 35 行实层类型属 #4 却缺锚)。映射表 docs 未冻结→上报。
- **人双拍**:(a) type→#4 三层映射批准冻结,登记 `taosha/docs/taosha-spec-appendix-C.md`(预喜=预增/略增/续盈,预亏=预减/略减/首亏/续亏,扭亏独立,不确定/其他=层外;**污染标注 LLM拟定/人批冻结/未触样本收益数据**);(b) 35 行实层缺锚=**排除**(不可定位事件日、非合格,不补锚),排除行按年份分解入附录C、不静默。**C3 关闭**。正式入档随 v1.5。

### 状态
**Q2 行情主线 ✅ 全部收口**(回填+V1–V5+C3关闭+#4映射冻结)。commit 链 `4c14455→d4c4574` 已 push + 阿里云 ff 同步,两台一致。**待办(非现在动工)**:L1 巨潮码填充、L3 减持 PDF 解析增补(切片2后随v1.5)、L4 category 抽验、附录C正式入档随v1.5。下一步待人令:切片2 或 巨潮件采集。

---

## 节点 2026-07-07 · v1.5 批复生效 + 我侧三件激活

> v1.5 A–G 全批(architecture 仓 + 知识库均已落地)。我侧三件随之激活执行。

### ① 状态持久化纪律入仓宪法
- 新建**仓根 `CLAUDE.md`**(全仓通用,子目录红线在其上叠加),追加"状态持久化纪律(v1.5)"原文:开工读 `ops/STATE.md` / 收工必写 STATE / 会话记忆为草稿·库+STATE 为准 / 改判须显式作废旧条目不并存 / 裁定不得善意改写。
- 首次实例化 `ops/STATE.md`(收工态)。

### ② 对数条款转附录 D
- 对数条款原在**冻结本体** `taosha-spec-v0.2-frozen.md:88`(泛化"estudy2 对数一致")。按"正文永不重开",不改本体,新建**附录 D** 承载 v1.5 新文本并**显式取代**本体那句(estudy2 **0.10.0 版本钉死**、GitHub 归档源装、源码快照入仓;背景=CRAN 移除+上游归档+未决 issue #12/#16;分歧逐笔归因先核参照未决 issue、CAR 聚合分歧附手算)。

### ③ 状态变更
- `taosha-spec-appendix-C`:"待 v1.5" → **正式入档**(v1.5 生效)。
- **L3**(巨潮 PDF 解析增补):"待 v1.5" → **已入清单,切片 2 验收后动工**。
- 改判纪律清扫:全仓 "待/随 v1.5" 引用(caveats C3/L3、coverage、q2-facts、ROADMAP)一并改为已生效态,不留新旧并存。

### 状态
v1.5 我侧三件 ✅ 落地。**下一步 = 切片 2 开工令(人单独下达),此前不动工。**
