# exp22 公告索引 v6 · `IncompleteRead` 网络重试窄修令

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、事实与授权

`bisect_v5` 于 `2026-08-10 19:58:04+08` 在 `000155.SZ` 的 pass A HTTP 响应读取阶段
抛出 `http.client.IncompleteRead(13652 bytes read)`，metadata exit=`1`，监督链按设计停止；
停止点为 `valid_done=17/646 / v5_reads=3469 / errors=5 / downstream=0`。旧 v1/v2/v3/v4/v5
容器、日志、失败页和 17 个合法 marker 均须保留。

现有 `cninfo._retry()` 只捕获可重试 HTTP 状态、`URLError` 与 `TimeoutError`；分块响应中途断开
未进入既有三次整请求重试。John 在收到诊断与最小建议后回复：

> 按照你的计划来执行任务

据此限缩登记为本窄修、验收、推送、阿里云精确 fast-forward，以及验收通过后以全新 v6 容器
从 `17/646` 续跑的授权；不扩解为任何数据库或研究状态变更。

## 二、唯一生产改动

仅将 `http.client.IncompleteRead` 纳入 `cninfo._retry()` 既有三次网络重试：每次必须重做完整
HTTP 请求，残缺字节不得解析、保存或进入双读集合。重试次数、退避、串行限流、v5 双读、日期
二分、单日漂移与全部结构性 fail-closed 规则均不得改变。

## 三、验收与续跑

1. 离线攻击 fixture 须证明前两次 `IncompleteRead`、第三次成功，恰为三次完整尝试与两次退避。
2. exp22 二分、定位、索引与路由专项，规模、架构、`py_compile`、`git diff --check` 全绿。
3. 推送后阿里云须精确 fast-forward；远端复验同组闸门。
4. 启动前须读回 `routes=646 / valid_done=17 / first_pending=000155.SZ / v5=3469 /
   errors=5`，旧证据不变；不符即停。
5. 新写入只能进入 `bisect_v6`，使用全新容器与监督日志。metadata 非零不得启动 documents、
   UNPROVEN queue 或 12 票独立读回；禁止自动重启。

## 四、停止线

零数据库写入、零利润 PIT、零终版 PAP、零密封、零冻结、零 StudySnapshot、零 manifest、
零收益读取、零研究运行、零 persist。E1 继续为 `OPEN_FAIL_CLOSED`。
