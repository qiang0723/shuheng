# exp16 `yearend_strength` · PAP草案交付（2026-07-30）

## 结论

NOT-FROZEN草案已生成：
`taosha/docs/yearend-strength-pap-draft-2026-07-30.json`。

- 顶层18键，`pap_schema_version=2`、`analysis_type=event`；
- 文件SHA256=引擎`canonical_pap_sha256`=
  `28377486e4b3b0bd8ac8ea57c00c13081cd487afa3f8bfefcc1dab3f66ce5eb6`；
- 本地与阿里云Python3.14.4均`validate_pap=PASS`、窗口解析=`(5,20,60)`；
- 本digest仅为草案候选，**不得用于冻结、driver或正式运行**。

## 1. 已裁口径映射

| 人裁口径 | PAP落位 |
|---|---|
| 12月最后10个SSE开市日的10个日收益，基期为窗口前一开市日 | `event_def` d0..d10 |
| 相对财富跑赢≥5%，等价累计对数超额≥ln(1.05) | `event_def` Decimal公式 |
| 严格11-bar完整面板，缺失即fail-closed | `event_def`、`cleaning`、`reporting_commitments` |
| 次年首开市日为事件锚且当日为τ0；仅缺bar顺延≤5 | `event_def`、`cleaning`、`window`、`engine_params` |

四项均为确定性单值，无运行时选择。窄闸其他三个候选读法仅进入
`diagnostic_dimensions.selection_definition_audit`作NOT_FOR_VERDICT历史对照，并明确不得结果后
复活。

## 2. 对账参考

snapshot74/market_return88下，相对财富口径参考=`7,751事件`，selection SHA=
`057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`。年度证券面板
`46,290=完整44,417+缺bar拒1,873`。以上只作冻结前同向量参考，不构成正式运行硬断言；
正式数量由未来exp16自有manifest与冻结规则确定性产生。

## 3. 结构与能力边界

- 事件版18键结构沿exp10/11范式；无signed、组间差或收益分层判决；
- 直接复用snapshot价格/日历、market_return、ViewReader、`tau0_on_anchor`、runner和ADJ-BMP；
- 冻结后预计只需常规rules/driver/fixture/report四件，不新增视图、数据资产或统计内核；
- 独立事件日仅14个，`clustering_audit`与正式result报告事件日数、rho、N_eff已写入承诺，
  不因低功效调整阈值。

## 4. 终版前待人一次确认

1. 三窗建议沿既有事件版=`5/20/60`，主窗5日唯一判决；
2. 估计期建议=`250..91`、160日窗、有效覆盖门=`112/160`；
3. **ST处置待裁**：甲=`keep`（更贴登记“全市场全A股”字面）；乙=`reject`（沿平台早期默认清洗）。
   两者会改变样本，必须在终版前明确；草案未代裁；
4. `sample_gate=30`、全市场等权benchmark、`adj_bmp_main_only`、无收益分层轴；
5. cost四值仅schema/执行审计，不控制CAR取样；
6. holdout、field roles、digest binding与llm/prescreen效力沿承；
7. 终版digest通过复核后，再由John亲拟方向与把握度。登记态“人未定”保持不动。

## 5. 边界与停止线

本单元只新增令文、草案、交付档与STATE；零生产代码、零数据库写入、零样本重跑、零收益
结果读取、零冻结、零manifest、零正式运行、零persist。exp16仍为`registered`且三槽空。

**现停交验点；下一步只能由人确认第4节后，另行授权终版PAP文本收口。**
