# Web 静态快照验证（2026-08-09，UTC+8）

## 提取边界

- 数据库：阿里云 `taosha`，通过 `TAOSHA_APP_DSN` 建立会话；
- 连接级只读：`PGOPTIONS=-c default_transaction_read_only=on`；
- 会话实测：`SHOW transaction_read_only = on`；
- 数据截止：`2026-08-09 22:14:05.537694`（UTC+8 / Asia/Shanghai）；
- SQL：`docs/web-snapshot-2026-08-09/extract.sql`；
- 零数据库写入、零在线 API、零登录、零研究运行。

## 守恒与身份

- 台账 26 行，状态分布 `registered 6 / frozen 2 / done 16 / closed 2`，合计 26；
- `done` 中 exp7 为合成冒烟，不计正式真实研究，因此正式真实闭卷研究为 15 条；
- 正式真实统计显著恰 1 条：exp568，效力为 `llm/prescreen`；
- `full` 效力的正式真实闭卷研究 4 条（exp3/4/5/24），均为 `NOT_SIG`；
- 校准册 12 条，方向命中 5、未命中 7；
- exp19 与 exp14 均已由 `registered` 更新为 `done/NOT_SIG`，其全精度 result 指标已进入 `calibration_results.csv`；
- exp18、exp21、exp23 仍为 `registered`，exp1、exp6 仍为 `frozen`。

## 展示读法

- 统计显著不等于可交易；exp568 仍只具预筛选效力；
- `NOT_SIG` 不改写为“没有效应”；
- exp19/exp14 的密封方向均未命中，累计校准为 `5/12`；
- Web 只消费本目录静态件，不在运行时访问数据库或研究结果服务。
