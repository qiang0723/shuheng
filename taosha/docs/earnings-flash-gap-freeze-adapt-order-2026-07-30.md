# exp17 `earnings_flash_gap` · 冻结与最小适配令

日期：2026-07-30（UTC+8）

## 人令与密封预判

John 在终版复核补正闭合后回复：

> 继续开发吧

经施工方说明本实验背景后，John 亲拟预判原文：

> 正，把握度80%

本预判仅押主窗 `[0,+4]` signed 市场调整后 CAR 方向为正，不押幅度或统计显著性；
只绑定终版 PAP digest
`92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`，不得改述或平移。

## 一、冻结前硬闸

任一不符立即停止：

1. exp17 为 `registered`，`frozen_at/result_json/done_at` 为空，来源/效力为 `llm/prescreen`；
2. 无 exp17 研究 manifest、运行结果或 addendum；
3. 终版文件 SHA、引擎 canonical 重算与本令 digest 三者逐字相等；
4. source snapshot 340 在权威行、qbase 镜像、publication attestation 三处一致，qbase 向量含
   `express=15/forecast=1/daily=6/adj_factor=7/stock_basic=6/namechange=7/trade_cal=10`；
5. 台账基线 26 行，分布 `registered=9/frozen=2/done=13/closed=2`。

## 二、冻结

使用既有状态机，同一 `taosha_app` 连接、单事务、`FOR UPDATE` 再断言：写入终版 canonical
原文后执行 `registered→frozen`，一次 COMMIT。读回 status/frozen_at/PAP canonical、
parsed equality 与载荷 MD5；台账只迁 exp17 一行，期望分布 `8/3/13/2`。冻结后真实改动探针
必须被不可变触发器拒绝并回滚零残留。

## 三、最小适配

仅新增 exp17 专属纯规则、driver、报告模块和两套 fixture，并在通用报告路由增加最小显式分支：

1. B1：同票同期仅接受恰一条 `update_flag='0'`；缺失、多条或冲突整组剔除；
2. A1：取快报前最近一次公开且区间完整的预告；同一最新日多条不同区间整组剔除；
3. C1：`actual_wan=express.n_income/10000`，严格 `>upper=up`、`<lower=down`，闭区间内及恰等
   不成事件；全程 Decimal；
4. 事件锚只能是初始快报 `ann_date`，同日预告不算前置，事件键重复或方向冲突整组剔除；
5. engine_params 及 `signed_ar` 全键逐字消费；方向白名单只能取 PAP
   `diagnostic_dimensions.axes.direction={up,down}`，不得使用 exp24 专属旁路；
6. 正式 result 从台账写 `audit.experiment_identity`，report 缺身份或非 llm/prescreen 必须
   fail-closed，fixture 包含删除身份攻击；
7. source snapshot 340 只作 recon 锚，正式模式必须拒绝其冒充 exp17 研究 manifest。

统计内核、清洗内核、qbase 表与视图、PAP schema 不得修改。单文件、单函数保持小而可维护；
不得复制可下沉的通用大块。

## 四、行为验收停止线

用 snapshot 340 只读 recon，复现冻结前参考：24,381 输入行、24,375 组、B1 剔 6 组、
A1 最新日区间冲突 0、方向事件 2,529（up 997/down 1,532）；同时给 selection SHA、互斥漏斗
恒等式与双跑确定性。参考数在本行为单元是同向量硬闸，不得追数或改规则。

专项 fixture、既有离线全家福与合成 e2e 必须全绿。完成停在行为验收点；本令不授权生成
exp17 正式研究 manifest、读取正式收益、执行 §7 或 persist。

