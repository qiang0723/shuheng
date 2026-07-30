# exp16 `yearend_strength` · 冻结回执（2026-07-30）

## 结论

exp16 已按人令冻结，冻结载荷为终版 PAP canonical 原文：

- PAP digest：`3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- 状态：`frozen`；
- `frozen_at=2026-07-30 11:01:09.498726+08`；
- `result_json/done_at` 均空；
- PAP parsed equality=`true`，载荷 MD5=`191628fbd5860ec2ede40c0418d44f54`；
- 台账 26 行，由 `registered 10 / frozen 2 / done 12 / closed 2` 恰迁为
  `registered 9 / frozen 3 / done 12 / closed 2`，零新增行。

## 冻结事务

冻结前只读断言全部通过：exp16 为 registered、三槽空、零 exp16 manifest、终版文件 SHA / 引擎
canonical / 人令 digest 三者全等，数据库仍为 10 键登记载荷。

执行使用 `taosha_app` 同连接单事务：`FOR UPDATE` 再断言 → PAP 载荷更新为终版 canonical 原文 →
`ledger.freeze(16)` → 一次 COMMIT。事务后独立只读复核全部通过。

人的预判原文为“正，把握度50%，我的猜测其实不重要，重要的是实际数据”。校准册只登记判断部分
“正，把握度50%”，仅押主窗方向，不押幅度或显著性；后一句作为研究纪律留痕，不进入统计。

## 痕迹与边界

- 人令留痕 commit：`58e3bc5`；
- 冻结脚本及日志：阿里云 `/root/s16freeze/`；
- 首次执行前置脚本时因未设置 `PYTHONPATH` 在导入阶段退出，尚未建立数据库连接；补齐运行环境后同一
  脚本通过。该环境启动痕不构成冻结尝试或数据库动作；
- 零正式 manifest、零正式事件后收益、零正式运行、零 persist。

