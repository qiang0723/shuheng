# exp22 `delist_warning_financial` 历史规则矩阵只读证据报告

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论先行

**本单元按授权完成“机器可读矩阵草案 + 官方证据索引 + 冲突菜单”，但历史规则矩阵轴尚未达到 B1 的冻结标准。**

- 已形成 17 个交易所/历史板块/制度阶段行，覆盖 `2011-01-01 ≤ event_date < 2024-07-01`；
- 已索引 25 份上交所或深交所官方规则正文、发布通知、过渡安排、问答及制度说明；
- 已证明 2012、2020、2024 三次主要制度切换，深市中小板合并、创业板旧制不适用以及科创板特殊上市标准等边界；
- 仍有 11 项冲突或事件级证明义务，其中 2013—2019 部分中间修订的精确施行日、规则正文“净资产”与 C1 归母权益字段的绑定、追溯重述与存量公司过渡、科创板特定上市标准门尚不能由本单元唯一闭合；
- 因此矩阵身份固定为 **`DRAFT_NOT_FOR_FREEZE`**，全部行 `freeze_eligible=false`；exp22 不得进入终版、密封或冻结；
- **G2 起点未填写，机器件中保持 `g2_start=null`。** 本报告不提出既成起点，也不把某一制度切换日转写为研究期起点。

交付：

1. `taosha/docs/delist-warning-financial-rule-matrix-draft-2026-08-10.json`
2. `taosha/docs/delist-warning-financial-rule-evidence-index-2026-08-10.json`
3. 本报告

机器件 SHA256：

- 矩阵草案：`02e095f579d07a9efb8395e6dbb634c422677b8329e6ed16c855e7f95d965513`
- 证据索引：`b8ce8cd0f04c7a67734dfa22b41b3e992bc2d407a5329296a7365ac2a5c6c202`

## 二、已证明的制度骨架

### 2.1 上交所主板

1. 2011 年初仍处于 2008 版规则阶段；连续亏损是既有退市风险警示指标，而净资产为负是 2012 改革新增指标。2012 新规自 2012-07-07 施行，新指标从 2012 年年报首次适用，既有连续亏损期限则连续计算。来源见 [2008版规则发布通知](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20150912_3988237.shtml)、[2012版规则发布通知](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20150912_3988587.shtml)及[2012改革问答](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20150912_3988578.shtml)。
2. 2012 改革至 2020 改革前，连续两年亏损与最近一年期末净资产为负均可直接触发财务类退市风险警示；追溯重述也可能触发，且实施须由上市公司公告。具体条款以[2013版规则正文](https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/10785193/files/a58091aef75c46c0a43ce2cd11d1379c.pdf)交叉确认。
3. 2020 改革后，单一连续亏损被净利润与营业收入组合指标替代；该组合指标不属于 A1 的“连续亏损”原因。A1 在该阶段仅可保留净资产为负分支。存量连续亏损公司另有其他风险警示过渡，不能冒充财务类 `*ST`。来源见[2020版规则通知](https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/c_20201231_10785038.shtml)及[改革问答](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20201214_5279592.shtml)。
4. 2024-04-30 发布的新标准不是按发布日期直接回溯到 2023 年报事件；官方通知明确新财务类标准从 2024 年年报首次适用，2023 年年报披露后的处置继续按原规则。来源见[2024版规则通知](https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/c_20240430_10785259.shtml)。

### 2.2 上交所科创板

1. 科创板自开市即采用利润收入组合与净资产为负等财务类指标，未采用 A1 意义上的单一连续亏损直接触发；因此该板块自始只有净资产为负分支可能落入 A1。来源见[2019年科创板规则正文](https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/10118921/files/9bd863640cc44cfb8db0a7e756df68dc.pdf)。
2. 特定研发型上市标准公司存在“第四个完整会计年度”适用门。若不能证明公司的上市标准和完整会计年度计数，必须 fail-closed。
3. 2024 新标准同样从 2024 年年报首次适用，holdout 前 2023 年报事件沿用原规则。来源见[科创板2024版通知](https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20240430_10777832.shtml)。

### 2.3 深交所主板与历史中小企业板

