# exp14 `ex_div_gap` · 最小只读视图与冻结前数据对账报告

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 施工令：`taosha/docs/ex-div-gap-datarecon-order-2026-08-09.md`
- 代码 commit：`594c20b47452bc12d17187ddc84caf6d952f01e0`
- 草案：`taosha/docs/ex-div-gap-pap-draft-2026-08-08.json`
- 草案 digest：`b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`
- 结论：**数据对账通过；exp14 停在冻结前数据对账交验点。草案仍为 NOT-FROZEN。**

## 1. 授权面与主动收窄

本单元只完成：

1. `dividend` 批17与 `adj_factor` 批7的 exp14 专属 current/snap 最小忠实投影；
2. A1/B1/C1/D1 中的事件侧、版本、Decimal 阈值、因子资格门和组成审计；
3. source snapshot375 下 current/snap 双路与两次独立运行的确定性对账。

本地实现审查时曾出现 daily/bar 与专属 calendar 视图草稿。施工令第三节只授权
`dividend/adj_factor` 专属投影，且本单元只核事件侧和因子，因此该扩面在 commit 前主动删除。
最终生产 DDL 只有四张视图；交易日历复用既有 `explore_reader_calendar_snap`，未增加 daily/bar
视图，未读取价格、事件后收益、CAR 或显著性。

## 2. 生产应用与身份

阿里云 `/opt/quant` 快进到 `594c20b` 后，由 `qbase_app` 单事务应用：

```text
qbase/sql/028_ex_div_gap_reader.sql
BEGIN → 4×CREATE VIEW → 4×COMMENT → 4×GRANT SELECT → COMMIT
```

四张视图：

- `explore_reader_ex_div_gap` / `_snap`：dividend 最小事实列；
- `explore_reader_ex_div_factor` / `_snap`：adj_factor 最小事实列。

视图只做 current/snapshot 批次路由、`<2024-07-01` holdout 与 SH/SZ 正向白名单；
阶段、版本、阈值、因子变化和事件资格全部留在 taosha L2。`taosha_engine` 只获四张视图
SELECT；对 `dividend_snap` 的直接 SELECT 攻击仍为 `permission denied`。

运行环境：

- 镜像：`shuheng-quant:579a354`；
- image ID：`sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
- 架构/身份：`amd64`，`uid=10001(shuheng)`，非 root；
- 当前代码只读挂载 `/opt/quant:/workspace:ro`；容器根文件系统只读，仅专属取证目录可写；
- qbase 连接从建立起使用 `default_transaction_read_only=on`，实测为 `on`。

## 3. 数据锚与 current/snapshot 对账

source snapshot375：

- digest：`2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；
- 本单元实际消费键：`dividend=17 / adj_factor=7 / trade_cal=10`；
- snapshot375 完整 qbase 向量仍为13键，未修改；
- snapshot375 仅是源级快照，不是 exp14 研究 manifest。

只读视图实测：

| 视图腿 | current | snapshot375 | 批次 |
|---|---:|---:|---|
| dividend | 46,250 | 46,250 | batch17 |
| adj_factor（holdout+SH/SZ视图全量） | 15,688,523 | 15,688,523 | batch7 |

recon 仅为候选事件请求最小因子键：8,122 个请求键，返回 8,122 行；交易日历 8,187 日。
current 与 snapshot375 的来源批次、最终选择、漏斗、逐年组成和 selection SHA 均精确一致。

## 4. 严格人裁口径下的漏斗

### 4.1 方案与版本

```text
dividend 最小视图行                         46,250
研究窗内 div_proc=实施 行                  35,280
方案组 (ts_code,end_date)                  35,272
  = required_invalid                            0
  + timing_invalid                              1
  + component_invalid                      28,084
  + multi_null                                  5
  + multi_conflict                              0
  + qualified                               7,182
qualified = below_threshold 3,115 + threshold 4,067
```

`component_invalid` 主要是送/转两个分项均空、不能按人裁规则从合计忠实重建的非高送转组；
窄闸已经证明研究窗高送转实施行均可由至少一个分项精确重建，因此这一档未以代理值补样本。

