# exp24 sox_spillover 冻结与最小适配 · 行为验收（2026-07-28）

## 结论

**通过，停在行为验收点。** exp24 已按人令冻结；事件规则、同日 τ0、signed 统计穿线、driver、报告与攻击 fixture 已完成。未生成 exp24 研究 manifest，未读取正式 A 股收益，未正式运行，未 persist。

## 1. 冻结凭证

- 冻结 PAP：`sox-spillover-pap-final-v2-2026-07-28.json`
- 文件 SHA256 = 引擎 canonical digest = DB 载荷 canonical digest：`be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`
- 预判原文：**“同向，把握度60%”**；按冻结 PAP 映射为主窗 signed CAR 为正，只押方向，不押幅度或显著性。
- 状态迁移：`registered → frozen`，同连接单事务一次提交；`frozen_at=2026-07-28 19:43:43.332816+08`。
- 读回：exp24 为 `frozen`，`result_json/done_at` 为空；DB JSONB 文本 MD5=`22cf1d8b2ab9a25fb19382694678d20a`。
- 台账仍 25 行，分布由 `13/2/9/1` 迁为 `12/3/9/1`，零新增行。

冻结脚本与日志仅存阿里云内部证据目录 `/root/s24freeze/`。

## 2. 最小适配触碰面

施工 commit：`0c55af73a912b3c51da01574d4eb2474b31a4930`。

- 新增 exp24 专属规则、reader、driver、报告帮助模块及两套 fixture；
- 新增 `qbase/sql/021_sox_spillover_reader.sql`，定义 current/snapshot 只读视图对与 holdout；**本行为单元未将该 DDL 应用于生产库**；
- 通用引擎只新增两个显式、默认关闭的能力：`tau0_on_anchor=False` 与 `direction_layers=None`。exp24 driver 固定消费为 `True` 和 `("up","down")`，非法组合 fail-closed；既有实验默认路径不变；
- signed 变换仍沿 exp20 已冻结路径，作用于事件窗、估计期残差、秩方向及相关修正输入，不是只改最终展示符号；
- 报告专属内容拆入小模块，未继续膨胀通用 `report.py`。新增生产模块最大函数长度：rules 34 行、driver 31 行、reader 12 行、report helper 20 行。

## 3. 攻击 fixture 与回归

- `verify_sox_spillover_rules`：`23/23 PASS`；
- `verify_sox_spillover_adapter`：`28/28 PASS`；
- 覆盖：Decimal ±3% 闭区间、北京日历映射、D4 多对一整段剔除、半 PIT 成分区间、同日唯一性、同日 τ0、缺 bar 1/5/6、signed 全输入穿线、direction 白名单、PAP digest/engine_params 全键消费、snapshot247 正式模式防冒充、报告唯一顶层 verdict；
- 既有离线全家福通过；合成 e2e SHA 仍为 `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`，默认路径逐字节零回归；
- `git show --check 0c55af7` 通过。

## 4. 只读漏斗复现

生产 DDL 未获写入授权，因此未为验收临时 apply 021。复现使用 qbase 既有 current 视图，连接显式 `read_only=True`，两次独立 SELECT + 同一 L2 规则计算，结果逐字一致：

- SOX 行 3,395；±3% 触发 314（up 161/down 153）；
- 映射日 301；D4 碰撞 9 日，剔除 22 个触发；
- 存活触发日 292（up 150/down 142）；
- 申万 801081.SI 成分输入 208，合法区间 203，异常区间 5 条 fail-closed；
- 展开候选 19,258，重复事件键 0，最终事件 19,258；漏斗恒等式通过；
- 两跑 selection SHA256 均为 `7a7840e596b755746fe5f038928fad622e2df83a32ba64d6105e9a9513b2acee`；
- 数据质量注记复现：currency 空字符串 388 行，close 缺失 0；边界恰等 0。

`snapshot_id=247` 只作源级快照，note 已明确“禁作研究 manifest 消费”；当前无 exp24 正式研究 manifest。

## 5. 当前停止线

- exp24：`frozen`；结果槽空；台账 `25=12/3/9/1`；
- 本地与阿里云代码 HEAD 均含施工 commit，工作树净；
- 未 apply 021、未创建 exp24 研究 manifest、未读取正式收益、未运行、未 persist。

下一步仅在外部复核通过并获新令后：应用并验收 021 只读视图对 → 创建 exp24 自有研究 manifest → §7 单次正式运行；persist 仍须结果验收后另令。