1. 2012 改革前，深市主板已有连续亏损指标但没有净资产为负退市指标；历史中小企业板则已经同时存在连续亏损和净资产为负指标。该差异由深交所[2012退市制度对照表](https://docs.static.szse.cn/www/aboutus/trends/news/W020180328462518001957.pdf)直接支持。
2. 2012 新规自 2012-07-07 施行；新增指标按 2012 年年报划断，既有连续亏损指标跨新旧规则连续计算。来源见[2012版规则通知](https://www.szse.cn/disclosure/notice/company/t20120718_508731.html)及[规则正文](https://docs.static.szse.cn/www/disclosure/notice/company/W020180328446393013021.pdf)。
3. 2020 改革后，单一连续亏损同样由利润收入组合指标替代；组合指标不能静默改写为 A1 连续亏损。来源见[2020版规则通知](https://www.szse.cn/disclosure/notice/general/t20201231_584052.html)及[改革问答](https://www.szse.cn/aboutus/trends/news/t20201231_584060.html)。
4. 中小企业板于 2021-04-06 并入主板。事件必须使用事件日历史板块身份；不得用当前板块归属覆盖历史。来源见[深市主板与中小板合并公告](https://www.szse.cn/aboutus/trends/news/t20210406_585442.html)。
5. 深市 2024 新标准同样从 2024 年年报首次适用；holdout 前 2023 年报事件继续按旧标准。来源见[深市主板2024版通知](https://www.szse.cn/lawrules/rule/repeal/rules/t20240430_607069.html)。

### 2.4 深交所创业板

1. 2020 改革前，创业板不实施与主板同构的 `ST/*ST` 制度，而采用退市风险提示、暂停上市和终止上市路径。旧制风险提示或暂停上市材料不能冒充 E1 官方“实施退市风险警示”公告。因此矩阵把 `2011-01-01 ≤ event_date < 2020-06-12` 标为 `NOT_APPLICABLE`，不是“零事件”。来源见[2012创业板规则通知](https://www.szse.cn/disclosure/notice/company/t20120420_508712.html)、[创业板退市制度方案](https://docs.static.szse.cn/www/lawrules/publicadvice/W020180328462435560438.pdf)及[2018规则通知](https://www.szse.cn/disclosure/notice/general/t20181116_557588.html)。
2. 2020 改革开始实施财务类退市风险警示，相关财务指标从 2020 年开始适用；旧暂停上市公司及 2019 年报另有过渡安排。来源见[创业板2020版通知](https://www.szse.cn/disclosure/notice/general/t20200612_578380.html)及[制度说明](https://investor.szse.cn/thematic/chinext/article/t20201022_582398.html)。
3. 2024 新标准从 2024 年年报首次适用，holdout 前仍适用原标准。来源见[创业板2024版通知](https://www.szse.cn/lawrules/rule/repeal/rules/t20240430_607070.html)。

## 三、为什么当前仍不能满足 B1

B1 要求“每个事件按交易所、历史板块、公告日、适用年度与过渡安排命中唯一规则版本”。本草案只闭合了主要制度段，尚有四类不可省略的事件级证明：

1. **逐版精确版本**：2013—2019 上交所、深交所存在若干中间修订。现有官方材料足以证明 A1 两类原因的主要语义没有被本报告随意改变，但尚不足以为每个事件日给出唯一规则版本号和精确施行边界。矩阵相关三行标为 `UNPROVEN_MINOR_VERSIONS`，其他语义段也只标 `PROVISIONAL_SEMANTIC_REGIME`，不得被 driver 消费。
2. **净资产字段绑定**：规则正文使用“净资产”“期末净资产”等规则术语，不能仅凭本单元证明其在每个历史阶段都必然对应 C1 `total_hldr_eqy_exc_min_int`。矩阵通过 `row_defaults.equity_field_binding_status=UNPROVEN` 统一拒绝默认绑定。
3. **存量与修订链**：追溯重述、已暂停上市、已实施风险警示、2020 改革存量过渡以及同一方案的后续修订，都必须依 E1 官方实施公告和财务 PIT 版本链逐事件连接。
4. **主体特殊门**：科创板特定上市标准公司必须额外证明上市标准与完整会计年度；深市中小板历史身份必须按事件日证明。

因此，本单元只证明“规则矩阵可建设”，没有证明“规则矩阵已经可用于生成 exp22 事件”。

## 四、机器件结构与冲突菜单

矩阵顶层包含：

- `matrix_rows`：17 个制度段；
- `global_consumer_rules`：A1 原因白名单、组合指标排除、历史板块、公告义务与 fail-closed 规则；
- `row_defaults`：所有行默认字段绑定未证、需要事件与公告证据、禁止冻结；
- `conflict_menu`：11 项冲突，每项含描述、触发停点、责任证据单元与状态；
- `g2_start=null`：明确拒绝代填研究期起点。

冲突菜单的确定处置包括：

- `C06`：创业板 2020 前关闭为 `NOT_APPLICABLE`；
- `C07`：2020 后利润收入组合指标关闭为 A1 排除项；
- `C09`：2024 新标准首次适用年度由官方过渡条款关闭；
- 其余 8 项继续 `OPEN`，必须通过逐版规则、事件公告、财务 PIT 或主体身份资料闭合，不能由矩阵作者代裁。

## 五、机械校验要求

本单元交验前须满足：

1. 两份 JSON 可解析，schema 均为 1；
2. 25 个来源 ID 唯一且全部为 `sse.com.cn` 或 `szse.cn` 官方域名；
3. 17 个矩阵 row ID 唯一，时间区间均非空且全部落在授权范围内；
4. 每个 `source_id` 与 `transition_id` 均能回指证据索引或冲突菜单；
5. `row_count=17`、`conflict_count=11`、`mechanism_not_applicable_rows=1` 与实物一致；
6. `g2_start` 必须为 `null`，`artifact_status=DRAFT_NOT_FOR_FREEZE`，`freeze_eligible=false`；
7. 全仓 diff 只能触及本单元文档与 `ops/STATE.md`，不得出现代码、SQL、数据库或研究产物变化。

实测：上述 1—6 全部为 `True`；25 个来源全部至少被一个矩阵行引用；同一交易所/板块内相邻制度段无缺口、无重叠；`git diff --check` 通过。

## 六、停止线与下一步边界

本单元没有执行接口采集、数据库访问或写入，也没有修改生产代码、PAP、实验状态、StudySnapshot、manifest、收益数据或正式运行产物。

exp22 继续停在数据闭合前。规则矩阵轴的下一步若要闭合，须另令补齐“逐版精确规则 + C1字段绑定证据 + 事件级过渡”；另外两轴仍是 E1 官方实施公告证据与 D1 完整经审计利润 PIT。三轴均形成全量连续覆盖后，才能向 John 呈报 G2 起点菜单；本报告不得被解释为其中任一起点。