B1 终版人裁明确：同组多行六字段任一含 NULL 即不可折叠。实测 `multi_null=5`，全部整组
fail-closed；零容差、零任取、零 `update_flag` 回填。

### 4.2 阈值、事件键与 A1 因子门

```text
Decimal stk_div >= 0.5                    4,067
事件键重复整键剔除                       -6  (3组)
因子门前候选                             4,061
  = factor_changed                       4,035
  + factor_static                           26
  + calendar/current/previous missing        0
  + factor_invalid                           0
最终数据侧参考事件                       4,035
恰等 0.5                                 1,083
```

六条恒等式 `group/threshold/event_key/factor/yearly/regime` 全部为 true。因子输入无重复键、
冲突键或无效值。

相对窄闸阶段尚未落 B1-NULL 细则的参考数 4,038，严格人裁后净少3个最终事件：阈值候选
由4,071降至4,067；其中一个原属因子静态候选，静态计数由27降至26。该变化来自冻结前已裁
规则，不是追数或按分布调整。

### 4.3 逐年与监管组成（全部 NOT_FOR_VERDICT）

| 年份 | 事件 | 年份 | 事件 |
|---|---:|---|---:|
| 2011 | 440 | 2018 | 307 |
| 2012 | 421 | 2019 | 171 |
| 2013 | 333 | 2020 | 135 |
| 2014 | 365 | 2021 | 121 |
| 2015 | 618 | 2022 | 135 |
| 2016 | 511 | 2023 | 110 |
| 2017 | 359 | 2024H1 | 9 |

逐年合计 `4,035`。监管粗三分：`<2017=2,688 / 2017-01-01..2018-11-22=664 /
>=2018-11-23=683`，合计同为 `4,035`。该三分不是精确法律制度分层，不计算收益或显著性。

## 5. 确定性与验证

两次 recon 均在单次进程内分别执行 current/snapshot 路径，并独立重跑两次：

- `current_snapshot_exact_match=true`；
- selection SHA：`ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；
- selection 内容 SHA：`33efedc3b943b637e58aa9cbe3b46c74f6857a750d187b087da07582abe78f76`；
- 两件完整 JSON 字节级相同，SHA256 均为
  `a6704a2d8ebfd5998ac26deeaf0159728e664baecff38293da2f3662dfd426d4`。

验证结果：

- exp14 rules：14/14 PASS；
- exp14 adapter：15/15 PASS；
- qbase DDL：15/15 PASS；
- 既有离线回归：29组全绿；
- 规模闸门：`files=222 / lines=32,867 / functions=909 / debt_files=20 /
  debt_functions=50`，无新增债务例外；
- 13类秘密扫描：`TOTAL_HITS=0`；
- 取证目录11件文件 `SHA256SUMS -c` 全部通过。

## 6. 状态、失败痕迹与停止线

运行后只读回验：

- exp14 仍为 `registered`，`frozen_at/result_json/done_at` 三槽全空；
- 台账仍为26行：`registered=7 / frozen=2 / done=15 / closed=2`；
- StudySnapshot 仍为20行、max=398；零新源快照、零研究 manifest；
- 草案 digest 未改、仍 NOT-FROZEN；
- 零收益、零 CAR、零显著性、零 result、零 persist。

后核验曾有两次连接前命令编排错误：第一次 DSN 被本地 shell 提前展开，psql 在默认本地
socket 以 root 身份失败；第二次修正命令在远端 shell 解析期失败。两次均未建立数据库连接，
未产生数据库写入；首次空 stdout 痕迹永久保留为 `postverify_taosha_attempt1.log`，最终只读
后核验成功。

内部取证目录：阿里云 `/root/s14datarecon/`。本报告完成后立即停交验点。下一步只能由 John
另令终版 PAP 文本收口；4,035 与本次 selection SHA 是 snapshot375 同锚的冻结前参考，
不得自动升格为正式运行硬断言。
