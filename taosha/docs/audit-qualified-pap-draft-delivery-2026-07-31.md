# exp18 `audit_qualified` · PAP 草案交付

- 日期：2026-07-31（UTC+8 / Asia/Shanghai）
- 草案：`taosha/docs/audit-qualified-pap-draft-2026-07-31.json`
- 状态：**NOT-FROZEN**
- 文件 SHA256：`c48e934787a072c651d351e33ab42fc642e16c0a6a6f183aeb92b774c2291375`
- canonical digest：`c48e934787a072c651d351e33ab42fc642e16c0a6a6f183aeb92b774c2291375`
- 结构：18 键；`validate_pap=PASS`；窗口解析=`(5,20,60)`；文件字节与 canonical 串本体逐字相等。

## 一、登记与窄闸事实到键位的映射

| 已确定事实或纪律 | 草案落点 |
|---|---|
| 主事件仅为年报审计意见精确属于`保留意见/无法表示意见/否定意见` | `event_def` |
| `标准无保留意见`及`带强调事项段的无保留意见`不入主事件集 | `event_def`、`reporting_commitments` |
| `ann_date`是唯一候选公告锚；`end_date`只作年度报告期，禁止回填事件日 | `event_def`、`cleaning`、`window` |
| 接口没有独立首次披露日、修订标记或版本序号 | `bias_statement`、`snapshot_batch_req`、`reporting_commitments` |
| 同票同期多行、公告日冲突、意见冲突或版本不可判须 fail-closed | `event_def`、`cleaning`、`diagnostic_dimensions` |
| 现有单事件集聚集校正能力足够，不需要 signed、组间差或分层 verdict | `analysis_type`、`verdict_authority`、`engine_params` |
| 三类目标意见只作组成审计，不产生分层判决 | `diagnostic_dimensions`、`engine_params`、`reporting_commitments` |
| `llm/prescreen`效力水印缺失即 fail-closed | `verdict_power_note`、`reporting_commitments` |
| 数据落地后不得根据分布改白名单、年度边界或公告锚 | `bias_statement`、`snapshot_batch_req`、`reporting_commitments` |
| 全量候选尚不可得，10票探针只证明字段和分类形态 | `bias_statement`、`diagnostic_dimensions`、`reporting_commitments` |

## 二、草案建议值

- 公告顺延：`postpone_policy=unified_announcement`；公告日后首个有真实 bar 的价格观察日为 τ0，仅缺 bar 顺延不超过 5 个交易日。
- ST 处置：建议 `st_policy=keep`。非标审计意见与 ST 状态高度相关，`reject` 会对登记命题作选择性删样；本草案不设置 ST 收益分层判决轴。
- 异常组：同票同期缺失、多行、公告日冲突、意见冲突或修订语义不可判，建议整组 fail-closed，不任取最早或最晚、不合并。
- 研究范围：建议 `2011-01-01 <= ann_date < 2024-07-01`；三窗口 5/20/60；估计窗 250..91、覆盖门 112/160；`sample_gate=30`。
- 基准与判决：全市场等权基准；唯一顶层判决=`adj_bmp_main_only`；组成审计全部 NOT_FOR_VERDICT。
- cost：既有四值只作 schema 与执行审计，不控制 CAR 取样，不得表述为可成交策略证据。
- holdout、field roles 与 canonical digest binding 沿既有冻结范式。

## 三、待 John 一次确认

1. 确认 `postpone_policy=unified_announcement`。
2. 确认 `st_policy=keep`；若改为 `reject`，须明确接受对非标审计样本的选择性删样。
3. 确认同票同期多行、冲突或版本不可判时整组 fail-closed。
4. 确认精确三类白名单，以及标准无保留和带强调事项段无保留的排除。
5. 确认研究期、5/20/60 窗口、估计期与覆盖门、sample gate、全市场等权基准、cost 四值、holdout、field roles 与 digest binding 的沿承建议。
6. 确认三类意见只做组成 NFV，不设收益分层判决轴。
7. 确认冻结前数据硬门；未闭不得冻结，也不得把10票探针数字改写成正式候选断言。

## 四、冻结前数据硬门

以下三项必须先形成可验收实物，且须由后续另令授权：

1. `fina_audit` append-only 全量事实批次与 current/snap 最小只读视图；
2. 全量意见枚举、缺失、重复、同票同期多行、公告日冲突、意见冲突及孤儿证券量化；
3. 公告原文或公告索引抽核 `ann_date` 的首次披露与修订语义；不能证明即停止，不得使用报告期末、入库时间或后续更正日替代。

## 五、边界与停点

本单元仅新增 PAP 草案及交付留痕：零生产代码、零数据库写入、零数据采集落库、零冻结、零 manifest、零收益读取、零正式运行、零 persist。exp18 仍应保持 `registered` 三槽空。

草案 digest 仅供本轮交验；任何终版文本变更都必须生成新 digest。当前停在草案交验点，未经 John 对第三节逐项确认及另行授权，不进入数据闭合、终版或冻结。
