# exp19 `dividend_surprise` · PAP 终版文本收口交付

- 日期：2026-08-06（UTC+8 / Asia/Shanghai）
- 状态：**尚未冻结的终版候选**

## 一、终版实物

- 文件：`taosha/docs/dividend-surprise-pap-final-2026-08-06.json`
- 文件 SHA256 = `canonical_pap_sha256()` =
  `4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`
- 本地与阿里云 `/opt/quant`（HEAD `581565b7a86f7b0afc4ed5079f291a4c4404d30f`）独立复算逐字一致；
  阿里云证据=`/root/s19papfinal/canonical_check.txt`；
- 顶层 19 键；`validate_pap=PASS`；`parse_test_windows=(5,20,60)`；
- 文件字节本体恰为 canonical JSON 加末尾单换行；
- 人的方向与把握度未密封，本文件未代填。

## 二、裁定与数据身份

- A=A1：只取初始预案税前现金每股分红 `cash_div_tax`；
- B=B2-P1：`2021-01-01 <= current_initial_ann_date < 2024-07-01`；
- C=C1：纯百分比，prior=0/缺失/不可判分计排除；
- D=D1：50% 闭区间，Decimal 精确比较；
- E=E1：严格单行初始预案，异常组整组 fail-closed；
- ST=`keep`；`postpone_policy='unified_announcement'`；其余沿承值按既有人裁；
- dividend 事实批=17；冻结前源级锚=snapshot 375，digest=
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；
  snapshot 375 只作源级数据锚，不得冒充未来 exp19 研究 manifest。

## 三、冻结前参考与免责

snapshot 375/dividend 17 下：177,873 全量行、97,543 年度范围行、52,027 年度组、
E1 严格初始 26,467 组、无初始 25,560 组；全期机械分类 up 2,679/down 3,436/
inside 8,596/zero_undefined 6,501/missing_prior 2,451/unresolvable 2,804。

B2-P1 冻结清洗前机械候选参考 5,055（up 2,253/down 2,802）。上述数量只作同数据锚
NFV 质量与漏斗参考，**不构成正式运行硬断言**；正式数量以 exp19 自有研究 manifest 与
冻结规则确定性产出为准，同向量不一致须停下报人。

公告原件抽核 19/20，公告年 2020–2024 为 15/15；唯一失败 `603259.SH 2019-06-19`
表值 `0.58002/股` 与官方 `0.58/股` 精确不一致，不设容差、不回填。

## 四、草案到终版 diff

键集无增减。12 个顶层键变化：`benchmark`、`bias_statement`、`cleaning`、
`diagnostic_dimensions`、`engine_params`、`event_def`、`pool`、`reporting_commitments`、
`snapshot_batch_req`、`verdict_authority`、`verdict_power_note`、`window`。

7 个顶层键逐字节不变：`analysis_type`、`cost`、`holdout`、`pap_digest_binding`、
`pap_schema_version`、`sample_gate`、`signed_ar`。变化只用于：

1. A1/B2-P1/C1/D1/E1 与沿承裁定正式落位；
2. 写入 dividend 17、snapshot 375 及数据质量实物；
3. 将正式水印三件套列为适配硬要求；
4. 删除草案态菜单、建议、待裁和数据未闭措辞。

阈值、方向、百分比公式、公告锚、三窗、估计窗、sample gate、cost、holdout、signed 变换与
唯一判决结构均未因样本分布改变。终版全文对
`NOT-FROZEN/草案/待人/待终版/建议/菜单/尚未/不冻结` 等残留态扫描为 0；草案 digest
亦未进入终版。

## 五、草案保全与停止线

草案文件保持原样，SHA 仍为
`b61c1a00e58181d6756b7ea8d06b15638104d5f2c267c3986ecc1252dcf47c9b`，另立
NOT-FROZEN/SUPERSEDED 状态标记。

本单元零生产代码、零数据库写入、零冻结、零 exp19 研究 manifest、零收益读取、零正式运行、
零 persist。下一步=外部限域复核终版 digest；通过后由 John 亲拟方向与把握度，再另下冻结令。
