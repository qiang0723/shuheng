# Q1 · Entity Master 种子采集验收留档 · 2026-07-06

> 施工清单 v0.3 Q1:Entity Master 最小版(ts_code 锚 + 别名史;stock_basic/namechange 种子)。
> 执行:2026-07-07 00:06 CST(as-of 2026-07-06),阿里云新机 `/opt/venvs/qbase-ingest` 跑 `seed_entity.py`。
> 数据 = tushare 实时最新全量快照,参考主数据非回测行情,**不触发密封预判钩子**。

## 采集口径

- **entity_master**:tushare `stock_basic` L/D/P 三态全宇宙(默认只返 L,退市/暂停须显式 status),ts_code 锚,含退市。
- **entity_alias**:tushare `namechange` 历史名(alias_type='name'),分 ts_code 分片全量拉(抗 #1858 静默截断)。
- **忠实存全口径(人批 2026-07-06)**:namechange 源系统性脏(见下),L1 = 忠实底料零判断。落库前只做**整行去重**(去逐字节相同的双投递);同自然键的 distinct 行(end 空/填、U/W 后缀、错别字同日两名)**全部照落**。"哪个 end 真 / 哪个名 canonical" 留给 Q3 `v_entity_alias` 视图集中归一(可 PAP 改)。符合 qbase 铁律7(表存事实、视图归一)。
- 迁移 `005_entity_alias_faithful.sql`:唯一约束由 `(batch,ts_code,alias_type,alias,start_date)` 放宽为全字段元组 `UNIQUE NULLS NOT DISTINCT (…,end_date,ann_date)`,语义 = "同批内无逐字节相同两行",与脚本整行去重同一不变量。

## namechange 源脏的证据(全宇宙扫描,决定口径的依据)

```
源总行 raw=34330 / 整行去重掉 14325(纯双投递) → distinct=20005
(ts_code,name,start_date) 碰撞键 1804 个,涉及 1059 只 ts_code(全宇宙 18%)
  子类 end(空 vs 日期)     : 1801   ← 陈旧"仍当前"快照 vs 真实结束日,主形态
  子类 end(>1 个非空日期)  :   15
  子类 ann_date 不同        :    1
(ts_code,start_date) 但 name 不同(U/W 后缀 / tushare 错别字): 74 个
```

## 落库结果(seed_entity.py 输出)

```
stock_basic 合计 5861 行 / 唯一 ts_code 5861(退市 D=334)
namechange 分片:源拉 34330 行 → 整行去重后 20005 名(去双发 14325) / 整拉对照 10000 / 去重后仍多出 10005(#1858 截断证据)
落库核行数:entity_master=5861(应=5861) entity_alias=20005(应=20005) batch=(6,7)
✅ 种子完成,核行数一致。
```

**#1858 证据**:整表单拉只回 10000 行(被静默截断),分片全量拉 distinct 20005 行,多出 10005 行——证明分片抗截断有效,单拉不可信。

## 落库后回读核查(psql,身份 qbase_app)

| # | 检查 | 期望 | 实测 |
|---|---|---|---|
| 1 | entity_batch 批次数 + lineage | 恰 2 批,三字段完整 | ✅ batch 6=stock_basic / 7=namechange |
| 2 | entity_master 行/唯一 ts_code/三态 | 5861 / 5861 / L5527 D334 P0 | ✅ 全对 |
| 3 | 退市票在册(防幸存者偏差) | D 态含近期退市 | ✅ 退市创兴/沪科/太和…delist_date 在册 |
| 4 | entity_alias 行 / 唯一自然键 | 20005 / 18188 | ✅(1804 键忠实保留碰撞) |
| 5 | 忠实证据:000004.SZ *ST国华 20250430 | end 空 + 20260622 两行都在 | ✅ 两行都在 |
| 6 | 忠实证据:同自然键 >1 行的键数 | ≈1804 | ✅ 1804 |
| 7 | 忠实证据:002143.SZ 20191018 错别字两名 | 印纪退 + 退市印记 都在 | ✅ 都在 |
| 8 | 双时戳无 NULL(master/alias) | 0 | ✅ 0 / 0 |
| 9 | alias.valid_time = start_date 当日 | UTC 当日零点 | ✅(平安银行 2012-08-02 等) |
| 10 | 焊死触发器在岗 | 三表 BEFORE U/D 冻结 | ✅ 3/3 |

## 如实记录(非缺陷,忠实反映源)

- **entity_alias 唯一 ts_code=5860,比 master 少 1**:有 1 只票 tushare namechange 返回空(从无改名史),无别名行。忠实存源,不补造。
- **DDL 审计**:apply 005(ALTER TABLE ×2)进 `audit.ddl_audit`,哨兵当日报 🔴 待人工复核(=本职,明日归 0)。
- **identity 跳号**:entity_batch batch_id 从 6 起(1–5 为先前失败/诊断批次占号,失败批已随事务回滚,无脏批行)。identity 跳号正常,不影响。

## 补充证据(应验收要求,2026-07-07 补,人签收前提)

### 证据① · 对账差一落名字(5861 vs md.security 5862;D 334 vs 335)
`md.security`(老库)与 `entity_master`(tushare)ts_code 全集对称差 = **恰一只**:

```
T00018.SH  上港集箱(退)  list_status=D  delist_date=2006-10-20   ← 老库有、tushare 现行 stock_basic 已不返
tushare ∖ md.security = ∅(新库无任何老库外的多余票)
```

它是 D 态,**同时**吃掉总数(5862→5861)与 D 数(335→334)各 1,两处 off-by-one 归一到这一只。

**对账方法 + 差集原文**(两库同字段口径取全集,只比 ts_code 集):
```
老库:  ssh aliyun-old sudo -u postgres psql marketdata -tAF','
         -c "SELECT ts_code,list_status,name,delist_date FROM md.security ORDER BY ts_code"          → 5862 行
新库:  psql "$QBASE_APP_DSN" -tAF','
         -c "SELECT ts_code,list_status,name,delist_date FROM public.entity_master ORDER BY ts_code"  → 5861 行

$ comm -23 old_ts.txt new_ts.txt      # md.security ∖ tushare(老有新无)
T00018.SH
$ comm -13 old_ts.txt new_ts.txt      # tushare ∖ md.security(新有老无)
                                       ← 无输出 = 反向差集为空(新库无任何老库外多余票)
```

**tushare 现行接口直查 T00018.SH 原文**(证 tushare 侧已剔除,非我方管线丢弃):
```
=== tushare stock_basic 三态直查 ts_code=T00018.SH ===
  list_status=L: 返回 0 行
  list_status=D: 返回 0 行
  list_status=P: 返回 0 行
  → 三态合计 0 行(tushare 现行宇宙已无此码)
对照 600193.SH(退市创兴,D)返回 1 行 → 证接口/参数无误,唯 T00018 查不到
```

**归因**:tushare 现行 stock_basic 已剔除该 2006 年极早退市码("T"前缀老格式),老 marketdata 快照建得早仍留存——tushare 口径随时间对上古退市的收缩,非我方丢数。⚠ 如实标注:说明 tushare "含退市全宇宙" 对 2007 前退市并非绝对完备;若需补齐,Q2 marketdata 回填(含老库)可捞回 T00018.SH(登记为可选项,见 `caveats-and-ledger.md`)。

### 证据② · 巨潮映射位(验收单原项,显式确认)
`entity_alias` 现有 `alias_type` 取值**仅 `name`(20005 行),Q1 未落任何巨潮码**。
巨潮 secCode/orgId 映射位**已预留、非专列**:按 004 DDL 设计(§4.1),走 `alias_type` 通用位——Q2 起加 `alias_type='cninfo_seccode'/'cninfo_orgid'`、`alias`=码值,**无需改表**。**预留于 (alias_type, alias) 多态对,Q2 采集件落地时填充**。

### 证据③ · #1858 直接实证(NULL ann_date 行未被丢弃 = 防生存偏差)
tushare namechange 一次性全量拉受硬截断;缺陷杀伤集中在**无公告日(ann_date=NULL)的上古改名行**。分片 vs 一次性核对:

```
分片落库(我方表,忠实全量) total=20005 | ann_date=NULL 14966(75%) | 非NULL 5039
一次性全量拉 namechange()    total=10000 | ann_date=NULL  6502       | 非NULL 3498(单次调用硬上限 10000)
差 10005 行,其中 NULL-ann 占 8464(85%)—— 被截断丢掉的绝大多数正是无公告日的老改名行
```

**证明未丢**:14966 条 NULL-ann 行**已在库**(占 alias 75%);若用一次性拉,总量封顶 10000、且 85% 的丢失量恰是这些 NULL-ann 老行(退市/早期改名)。分片全保住 → 生存偏差未从第一张表混入。

## 结论

Q1 Entity Master 种子采集**落库完成、核行数一致、忠实存全口径落实、焊死在岗**,三项补充证据已补齐。待人签收 → ROADMAP 标 ✅。
