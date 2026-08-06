# exp19 `dividend_surprise` · 冻结与最小适配令

- 日期：2026-08-06（UTC+8 / Asia/Shanghai）
- 终版 PAP digest：`4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`

## 人令与密封原文

终版 PAP 经 Fable 限域复核，结论为 `A0/B0/C1 → 通过，可进入方向密封与冻结裁定`。
John 在事件机制与数据盲边界说明后亲拟密封原文：

> 正，把握度60%

该密封唯一解释为主窗 `[0,+4]` 合并 signed 市场调整后 CAR 方向为正；只押方向，不押幅度或
统计显著性，只绑定上述终版 digest，不继承或平移登记阶段表述。

John 随后逐字授权：

> 批准冻结 exp19 dividend_surprise 终版 PAP，并进入最小适配；绑定 digest 4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4 与密封原文「正，把握度60%」。本令不授权研究 manifest、正式收益读取、§7运行或 persist。

## 一、冻结前硬闸

任一不符立即停止并报人：

1. exp19=`registered/trial1/llm/prescreen`，`frozen_at/result_json/done_at` 均空；
2. exp19 无研究 manifest、正式运行、result 或 addendum；
3. 终版文件 SHA、引擎 canonical 重算与本令 digest 三者逐字相等；
4. source snapshot 375 在权威行、qbase 镜像与 publication attestation 三处 digest 均为
   `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，qbase 向量含
   `dividend=17`；375 只作源级快照，不得冒充 exp19 研究 manifest；
5. 台账基线为 26 行，分布 `registered=8/frozen=2/done=14/closed=2`。

## 二、冻结执行

使用既有状态机与同一 `taosha_app` 连接，单事务 `FOR UPDATE` 再断言：写入终版 canonical
原文后执行 `registered→frozen`，一次 COMMIT。读回 `status/frozen_at/pap_json`，提交文件、
引擎与数据库侧 canonical、parsed equality、载荷 MD5；台账只迁 exp19 一行，冻结后分布应为
`7/3/14/2`。冻结后对 PAP 的真实改动探针必须被不可变触发器拒绝并回滚零残留。

## 三、冻结成功后的最小适配

只新增 exp19 专属小模块与必要的最小路由，不改统计与清洗内核：

1. Decimal 纯规则：A1/B2-P1/C1/D1/E1、相邻财年连接、初始预案公告锚、异常组与事件键冲突
   整组 fail-closed；实施、通过、修订值不得回填；
2. driver：冻结 PAP digest 三重断言，`engine_params`/`signed_ar`/`axes.direction` 全键逐字消费，
   正式模式拒绝 snapshot375 冒充研究 manifest；
3. result 写入台账身份 `audit.experiment_identity`，报告缺失或非 `llm/prescreen` 水印即
   fail-closed；direction 只作 raw NFV，顶层只保留合并 signed 单判决；
4. rules 与 adapter 两套攻击 fixture，至少覆盖恰等正负50%、prior=0/current=0、缺上年、
   多初始行、多公告日、多金额、flag1/后续阶段回填拒绝、非相邻财年、重复事件键、身份水印删除、
   snapshot375 防冒充与 PAP 全键消费；
5. 复用既有 qbase dividend current/snap 只读视图与 signed 统计路径；不得新建平台能力，单文件、
   单函数保持小而可维护，不复制可下沉的大块。

## 四、行为验收停止线

以 snapshot375/dividend17 做只读 recon，复现冻结前机械参考 `5,055=up2,253+down2,802`，
提交完整漏斗、恒等式、selection SHA 与双跑确定性；该数只作为同数据锚的行为对账，不能冒充
正式运行样本数，差异须停下归因，不得追数或改冻结规则。专项 fixture、既有离线全家福、数据库
硬门与合成 e2e 均须全绿。

完成即停行为验收点。本令不授权生成 exp19 研究 manifest、正式收益读取、§7 正式运行、
result persist 或任何敏感性分析。
