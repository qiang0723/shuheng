# exp14 `ex_div_gap` · PAP 终版文本收口交付

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 状态：**尚未冻结的终版候选**
- F-first 令：`taosha/docs/ex-div-gap-pap-final-order-2026-08-09.md`
- F-first commit：`416ff59`

## 一、终版实物

- 文件：`taosha/docs/ex-div-gap-pap-final-2026-08-09.json`
- 文件 SHA256 = `canonical_pap_sha256()` =
  `a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；
- 顶层 18 键；无 `signed_ar`；`validate_pap=PASS`；`parse_test_windows=(5,20,60)`；
- 文件字节本体恰为 canonical JSON 加末尾单换行；
- 人的方向与把握度未密封，本文件未代填。

## 二、人裁落键

- A=A1：除权日 `adj_factor` 相对前一 SSE 开市日发生变化才具事件资格；
- B=B1：六字段全部非 NULL 且日期/Decimal 逐项精确一致才可折叠，否则整组 fail-closed；
- C=C1：既有后复权总回报为唯一主 CAR，`tau0=ex_date` 当日；raw 机械跳空仅 NFV；
- D=D1：监管阶段只作组成 NFV，不计算收益、显著性或独立 verdict；
- ST=`keep`；`postpone_policy='missing_bar_only'`；
- 研究期、三窗、估计期覆盖门、sample gate、全市场等权 benchmark、ADJ-BMP 唯一判决、cost、
  holdout、field roles、digest binding、无收益分层轴与 `llm/prescreen` 水印按既有人裁落位。

## 三、数据身份与冻结前参考

- source snapshot 375，digest=
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；
- 本假设冻结前实际对账消费 `dividend=17 / adj_factor=7 / trade_cal=10`；
- snapshot 375 只作源级数据锚，不得冒充未来 exp14 研究 manifest；
- snapshot375 同锚参考：`4,035` 个事件、恰等 `0.5` 为 `1,083` 个、selection SHA=
  `ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；
- 漏斗参考：`35,280` 实施行→`35,272` 方案组→qualified `7,182`→阈值 `4,067`→
  事件键存活 `4,061`→A1 最终 `4,035`，因子静态 `26`；
- 上述数字均为冻结前同锚 NOT_FOR_VERDICT 数据质量参考，**不构成正式运行硬断言**。未来正式
  运行令须另行钉定研究 manifest、事件数与 selection SHA。

Fable 数据对账复核的 C 级项（8 个多行组“窄闸分类→对账分类”交叉表）按默认不在本单元
扩做，留待冻结取证包收口。

## 四、草案到终版逐键 diff

键集无增减。12 个顶层键变化：`benchmark`、`bias_statement`、`cleaning`、
`diagnostic_dimensions`、`engine_params`、`event_def`、`pool`、`reporting_commitments`、
`snapshot_batch_req`、`verdict_authority`、`verdict_power_note`、`window`。

6 个顶层键逐字不变：`analysis_type`、`cost`、`holdout`、`pap_digest_binding`、
`pap_schema_version`、`sample_gate`。变化只用于：

1. A1/B1/C1/D1、ST、postpone 与沿承裁定正式落位；
2. 写入 dividend17、adj_factor7、trade_cal10、snapshot375 与数据质量实物；
3. 把 `4,035 / 1,083 / selection SHA` 登记为 NFV 冻结前参考；
4. 删除菜单、建议、待裁、数据未闭与 NOT-FROZEN 状态措辞。

Decimal `0.5` 闭区间、事件锚、研究期、三窗、估计期、sample gate、cost、holdout 与唯一判决
结构均未因数据分布改变。

## 五、机械验证与残留态

- 草案文件保持原样，SHA 仍为
  `b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`；
- 另立 NOT-FROZEN/SUPERSEDED 状态标记；
- 终版全文对 `NOT-FROZEN / NOT_FROZEN / 草案 / 建议 / 待裁 / 待人 / 待终版 / 尚未 /
  不冻结 / 菜单` 残留态扫描为 0；
- 草案 digest 在终版全文中为 0 命中；
- `git diff --check` 通过；终版仅为文本候选，未触碰生产代码或数据库。

## 六、停止线

本单元零生产代码、零数据库写入、零冻结、零 StudySnapshot、零研究 manifest、零收益读取、
零正式运行、零 result、零 persist。下一步仅为外部限域复核终版 digest、schema 与逐键 diff；
通过后由 John 亲拟方向与把握度，再另下冻结令。
