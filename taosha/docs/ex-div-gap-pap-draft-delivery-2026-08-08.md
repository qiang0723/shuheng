# exp14 `ex_div_gap` · NOT-FROZEN PAP 草案交付

日期：2026-08-08（UTC+8 / Asia/Shanghai）

## 一、技术结论

NOT-FROZEN草案已生成：
`taosha/docs/ex-div-gap-pap-draft-2026-08-08.json`。

- 顶层18键，`pap_schema_version=2`、`analysis_type=event`，无 `signed_ar`；
- 文件SHA256=引擎 `canonical_pap_sha256`=
  `b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77`；
- 文件字节本体=canonical紧凑JSON+末尾单换行；
- `validate_pap=PASS`，窗口解析=`(5,20,60)`；
- 本digest仅为草案候选，**不得用于冻结、driver、研究manifest或正式运行**。

草案采用现有单事件集、market benchmark、三窗口与 `adj_bmp_main_only` 路径；监管阶段、
因子变化与不复权机械重置均不产生第二顶层判决。

## 二、A–E 人裁菜单

### A · `adj_factor`变化资格门

| 选项 | 口径 | 实质影响 |
|---|---|---|
| **A1（技术建议）** | 除权日 `adj_factor` 必须相对前一交易日变化 | 主样本只保留价格序列可证明已执行公司行动调整的事件；冻结前参考4,038，排除27个因子静态候选 |
| A2 | 实施+时序+版本+事件键+Decimal阈值即入集 | 冻结前参考4,065；27个静态候选保留并强制质量告警，但“名义价格重置”机制证据较弱 |

不得按A1/A2的样本数量选择口径。Fable所列“27个成因未枚举”C项默认不扩查；若选A1，
该项不再影响冻结资格；若选A2，冻结前须只读分类并披露其成因，但不得据分类结果事后改门。

### B · 多版本折叠

| 选项 | 口径 | 实质影响 |
|---|---|---|
| **B1（技术建议）** | 同方案多行仅在六个消费字段逐项精确一致时确定性折叠 | 保留可证明同一实际方案的重复版本；任何日期/Decimal冲突整组剔除 |
| B2 | 任何多行方案一律整组fail-closed | 最保守，连完全一致的5组也剔除；不需要折叠规则，但扩大样本损失 |

六个消费字段=`ex_date/stk_div/stk_bo_rate/stk_co_rate/imp_ann_date/record_date`；
`update_flag`只作版本审计，不要求为0，不得任取最早、最新、最大比例或预案值。

### C · 复权主CAR与 `tau0`

| 选项 | 口径 | 实质影响 |
|---|---|---|
| **C1（技术建议）** | 后复权总回报为唯一主CAR；`tau0=ex_date`当日；不复权机械重置仅NFV | 忠实检验机械除权被消除后是否仍有正异常收益；直接复用既有同日开关 |
| C2 | 停止exp14，重新登记不复权机械价格研究 | 不把约−40.55%的机械跳空混入CAR；新命题须另走登记/PAP链 |

C1与 `postpone_policy='missing_bar_only'` 是不可拆组合；不得沿用公告事件的
`unified_announcement`，也不得把不复权跳空直接送入现有CAR。

### D · 监管阶段

| 选项 | 口径 | 实质影响 |
|---|---|---|
| **D1（最小技术建议）** | 监管阶段仅报告事件数量、比例、恰等边界与板块可用性，全部NFV | 零新统计能力；三阶段只作粗粒度组成诊断，不冒充法律制度分层 |
| D2 | 增加监管阶段CAR/ADJ-BMP诊断 | 冻结前须闭合板块历史映射并另令增加最小通用诊断轴；治理冻结期不允许则停止exp14冻结 |

两案均不得按监管5/8/10股阈值改写登记的统一每股0.5阈值；D2也不得借用forecast专属
`type_strata`、产生递归verdict或拆分alpha。

### E · 沿承项

请逐项确认：

1. 研究期建议=`2011-01-01 <= ex_date < 2024-07-01`；
2. 三窗口建议=`5/20/60`，主窗5日唯一判决；
3. 估计期建议=τ轴前250至前91交易日、160日窗、有效覆盖门112/160；
4. `sample_gate=30`、`benchmark_mode='market'`、`verdict_policy='adj_bmp_main_only'`；
5. `postpone_policy='missing_bar_only'`并由driver在冻结文本双重断言后启用
   `tau0_on_anchor=True`；`unified_announcement`不属于本事件的合法沿承值；
6. ST处置：E-ST1=`keep`（技术建议，避免监管/财务状态相关的选择性删样）；
   E-ST2=`reject`（沿平台早期默认，但会改变样本）；
7. cost四值只作schema与执行审计，不控制CAR取样；
8. holdout、field roles、digest binding、无收益分层轴与llm/prescreen身份水印沿既有事件版；
9. 人的方向与把握度只能在终版digest通过复核后另行密封，登记方向“正”不得自动平移。

## 三、已锁定事实与待裁边界

草案已锁定、不是菜单的事实：

- 事件只来自 `div_proc=实施`，且 `imp_ann_date < ex_date`；
- 送转合计=`Decimal(str(stk_div))`，阈值 `>=Decimal('0.5')`，恰等入选；
- 现金分红、标题、预案、通过、未通过、停止实施、后验完成状态均不得代理；
- 合计与分项冲突、同票同除权日多方案冲突一律整组/整键fail-closed；
- 前复权与后复权同窗收益恒等，不复权跳空不是投资者财富损失；
- 统一0.5是研究事件定义，不是所有时期/板块的监管法律标签。

仍待人裁的是A、B、C、D及E九个沿承子项。草案里的A1/B1/C1/D1、ST keep和其他值均明确
标为技术建议，不视为已裁。

## 四、冻结前同锚参考与能力边界

snapshot375 / dividend17下的数据侧参考为：

```text
35,280 实施行
→ 35,272 方案组
→ 35,269 版本一致组
→ 4,071 Decimal阈值候选
→ 4,065 事件键存活
→ 4,038 A1因子门参考
```

- 因子静态=27；A1下恰等0.5=1,083；
- 这些数只作冻结前同锚对账，A2参考、正式事件数和selection SHA均须在人裁后由专属钉批视图重算；
- 源级snapshot375 digest=
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，
  已含dividend17与价格/因子/日历批，但不是exp14研究manifest；
- 冻结前最小工程只应是exp14专属current/snap只读投影视图及确定性rules/recon；不得修改
  dividend底表或扩建通用公司行动平台；
- 若选D2，板块历史映射与通用监管诊断轴成为新增冻结硬门；若选D1，现有统计内核足够。

## 五、机械验收与残留态

已完成：

- 顶层键数=18，键集与既有事件版范式一致；
- `validate_pap=PASS`；
- `parse_test_windows=(5,20,60)`；
- 文件SHA、canonical重算与canonical字节本体三者一致；
- `signed_ar`、正式selection SHA、exp14研究manifest ID、冻结时间、运行结果均不存在；
- `NOT-FROZEN`标记在场，A–E“待人裁/技术建议”语义在场；
- 本单元未读取收益，未生成视图、生产代码、数据库写、StudySnapshot、manifest、冻结、运行或persist。

## 六、下一停点

现停在人裁交验点。下一步只能由John逐项裁定A–E；完成裁定后再另令最小数据读取件与
只读recon，不能凭本草案直接冻结。exp18/exp23继续停既有语义硬门，exp21保持已裁草案待
数据闭合，不并行恢复。
