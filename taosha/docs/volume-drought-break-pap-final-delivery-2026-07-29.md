# exp10 `volume_drought_break` PAP 终版文本收口交付（2026-07-29）

## 1. 终版实物

- 文件：`taosha/docs/volume-drought-break-pap-final-2026-07-29.json`
- 文件SHA256 = 引擎canonical digest：`18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`
- 结构：schema v2、18个顶层键；`validate_pap=PASS`；检验窗解析`(5,20,60)`。
- 字节口径：词典序键、紧凑分隔符、UTF-8、末尾单换行；本地独立复算已通过。
- 状态：终版候选，**尚未冻结**。方向与把握度预判尚未绑定。

## 2. 授权来源补正

终版令`volume-drought-break-pap-final-order-2026-07-29.md`已逐字收录：

1. 窗口原提示中的B选项；
2. 窗口原提示中的七项默认清单；
3. 人的裁定原文“按B和默认项”；
4. 本次不足60根历史、prior60跨停牌正向释义及五组沿承项确认。

草案令`af6e370`中的来源描述“逐字对应上一轮交验请求”已显式作废，仅补正证据指针，不改变事件语义与样本。

## 3. 草案→终版程序化diff

顶层键集不变。18键中10键逐字相等，变化恰8键：

| 变化键 | 授权类别 | 变化边界 |
|---|---|---|
| `benchmark` | 沿承项确认 | 删除草案待确认措辞，确认全市场等权/market |
| `cleaning` | 沿承项确认 | 确认估计期、覆盖门、missing_bar_only、cost仅审计；删除草案占位措辞 |
| `engine_params` | 沿承项确认 | 冻结候选值转为人确认值；值本体未变 |
| `event_def` | prior60释义+沿承项确认 | 仅将prior60定义中的“连续真实bar”改为“有效真实bar”，补入跨停牌正向句；保留“历史不足60根不参与状态判定”；τ0候选措辞转正式 |
| `reporting_commitments` | 证据锚 | 钉入重算脚本SHA及prior60实现说明；NOT-FROZEN草案措辞转为冻结前参考措辞 |
| `snapshot_batch_req` | 流程沿承确认 | 草案重算基改为冻结前重算基，明确批次变化停报 |
| `verdict_authority` | 沿承项确认 | 删除草案待确认措辞，确认ADJ-BMP唯一判决及field roles |
| `window` | 沿承项确认 | 删除草案待确认措辞，确认τ0与5/20/60三窗 |

其余10键（含`analysis_type/bias_statement/cost/diagnostic_dimensions/holdout/pap_digest_binding/pap_schema_version/pool/sample_gate/verdict_power_note`）逐字相等。终版全文`PAP草案/待终版/候选口径/草案建议/本草案`残留均为0。

## 4. prior60实现对账锚

- 终版原文：`「最近60根」指最近60根有效真实bar,可跨停牌与日历缺bar;停牌/缺bar仅打断低量段与armed状态,不清空滚动60日历史。`
- 既有双跑脚本：阿里云`/root/s10pap/s10_pap_b.py`
- 脚本SHA256：`98b2a41bb075f028a70e1eef6ddc60adac67ba424d69fae1d678b864cf7c4cde`
- 双跑result SHA256：`989a4ba2090ef1c5dab40f9445e8ef34eacad2ea120a0fa1ff4ab42afde257ec`
- selection SHA256：`3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`

脚本在日历缺bar分支只重置`low_run/low_start/armed/wait`，不清空`prior`；与终版正向措辞一致。本单元不重跑漏斗，研究期参考数维持`13,889`。

## 5. 版本纪律与边界

- 草案JSON本体未改，草案digest仍为`d2c67942713b75bec76482c51223d77ecf2c142a8e0fa9020932f2f5dc409170`，另立NOT-FROZEN superseded标记；该digest不得进入冻结、driver或正式运行。
- 本单元零生产代码、零数据库写入、零冻结、零manifest、零事件日后收益读取、零正式运行、零persist。
- 下一步仅为外部复核终版digest/schema/键级diff；通过后由人另行给出方向与把握度预判并绑定终版digest。
