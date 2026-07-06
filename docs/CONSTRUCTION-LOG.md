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
等人示意进 **Q1**(Entity Master 最小版)。焊死结构(受限用户 / `ddl_audit` 事件触发器 / 备份 cron / 哨兵 + DROP TRIGGER 防拆验收)随 Q1 建库一起落。
