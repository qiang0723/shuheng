# exp14 `ex_div_gap` · 数据对账前人裁留痕

- 日期：2026-08-08（UTC+8 / Asia/Shanghai）
- 草案提交：`7133c5d29bb2b669d299d196d264e2c2f2c98ba2`
- 草案：`taosha/docs/ex-div-gap-pap-draft-2026-08-08.json`
- 草案 digest：`b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`
- 草案外审：Fable `A0/B0/C1 → 通过，可进入人裁收口`
- 状态：NOT-FROZEN；本裁定不授权数据对账、视图施工、终版PAP、冻结、StudySnapshot、manifest、收益读取、运行或persist。

## 一、John 裁定原文（逐字）

> 菜单A=A1；菜单B=B1，六个比较字段任一含NULL即不可折叠、整组fail-closed；菜单C=C1；菜单D=D1；ST处置=keep；postpone_policy=missing_bar_only，tau0=ex_date当日。研究期、三窗口、估计期覆盖门、sample gate、全市场等权基准、ADJ-BMP唯一判决、cost、holdout、field roles、digest binding及llm/prescreen水印均按草案建议确认。数据对账与最小只读视图另令，当前草案digest不得冻结。

## 二、逐项效力

1. **A=A1：`adj_factor`变化为资格硬门。** 除权日因子必须相对前一SSE开市日发生变化，
   才进入主事件集；窄闸所见27个因子静态候选不进入A1主样本。不得按事件数量调整该门，
   也不为A1另开成因扩查。
2. **B=B1：六字段精确一致才可确定性折叠。** 同一`(ts_code,end_date)`方案组的多行，只有
   `ex_date/stk_div/stk_bo_rate/stk_co_rate/imp_ann_date/record_date`全部非NULL，且日期或Decimal
   逐项精确一致时才可折叠；任一字段为NULL或存在任何冲突，整组fail-closed。不任取最早、
   最新或最大比例，`update_flag`只作版本审计、不要求为0。
3. **C=C1：复权总回报为唯一主CAR，`tau0=ex_date`当日。** 主判决只消费既有后复权总回报
   close；前/后复权同窗收益等价。不复权机械跳空只作结构化NOT_FOR_VERDICT诊断，不得进入
   CAR、方向或显著性；若将来要研究机械跳空，必须停止exp14并重新登记。
4. **D=D1：监管阶段只作组成NFV。** 仅报告三个粗粒度阶段的事件数量、比例、恰等边界及
   板块可用性；不计算阶段CAR、ADJ-BMP或独立verdict，不拆alpha，不建设板块历史映射或通用
   监管收益诊断轴，也不得借用forecast专属`type_strata`。
5. **`st_policy=keep`。** 保留ST事件，不设置ST收益分层判决轴。
6. **`postpone_policy=missing_bar_only`，`tau0=ex_date`当日。** 除权日有真实bar即为价格观察
   τ0；仅缺bar/停牌可沿SSE开市日轴顺延不超过5日，第6日仍无bar则剔除。一字板只要有真实bar
   即不顺延，且不得表述为可成交收益。公告事件的`unified_announcement`不适用于本事件。
7. **其余沿承项确认。** 研究期=`2011-01-01 <= ex_date < 2024-07-01`；窗口=5/20/60，主窗
   `[0,+4]`唯一判决；估计期为τ轴前250至前91交易日、160日窗、有效覆盖门112/160；
   `sample_gate=30`、全市场等权`benchmark_mode='market'`、`adj_bmp_main_only`唯一顶层判决；
   cost四值仅作schema与执行审计；全A排北交所、含退市实体；holdout、field roles、digest
   binding、无收益分层轴及`llm/prescreen`身份水印均按草案建议确认。

## 三、尚未施工且不得代填

- **最小只读视图与正式数据对账。** exp14专属current/snap投影、A1漏斗、缺bar顺延、逐年与
  监管组成、正式事件数及selection SHA均须John另令；不得把snapshot375下的4,038参考数直接
  升级为正式运行硬断言。
- **研究数据身份。** snapshot375仍只是源级快照，不是exp14研究manifest；正式运行前须另令
  生成exp14自有StudySnapshot manifest并独立验收。
- **人的方向与把握度。** 仍须在终版PAP新digest通过复核后由John亲拟；登记方向“正”只属
  题目背景，不得自动平移为密封预测。

## 四、草案身份与边界

- 草案JSON保持原样，digest仍为
  `b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`；
- 该digest只作历史NOT-FROZEN草案锚，**不得冻结**；人裁值与正式对账身份落入终版后必须生成
  新digest；
- 本裁定只授权逐字留痕，不授权接口重探、全量采集、缓存入仓、生产代码、视图、数据库写入、
  数据对账、终版PAP、冻结、StudySnapshot、manifest、收益读取、正式运行或persist；
- 下一步只能由John另令exp14最小只读视图与数据对账；exp18、exp23继续停原语义硬门，exp21
  维持已裁草案待数据闭合，不并行恢复。
