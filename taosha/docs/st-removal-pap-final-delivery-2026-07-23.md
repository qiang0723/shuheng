# exp12 `st_removal` PAP 终版文本收口单元 · 交付档(2026-07-23)

> 授权依据 = 人终版收口令 2026-07-23(原文留痕 `taosha/docs/st-removal-pap-final-order-2026-07-23.md`,
> F 条 commit `3564a23` 先于本单元施工)。**本令不是冻结令:终版为 NOT-FROZEN 候选,
> 冻结与预判绑定须人另下令。** 禁区遵守实录见 §6。

## 1. 终版 PAP 实物与验证

- 实物 = `taosha/docs/st-removal-pap-final-2026-07-23.json`(新建,草案文件零覆盖;
  canonical 字节本体=词典序排序键+紧凑分隔符+UTF-8(ensure_ascii=False)+末尾单换行)。
- **文件 SHA256 == 引擎 `canonical_pap_sha256` 重算 digest ==
  `62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`**(逐字相等断言过;
  两台各自重算一致,见 §5)。
- **状态 = NOT-FROZEN 终版候选**:未写库、未入冻结记录;冻结令+方向把握度预判(人亲拟)
  绑定本 digest 须人另下。
- `validate_pap` PASS;`parse_test_windows` = (5, 20, 60);`pap_schema_version=2`,
  `analysis_type='event'`;18 键,键集与草案完全相同(与 exp13 同构、差异 3 处之说明不变)。

## 2. 人令条款 → 落点映射

| 令条款 | 落点 |
|---|---|
| 沿承键批准(检验窗5/20/60·估计窗250~91·112/160覆盖门·sample_gate=30·holdout·adj_bmp_main_only·field roles·digest binding·全市场等权基准) | `window`/`cleaning` 内"人终版令2026-07-23批准(沿承)"落记;`sample_gate`/`holdout`/`verdict_authority`(含 field_roles)/`pap_digest_binding`/`benchmark` 键本体零改动 |
| τ0 唯一口径=ann_date 之后首个有真实 bar 的交易日;只有停牌/缺 bar 顺延;一字涨停或跌停有真实 bar 即进入 CAR 不作顺延 | `cleaning` + `event_def` + `window` 三处统一措辞;『可交易日』字样全文清零,两读并列文字全部删除 |
| postpone_policy 唯一表达"仅缺 bar 顺延"的冻结值,不留运行时选择 | `engine_params.postpone_policy='missing_bar_only'`(新冻结值;适配义务见 §4)|
| cost 仅 schema/执行审计字段;limit_up_board_untradeable 不控 CAR 取样;不得表述为可成交策略证据 | `cost` 四值本体零改动;角色约束落 `cleaning`(不控取样)+ `diagnostic_dimensions.execution_limit_audit`(不得表述为可成交策略证据)|
| 一字板事件数量和比例=结构化 NOT_FOR_VERDICT 执行限制报告 | 新增 `diagnostic_dimensions.execution_limit_audit` + `reporting_commitments` 承诺条;**操作锚=τ0 日为一字板(存在真实 bar 且 limit_status='one_word')的事件计数与占最终事件集比例**(如需扩展至窗内其他日,冻结令时人另定) |
| 641 仅 batch 7 对账参考,非硬断言;正式数量以 exp12 研究 manifest+冻结规则确定性产出为准 | `reporting_commitments` + `snapshot_batch_req.note`(批次变化不得静默沿用、停下报人)|

## 3. 草案→终版程序化逐键 diff

构建/验证件 = AWS scratchpad `build_exp12_final.py`(逐处替换断言旧文唯一在场;
不入 git,产物只有终版 JSON 本身)。

### 3.1 改动键 = 恰 7 键,11 处替换(全部可溯至令条款)

