# exp17 `earnings_flash_gap` NOT-FROZEN PAP 草案交付

日期：2026-07-30（UTC+8）

授权令：`earnings-flash-gap-pap-draft-order-2026-07-30.md`

草案：`earnings-flash-gap-pap-draft-2026-07-30.json`

## 结论

草案单元完成，**NOT-FROZEN**。本件只把已知事实、数据盲期锁定项、三项人裁菜单和既有
signed 单判决结构写成可复核文本；不构成冻结、数据施工或运行授权。

## 1. 结构与 digest

- 顶层 19 键，沿 exp20 signed 事件版结构并显式保留独立 `signed_ar` 键；
- 文件 SHA256 = 引擎 `canonical_pap_sha256()` =
  `b3c992bccc81af6384753f451eff779bddd60cfcb0838ecf5e524f5c0be80a39`；
- `validate_pap = PASS`；`parse_test_windows = (5, 20, 60)`；
- `diagnostic_dimensions.axes.direction = [up, down]` 在场；PAP 外方向白名单旁路字符串零命中；
- 文件本体为 canonical JSON 加末尾单换行，当前 digest 仅为草案候选，不得进入冻结、driver 或正式运行。

## 2. 令文到键位映射

| 令文要求 | PAP 键位 | 落地 |
|---|---|---|
| 已闭合 `update_flag` 探针，不重复 | `bias_statement` / `diagnostic_dimensions.data_quality_disclosure` / `snapshot_batch_req` | 记录 92/92 为 0 只证明字段存在，不外推全量无修订；未再次访问接口 |
| signed 硬约束 | `diagnostic_dimensions.axes.direction` / `engine_params` / `signed_ar` | 白名单仅 `up/down`，事件级逐 τ 翻转先于聚合与检验，单一顶层 verdict |
| 盲期锁定 | `event_def` / `reporting_commitments` / `bias_statement` | 严格比较、恰等不成事件、完整区间、同日不算前置、事件锚与研究期建议全部预写 |
| 三项人裁菜单 | `event_def` | A 预告基准、B 初始快报异常组、C 会计归属均列选项、影响与技术建议，未代填 |
| 数据前置 | `diagnostic_dimensions.data_quality_disclosure` / `snapshot_batch_req` / `reporting_commitments` | express 全量、源快照、初始/修订量化及会计口径未闭均禁止冻结 |
| prescreen 效力 | `verdict_power_note` / `reporting_commitments` | 正式 result/report 强制台账身份与 `llm/prescreen` 水印，缺失 fail-closed |

## 3. 数据盲期一次锁定项

以下项目已经在未落地 express 全量数据时写入草案；终版可由 John 直接确认或改判，但不得依据
后续样本数量、方向比例或结果优劣调整：

1. `actual_wan = n_income / 10000` 的机械单位换算；
2. `actual_wan > upper` 为 `up`、`actual_wan < lower` 为 `down`；
3. 落在闭区间内或恰等边界均不成事件；
4. 预告上下沿必须同时完整且 `lower <= upper`，数值不可判不得代理回填；
5. 只有 `forecast.ann_date < express.ann_date` 才算已公开预告，同日不算；
6. 快报事件锚只能是初始快报实际 `ann_date`，`end_date` 只作连接键；
7. 事件键、重复与方向冲突整组 fail-closed；
8. 研究期建议为 `2011-01-01 <= initial_ann_date < 2024-07-01`；
9. 主窗与 signed 统计口径、sample gate、holdout、benchmark、清洗和 cost 的沿承建议。

express 落地后，允许闭合的范围仅为数据身份、初始/修订冲突的实物形态，以及 John 对下列三项
菜单作出的结构性裁定；每处变化须逐字留调整前后文本与理由。未列项目默认归入锁定项。

## 4. 三项人裁菜单（未代裁）

### A. 预告基准版本

- A1：快报前最近一次公开且区间完整的预告。技术建议；最接近事件前市场已知信息，但可能减少偏离事件。
- A2：同报告期首次公开且区间完整的预告。保留最初预期，但可能把快报前已公开修订再次计作惊喜。

冻结前须并算两口径的配对数、`up/down/inside/boundary` 和事件集合差异；不得按样本量择优。

### B. 初始快报异常组

- B1：`update_flag=0` 缺失、多条或字段冲突全部整组 fail-closed。技术建议；宁剔勿错，样本损失较大。
- B2：多条 flag0 仅在 `ann_date/n_income` 逐字段完全一致时确定性折叠，其余整组 fail-closed。可保留纯重复组，但增加折叠规则。

两案均禁止用 flag1 修订行或任取最早/最晚日期回填初始锚。

### C. 实际利润会计归属

- C1：以公司公告原文抽核证明两侧归属范围一致后采用 `n_income/10000`。技术建议。
- C2：不能证明一致或发现不一致即停止 exp17，不冻结，不改用同比幅度、文字类型或其他代理。

## 5. 冻结前置的可量化项

全量 express 落地后，终版冻结前至少须给出：

- 总行数、证券数、报告期组数、覆盖期、缺失、重复、孤儿和逐年分布；
- `update_flag=0/1/缺失` 的行数与组数；
- 因 flag0 缺失、重复或冲突触发的整组剔除数；
- 若 flag1 行数为 0，明确“字段对 express 修订的实测判别力未建立”，并量化异常组规则的样本损失；
- A1/A2 两口径并算与事件集合差异；
- 公司公告原文抽核清单及 `n_income` 会计归属结论。

任一项未闭合，或三项人裁未完成，不得形成可冻结终版。

## 6. 沿承建议清单（均未裁）

- 窗口：公告日后第一个交易所交易日起 5/20/60 日，`unified_announcement` 顺延；
- 估计期：前 250 至前 91 日，共 160 日；覆盖门 112/160；
- `sample_gate=30`；全市场等权 benchmark；`adj_bmp_main_only` 唯一判决；
- ST=`reject`；不设收益分层 verdict；方向只作 raw NFV 诊断；
- cost 四值仅 schema 与执行审计；holdout=`2024-07-01`；
- digest binding、field roles、effect alignment 与 prescreen 水印沿既有 signed 冻结范式。

## 7. 边界与残留态

- 未重复 10 票探针；零 express 全量采集、零缓存入仓、零落库；
- 零生产代码、零数据库写入、零冻结、零 manifest、零收益读取、零运行、零 persist；
- 草案中 `NOT-FROZEN` 明示 10 处；方向旁路字符串零命中；
- 人的方向与把握度未代填；当前草案 digest 不得被 driver 或正式运行消费。

完成后停交验点，等待 John 对三项菜单与沿承项逐项裁定；未令不动。
