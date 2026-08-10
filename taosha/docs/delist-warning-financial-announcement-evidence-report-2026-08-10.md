# exp22 `delist_warning_financial` 官方实施公告证据轴只读核查报告

日期：2026-08-10（UTC+8 / Asia/Shanghai）  
结论：**官方公告全量索引工程具有技术可行性，值得在另行授权后建设；但当前 E1 公告证据硬门仍为 `OPEN_FAIL_CLOSED`，exp22 不得进入终版、密封或冻结。**

## 一、答案先行

本轮得到两个不能混写的结论：

1. **工程可行性：YES。** [上交所上市公司公告入口](https://www.sse.com.cn/disclosure/listedinfo/announcement/)、[深交所上市公司公告入口](https://www.szse.cn/disclosure/listed/notice/index.html)与[巨潮资讯公告查询](https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice)构成稳定的官方/法定披露入口。跨上交所主板、深交所原中小板和创业板的原件表明，正文通常能同时承载“实施动作、A1原因、规则条款、公告日、证券身份”五类字段。因此，未来另开全量官方公告索引工程不是在赌一个不存在的数据面。
2. **当前冻结资格：NO。** 本次是刻意分层的非全量探针，没有采集逐证券公告全集。单份 PDF 不能自证“同一方案没有更早实施公告”，也不能排除继续实施、修订、撤销或同日相关公告。严格六项合取在 11 个研究窗内探针中为 **0/11**；这个 `0/11` 只表示本轮未证明首次性，**不是市场事件发生率、公告覆盖率或无事件结论**。

所以，公告证据轴的正确停点是：

- `worth_separately_authorized_full_index_build=true`；
- `current_e1_hard_gate=OPEN_FAIL_CLOSED`；
- `freeze_eligible=false`；
- `g2_start=null`。

本报告不把“值得施工”写成“已经闭合”，也不把“严格通过为零”写成“市场不存在事件”。

## 二、官方入口能证明什么，不能证明什么

### 1. 已证明

- 上交所、深交所都有上市公司公告官方查询入口；巨潮资讯是深交所法定信息披露平台并提供沪深各历史板块公告入口。
- 原件正文可以直接给出实施动作、触发原因、规则条款、实施日期、证券代码与简称变化。例如：
  - [600265.SH 2013 年实施公告](https://static.cninfo.com.cn/finalpage/2013-05-02/62447733.PDF)明确 2011、2012 年连续亏损及实施日期；
  - [600518.SH 2021 年实施公告](https://static.cninfo.com.cn/finalpage/2021-04-28/1209841773.PDF)明确 2020 年期末归母净资产为负；
  - [002418.SZ 2020 年实施公告](https://static.cninfo.com.cn/finalpage/2020-04-29/1207664414.PDF)明确连续亏损；
  - [300108.SZ 2022 年实施公告](https://static.cninfo.com.cn/finalpage/2022-06-29/1213856951.PDF)明确创业板负净资产规则与实施日期。
- 文档角色可以用正文语义而非标题关键词 fail-closed 区分。“可能被实施”“继续实施”“撤销”“其他风险警示”和二手转述均有真实样本。

### 2. 尚未证明

- 本轮没有验证任何公告查询接口、分页、排序、截断或历史完整性；页面可访问不等于全量检索已闭合。
- 本轮没有保存逐证券公告全集及原件内容 SHA，因此无法证明每个方案的首次性和公告链完整性。
- 单份“关于实施”的原件即使前五项字段齐全，也不能排除同日重复、修订或更早同方案实施文件。
- 本轮没有形成正式事件、候选数、逐年覆盖率、selection SHA 或 G2 起点菜单。

## 三、分层探针结果

本轮共登记 12 件原件/相关材料：11 件位于研究窗，另 1 件 2026 年科创板材料只作字段结构证明、排除在研究窗分母之外。研究窗内主状态恰等为：

`11 = 首次性未证5 + A1原因不符1 + 非实际实施1 + 继续实施1 + 撤销后续1 + 非事件原件1 + 其他风险警示1`。

| 探针 | 层 | 结论 | 关键原因 |
|---|---|---|---|
| [600265.SH / 2013](https://static.cninfo.com.cn/finalpage/2013-05-02/62447733.PDF) | SSE 主板 | `FIRSTNESS_UNPROVEN` | 前五项齐全；缺完整公告链 |
| [600408.SH / 2015](https://static.cninfo.com.cn/finalpage/2015-04-30/1200948583.PDF) | SSE 主板 | `FIRSTNESS_UNPROVEN` | 前五项齐全；缺完整公告链 |
| [600518.SH / 2021](https://static.cninfo.com.cn/finalpage/2021-04-28/1209841773.PDF) | SSE 主板 | `FIRSTNESS_UNPROVEN` | 负归母净资产明确；首次性未证 |
| [002418.SZ / 2020](https://static.cninfo.com.cn/finalpage/2020-04-29/1207664414.PDF) | SZSE 原中小板 | `FIRSTNESS_UNPROVEN` | 连续亏损明确；首次性未证 |
| [300108.SZ / 2022](https://static.cninfo.com.cn/finalpage/2022-06-29/1213856951.PDF) | SZSE 创业板 | `FIRSTNESS_UNPROVEN` | 负净资产明确；首次性未证 |
| [688309.SH / 2024](https://static.cninfo.com.cn/finalpage/2024-06-07/1220288718.PDF) | SSE 科创板 | `FAIL_A1_REASON` | 原因为净利润与收入组合，正文明确净资产不为负 |
| [600198.SH / 2021](https://static.cninfo.com.cn/finalpage/2021-01-28/1209203239.PDF) | SSE 主板 | `FAIL_NOT_IMPLEMENTATION` | 仅为“可能被实施” |
| [002356.SZ / 2020](https://static.cninfo.com.cn/finalpage/2020-05-29/1207873251.PDF) | SZSE 原中小板 | `FAIL_NOT_FIRST_CONTINUATION` | 明确为继续实施，且原触发原因不同 |
| [002194.SZ / 2019](https://static.cninfo.com.cn/finalpage/2019-08-14/1206519903.PDF) | SZSE 原中小板 | `FAIL_WITHDRAWAL_FOLLOWUP` | 撤销公告只可回溯，不可替代原实施公告 |
| [600086.SH / 2020](https://static.sse.com.cn/disclosure/bond/announcement/company/c/2020-07-02/3910832993883200741447841.pdf) | SSE 主板 | `FAIL_NOT_ORIGINAL_EVENT_DOCUMENT` | 交易所债券报告是官方二手转述 |
| [300089.SZ / 2022](https://static.cninfo.com.cn/finalpage/2022-04-30/1213266876.PDF) | SZSE 创业板 | `FAIL_RELATED_OTHER_WARNING` | 当前文件为其他风险警示，只指向另份目标公告 |
| [688066.SH / 2026](https://static.cninfo.com.cn/finalpage/2026-04-30/1225265910.PDF) | SSE 科创板 | `OUT_OF_SCOPE_SCHEMA_PROOF` | 只证当前原件结构；晚于 holdout，不进研究窗 |

其中 6 件满足除首次性之外的五项检查；5 件是初始实施形态、只因缺完整公告链而阻塞，另 1 件明确属于“继续实施”。这说明首次性不是可以从标题或单份 PDF 默认推导的小字段，而是需要方案链的独立证据门。

本轮不绘制频率图：探针是为覆盖文档角色与失败形态刻意选择，不是概率样本；图形化会制造代表性错觉。

## 四、最小机器证据合同

机器合同见 `delist-warning-financial-announcement-evidence-contract-2026-08-10.json`。正式公告轴至少必须保留：

- 原件来源 ID、URL、内容 SHA、公告 ID、公告日、证券代码与公司名称；
- 文档角色、实施日期、A1 原因代码与财务年度；
- 规则来源与条款；
- 方案 ID、前后公告 ID、首次性证明；
- 六项逐项布尔结果和唯一失败码。

首次性最低证明不是“标题含实施”，而是：逐证券研究期公告全集已完整枚举；文档角色已区分；正文交叉引用已形成前后方案链；同一方案不存在更早实施公告；多份同日原件或方案身份冲突时整组 `FAIL_CLOSED`。

继续禁止使用 `*ST`/ST 名称、namechange、财报同日、审计意见、标题、后验状态、搜索摘要或后续公告转述补字段。

## 五、若另令全量施工，验收线必须先写死

公告索引工程只有在另行授权后才能开工，且至少需要以下硬门：

1. 交易所/法定披露平台的查询参数、分页、排序与截止边界原文留痕；
2. 逐证券请求全集、响应全集与去重公告 ID 集合守恒；
3. 原件逐件保存内容 SHA，并保留不可下载、重定向与重复文件；
4. 对“可能、首次实施、继续、修订、撤销、终止、其他风险警示、二手转述”作正文级角色分类；
5. 解析正文交叉引用为方案图，首次性与方案身份不能唯一证明即整组拒绝；
6. 按交易所、历史板块、公告年度报告检索分母、原件可得数、六项通过数与互斥失败原因；
7. 完整覆盖结束前不得生成 exp22 事件、selection SHA、终版 PAP 或 G2 起点菜单。

技术判断是**值得建设**，因为官方入口和原件字段面都存在；但建设成本是“完整公告索引 + 原件归档 + 方案关系图”，不是一次关键词检索或几十份 PDF 抽核。若 John 不授权这一层，exp22 应继续停在 E1 硬门，不得改走代理锚。

## 六、机器校验与交付锚

| 文件 | 内容 | SHA256 |
|---|---|---|
| `delist-warning-financial-announcement-evidence-index-2026-08-10.json` | 3 个官方入口 + 12 件原件/相关材料 | `5e153d9e7d36f10a5a6eeaaf3d466f6f0068210da841bcfcdef67d3913b53bd1` |
| `delist-warning-financial-announcement-evidence-contract-2026-08-10.json` | 最小字段、六项合取、失败码与未来全量验收线 | `7bb6e70db3b5de9c2a979c2f5b67d54edd97a7ec312ccc687d7eca18ae4b0a84` |
| `delist-warning-financial-announcement-probe-2026-08-10.json` | 11 件研究窗探针 + 1 件窗外结构探针 | `5ba0a3b8d8bd890c703e621122d5bfdfb41ba29971fa601323a57b056c64a942` |

机械检查通过：

- 证据索引 15 个 source ID 唯一；
- 12 个 probe ID 唯一，且全部 source ID 可解析；
- 研究窗内探针 11，窗外结构探针 1；
- 严格六项通过 0，五项通过 6，其中纯首次性阻塞 5；
- 主状态计数恰等 12；
- 三件 JSON 均可解析，`freeze_eligible=false`、`g2_start=null`。

## 七、边界与停点

本轮只读官方公开网页与公告原件并写文档/JSON：零接口采集、零缓存入仓、零数据库访问或写入、零生产代码、零 PAP、零密封、零冻结、零 StudySnapshot、零 manifest、零收益读取、零运行、零 persist；未恢复 exp18、exp21、exp23，未启动完整利润 PIT。

exp22 停在公告证据交验点。下一步若继续，须 John 另令“完整官方公告索引工程”或改排“完整经审计利润 PIT 轴”，一次只开一件；本报告不代填 G2，也不赋予冻结资格。
