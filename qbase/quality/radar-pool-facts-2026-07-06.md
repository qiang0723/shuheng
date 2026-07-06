# 雷达「股池」形式 · 事实报告 · 2026-07-06

> 应人要求(C):只报事实,不给方案。老 radar 库只读查得。

## 直接回答

雷达库里没有"带历史的股池表"。观察宇宙 = `entities` 表,**仅当前快照,覆盖式,无成员进出历史**。

| 问 | 事实 |
|---|---|
| **哪张表** | `radar.entities`——雷达观察宇宙。由 `ingest_watchlist.py` 填充(脚本名即 watchlist) |
| **结构** | 4 列:`canonical_id bigint`、`canonical_name text`、`stock_code varchar`、`aliases text[]`。**无任何时间列**(无 trade_date / observed_time / in_date / version) |
| **有无成员进出历史行** | **无**。151 行,`stock_code` 151 个全唯一(无同票多行);无 in/out date、无快照日、无 observed_time → 无法读出"任一历史日池内是谁" |
| **仅当前快照?** | **是**。覆盖式当前态;增删成员不留痕 |

## 旁证(radar 全表时间列扫描)

- 带 append 双时戳的是**信号/事件流**:`heat_signal`(3590,trade_date+valid_time+observed_time)、`heat_segment`、`ev_event`、`ext_moneyflow` 等——它们是每日信号/事件,**不是策展股池**;`heat_signal` 只回溯到 2026-05-20。
- `sector_map` 有 `in_date/out_date`——那是**行业成分**的进出,非股池。
- `entities`、`ev_arg_*` 等无时间列 = 当前态表。
- 成员快照类表 `ref_membership_snap`(snap_date)在 **research_view(观象)库**,不在 radar,且仅 3 个快照(07-03~07-05)。

## 事实对协议分支的映射(不替你决策)

- 用 `entities` 重建历史池 = 用今天的宇宙套过去 = 幸存者偏差(= 协议 c,你已否决)。
- 用每日 `heat_signal` 触发集当池 = 与假设 #1 同源耦合、改变 #2 含义(你已排除)。
- 两者都不可用 → 与你选定的**协议 (b)**(确定性规则池,公共事实定义、任意历史日可重算)一致。池规则参数待你事前冻结。
