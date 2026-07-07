# Q2 · 行情回填 forecast + holdertrade · V1–V5 验收报告(2026-07-07)

> STATE 记录 / 验收留档。库为唯一真身,以下均 SELECT 实证。回填=`seed_facts.py`,源=tushare 分 ts_code 分片全量,锚 entity_master batch=6(含退市 5861)。

## 落库事实

| 表 | batch | 源 | 源拉→去重 | 终值 | distinct ts_code |
|---|---|---|---|---|---|
| `forecast_snap` | #1 | `tushare:forecast` | 147938 → 138458(去双投递 9480) | 138458 | 5707 |
| `holdertrade_snap` | #2 | `tushare:stk_holdertrade` | 182831 → 179843(去双投递 2988) | 179843 | 5263 |

脚本自检「核行数一致」通过。双时态:`valid_time`=公告时刻(UTC 入库),`observed_time`=批次时刻。

## V1–V5 验收(全过)

- **V1 源口径 ✅** — 源=tushare 全宇宙分片(`fact_batch.source` 实证)。**≠ 老机 marketdata `md` schema**:老机地图记载 forecast=766 / holder_trade=1131,与本次 138458 / 179843 量级差 2 个数量级,系不同总体,**不默认等价**(未连老机,凭源标签 + 量级佐证)。
- **V2 双发去重 ✅ 零残留** — forecast total 138458 == distinct(业务列) 138458;holdertrade 179843 == 179843。源双发已在脚本整行去净,库无精确重复。⚠ 注:snap 表主键仅代理键 `id`、无自然键唯一约束,去重靠脚本;本次实测有效,后续增量须维持同纪律。
- **V3 退市完整 ✅** — 宇宙 batch=6 = 5861(退市D=334/上市L=5527/暂停P=0)。facts 覆盖退市D票:forecast **324/334**(11056 行)、holdertrade **243**。退市票如实在库,防幸存者偏差成立(未覆盖的少数退市票=其生命周期内未发过对应公告,非被剔除)。
- **V4 first_ann_date ✅** — 非空率 **99.93%**(138367/138458);both-nonnull 中 first_ann≠ann_date 占 **9.65%**(13346 行)。证 **#4 事件日必须锚 first_ann_date**:9.65% 的预告经过修正,若锚 ann_date(最新披露日)则事件日后移=前视偏差。**R3 口径实证成立。**
- **V5 PIT 快照链 ✅** — 样本 `600053.SH` end=2020-12-31,修正 4 次:ann 2020-04-29 → 2020-08-26 → 2020-10-29 → 2021-01-30,**first_ann_date 恒=2020-04-29**,末次(2021-01-30)才填 net_profit 数字。锚首披日=4 次事件均锚 2020-04-29(市场首次得知),不被后续修正日误导;各行 valid_time=各自 ann 日 08:00+08。**PIT 语义成立。**

## 关键确认:valid_time 与 first_ann_date 同粒度对齐(人 2026-07-07 指定留档)

事件研究的**事件日锚**与**双时态 valid_time** 在本设计里语义分工清晰、粒度对齐:
- `first_ann_date` = **事件锚**(市场首次得知该预告之日),#4 用它定 T0。同一预告多次修正,first_ann_date 恒定 → T0 唯一,不漂移。
- `valid_time` = 该**具体披露行**的事件发生时刻(每次修正各自的 ann 时刻,UTC)。多修正 = 多行,各有各的 valid_time。
- 二者不冲突、不合并:first_ann_date 锚"事件序列的起点"(跨行恒定),valid_time 记"每一次披露的时点"(逐行)。V5 的 600053.SH 4 行即实证——4 个 valid_time、1 个 first_ann_date。这正是 bitemporal + 事件研究该有的对齐。

## 挂账 C3(✅ 已关闭 2026-07-07)

forecast_snap 91 行 first_ann_date 为 NULL。**#4 事件日锚 = first_ann_date,无 fallback 分支**(裁定禁用 ann_date fallback)。处置(人 2026-07-07 双拍):
- **(a) type→#4 三层映射人批冻结** → `taosha/docs/taosha-spec-appendix-C.md`(预喜=预增/略增/续盈,预亏=预减/略减/首亏/续亏,扭亏独立,不确定/其他=层外;污染标注 LLM拟定/人批冻结/未触收益数据)。56 行 type='其他'=层外、非 #4 事件。
- **(b) 35 行实层缺锚 = 排除**(缺锚不可定位事件日、非合格事件,不补锚),排除行按年份分解见附录C,不静默。
附录C 已随 v1.5(2026-07-07 生效)正式入档。
