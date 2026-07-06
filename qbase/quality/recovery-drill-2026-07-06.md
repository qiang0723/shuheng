# 恢复演练留档 · 2026-07-06

> 施工清单 v0.3 第一日 · 第3项「恢复演练(一石三鸟)」:四平台备份真实恢复 + 抽查行数。
> 副本=备份验证产物,**非第二真身**;qbase 视图上线后真身仍指向老库。

## 方法

- 老机(10.0.0.196)四平台备份 →**内网** scp → 新机(10.0.0.197)`/root/recovery_drill/` → 真实恢复 → 逐表 `count(*)`。
- 老机 / 新机 Postgres 均为 **18.4**,恢复零兼容问题。
- **纪律**:坩埚(crucible)、观澜(guanlan)全程只作为**文件**处理,**仅数行**,不读任何判断/决策内容列。

## 备份来源与恢复结果

| 平台 | 备份文件(老机) | 格式 | 恢复目标(新机) | 结果 |
|---|---|---|---|---|
| 雷达 radar | `/opt/radar/backups/radar_2026-07-05.dump` | pg custom | `radar_restore` | ✅ 22 表 |
| 观象 research_view | `/opt/research_view/backups/research_view_20260706.dump`(11:15) | pg custom | `research_view_restore` | ✅ 30 表 |
| 坩埚 crucible | `/root/crucible-backups/crucible_judgment_20260706.db.gz` | sqlite.gz | 解压计数 | ✅ 1 表 |
| 观澜 guanlan | `/opt/guanlan/data/guanlan.db`(见注3) | sqlite | 复制计数 | ✅ 3 表 |

## 行数对照

### 雷达 radar —— 恢复 == 现场(逐表完全一致,雷达无人值守未增量)

总计 **32,485 行 / 22 表**,恢复副本与老库现场逐表相等。要点表:
`raw_announcements 15600 · heat_signal 3590 · irm_qa_recon 2463 · raw_irm_qa 2463 · heat_segment 1490 · ev_event 493 · slow_event 360 · sector_map 264 · entities 151`

### 观象 research_view —— 恢复(11:15 快照)≤ 现场(19:00),差额=盘中 append

| 表 | 恢复(11:15) | 现场(19:00) | 说明 |
|---|---|---|---|
| raw_news | 4715 | 5487 | 盘中新闻续采 |
| mf_intraday_node | 1460 | 3588 | 盘中分时资金流 |
| task_log | 1218 | 1594 | 运行日志 |
| research_report | 479 | 492 | 研报续增 |
| report_increment | 8 | 14 | 增量续增 |
| 其余 25 表 | — | — | 逐表一致 |

差额均为 **恢复 ≤ 现场** 的单向增长,与 append-only + 日频走量吻合;备份是有效的时点快照,非缺损。要点表(两侧一致):`stock_node 267 · heatmap_stock 247 · theme_node 151 · decision_card 12 · judgment_card 8 · ledger 0`。

### 坩埚 crucible —— 仅数行

| 快照 | 表 | 行数 |
|---|---|---|
| 2026-07-06 | judgments | 81 |
| 2026-07-05 | judgments | 81 |

两日相等 → 坩埚「只运行,等判决日」,期间未产新判断。**全程未读任何判断内容。**

### 观澜 guanlan —— 仅数行

`holding 17 · timing_state 21 · decision 0`

## 结论

**四平台备份全部真实可恢复,行数核验通过。** 恢复副本留在新机 `/root/recovery_drill/`,不进 git、非真相源;可按季度演练复用,亦可清除。

## 需你留意(非阻塞)

1. **观澜无独立每日备份**:其它三平台有 backups/ 目录轮转,观澜只有 live `guanlan.db`(最近改动 06-29)。本次以该 live 文件作恢复对象。是否给观澜也上每日备份轮转,请你定。
2. **人的 ledger**:老库 `research_view.ledger` 表为 0 行;台账疑似走 CSV(`/opt/research_view/scripts/manage_ledger.py` + `backups/exports_*.tar.gz`)。请确认「人的 ledger CSV」具体落点,以纳入新机备份链覆盖确认。
3. 老机 backups/ 内有 `env_taipei_20260706` 等 .env 文件,**未读取**,只知其存在。

— 待人签收 —
