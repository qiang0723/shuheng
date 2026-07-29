# exp15 `st_imposition` · 冻结前只读准确性窄闸报告（2026-07-29）

## 结论

**可进入PAP草案。** exp15本身无数据或统计能力硬阻塞：现有namechange批次、019只读视图与单事件集ADJ-BMP路径足以确定性表达“普通状态→ST/风险警示状态”。本结论不授权PAP、冻结、manifest、收益读取或正式运行。

冻结前仍须由John裁定一项：exp15与exp22的family及α分配。现有实物无法精确识别exp22的“财务原因”，但名称状态代理显示高度包含关系，见§4。

exp15来源=`llm`、效力=`prescreen`，不得表述为`human/full`。

## 1. 状态与执行边界

只读实核：

- exp15=`registered`，`frozen_at/result_json/done_at`均空；addendum=0，零exp15 manifest；
- exp12=`done`，exp22=`registered`；
- 台账25行=`registered 11 / frozen 2 / done 11 / closed 1`；
- 输入=`explore_reader_namechange`，namechange=`batch7`，18,868行、5,532票，研究视图列面仅`ts_code/alias/start_date/ann_date/snapshot_batch`；
- 底表`entity_alias`经qbase_app只读元数据核验，列面为`id/batch_id/ts_code/alias_type/alias/start_date/end_date/ann_date/valid_time/observed_time`，无`change_reason`或风险警示原因字段。

第一次脚本以`taosha_engine`查询experiment基线时被权限闸拒绝，发生在事件扫描前，零写入；随后仅将台账基线连接改为`taosha_app`并强制`default_transaction_read_only=on`，namechange仍由`taosha_engine`只读身份消费。最终脚本双跑逐字节一致。

## 2. exp15事件识别实测

本次机械核验口径（**未冻结**）：

- 段位折叠、名称状态优先级、退市双谓词、公告锚与fail-closed结构沿exp12同源纪律；
- 候选=`前段normal → 后段st`；`*ST/S*ST/G*ST/SST/ST`均属ST状态，退市名优先判为delist；
- 事件锚=后段唯一`ann_date`，不得用`start_date`回填；
- 仅作数量核验时借用exp12覆盖边界：`2011-01-01 ≤ ann_date < 2024-07-01`。该起点须在PAP阶段由人确认，不因本报告自动冻结。

漏斗：

| 阶段 | 数量 | 说明 |
|---|---:|---|
| namechange输入行 | 18,868 | batch7、排北、holdout视图焊死 |
| 名称段 | 17,133 | 同票同`start_date`孪生折叠 |
| 有前段转换 | 11,601 | 段位相邻转换 |
| normal→ST候选 | 1,277 | 含后续fail-closed档 |
| 锚缺失 | 510 | 不以生效日回填 |
| 状态不可判 | 1 | mixed孪生段，fail-closed |
| 研究期外 | 1 | 机械研究期口径 |
| 锚冲突/ann>start/重复键 | 0/0/0 | 实测 |
| 最终候选事件 | **765** | 646票，恒等式成立 |

最终候选构成：

- 普通→带星ST：`560/765=73.20%`；
- 普通→不带星ST：`205/765=26.80%`；
- 公告到生效间隔：同日9、1–3日506、4–7日245、超过7日5；
- 事件键SHA256=`93a8d08740b93da50a148b33ca8a4206fe9a4c2ba3b0d863d44d473f779fd89f`；
- 逐年：2011:16 / 2012:26 / 2013:23 / 2014:35 / 2015:42 / 2016:57 / 2017:56 / 2018:52 / 2019:84 / 2020:102 / 2021:74 / 2022:57 / 2023:66 / 2024H1:75。

真实边界样本包括：`000004.SZ`国华网安→ST国华（ann 2022-04-30，生效05-06）；`000007.SZ`全新好→*ST全新（ann 2021-04-29，生效04-30）；同票再次普通→*ST可形成新的、不同公告键事件。退市段→ST、ST→ST等非目标转换不进入候选。

## 3. exp15与exp12：反向事件、精确键不重叠

在同一batch7、同一机械研究期与同一段位算法下：

- exp15最终候选=`765`，646票；exp12闭卷规则复算=`641`，514票；
- 精确事件键交集=`0`：`0/765=0%`、`0/641=0%`；
- 证券交集=`430`：占exp15证券`430/646=66.56%`，占exp12证券`430/514=83.66%`。

证据说明两者经常发生在同一公司，但不是同一时点的重复样本；一个测普通→风险警示的制度性卖压，另一个测风险警示→普通的撤销反应，方向相反。**建议：exp15与exp12维持独立family**，沿exp11与反向机制假设不同family的在案先例。

## 4. exp15与exp22：精确原因不可判，名称代理高度包含

exp22登记命题是“因连续亏损/净资产为负被实施退市风险警示”。现有namechange底表与研究视图均没有`change_reason`，仅凭名称不能区分连续亏损、净资产为负、审计意见或其他退市风险警示原因。因此：

- **exp22精确候选事件集当前不可确定性生成；精确重叠数不可计算。** 这构成exp22自身的数据前置缺口，不阻塞exp15；
- 不得把`*ST`字面直接冒充exp22正式事件集；
- 仅作NFV名称状态代理上界：取exp15最终候选中后段含`*ST`者，共`560`事件、477票，事件键SHA256=`a15124adba9d30e2e820e87a650ae09d51ef9b6ff67599cef64eae979ef3eb57`；
- 该代理与exp15交集=`560`，占exp15=`560/765=73.20%`，占代理=`560/560=100%`。

这不是exp22样本量结论，而是族关系风险证据：exp22一旦未来补齐原因字段，其候选很可能是exp15的条件子集。**保守建议：exp15与exp22按同族处理；若当前推进exp15，冻结前按trial 2、族内α减半预注册。** 最终family字段、trial与α口径由John裁定，本单元零台账写入。

## 5. 能力与下一步

可直接复用：

- qbase 019 namechange current/snapshot只读视图；
- exp12段位折叠、退市双谓词、公告锚、fail-closed与漏斗审计结构；
- 现有单事件集`adj_bmp_main_only`判决路径、三窗与报告框架。

预计最小适配仅为exp15反向事件规则、driver、fixture与报告分支；不需要新增数据资产、统计内核或平台能力。若PAP/施工阶段发现必须新增能力，须按M gate立即停报，不得在冻结期顺手建设。

下一步只能是：John先裁定exp15↔exp22的family/trial/α，然后另令PAP草案；方向与把握度在终版digest复核通过后由John亲拟绑定。

## 6. 证据与禁区

- 最终双跑result SHA256均为`e2cc75d31d220fb188c9d067d92bf5de7291f295d937925f3a49a82814e66c80`；脚本SHA256=`42dc352764707664da46777722ee8a58b2d2c8061a543719e2e21cc54beed025`；
- 证据目录=`/root/s15gate/`，含双跑JSON、元数据探针与脚本；
- 全程零生产代码修改、零数据库写入、零PAP、零冻结、零manifest、零收益/CAR/显著性读取、零正式运行、零persist。

完成窄闸即停交验点。
