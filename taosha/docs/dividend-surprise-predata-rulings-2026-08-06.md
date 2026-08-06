# exp19 `dividend_surprise` · 数据闭合前口径裁定

- 日期：2026-08-06（UTC+8 / Asia/Shanghai）
- 草案提交：`3021cb315f987f3221f47adc882c6a987b04abd1`
- 草案 digest：`b61c1a00e58181d6756b7ea8d06b15638104d5f2c267c3986ecc1252dcf47c9b`
- 草案外审：Fable `A0/B0/C2 → 通过，可进入人裁收口`

## 一、John 裁定原文

> 菜单A=A1；菜单B=B2，精确研究期起点待全量覆盖报告后由我另裁，不得代填；菜单C=C1；菜单D=D1；菜单E=E1；st_policy=keep；postpone_policy=unified_announcement；其余沿承项按草案建议确认。随后另令数据闭合，当前草案digest不得冻结。

## 二、逐项效力

1. **A=A1：仅税前现金每股分红 `cash_div_tax`。** 不纳入送股/转增，不建立换算公式；税后 `cash_div` 不得与税前值混用。
2. **B=B2：按全量数据与公告证据的可证明范围缩短研究期。** 精确研究期起点尚未裁定，必须等待全量覆盖报告后由John另裁；30票探针的2019断点不得直接代填，也不得依据事件数、方向比例或收益结果选起点。
3. **C=C1：纯百分比口径。** 上年明确为0、上年无记录、上年组不可判三类分开计数并排除；当年为0且上年严格大于0时按−100%可判；不新增“0→正”的离散事件规则。
4. **D=D1：阈值50%且含端点。** 使用Decimal精确比较，`change>=+50%`为up、`change<=-50%`为down；不得按边界样本数量改判。
5. **E=E1：严格单行。** 同票同期须恰一条 `div_proc=预案 AND update_flag=0` 的初始行；缺失、多行、多公告日、多指标值、字段冲突或未知flag均整组fail-closed，不折叠、不择一、不回填。
6. **`st_policy=keep`。** 保留ST事件，不设置ST收益分层判决轴。
7. **`postpone_policy=unified_announcement`。** 初始预案 `ann_date` 为日历锚；τ0从其后第一个交易所交易日开始，缺bar、停牌与一字不可交易统一顺延不超过5个交易所交易日，第6日仍不可交易则剔除。
8. **其余沿承项确认。** 三窗5/20/60、估计期前250至前91日与覆盖门112/160、`sample_gate=30`、全市场等权benchmark、`adj_bmp_main_only`唯一判决、cost四值仅schema与执行审计、holdout/field roles/digest binding/effect alignment、direction raw NFV诊断及`llm/prescreen`水印，均按草案建议确认。

## 三、尚未裁定且不得代填

- **精确研究期起点。** 菜单B只裁定走B2路径，不等于裁定2019或任何其他年份；须由全量阶段覆盖、历史公告证据与失败分布形成只读报告后，John另行给出明确日期。
- **全量数据身份与对账数。** dividend事实批次、current/snap视图、源级StudySnapshot、阶段/版本/零分母/缺年/逐年覆盖均尚未施工，不得把30票探针数字升级为正式锚。

上述任一项未闭合前，不得生成可冻结终版 PAP，不得密封方向，不得冻结或运行。

## 四、草案身份与边界

- 草案 JSON 保持原样，digest仍为 `b61c1a00e58181d6756b7ea8d06b15638104d5f2c267c3986ecc1252dcf47c9b`；
- 该 digest 自本裁定后仅作历史草案锚，**不得冻结**；人裁落入终版后必产生新digest；
- 本裁定只授权逐字留痕，不授权全量采集、缓存入仓、落库、生产代码、数据库写入、终版PAP、冻结、manifest、收益读取、正式运行或persist；
- 下一步只能由John另令 exp19 数据闭合单元；exp18继续停原语义硬门，不并行恢复。
