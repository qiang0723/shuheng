# exp17 `earnings_flash_gap` · PAP 终版文本收口交付

日期：2026-07-30（UTC+8）

> 本件是**尚未冻结的终版候选**。只完成 A1/B1/C1、既有沿承口径与数据身份的文本收口。

## 1. 终版实物

- 终版候选：`taosha/docs/earnings-flash-gap-pap-final-2026-07-30.json`
- 文件 SHA256 = 引擎 `canonical_pap_sha256()` =
  `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`
- 顶层 19 键；`validate_pap=PASS`；`parse_test_windows=(5,20,60)`；
- 文件字节本体恰为 canonical JSON 加末尾单换行；本地与阿里云引擎独立重算同值；
- 人的方向与把握度仍未密封，不在本文件代填。

## 2. 人裁与数据身份

- A=A1：取快报前最近一次公开且区间完整的预告；数据施工令已禁止重算 A2 供选口径；
- B=B1：同票同期 flag0 缺失、多条或冲突整组 fail-closed；不得折叠或任取；
- C=C1：`n_income` 按归母净利润（元）解释，除以 `10^4` 与 forecast 万元区间比较；
- ST=`reject`；`postpone_policy='unified_announcement'`；其余沿承值按数据落地前人裁不变；
- express 事实批次=15；冻结前源级锚=snapshot 340，digest=
  `b32c5b7f0c333c4f157822c99cd150f87cff6b450a3c12f3686437b46357af4c`；
  snapshot 340 只作源级数据锚，不得冒充未来 exp17 研究 manifest。

## 3. 冻结前参考与免责

snapshot 340/express 15 下：24,381 行、24,375 同票同期组，flag1=0；B1 剔除冲突 6 组。
A1 参考方向事件 2,529（up 997/down 1,532），事件键碰撞和方向冲突均为 0。上述数量仅为
同数据锚的质量与漏斗参考，**不构成正式运行硬断言**；正式数量以 exp17 自有研究 manifest 与
冻结规则确定性产出为准，同向量不一致须停下报人。

## 4. 草案到终版 diff

键集无增减。12 个顶层键变化：`benchmark`、`bias_statement`、`cleaning`、
`diagnostic_dimensions`、`engine_params`、`event_def`、`pool`、`reporting_commitments`、
`snapshot_batch_req`、`verdict_authority`、`verdict_power_note`、`window`。

7 个顶层键逐字节不变：`analysis_type`、`cost`、`holdout`、`pap_digest_binding`、
`pap_schema_version`、`sample_gate`、`signed_ar`。变化只用于：

1. 菜单 A/B/C 收口为 A1/B1/C1；
2. 沿承建议转为既有人裁正式值；
3. 写入批 15、snapshot 340 与冻结前实测质量披露；
4. 把正式水印三件套列为适配硬要求。

阈值、严格比较、恰等不成事件、研究期、三窗、估计窗、sample gate、cost、holdout、
signed 变换与唯一判决结构均未因数据分布改变。终版全文对 `NOT-FROZEN/草案/待人/待终版/建议/菜单`
等残留态扫描为 0；草案 digest 亦未进入终版。

## 5. 草案保全与停止线

草案文件保持原样，SHA 仍为
`b3c992bccc81af6384753f451eff779bddd60cfcb0838ecf5e524f5c0be80a39`，另立
NOT-FROZEN/superseded 状态标记。

本单元零生产代码、零数据库写入、零冻结、零 exp17 研究 manifest、零收益读取、零正式运行、
零 persist。下一步只能是终版 digest 外部复核；复核通过后由 John 亲拟方向与把握度并另下冻结令。
