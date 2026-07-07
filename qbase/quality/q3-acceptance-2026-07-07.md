# Q3 · explore_reader 归一视图族 完整验收包（2026-07-07）

> 切片3 硬前置。交人审 → 过则发切片3 开工令。载体 = `qbase/sql/008_explore_reader.sql`（三视图）+ `009_engine_role.sql`（引擎只读角色）。
> 库实物为唯一真身；本包数字均来自 aliyun-new `qbase` 现场查询。

## 交付物清单

| # | 交付物 | 状态 | 证据 |
|---|---|---|---|
| A | 008 三视图（prices/calendar/events）DDL | ✅ | `qbase/sql/008_explore_reader.sql` |
| B | 009 引擎只读角色 `taosha_engine`（权限焊死） | ✅ | `qbase/sql/009_engine_role.sql` |
| C | 越权实测（引擎直查 5 底表被拒） | ✅ | §3 |
| D | holdout 泄漏测试（经视图查 ≥2024-07-01 返空） | ✅ | §4 |
| E | 行情重灌 + 完整性核对（6000 硬顶破除、逐票闭合） | ✅ | `q3-rebackfill-integrity-2026-07-07.md` |
| F | limit_status 推导规则文档 | ✅ | `q3-limit-status-rule-2026-07-07.md` |
| G | is_st 推导规则文档（含缺陷发现+裁定+修复） | ✅ | `q3-is-st-rule-2026-07-07.md` |
| H | is_st PIT 正确性缺陷处置（446 票污染修复） | ✅ | §5 + G |

## 1. 三视图（契约对齐 Q3 零改造）

- `explore_reader_prices`：逐 [证券×真实交易日] 价格行 + 归一列（close=后复权/is_suspended=false/limit_status/board/is_st/industry）。holdout `WHERE trade_date < '2024-07-01'` 焊在 DDL。
- `explore_reader_calendar`：SSE 权威交易日轴（is_open=1），供切片3 引擎按 trade_cal 断档判停牌。
- `explore_reader_events`：业绩预告事件锚（first_ann_date 无 fallback + type→附录C 三层 + 缺锚/层外剔除）。
- 列契约逐字段对齐切片2 `reader/contract.py`（`docs/explore-reader-contract.md`）。

## 2. 视图路由到重灌新批

价格底料取 `max(batch_id)` 动态路由：daily→batch6（17,943,344）/ adj_factor→batch7（18,762,389）。旧截断批 batch3/4 被 supersede、append-only 保留。详见交付物 E。

## 3. 越权实测（权限物理隔离）

引擎 role `taosha_engine` 仅 SELECT 三视图，直查 5 底表（forecast_snap/holdertrade_snap/bar_daily_snap/adj_factor_snap/trade_cal_snap）全部 `permission denied`。（详见 009 建成验证记录，越权两件套已过。）

## 4. holdout 泄漏测试

经三视图查 `trade_date >= '2024-07-01'`（及 events 的 first_ann_date）全部返 0 行。holdout 线焊在视图 WHERE，非应用层。

## 5. is_st PIT 缺陷处置（本次核心发现）

写规则文档时在重灌真数据实测 `000004.SZ`（多次 ST↔摘帽），发现旧 is_st 逻辑被 namechange 脏孪生行（end=NULL 含ST行）永久拉 true → **446 票摘帽后误判恒 ST**。已修（latest-effective-name PIT，折叠孪生+LEAD划界），并落地人的 is_st 边缘裁定（①同日保守/②退市整理期字面false/③否三态）。完整 = 交付物 G。

**诚实声明**：STATE 旧「is_st PIT 已验」结论作废——008 初版验证时抽验未覆盖「摘帽段」，验证不充分。本次实测补齐、缺陷已修、单票+全表双验（见 G §6）。

## 6. 待切片3 承接（Q3 已交、非 Q3 缺口）

- 引擎 `cleaning.py` 现直读 is_suspended/limit_status flag；真实数据停牌=缺行 → 切片3 引擎须改按缺行 + `explore_reader_calendar` 权威轴判停牌（非 flag）。Q3 已交 calendar 视图，引擎适配属切片3。
- 次要完整性：coverage>1.0 共 242（list_date 晚于首 bar，待归因）/ null 存续 245（holdout 后上市，正常）——重灌后一并复核项，不阻 Q3。

## 7. 结论

Q3 explore_reader 视图族 = 价格半边（重灌全史 + 归一列，is_st 缺陷已修）+ 日历轴 + 事件锚，契约对齐、holdout/越权焊死、完整性核对闭合。**建议验收 → 发切片3 开工令。**
