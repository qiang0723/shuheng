# Q3 · explore_reader_prices.limit_status 推导规则（2026-07-07）

> Q3 归一列 `limit_status` 的口径文档，随 Q3 验收包交人过目。载体视图 = `explore_reader_prices`（`qbase/sql/008_explore_reader.sql`）。
> 铁律 7：视图只做归一（制度事实的机械应用），**不打质量分、不做信号判断**。limit_status 是把原始 OHLC + 交易所涨跌停制度映射为一个分类标签，属归一、非加工。

## 1. 输出取值

`limit_status ∈ {none, limit_up, limit_down, one_word}`，逐 [证券×真实交易日] 一值。

| 值 | 含义 |
|---|---|
| `none` | 未触及涨跌停 |
| `limit_up` | 收于涨停价（未全日封死） |
| `limit_down` | 收于跌停价 |
| `one_word` | 一字板：全日一价且封停（涨或跌） |

## 2. 输入 = 原始价（非后复权）

判定用 `bar_daily_snap` 的**原始** `close`(raw_close) / `pre_close`(raw_pre_close) / `open,high,low`。
⚠ **不用后复权价**：涨跌停是对当日原始价相对昨收的限制，后复权（×adj_factor）会破坏绝对价关系、令判定失真。契约 `close` 列吐后复权（供收益），limit_status 判定另取原始价——两者刻意分离。

## 3. limit_pct 限幅分档（制度事实）

```
is_st              → 0.05      -- 风险警示 5%(见 is_st 规则文档)
board = 'main'     → 0.10      -- 主板 10%
board = 'chinext'  → 2020-08-24 前 0.10 / 当日及之后 0.20   -- 创业板注册制 regime
board = 'star'     → 0.20      -- 科创板 20%
else(含 'bse')     → 0.30      -- 北交所 30%
```
- 优先级：is_st 最高（ST 股无论板别均 5%），其次 board。
- `board` 由 ts_code 前缀判：`\.BJ$`→bse / `^688`→star / `^(300|301)`→chinext / else main。
- 创业板 2020-08-24 = 注册制涨跌停由 10% 改 20% 的 regime 边界（与切片2 `frozen_ashare` 同源日期）。
- **is_st 联动**：limit_pct 首档取决于 is_st，故 is_st 的 PIT 正确性直接决定 limit_status。2026-07-07 修复 is_st 446 票污染后，这些票摘帽区间的 limit_pct 由误挂 5% 回归 board 限幅（见 is_st 规则文档 + §6 分布变化）。

## 4. 涨跌停价 = 分价位取整（round 到分）

```
涨停价 = round(raw_pre_close × (1 + limit_pct), 2)
跌停价 = round(raw_pre_close × (1 − limit_pct), 2)
```
**分价位取整（round(·,2)）是要害**：交易所按「前收盘 × (1±幅度)」计算涨跌停价并**四舍五入到分（0.01 元）**。不取整则浮点乘积几乎永不等于实际成交的整分价、判定恒 `none`（漏检）。取整到 2 位小数复现交易所的报价精度。

## 5. 判定逻辑（视图 SELECT 段，逐行）

```
raw_pre_close IS NULL 或 = 0                         → none        -- 首日/无昨收,无从判
o=h=l=raw_close 且 raw_close = 涨停价                → one_word    -- 一字涨停
o=h=l=raw_close 且 raw_close = 跌停价                → one_word    -- 一字跌停
raw_close = 涨停价                                    → limit_up
raw_close = 跌停价                                    → limit_down
否则                                                  → none
```
一字板判据 = 开=高=低=收（全日一个价）且该价 = 涨/跌停价（封死）。先判 one_word 再判普通涨跌停（一字是涨跌停的强封死子集）。

## 6. 已知近似（人裁不修，原样记录）

1. **退市整理期首日无限幅**（334 票 × 首日 1 行，人裁 2026-07-07 不修）：退市整理期首个交易日交易所不设涨跌停（首日无限幅），视图仍按 board 10% 判，该首日行的 limit_status 可能误标。影响 = 每只退市整理股首日 1 行，量级微小；人裁不修，在此注记。
2. **is_st 边缘裁定的联动**：退市整理期「XX退」按裁② is_st=false→落主板 10%（数值正确，见 is_st 规则文档裁②依据）；同日双名冲突按裁① 保守含 ST→5%。两脏点见 is_st 规则文档。

## 7. 分布实测（重灌 + is_st 修复后，库实物）

全表 limit_status 分布（库实物，holdout 后 total=15,295,821 行）：

| limit_status | 修前(is_st旧) | 修后(is_st已修) | 差 |
|---|---|---|---|
| none | 14,892,671 | 14,889,390 | −3,281 |
| limit_up | 218,357 | 220,757 | +2,400 |
| limit_down | 130,552 | 130,863 | +311 |
| one_word | 54,241 | 54,811 | +570 |

**守恒校验**：none 减少 3,281 = 涨跌停三态增加之和（2400+311+570）。这 3,281 行是 446 票摘帽后被误挂 5% 限幅、导致真实 10% 触板被判 none 的漏检行；is_st 修复后 limit_pct 回归 board 10%，正确翻为涨跌停。数字精确守恒 = 修复无副作用、恰好落回制度真值（呼应 is_st 规则文档裁②依据）。
