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
