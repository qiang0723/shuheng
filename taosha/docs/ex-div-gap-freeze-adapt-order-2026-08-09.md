# exp14 `ex_div_gap` · 冻结与最小适配令

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 终版 PAP：`taosha/docs/ex-div-gap-pap-final-2026-08-09.json`
- 终版 PAP digest：`a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`

## 人令与密封原文

终版 PAP 经 Fable 限域复核，结论为 `A0/B0/C0 → 通过`。John 在事件机制说明后亲拟密封原文：

> 正，把握度60%

该密封唯一解释为主窗 `[0,+4]` 后复权、市场调整后 CAR 方向为正；只押方向，不押幅度或
统计显著性，只绑定上述终版 digest，不继承或平移登记阶段“正”的表述。

John 随后逐字授权：

> 批准冻结 exp14 ex_div_gap 终版 PAP，并进入最小适配；绑定 digest a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7 与密封原文「正，把握度60%」。本令不授权研究 manifest、正式收益读取、§7运行或 persist。

## 一、冻结前硬闸

任一不符立即停止并报人：

1. exp14=`ex_div_gap/trial1/llm/prescreen/registered`，`frozen_at/result_json/done_at` 均空，
   addendum=0；
2. exp14 无研究 manifest、正式运行、result 或遗留进程；
3. 终版文件 SHA、引擎 canonical 重算与本令 digest 三者逐字相等；草案仍为原 SHA 且标记
   NOT-FROZEN/SUPERSEDED；
4. source snapshot 375 在权威行、qbase 镜像与 publication attestation 三处 digest 均为
   `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，完整 qbase 向量13键，
   实际对账消费 `dividend=17/adj_factor=7/trade_cal=10`；375 不得冒充 exp14 研究 manifest；
5. snapshot375 同锚 current/snap 选择精确一致，冻结前参考=`4,035`、恰等=`1,083`、selection SHA=
   `ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；
6. 台账基线为26行，分布 `registered=7/frozen=2/done=15/closed=2`。

## 二、冻结执行

使用既有状态机与同一 `taosha_app` 连接，单事务 `FOR UPDATE` 再断言：写入终版 canonical 原文后
执行 `registered→frozen`，一次 COMMIT。读回 `status/frozen_at/pap_json`，核文件、引擎与数据库
canonical、parsed equality、载荷 MD5；台账只迁 exp14 一行，冻结后应为26行
`registered=6/frozen=3/done=15/closed=2`，结果双槽仍空。冻结后对 PAP 的真实改动探针必须被
不可变触发器拒绝并回滚零残留。

## 三、冻结成功后的最小适配

只新增 exp14 专属小模块与必要的最小报告路由，不改统计与清洗内核，不扩数据平台：

1. 复用既有 `ex_div_gap_rules` 与专属 qbase current/snap 视图；规则保持 A1/B1、Decimal
   `stk_div>=0.5` 闭区间、分项精确一致、重复事件键整组剔除及 D1 组成 NFV；
2. driver 对终版 digest 三重断言，逐字消费 8 键 `engine_params`；正式模式拒绝 snapshot375
   冒充研究 manifest；`tau0_on_anchor=True` 仅在逐字核到冻结 `event_def/cleaning/window` 的
   `tau0=ex_date` 当日语义后启用，不设 CLI 自由入口；
3. `EventRow.first_ann_date=ex_date`，单事件层固定为 `ex_div_gap`；主路径只消费既有后复权价格，
   raw 机械跳空与监管三分只进结构化 NFV，不生成额外 verdict 或收益分层；
4. result 写入台账身份 `audit.experiment_identity`，报告缺失或非 `llm/prescreen` 水印即
   fail-closed；报告须消费选择漏斗、因子门、边界、逐年和监管组成，并维持唯一顶层 verdict；
5. rules 与 adapter 攻击 fixture 覆盖 B1-NULL、多行冲突、恰等0.5、事件键重复、因子静态/
   缺失/冲突、PAP 8键缺多、digest 篡改、snapshot375 防冒充、`tau0_on_anchor` 文本硬门、身份
   水印删除和报告 NFV 术语；
6. 冻结取证包补 8 个多行组“窄闸分类→严格B1对账分类”逐组去向表，只读既有事实，不改规则、
   不重跑研究；
7. 遵守文件≤300行、函数≤60行与现行规模棘轮；复用通用能力，不复制大块代码。

## 四、行为验收与停止线

以 source snapshot375 做只读 recon，精确复现 `4,035`、恰等 `1,083`、selection SHA
`ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f` 及全部恒等式；current/snap
与双跑须确定一致。上述仅为同锚行为参考，不冒充正式运行样本数；差异即停并归因，不追数、不改
冻结规则。专项 fixture、既有离线全家福、数据库硬门、规模闸门与合成 e2e 均须全绿。

完成即停行为验收点。本令不授权生成 exp14 研究 manifest、正式收益读取、§7 正式运行、result
persist 或敏感性分析。
