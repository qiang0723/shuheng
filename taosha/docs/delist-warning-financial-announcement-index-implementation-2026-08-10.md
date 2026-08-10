# exp22 完整官方公告索引 · 本地实现交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

本地实现已完成并通过专项攻击 fixture、规模闸门与架构闸门；**尚未执行 batch7 路由导出或全量公告采集**。下一步只能在本提交推送、阿里云 fast-forward 读回后，按工程令依次执行一次只读路由导出、官方元数据全集、宽召回原件物化、证据合同待核队列与至少 12 票独立二次读回。

本地 live API 单日核验同时抓出旧证据错链，已由独立补正 commit `08a7891` 显式作废并替换；错误证据没有进入索引器 fixture 或未来全量锚。

## 二、七件实现与边界

| 文件 | 行数 | 职责 |
|---|---:|---|
| `taosha/harness/export_delist_warning_routes.py` | 130 | 连接参数级只读导出 batch7 广义普通→ST 路由；硬断 765/646/560/205、两恒等式与事件键 SHA |
| `taosha/harness/verify_delist_warning_routes.py` | 45 | 路由纯函数、只读状态与参考硬闸攻击 fixture |
| `qbase/ingest/delist_warning_announcement_index.py` | 266 | 官方 orgId、逐证券全公告分页、write-once 原始页、断点完成件、全局索引与宽召回路由 |
| `qbase/ingest/delist_warning_announcement_documents.py` | 85 | 宽召回 PDF/HTML 原件 SHA 物化；失败逐件登记，不把标题当正文证据 |
| `qbase/ingest/delist_warning_announcement_contract.py` | 72 | 将原件映射为证据合同待核队列；正文未核保持 `UNPROVEN`，永不自动闭 E1 |
| `qbase/ingest/verify_delist_warning_announcement_readback.py` | 111 | 按交易所/历史板块/公告年度选至少 12 票，独立重读并对 ID 集合、顺序与规范化行三重恰等 |
| `qbase/ingest/verify_delist_warning_announcement_index.py` | 237 | 元数据、分页、恢复、原件、合同队列和读回攻击 fixture |

所有文件均低于新代码 `300 行/文件、60 行/函数` 上限；未增加规模或架构债务。qbase fixture 初版曾直接 import taosha 路由模块，被架构闸门以“层级倒置”拒绝；已拆成 taosha 专属 fixture，不加基线例外。

## 三、机械保证

### 1. 路由

- 默认只从 `TAOSHA_ENGINE_QBASE_DSN` 取只读身份，值不回显；
- `psycopg.connect(..., options="-c default_transaction_read_only=on")` 从首事务起只读，并保存 `SHOW transaction_read_only`；
- batch7、事件数 765、证券数 646、带星 560、不带星 205、漏斗恒等式与组成恒等式任一不符即停；
- 路由件身份固定为 `ROUTING_ONLY_NOT_EXP22_CANDIDATES`，并保存排序事件键 SHA。

### 2. 官方元数据

- 官方 orgId 映射为空、重复或缺证券即停，不猜映射；
- 每证券 `category=""`，时间边界固定 `1991-01-01..2024-06-30`；
- 页内/跨页重复、混票、越界、空页仍 `hasMore`、重复页、总数漂移或去重数不等 API 总数任一即停；
- 原始页 write-once：既有页与重读响应不一致即停，不覆盖；
- done marker 同时绑定起止日、页数、原始页树 SHA 与规范化件 SHA；损坏或参数漂移拒绝覆盖；
- 全路由完成前不写“完成” manifest；标题正则只写宽召回队列，`e1_gate_closed=false`。

### 3. 原件、合同与读回

- 原件按公告 ID 去重，跨证券同公告保留全部路由身份；PDF/HTML 以实际魔数识别并存 SHA；未知媒体、不可得或内容漂移显式失败；
- 合同队列不得从标题推断文档角色、A1 原因、规则、方案或首次性；正文未核统一 `UNPROVEN_BODY_CONTRACT_PENDING`，原件缺失为 `FAIL_ARCHIVE_COMPLETENESS_UNPROVEN`；
- 二次读回至少 12 票，按交易所/历史板块/公告年度确定性取样，主索引与新 API 响应的公告 ID 集合、排序和规范化行须三重恰等。

## 四、验证

```text
verify_delist_warning_announcement_index: 42/42 PASS
verify_delist_warning_routes: 4/4 PASS
verify_code_size: PASS; files=238, lines=35392, functions=1040, debt_files=20, debt_functions=50
verify_architecture: PASS; modules=169, edges=372, cross_experiment_debts=2
py_compile: PASS
git diff --check: PASS
```

攻击面包括：路由身份/排序、orgId 空/重、混票、时间越界、页内/跨页重复、空页 `hasMore`、API 总数不等与漂移、成功页响应漂移、损坏 done 件覆盖、原件未知媒体、合同标题旁路、独立读回不等与少于 12 票。

## 五、阿里云执行顺序（推送后）

1. 只读导出路由并核 `transaction_read_only=on`、765/646/560/205、事件键 SHA；
2. 串行运行元数据全集，完成条件为 646 路由恰等成功、errors 为空；
3. 物化宽召回原件并登记所有失败；
4. 生成证据合同待核队列，保持 E1 未闭；
5. 至少 12 票独立二次读回；
6. 汇总逐交易所/历史板块/公告年度守恒与二元结论后停交验点。

若官方接口、orgId、分页、原件或读回任一硬门失败，保留部分目录与错误日志并停下，不换关键词代理、不生成事件或 G2 起点。

## 六、停止线

本地阶段零数据库连接或写入、零全量公告采集、零利润 PIT、零事实表/视图、零终版 PAP、零密封/冻结、零 StudySnapshot/manifest、零收益读取/运行/persist；exp18/21/23 未恢复。

## 七、阿里云启动期补正

推送后首次宿主 Python 启动因缺 `psycopg` 在导入期停止，未建立数据库连接；改用既有钉版镜像提供运行时并只读挂载 HEAD 后，连接从参数级带 `default_transaction_read_only=on` 成功建立，但第一条 `SHOW transaction_read_only` 因 `dict_row` 被位置索引 `[0]` 而 `KeyError` 停止。该轮只执行 `SHOW`，未读取业务表、未写库、未生成路由件。

最小补正把读回改为字段名 `transaction_read_only`，并新增合法 `on` 与非法值拒绝两条 fixture；路由 fixture 由 `4/4` 增至 `6/6`，公告 fixture仍 `42/42`，规模闸门更新为 `238文件/35408行/1041函数/债务不增`，架构闸门仍 `169模块/372边/横向债务2`。补正不改路由规则、参考数、数据库权限或采集逻辑。

第二次路由尝试已通过只读门、两恒等式与 765/646/560/205 全部数值硬闸，但 `snapshot_batch` 失败。独立只读分布确认视图 18,868 行的真实字段值均为字面量 `batch7`，实现误写为 `"7"`；现只把参考字面量与 fixture 同步为 `batch7`，保留批次恰等断言，不改任何计数或选择规则。
