# exp24 §7 执行停止点：Docker DSN 接线阻塞（2026-07-28）

## 结论

按人令 fail-closed 停止。**021 已应用并验收；未创建 exp24 研究 manifest，未读取正式 A 股收益，未执行正式研究，未 persist。**

## 已完成

- 人令留痕 commit：`287d95f`；
- 七键 current == source snapshot247 == 令定值：`daily6/adj_factor7/stock_basic6/namechange7/trade_cal10/sox_daily13/sw_member14`；
- exp24=`frozen`、PAP canonical=`be26a7f4…8f27`、结果槽空、台账`25=12/3/9/1`；
- 021 由 qbase_app 单事务应用成功；
- taosha_engine 可读四个 exp24 视图，current/snapshot 均为 SOX 3,395 行、成员 208 行，holdout 泄漏 0；两个底表越权攻击均被拒。

## 阻塞事实

正式 driver 的 snapshot247 `--recon-only` 在任何数据读取前退出：

`PermissionError: [Errno 13] Permission denied: '/opt/quant/.env'`

生产 Docker 以非 root 用户运行，并通过 `--env-file /opt/quant/.env` 将 DSN 注入环境；宿主 `.env` 正确保持 `root:root 0600`。但 `SoxSpilloverReader` 与通用 `ViewReader` 当前只从文件读取 DSN，没有优先消费已注入的环境变量。日志：阿里云 `/root/s24run/recon247.log`。

## 未采用的绕路

- 未改用 root 容器；
- 未放宽 `.env` 权限；
- 未复制明文秘钥；
- 未绕过 driver 手工正式运行；
- 未在“本令不授权代码修改”边界下擅自修复。

## 最小建议（待人另行授权）

仅修改 reader 的 DSN 解析顺序：显式参数 → `os.environ` → `.env` 文件兜底；不改变变量名、数据库权限、事件规则或统计逻辑。补环境优先/文件兜底/缺失拒绝 fixture，跑既有零回归后，从 snapshot247 recon 重新接续。正式 §7 尚未启动，单跑名额未消耗。
