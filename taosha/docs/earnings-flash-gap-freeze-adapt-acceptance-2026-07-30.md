# exp17 earnings_flash_gap 冻结与最小适配验收

日期：2026-07-30（UTC+8）
停止点：行为验收；未生成 exp17 研究 manifest，未正式运行，未 persist。

## 1. 授权与冻结

- 人的密封原文：`正，把握度80%`。唯一解释为主窗 `[0,+4]` 合并 signed、市场调整后 CAR 方向为正；不押幅度或统计显著性。仅绑定 PAP digest
  `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`。
- 冻结与适配令：`earnings-flash-gap-freeze-adapt-order-2026-07-30.md`，F 条先行 commit `ccf0628`。
- 施工盘点发现 exp20 既有 forecast 视图刻意不暴露利润区间，无法承载 exp17 A1/C1。人补充授权仅新增 exp17 专属 forecast 利润区间 current/snap 只读视图；留痕
  `earnings-flash-gap-freeze-adapt-addendum-2026-07-30.md`，commit `0fb0c6a`。
- 冻结前 exp17=`registered`、结果三槽空、台账 `26=registered9/frozen2/done13/closed2`，终版文件 SHA、引擎 canonical 与令定 digest 三者相等。
- 第一次冻结脚本因 `dict_row` 被误作位置元组，在任何写入前停止；失败脚本与空日志保留。修正为显式字段访问后，同连接单事务
  `FOR UPDATE → pap_json=终版 canonical → freeze(17) → COMMIT` 一次成功。
- 冻结读回：`frozen_at=2026-07-30 22:36:24.132972+08`，载荷 MD5=`993a32d953b294f5bbd11566922f45d2`，parsed equality 成立；不可变探针被铁律④拒绝且回滚后 MD5 不变；台账变为 `26=8/3/13/2`。

## 2. 最小适配触碰面

施工 commit `db07534`，共八文件；统计内核 `runner.py`、清洗内核、PAP schema、既有 exp20 视图均未改。

- qbase：`024_earnings_flash_gap_reader.sql`，只新增利润区间 current/snap 视图，最小列面、holdout 与排北焊死，只授 `taosha_engine SELECT`。
- reader：70 行；连接从首事务起用 `default_transaction_read_only=on`，实测 `SHOW transaction_read_only=on`。
- 规则：172 行纯函数，Decimal 实现 A1/B1/C1、严格 up/down、恰等 boundary、重复键/方向冲突整组剔除与确定性 SHA。
- driver：183 行；PAP digest、11 个 engine 参数键、4 个 signed_ar 键、`axes.direction=[up,down]`、正式 manifest 身份与台账水印均 fail-closed；snapshot 340 只许 recon、正式模式拒绝冒充。
- 报告：50 行专属模块；通用 `report.py` 仅增加两个显式路由点。缺真实 StudySnapshot 或 `llm/prescreen` 身份水印即拒。
- 两套攻击 fixture：规则 120 行、适配 169 行。所有生产文件均低于 200 行，职责单一。

视图实物：属主均为 `qbase_app`，`taosha_engine` 仅有 SELECT；current 与 snapshot340 均为 127,166 行、最大 `ann_date=2024-06-29`、北交所 0 行。

## 3. 专项 fixture 与漏斗复现

- 本地 Python 3.14 Docker：规则 `13/13`、适配 `26/26` PASS。
- 阿里云钉版镜像 `shuheng-quant:579a354` + 当前 HEAD 只读挂载：同为 `13/13`、`26/26` PASS。
- 攻击面包含：负利润区间方向、恰等边界、A1 最近严格前置、同日预告排除、B1 flag0 缺失/多条、区间冲突、actual 空值、重复事件键、方向冲突、乱序确定性、PAP/signed 键篡改、PAP 外方向旁路、snapshot340 冒充、删除身份水印。

snapshot340 双跑逐字节一致，recon JSON SHA 均为
`5c777287b906d596381a861afe47ba30715d8eae31dbbbde8d2d44e46b9af935`；selection SHA 为
`cd1433f0e9cc5d60dea807dc7f4f7b26fbcf324392602205c466aa7be5bb05ac`。冻结参考逐项精确复现：

- express 视图输入 23,082 行 → 23,076 同票同期组；
- B1 剔除 6 → 存活 23,070；
- 互斥分类 = 孤儿 6,283 + 无严格前置 16 + 无完整区间 1,493 + A1 冲突 0 + actual 空 3 + up 997 + down 1,532 + inside 12,745 + boundary 1；
- 最终 signed 事件 2,529（up 997/down 1,532），事件键重复与方向冲突均 0，三条恒等式全真。

首次 recon 已通过规则与参考硬闸，仅在写 `/root/s17adapt/recon1.json` 时因目录属主不符停止；修正取证目录权限后成功。该次不涉及研究运行或数据库写入，痕迹如实保留。

## 4. 回归、证据与停止线

- 既有全部标准 `verify_*` harness 通过，含集成 `7/7`、镜像 `11/11`、血缘 `24/24`；核心数据库套件状态机 `46/46`、PAP gate `23/23`、addendum `14/14`、StudySnapshot probes `19/19`。
- 本地与阿里云默认合成 e2e 各双跑，四份 result SHA 均为历史基线
  `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`。
- `verify_pap_vs_spec` 是既知历史非全家福入口，只认识早期 family；本轮额外误跑后在 `synthetic_smoke` 抛既有 `KeyError`。失败日志保留，不修改该旧工具；标准清单另行完整通过。该边界与既有 exp10 验收记录一致。
- 证据：阿里云 `/root/s17freeze/`、`/root/s17adapt/`；两目录 `SHA256SUMS -c` 全部通过，秘密值模式扫描 0 命中。权限与旧工具两次非研究失败均保留原始痕迹。
- 运行后 exp17 仍 `frozen`，`result_json/done_at` 为空；台账仍 `26=8/3/13/2`；`study_snapshot` 仍 17 行、max=340。零 exp17 正式 manifest、零正式收益读取、零 §7、零 persist。

## 5. 结论

冻结凭证、A1/B1/C1 行为、signed 单判决适配、身份水印、snapshot340 对账与零回归均通过。当前停在行为验收点；下一步只能在外部复核通过并获人另令后生成 exp17 自有研究 manifest 与执行 §7 单次正式运行。persist 继续单独授权。
