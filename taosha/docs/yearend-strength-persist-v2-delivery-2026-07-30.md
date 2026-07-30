# exp16 `yearend_strength` v2 persist 闭卷交付

日期：2026-07-30（UTC+8）  
终令：`taosha/docs/yearend-strength-persist-v2-order-2026-07-30.md`  
授权原文：**“批准 exp16 以已验收 v2 result 执行 persist，并按 Fable 复核提出的 B1/B2 边界正式闭卷。”**

## 1. 终态

exp16 已以已验收 v2 result 正式 persist：

- status：`done`；
- done_at：`2026-07-30 18:14:21.514511+08`；
- verdict：`NOT_SIG`；
- frozen_at 保持 `2026-07-30 11:01:09.498726+08`；
- PAP canonical 保持
  `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- manifest 317 三处 digest 保持
  `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
- ledger 26 行，恰迁一行至
  `registered 9 / frozen 2 / done 13 / closed 2`。

库内 result 与 v2 result `parsed_equal=true`；canonical 序列化 SHA 双侧均为
`29eb6f0854be6dd7745b917271bb0f4475ffa587cb3b564ea3bd9acd4c747c4d`，
递归 `verdict` 键恰为一个。入库身份为
`exp16/yearend_strength/trial1/llm/prescreen`，与台账和 v2 逐字段相等。

## 2. 前置与事务

最终前置只读断言 `24/24 PASS`：v1 三件与 v2 两件全值 SHA、v1/v2 恒等、
唯一水印、身份、正式统计、冻结状态、PAP、manifest 三处与 ledger 全部命中。

第一次前置脚本在写库前安全停止：脚本自造“`audit.study_snapshot` 只能含
snapshot_id/digest 两键”的过严断言，而 result 实物还含冻结消费向量 `content`。
终令只要求 ID/digest 逐字段相等，故保留失败脚本与日志后收窄回令文口径；v2 原件
未修改、数据库零写入。修正后的前置 `24/24 PASS`。

persist 使用 `taosha_app` 同连接同事务：

1. v2 result 关键值 `10/10 PASS`；
2. `FOR UPDATE` 后冻结状态、空槽、PAP、身份、manifest、台账 `8/8 PASS`；
3. `ledger.start_running(16)`；
4. `ledger.finish(16, v2_result)`；
5. 一次 `COMMIT`。

零研究重跑、零收益重读、零 result 改写、零 PAP/manifest 改写、零旁路 SQL、零新增
experiment 行。postverify `17/17 PASS`；提交后状态机 `46/46`、PAP gate `23/23`、
addendum `14/14` 全绿。

## 3. v1/v2 归档边界

v1 原始单跑三件永久保留：

- result：`31b8115b47b9c69ee72bbd62a4849ec93dc180f6307cafcacd7ae2fba8156edb`；
- report：`79ca36833f8c6a8e31c291b70506f28a1a7a8ad32eb51bbc1dc328d652440709`；
- log：`e7bdfdd318317fc4ff0cb988825b3f5f8c8c904f62688d75db6b1e69e34b5b54`。

v2 权威修正版归档：

- result：`96cc24abe093e99fd4599193e51785655c48af7fedc9a2cbc580acd3a4de307b`；
- report：`aad35e96324b1b5947fde279b82c36195c7ec8cea74a64931ddf080cb403e68d`。

Fable B1/B2 固定说明：

- **B1**：当前 HEAD 对缺 `audit.experiment_identity` 的历史 v1 result 重渲染会
  fail-closed，属强制水印修复的预期后果。v1 report 是历史单跑原件，不再从 v1
  result 重渲染，也不放宽当前报告硬门。
- **B2**：v2 report 不是单跑直出，也不是 `report.render(v2_result)` 的逐字输出；
  它是在当前 renderer 验证唯一水印内容后，把该水印行插入 v1 report 所得，删除该行
  即逐字还原 v1 report。上列 v2 report SHA 是唯一权威修正版报告归档锚。

入库权威对象是确定性 v2 result；它相对 v1 result 恰新增
`audit.experiment_identity` 一键，删除该键即逐字还原 v1 result。

## 4. 统计结论与校准册第九条

正式结果保持不变：事件 `7,751`、`N_valid=6,942`、主窗 `N=6,881`、主窗
CAAR `-0.0031967252693485917`（`-0.3197%`）、ADJ-BMP
`-0.11178944002480809`，顶层唯一判决 `NOT_SIG`。

密封预判原文：**“正，把握度50%，我的猜测其实不重要，重要的是实际数据”**。
校准读数只登记“正，把握度50%”，仅押主窗方向、不押幅度或显著性，绑定上述 PAP
digest。实测为负，**方向未命中**；ADJ-BMP 不显著。校准册第九条据此入册，九条方向
读数为 `4命中/5未命中`。

闭卷固定读法：不得认定存在可靠正向或负向年末强势延续效应；朴素 t、Corrado、
日历 t、次级窗和稳健窗均为 `NOT_FOR_VERDICT`；τ0 一字板/涨跌停只作价格观察，
不构成可成交收益或可执行策略证据；效力为 `llm/prescreen`。

## 5. 证据与停止线

persist 证据目录：`/root/s16persist_v2/`。目录含终令、最终三脚本、首次失败前置脚本
与日志、最终 preassert/persist/postverify 日志、三套数据库回归日志、秘密扫描报告和
SHA256 清单。`SHA256SUMS -c` 全部通过；13 类秘密扫描 `TOTAL_HITS=0`。

exp16 正式闭卷，不再追加复核、重跑、敏感性分析或水印框架施工。exp10 的
result-bound 附注亦不再扩展。下一研究任务须另行排产。
