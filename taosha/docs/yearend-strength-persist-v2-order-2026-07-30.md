# exp16 `yearend_strength` v2 persist 终令

日期：2026-07-30（UTC+8）  
授权人：John  
授权原文：**“批准 exp16 以已验收 v2 result 执行 persist，并按 Fable 复核提出的 B1/B2 边界正式闭卷。”**

## 一、授权对象与不可变边界

本令唯一授权：以已验收的
`/root/s16run/delivery/result_exp16_v2.json` 作为 exp16 persist 的唯一 result
输入，走既有状态机单事务闭卷。

永久保留并禁止覆盖的 v1 原件：

- result：`31b8115b47b9c69ee72bbd62a4849ec93dc180f6307cafcacd7ae2fba8156edb`；
- report：`79ca36833f8c6a8e31c291b70506f28a1a7a8ad32eb51bbc1dc328d652440709`；
- log：`e7bdfdd318317fc4ff0cb988825b3f5f8c8c904f62688d75db6b1e69e34b5b54`。

已验收的 v2 归档件：

- result：`96cc24abe093e99fd4599193e51785655c48af7fedc9a2cbc580acd3a4de307b`；
- report：`aad35e96324b1b5947fde279b82c36195c7ec8cea74a64931ddf080cb403e68d`。

禁止研究重跑、收益重读、原件改写、PAP 改写、manifest 重建、旁路 SQL 或新增
experiment 行。v2 result 不得再补键或删键；v2 report 不得再渲染或改写。

## 二、事务前只读断言

任一不符立即停止，不修补、不自动重跑：

1. 上述 v1 三件与 v2 两件 SHA256 全值逐字相等；
2. v1→v2 result 的结构差异恰为新增
   `audit.experiment_identity` 一键；删除该键后序列化字节逐字还原 v1 result；
3. v2 身份恰为
   `exp_id=16/family=yearend_strength/family_trial=1/source_type=llm/verdict_power=prescreen`，
   递归 `verdict` 键恰为一个；
4. v2 report 含唯一水印行
   `实验身份: exp16 family=yearend_strength trial=1 source=llm power=prescreen`；删除该行后
   字节逐字还原 v1 report；
5. exp16 仍为 `frozen`，
   `frozen_at=2026-07-30 11:01:09.498726+08`，`result_json/done_at` 为空；
6. 数据库 PAP canonical 为
   `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
7. manifest 317 权威行、qbase 镜像、publication attestation 三处 digest 均为
   `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
8. v2 result 关键值全精度断言：顶层唯一 verdict=`NOT_SIG`、事件 `7,751`、
   `N_valid=6,942`、主窗 `N=6,881`、CAAR=`-0.0031967252693485917`、
   ADJ-BMP=`-0.11178944002480809`；
9. ledger 26 行，分布为 `registered 9 / frozen 3 / done 12 / closed 2`。

## 三、persist 执行

使用 `taosha_app`，同一连接、同一事务：

1. 入事务前完成上述全部只读断言；
2. `FOR UPDATE` 锁 exp16 行后，再断言 `status=frozen`、结果双槽空、PAP canonical
   未变；
3. 仅走既有状态机 `ledger.start_running(16)`；
4. 仅以已验收 v2 result 解析对象调用 `ledger.finish(16, result)`；
5. 一次 `COMMIT`。

禁止修改冻结 PAP、v1/v2 文件、report、manifest 或 result 内容；禁止旁路状态机。

## 四、persist 后只读核验

1. exp16=`done`、`done_at` 非空、顶层 verdict=`NOT_SIG`；
2. 库内 `result_json` 与 v2 result `parsed_equal`，canonical 序列化 SHA 双侧一致；
3. 库内 `audit.experiment_identity` 与 v2/台账身份逐字段相等，递归 verdict 仍唯一；
4. `frozen_at` 与 PAP canonical 不变；
5. ledger 仍为 26 行，分布恰为
   `registered 9 / frozen 2 / done 13 / closed 2`；
6. manifest 317 三处 digest 不变；v1 三件、v2 两件 SHA 不变；
7. 本地、GitHub、阿里云代码同步且工作区干净。

## 五、闭卷固定读法与 Fable B1/B2 边界

1. 密封预判原文为：**“正，把握度50%，我的猜测其实不重要，重要的是实际数据”**。
   校准读数只登记“正，把握度50%”，仅押主窗方向，不押幅度或显著性，绑定 PAP
   digest `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`。
   实测主窗 CAAR `-0.3197%`，方向未命中；ADJ-BMP 不显著，终态 `NOT_SIG`。
   校准册第九条据实入册，九条方向读数为 `4命中/5未命中`。
2. 不得认定存在可靠正向或负向年末强势延续效应；朴素 t、Corrado、日历 t、
   次级窗与稳健窗均为 `NOT_FOR_VERDICT`；效力为 `llm/prescreen`。
3. τ0 一字板/涨跌停审计仅为价格观察，不构成可成交收益或可执行策略证据。
4. **B1**：当前 HEAD 对缺少 `audit.experiment_identity` 的历史 v1 result 重渲染会
   fail-closed。这是修复后强制水印的预期后果；v1 report 作为历史单跑原件永久留存，
   不再从 v1 result 重渲染，也不为此放宽当前报告硬门。
5. **B2**：v2 report 是在当前 renderer 验证唯一水印内容后，将该水印行插入 v1
   report 所得；它不是单跑直出，也不是 `report.render(v2_result)` 的逐字输出。
   `aad35e96324b1b5947fde279b82c36195c7ec8cea74a64931ddf080cb403e68d`
   是唯一权威修正版 report 归档 SHA。入库权威对象是确定性 v2 result。

## 六、停止线

完成 persist、后核验、闭卷档与 STATE 后停工。不得追加复核、重跑、敏感性分析或
通用框架施工；exp10 附注与本次 exp16 闭卷均不再扩展。
