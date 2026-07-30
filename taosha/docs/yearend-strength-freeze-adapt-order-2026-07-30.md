# exp16 `yearend_strength` · 冻结与最小适配令（2026-07-30）

## 人令与绑定

终版PAP外部复核通过后，John密封预判原文：**“正，把握度50%，我的猜测其实不重要，
重要的是实际数据”**；随后明确回复：**“批准冻结并进入最小适配”**。

- 冻结PAP digest=
  `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- 校准册只登记判断部分原文“正，把握度50%”；唯一解释=主窗`[0,+4]`市场调整后CAR方向为正；
- 仅押方向，不押幅度或统计显著性；预判不参与样本、统计或顶层判决；
- 后一句“我的猜测其实不重要，重要的是实际数据”作为研究纪律原文留痕，不改写为预测内容。

## 一、冻结前只读确认

任一不符立即停止：

1. exp16=`registered`，`frozen_at/result_json/done_at`均空；
2. 无exp16正式manifest或运行记录；
3. 终版文件SHA、引擎canonical重算值、本令digest三者逐字相等；
4. 数据库当前PAP仍为未冻结登记载荷，不得已是终版；
5. 台账26行，分布`registered 10 / frozen 2 / done 12 / closed 2`。

## 二、冻结执行

使用既有状态机与`taosha_app`同连接单事务：`FOR UPDATE`再断言→载荷更新为终版canonical
原文→`ledger.freeze(16)`→一次COMMIT。不得改写终版、复制草案或运行时补键。

读回`status/frozen_at/pap_json`，核对parsed_equal、DB canonical与载荷MD5；台账只迁exp16既有
一行，冻结后应为26行=`registered 9 / frozen 3 / done 12 / closed 2`，结果槽仍空。

## 三、最小适配授权（冻结成功后，至行为验收止）

1. 新增exp16专属纯规则、driver、报告模块及两套fixture；不新增数据资产或统计能力；
2. driver使用exp16自己的8键`engine_params`白名单逐字消费，不复用exp12七键函数；
   `st_policy=keep`从冻结PAP消费；`tau0_on_anchor=True`仅作为冻结文本“τ0=event_date当日”的
   确定性适配常量，并须先逐字核验PAP事件与清洗文本，不留运行时选择；
3. 事件规则须使用Decimal精确实现：12月最后10个SSE开市日+前一开市日严格11-bar面板，
   `exp(ln(close_d10/close_d0)-sum(market_log_return_d1..d10))-1 >= 0.05`闭区间；事件日为
   次年1月首个SSE开市日；重复键、缺bar或异常值fail-closed；
4. 攻击fixture至少覆盖：10收益/11-bar边界、恰5%收录、略低拒绝、缺任一bar整组拒绝、
   不得以个股行序补足、市场收益缺失拒绝、次年事件锚与研究期边界、重复键全剔、
   ST keep、τ0当日与missing_bar_only、8键缺/多键拒绝、digest断言与报告术语；
5. recon在snapshot74/market_return88同向量上双跑；7,751与selection SHA
   `057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`为只读参考，须精确
   复现；不符即停并报人，不追数、不改冻结规则；
6. 全量fixture与既有合成e2e零回归；遵守小文件、小函数与单一职责，不复制既有通用逻辑。

## 四、边界与停止线

本令不授权生成exp16正式manifest、读取正式事件后收益、执行§7正式运行或persist。适配完成即
停在行为验收点，交冻结凭证、代码diff、专项fixture、recon与零回归证据；下一阶段另令。
