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
