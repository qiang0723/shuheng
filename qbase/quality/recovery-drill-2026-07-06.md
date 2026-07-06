# 恢复演练留档 · 2026-07-06

> 施工清单 v0.3 第一日第3项:四平台备份真实恢复 + 抽查行数。副本=备份验证产物,**非第二真身**。
> 🔹=判断/对账/记分类表(签收灵魂:不能只备行情漏判断)。⚠=源库现场>恢复副本(差额=备份后 append)。

## 执行留痕

- **恢复+计数**:2026-07-06 约 19:00 CST;**双列复核**:2026-07-06 20:00 CST。
- **账户**:root@新机(内网 10.0.0.197),经**内网** scp 从老机(10.0.0.196)取备份;PG 计数走 `sudo -u postgres`,SQLite 计数走 python3(老机)/sqlite3(新机)。
- **纪律**:坩埚/观澜全程只作文件处理,**仅 `count(*)`,未读任何判断内容列**。
- 新老机 PostgreSQL 均 18.4。

## 备份文件(生成日期)

| 平台 | 库/文件类型 | 备份文件 | 生成时间 |
|---|---|---|---|
| 雷达 radar | PG | `radar_2026-07-05.dump` | 2026-07-05 21:30 |
| 观象 research_view | PG | `research_view_20260706.dump` | 2026-07-06 11:15 |
| 坩埚 crucible | SQLite | `crucible_judgment_20260706.db.gz` | 2026-07-06 10:20 |
| 观澜 guanlan | SQLite | `guanlan.db`(live,见注) | 2026-06-29 22:36 |

## 行数对照(源库现场 vs 恢复副本)

### 雷达 radar —— 22/22 逐表一致(雷达无人值守,未增量)

| 表 | 源库 | 恢复 | | 表 | 源库 | 恢复 |
|---|--:|--:|---|---|--:|--:|
| entities | 151 | 151 | | irm_qa_concept_align | 33 | 33 |
| ev_arg_capacity | 177 | 177 | | irm_qa_heat_link | 101 | 101 |
| ev_arg_holding | 296 | 296 | | 🔹irm_qa_recon | 2463 | 2463 |
| ev_arg_order | 20 | 20 | | raw_announcements | 15600 | 15600 |
| 🔹ev_event | 493 | 493 | | raw_irm_qa | 2463 | 2463 |
| ev_order_contract_legacy | 124 | 124 | | sector_map | 264 | 264 |
| 🔹ev_reconciliation | 114 | 114 | | 🔹slow_event | 360 | 360 |
| ext_hk_hold | 221 | 221 | | slow_theme | 30 | 30 |
| ext_hsgt_flow | 57 | 57 | | 🔹heat_segment | 1490 | 1490 |
| ext_moneyflow | 4236 | 4236 | | 🔹heat_signal | 3590 | 3590 |
| ext_moneyflow_em | 36 | 36 | | ext_top_list | 166 | 166 |

### 观象 research_view —— 恢复(11:15快照)≤ 源库(20:00现场),差额=盘中 append

| 表 | 源库 | 恢复 | | 表 | 源库 | 恢复 |
|---|--:|--:|---|---|--:|--:|
| b7_weekly | 1 | 1 | | 🔹judgment_card | 8 | 8 |
| 🔹card_score | 0 | 0 | | 🔹ledger | 0 | 0 |
| chip_cost | 246 | 246 | | ⚠mf_intraday_node | 3588 | 1460 |
| daily_report | 9 | 9 | | moneyflow_rt_extra | 97 | 97 |
| data_flag | 22 | 22 | | node | 77 | 77 |
| 🔹decision_card | 12 | 12 | | ⚠raw_news | 5605 | 4715 |
| 🔹decision_score | 0 | 0 | | ref_membership_snap | 665 | 665 |
| fund_letter | 7 | 7 | | ⚠report_increment | 15 | 8 |
| heatmap_node | 75 | 75 | | research_digest | 5 | 5 |
| heatmap_stock | 247 | 247 | | ⚠research_report | 492 | 479 |
| holdings | 0 | 0 | | stock/stock_event | 250/57 | 250/57 |
| hotspot_daily | 5 | 5 | | stock_node | 267 | 267 |
| ⚠task_log | 1632 | 1218 | | tech_stock | 1308 | 1308 |
| theme_node | 151 | 151 | | watchlist | 0 | 0 |

### 坩埚 crucible / 观澜 guanlan

| 平台 | 表 | 源库 | 恢复 |
|---|---|--:|--:|
| 坩埚 | 🔹judgments | 81 | 81 |
| 观澜 | 🔹decision | 0 | 0 |
| 观澜 | holding | 17 | 17 |
| 观澜 | 🔹timing_state | 21 | 21 |

(观澜 `sqlite_sequence`=2 为 SQLite 内部序列表,非数据表,不计。)

## 判断类表专项核对(签收灵魂)

**判断/对账/记分数据确实在备份内,逐张有据:**
- 坩埚 `judgments` **81**、观澜 `timing_state` **21** / `holding` **17**、观象 `judgment_card` **8** / `decision_card` **12**、雷达对账 `irm_qa_recon` **2463** / `ev_reconciliation` **114** / 信号 `heat_signal` **3590**——**均非零且源=恢复一致**。
- 若干判断类表为 **0/0**(观象 `card_score`/`decision_score`/`ledger`/`holdings`/`watchlist`):**源库本就空**(记分未跑、ledger 走人本地 CSV),备份如实捕获空表,非备份遗漏——源恢两侧同为 0 即证。

## 结论

四平台备份**全部真实可恢复**,双列行数**逐表可核**:未运行的雷达三表全一致;日频走量的观象仅盘中续采的 5 张 append 表出现「恢复≤现场」正差;判断类数据零遗漏。恢复副本在新机 `/root/recovery_drill/`,非真相源。

**注(待你留意)**:观澜无独立每日备份轮转,本次以 live `guanlan.db` 为对象——你已批「上轮转」,随备份链一并做。 — 待人签收 —
