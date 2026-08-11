# exp22 公告索引：v7 分页视图漂移与防漏收口

时间口径：2026-08-11，Asia/Shanghai（UTC+8）。

## 一、结论先行

`bisect_v7` 已 fail-closed，不能按原证据合同安全重启。

会话 cookie 粘性没有提供稳定快照：同一证券、同一公告日、同一请求参数的一遍分页内，官方列表的总数和页边界仍可变化。任何“再试到两遍碰巧相等”、交集、并集、择一或多数表决，都会把上游瞬时视图误写成完整历史集合，继续禁止。

本单元完成一项只收紧的防漏修复：同一遍分页中，只要任意两页的 `totalAnnouncement` 不相等，立即报 `API总数跨页漂移` 并停止。新写入布局预留为 `bisect_v8`；`bisect_v7` 加入旧布局白名单，只能自验和保全，不能覆盖。

这项修复能防止误收，不能证明上游全集。因此当前不启动 v8。

## 二、v7 失败实物

- 启动基线：`routes=646 / valid_done=51 / first_pending=000607.SZ / errors=6 / downstream=0`。
- 容器：`s22-ann-index-v7`，exit `1`，完成于 `2026-08-11 10:21:42+08`。
- 停止点：`000607.SZ / 2021-04-30 / pass_b`。
- 错误：`跨页公告ID重复`。
- 停止后：`valid_done=51 / bisect_v7 raw reads=359 / errors=7 / documents=0 / contract=0 / readback=0`。
- 监督进程已停止，未自动重启；v1—v7 容器、日志、失败页、错误记录和 51 个合法 marker 全部保留。

原始页复算：

- pass A：page 1/2 的 `totalAnnouncement=32/32`，行数 `30+2=32`，页间无重复；
- pass B：page 1/2 的 `totalAnnouncement=32/35`，行数 `30+5`，page 2 中两个公告 ID 已在 page 1 出现；
- 因此不是本地排序、规范化或 cookie 丢失造成，而是上游分页视图在同一遍读取中发生变化。

## 三、限定诊断

以下只读探针均未改远端状态：

1. 固定 cookie、共享 cookie jar、同一 HTTPS 连接均不能持续得到相同全集；
2. 增补官网前端请求中的 `trade` 空字段不能消除 `32/35` 漂移；
3. 官方前端可用排序字段不能在同时间戳公告间提供稳定唯一次序；
4. 深交所官网当前页面另有官方 `POST /api/disc/announcement/annList` 路径，前端契约已核到 `stock/channelCode/seDate/pageSize/pageNum`，但 Mac 与阿里云的限定 CLI 探针均返回维护页，尚未形成可运行、可复核的替代源。

故本轮不能把“存在另一条官网路径”写成“替代源已闭合”。

## 四、代码收紧

触碰面仅三件：

1. `qbase/ingest/delist_warning_announcement_bisection.py`：同一遍分页的 API 总数必须逐页完全一致；
2. `qbase/ingest/delist_warning_announcement_index.py`：新布局改为 `bisect_v8`，保留 `bisect_v7` 只读自验；
3. `qbase/ingest/verify_delist_warning_announcement_bisection.py`：新增 `35→32` 跨页总数漂移攻击用例，并验证 v7 失败证据不可覆盖、v7 合法 marker 可继续自验。

没有改限流、网络重试次数、双遍逐字段全等、页内/跨页 ID 唯一、混票、越界、非终页满页或完成 marker 规则。

## 五、验收

钉版镜像 `shuheng-quant:579a354`（`sha256:e7b9b270…ebfc3`）只读挂载未提交补丁：

- bisection：`37/37 PASS`；
- index：`46/46 PASS`；
- localization：`6/6 PASS`；
- routes：`6/6 PASS`；
- `py_compile`：PASS；
- 规模：`241 files / 36,051 lines / 1,097 functions / debt 20+50`，PASS；
- 架构：`172 modules / 377 edges / cross-experiment debts=2`，PASS；
- `git diff --check`：PASS。

本机 Python 3.9 的 `X | None` 导入失败为既知环境限制；专项结果取钉版镜像，不把本机导入失败计作回归。

## 六、停止线与下一裁定点

当前只完成防误收，不恢复监督链。E1 仍 `OPEN_FAIL_CLOSED`，零数据库写入、零利润 PIT、零终版 PAP、零密封、零冻结、零 StudySnapshot、零 manifest、零收益、零研究运行、零 persist。

若继续 exp22，需要 John 在以下方向中另裁：

- 优先：授权独立交易所官方公告源的最小可行性与契约单元；成功后按交易所分源重建完整索引；
- 或：另行改判证据合同，明确是否允许“历史原始页最大总数 + 官方行并集 + 逐公告 ID/原件复核”的证明方式；该路与既有“禁止交并集”相冲突，未经新裁定不得采用；
- 或：维持停止，exp22 跨期挂账。

