# qbase · 数据口径注记 + 挂账台账

> 运行式登记表。两类内容:①**口径注记/已知不完备**(数据本身的边界,含"是否默认处理");②**挂账**(某验收点确认、留待后续验收点落地的项)。
> 纪律:注记只登记事实与边界,**不擅自补数/扩范围**;凡"是否处理"一律标默认值,默认=不动,改动需人拍。

## 一、口径注记 / 已知不完备

| # | 注记 | 实证 | 默认处理 | 备注 |
|---|---|---|---|---|
| C1 | tushare `stock_basic` 含退市宇宙对 **2007 年前退市不完备** | `T00018.SH`(上港集箱,退市 2006-10-20)老库 `md.security` 有、tushare 现行三态直查全返 0 行(见 `q1-entity-master-2026-07-06.md` 证据①) | **不捞回(可选项,非默认)** | Q2 marketdata 回填(含老库快照)可捞回;**是否捞回待人拍**。捞回则需注意其 observed_time 标回填批次、不冒充实时 |

## 二、挂账(留待后续验收点)

| # | 挂账项 | 起于 | 落地验收点 | 验收标准 | 状态 |
|---|---|---|---|---|---|
| L1 | 巨潮 secCode/orgId 映射填充 | Q1 签收(本次仅**确认设计位**:走 `entity_alias.alias_type` 通用位,未落任何巨潮码) | Q2 巨潮采集件落地 | ① `alias_type='cninfo_seccode'`/`'cninfo_orgid'` 填充行数(应≈在册主体数);② **secCode ↔ orgId 对射抽查**(同一 ts_code 的两码一致、可反查) | 🔒 待 Q2 |
| L2 | entity_alias 映射行的**完整性约束** | Q1 签收(原指令:Q2 填充前自查 (alias_type,alias) 唯一约束) | Q2 填充前(DDL) | 见下"⚠ 指令订正"——**非**盲加 (alias_type,alias) 唯一约束 | 🟡 待人确认订正 |

### ⚠ 指令订正(L2)· 需人拍

原指令:"Q2 填充前自查 (alias_type, alias) 上有无唯一约束/索引,无则加上"。**技术上直接加 `UNIQUE (alias_type, alias)` 是错的,会砸掉忠实存全**:

- `entity_alias` 是 **append-only 名史表**,`alias_type='name'` 的名字**天然重复**:跨 batch 重复(每次种子=新 batch,同名再现)、同 batch 内同名多段(如 `000995.SZ 皇台酒业` 在一批里出现 5 次不同 start_date)、甚至忠实存全下同 `(ts_code,name,start_date)` 多行。任何含 `name` 行的 `(alias_type,alias)` 唯一约束都会**拒掉合法历史行**。
- 巨潮码行 (`cninfo_seccode`/`orgId`) 是**映射语义**(1:1 身份码),与名史语义不同,不能共用一条唯一规则。

**订正方案(Q2 落地时做,scoped 到巨潮码行,不碰 name 行)**:
1. 正向(每主体每类型一码):`UNIQUE (batch_id, ts_code, alias_type) WHERE alias_type IN ('cninfo_seccode','cninfo_orgid')`(partial)。
2. 反向(每码映一主体):`UNIQUE (batch_id, alias_type, alias) WHERE alias_type IN ('cninfo_seccode','cninfo_orgid')`(partial)。
3. 查询加速(可选、非唯一):`INDEX (alias_type, alias)` 供码→ts_code 反查,**无害可随时加**。
4. **name 行不加任何唯一约束**(维持忠实存全)。

具体键组合待 Q2 巨潮码填充语义确定(每 ts_code 是否恰一 secCode/一 orgId)再定。DDL 会触发哨兵审计,属正常留痕。**请人确认此订正后,L2 按订正方案执行。**