| 键 | 处数 | 变化 |
|---|---|---|
| `cleaning` | 2 | ①"本裁定未另裁"→"人终版令2026-07-23批准沿承";②τ0 段整体重写:唯一口径+『仅缺bar顺延』+一字板有 bar 即 τ0 入 CAR+`missing_bar_only`+cost 不控取样;**删除 unified 两读并列全部文字** |
| `engine_params` | 2 | ①`postpone_policy`:'unified'→**'missing_bar_only'**;②note 增:终版令依据+新值语义+引擎值域未含→最小适配须另令、fail-closed 不得静默映射 |
| `event_def` | 1 | τ0 句改唯一口径(仅缺 bar 顺延;一字板有真实 bar 即进入 CAR 不作顺延;"第6日仍无真实bar"取代"仍不可交易") |
| `window` | 1 | τ0 措辞同步唯一口径;"本裁定未另裁"→"人终版令2026-07-23批准"(检验窗文本"后5/20/60日"逐字保留,解析不变) |
| `diagnostic_dimensions` | 2 | ①新增 `execution_limit_audit`(τ0 日一字板计数+比例,NFV 执行限制,不改判决、不得表述为可成交策略证据);②note:"本草案未设…人终版若增设另令"→"本假设未设…终版令亦未增设" |
| `reporting_commitments` | 2 | ①641 段:标明 batch_id=7 基、"仅只读对账参考,不是正式运行硬断言,正式数量以 exp12 研究 manifest 与冻结规则确定性产出为准,对账不一致停下报人";②增一字板 NFV 执行限制报告承诺 |
| `snapshot_batch_req` | 1(note 内两处) | "本草案单元禁止生成 manifest"→"PAP 文本单元〔草案及终版收口〕禁止…+终版令";641=batch 7 对账参考身份+批次变化停下报人 |

### 3.2 未动键 = 11 键逐字节相同

`analysis_type` / `benchmark` / `bias_statement` / `cost`(四值原样)/ `holdout` /
`pap_digest_binding` / `pap_schema_version` / `pool` / `sample_gate` /
`verdict_authority`(field_roles 原样)/ `verdict_power_note`。

### 3.3 变化仅限令内证明(逆向还原)

终版 JSON 上将 7 个改动键逆施草案旧值→canonical 序列化,**逐字节 == 草案文件**,
SHA256 还原 == `12e8366de0c60ca33065e1a53ac10cd3d92cbd8214c23f2498266ab5ab4dcf41`;
顶层键集断言不变(18 键)、改动键集合断言恰等于预期 7 键。即:除令内 11 处替换外零变化。

### 3.4 残留检查

终版全文:"两读"/"待人"/"S2-DEC3"/"本裁定未另裁"/"本草案"/"不可交易"/"可交易日" 出现次数
全部 = 0;"unified" 仅存于 `engine_params.note` 引擎现值域枚举(适配事实陈述,非并列解释)。

## 4. ⚠ 适配义务预告(本单元零施工,冻结后另令)

`postpone_policy='missing_bar_only'` 为**新冻结值**:引擎 `cleaning.clean_event` 现值域
{legacy, unified, unified_announcement} 未含,现引擎对本值 raise(天然 fail-closed,不会静默
错跑)。exp12 driver 本就未建;冻结后 driver+引擎最小适配单元(对本值逐字消费:仅停牌/缺 bar
计入顺延、一字板有真实 bar 即取为 τ0;公告日历锚几何沿 unified_announcement 同族语义于施工时
按冻结文本钉死)须人另下施工令,行为面 fixture 验收比照 exp13 适配单元。本单元生产代码零触碰。

## 5. 两台一致性

AWS 与 aliyun(/opt/quant)各自:文件 SHA256、引擎 canonical 重算、validate_pap、
parse_test_windows 四项一致(执行记录=commit 后 pull 复核,数字见 §1)。

## 6. 禁区遵守实录(照令§8)

- 生产代码零改动:本单元新增/改动仅 `taosha/docs/` 三件(终版 JSON/取代标记档/本档)
  + 人令留痕档 + `ops/STATE.md`。
- 零冻结:台账 exp12 保持 registered,pap_json 载荷未动,零库写。
- 零 manifest、零收益读取、零运行(全单元未连库;数字全部来自既有草案文件与文本变换)。
- 草案文件零改动(NOT-FROZEN 标记以取代标记档承载)。
- 完成后停交验点。**下一步只能由人另下:终版 digest `62a387a2…4353` 冻结令+方向把握度预判
  (人亲拟)绑定令**;冻结后适配施工另令(§4)。
