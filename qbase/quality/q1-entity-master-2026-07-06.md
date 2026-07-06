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

## 结论

Q1 Entity Master 种子采集**落库完成、核行数一致、忠实存全口径落实、焊死在岗**。待人验收签收 → ROADMAP 标 ✅。
