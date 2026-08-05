# exp19 `dividend_surprise` · NOT-FROZEN PAP 草案交付

- 日期：2026-08-05（UTC+8 / Asia/Shanghai）
- 授权令：`taosha/docs/dividend-surprise-pap-draft-order-2026-08-05.md`
- 草案：`taosha/docs/dividend-surprise-pap-draft-2026-08-05.json`
- 状态：**NOT-FROZEN；五项菜单与沿承值均未裁**

## 一、结论

草案单元完成。本件把登记命题、窄闸事实、数据盲期约束、五项人裁菜单与既有 signed 单判决结构写成可复核 PAP 文本；不构成全量数据施工、冻结或运行授权。

历史初始预案值的可证明性是当前最高风险项：30票探针的2011–2018年度组全部缺预案阶段行，实施态值又存在事件日后基准股本调整。草案因此把“禁止实施值回填”和“历史可证明范围”写成冻结硬门，但没有用探针自行缩短研究期。

## 二、结构与 digest

- 顶层19键：常规事件版18键加独立 `signed_ar`；
- 文件 SHA256 = 引擎 `canonical_pap_sha256()` = `b61c1a00e58181d6756b7ea8d06b15638104d5f2c267c3986ecc1252dcf47c9b`；
- 文件字节本体 = canonical JSON + 末尾单换行；
- `validate_pap = PASS`；`parse_test_windows = (5, 20, 60)`；
- `diagnostic_dimensions.axes.direction = [up, down]`；`signed_ar`四键完整；
- 五项菜单 A–E 各唯一出现一次；`NOT-FROZEN`在草案中明示10处。

该 digest 只标识当前草案候选；不得进入冻结、driver、manifest或正式运行。任何人裁落键都会产生新终版 digest。

## 三、授权到键位映射

| 授权要求 | PAP 键位 | 落地 |
|---|---|---|
| signed 19键结构 | `diagnostic_dimensions.axes.direction` / `engine_params` / `signed_ar` | up/down 白名单在 PAP 内；事件级逐τ符号变换先于聚合；单一顶层 verdict |
| 登记命题忠实 | `event_def` / `verdict_power_note` | 年度每股分红同比、预案公告锚、增正减负原文保留；50%明确仍待冻结 |
| 不回填实施值 | `event_def` / `bias_statement` / `snapshot_batch_req` / `reporting_commitments` | `update_flag`与`div_proc`分工；实施/通过/修订值不得回填，正式审计命中须为0 |
| 五项只列菜单 | `event_def` | A指标、B历史、C零/缺失、D阈值端点、E阶段版本各列选项、影响与技术建议，未代填 |
| 探针不外推 | `bias_statement` / `diagnostic_dimensions.data_quality_disclosure` / `reporting_commitments` | 30票数字只作形态证据，禁止作为正式事件数、覆盖率或研究期起点 |
| 冻结硬门 | `snapshot_batch_req` / `reporting_commitments` | 全量事实、current/snap、源快照、全量污染量化、历史公告证据未闭不得冻结 |
| prescreen效力 | `verdict_power_note` / `reporting_commitments` | 正式 result/report 强制 exp19 身份与 `llm/prescreen` 水印，缺失 fail-closed |

## 四、五项人裁菜单（未代裁）

### A. 指标范围

- **A1：仅税前现金每股分红 `cash_div_tax`。** 技术建议；单位单一、跨年可比并避免个人税率差异，但不覆盖只改变送股/转增的方案。
- **A2：纳入送股/转增。** 词义更广，但现金、送股和转增不是同一单位；John须另给明确换算公式与边界，未给公式不得冻结，施工方不得估值或直接相加。

### B. 历史初始值策略

- **B1：维持2011年起，补齐并逐组证明历史原始预案值。** 技术建议；最忠实于原研究期但数据与证据成本高，无法证明组整组剔除。
- **B2：按全量阶段覆盖与公告证据，由John明确缩短研究期。** 可降低历史覆盖偏差，但改变估计时期；起点不得由30票的2019断点代填，也不得按事件数、方向比例或收益结果决定。

### C. 零与缺失

- **C1：纯百分比口径。** 技术建议；上年明确0、上年无记录、上年组不可判分开计数并排除；当年0且上年>0按−100%可判。
- **C2：新增离散转换。** 上年明确0且当年>0定义为up；当年0且上年>0保留为down；无记录/不可判仍排除。此项扩大登记命题，必须人明确授权并只把来源类型作NFV组成审计。

### D. 阈值与端点

- **D1：50%闭区间。** 技术建议；`change≥+50% / ≤−50%`，逐字忠实登记的“≥50%”，Decimal精确比较。
- **D2：不确认50%或不含端点。** John须提供新的阈值和比较符原文；施工方不代拟，不能根据边界样本或候选数选择。

### E. 阶段与版本异常

- **E1：严格单行。** 技术建议；同票同期须恰一条 `div_proc=预案 AND update_flag=0`，任何缺失、多行、多日期、多值、冲突或未知flag整组fail-closed。
- **E2：只折叠逐字段完全一致的纯重复行。** `ann_date`、指标、`base_date/base_share`及全部冻结消费字段须相同，否则整组fail-closed。两案均禁用实施/通过/flag1或任取最早、最晚、最新值回填。

## 五、数据盲锁定候选与沿承建议

以下内容已在全量 dividend 数据出现前写入草案；终版可由John明确确认或改判，但不得依据后续事件数量、方向比例或收益结果调整：

1. 年度组必须为12月31日报告期，当年与上年必须为相邻财年；
2. 唯一候选公告锚为当前年度初始预案实际 `ann_date`；
3. 百分比候选公式为 `current/prior - 1`，仅在单位一致、当年非负、上年严格正时可判；
4. up/down进入合并 signed 主事件集，inside/zero/missing/unresolvable只计数；
5. 重复事件键与方向冲突整组 fail-closed；
6. 研究期候选为2011-01-01至holdout前，仍待菜单B与终版人裁；
7. 沿承建议：5/20/60三窗、`unified_announcement`、估计期250至91、覆盖门112/160、`sample_gate=30`、全市场等权、`adj_bmp_main_only`、ST=`keep`、cost四值仅审计、holdout=`2024-07-01`；
8. ST=`keep`为待裁建议，理由是reject可能选择性删除分红停止或下降的风险样本，不视为已裁。

## 六、冻结前置清单

1. qbase append-only `dividend`全量事实批次，保留阶段、版本、公告日、税前/税后每股值及基准股本事实；
2. current/snap最小只读视图，holdout与排北交所焊死，底表不授引擎；
3. 将 dividend 纳入源级 StudySnapshot；正式研究 manifest 留到冻结后另令；
4. 全量阶段、修订、多值、多公告日、缺失、重复、未通过、年度缺口、零分母及逐年覆盖量化；
5. 以公告原件或官方索引证明历史初始预案值。不能证明时只能停止冻结，或由John走菜单B明确缩短研究期；
6. 五项菜单与全部沿承项由John逐项确认，形成终版新digest。

## 七、边界与停点

- 零全量 dividend 采集、零缓存入仓、零落库；
- 零生产代码、零数据库写入、零冻结、零 manifest、零收益读取、零运行、零 persist；
- exp19仍应为 `registered` 且三槽空；
- exp18继续停在首次披露语义硬门，不并行恢复；
- 完成即停，等待Fable限域复核本草案及John对五项菜单和沿承项的后续裁定。
