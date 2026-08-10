# exp22 公告索引 v5 · 双读漂移定位窄修交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

本地窄修验收通过，停在推送与阿里云重启授权点。生产改动仅涉及日期二分读取器和公告索引
新布局常量；新写入固定为 `bisect_v5`，v1/v2/v3/v4 均只读保留。

## 二、规则实现

1. `_LeafMismatch` 只标记 pass A/B 分页状态不一致或规范化全集不一致；只有该类型且区间多于
   一日时，才保留父区间两件原始响应并按日期中点继续二分。
2. 父区间两次读取计入 `raw_reads`，但其任一集合均不进入输出；输出只由各子叶重新独立双读
   完全一致的规范化行组成。
3. 单日单页双读仍不一致时原异常继续上抛；单日多页继续执行 v4 双遍完整分页。
4. pass B 声称非终页但不足 30 行时属于结构性错误，立即停止而不进入二分。混票、越界、重复、
   计数不闭与页数超限同样不被定位逻辑捕获。
5. `SUPPORTED_LAYOUTS` 新增只读 `bisect_v4`，既有 v4 marker 可继续按其原页树 SHA 自验。

不存在第三次同区间重试、交集/并集、多数表决、父集合下传或 retry-until-equal 路径。

## 三、攻击与回归验收

```text
verify_delist_warning_announcement_bisection   = 30/30 PASS
verify_delist_warning_announcement_localization = 6/6 PASS
verify_delist_warning_announcement_index       = 39/39 PASS
verify_delist_warning_routes                    = 6/6 PASS
verify_code_size = PASS; files=241, lines=35956, functions=1087,
                   debt_files=20, debt_functions=50
verify_architecture = PASS; modules=172, edges=376, cross_experiment_debts=2
py_compile = PASS
git diff --check = PASS
```

定位专项实证：多日集合漂移与合法分页状态漂移均确定性分为两个子叶，父双读与子叶双读合计
`6` 件并守恒；结构性短页不被二分掩盖。原 fixture 首次达到 315 行被规模闸门拒绝，定位场景随后
拆入独立 110 行 verifier，生产行为未因拆分改变。v4 失败证据不覆盖与 v4 合法 marker 自验均有
攻击用例。

## 四、停止线

当前本地提交为 `aaadf53`；零 GitHub 推送、零阿里云 fast-forward、零新容器、零监督恢复。
远端保持 v4 exit=`1`、`done=10 / v4_reads=494 / errors=4 / downstream=0`，监控保持暂停。
继续须 John 另令。E1 仍为 `OPEN_FAIL_CLOSED`。

## 五、推送与续跑授权

交付明确列出的唯一下一步为：“推送三笔提交，阿里云精确 fast-forward、远端复验后以全新 v5
容器从 `10/646` 续跑。”John 随后回复：

> 继续

本回复据唯一指向登记为上述推送、远端精确读回、复验、v5 新容器与监督恢复授权；不扩解为
数据库写入、利润 PIT、终版 PAP、密封、冻结、StudySnapshot、manifest、收益读取、研究运行或
persist。旧 v1/v2/v3/v4 证据与四个失败容器必须保留。

## 六、GitHub 推送、远端复验与 v5 续跑

1. GitHub `origin/main` 已由 `d63b6f8` 推进至
   `0bdd5eb66edca0a7e6408a9b695e6f23fa492bd7`；阿里云 `/opt/quant` 在先验干净后精确
   fast-forward 至同一提交并保持干净。
2. 远端以钉版镜像 `shuheng-quant:579a354`、代码只读挂载重跑：二分 `30/30`、定位
   `6/6`、索引 `39/39`、路由 `6/6`，规模、架构与 `py_compile` 全部通过。
3. 启动前读回恰为 `routes=646 / valid_done=10 / first_pending=000046.SZ / v1=3 /
   v2=121 / v3=320 / v4=494 / v5=0 / errors=4`；四个旧失败容器及 v1/v2/v3/v4
   日志、失败页和合法 marker 均未删除。
4. 全新受限容器 `s22-ann-index-v5` 于 `2026-08-10 18:39:23+08` 启动，容器 ID 为
   `83c8b719b14aa724c8be36adda2c000be4e518ead7b4d0a3983aac99e6271548`；只读
   rootfs/代码、证据目录唯一可写、`cap_drop=ALL`，未注入数据库凭据。
5. 监督 PID=`786475`；脚本
   `/root/s22announcement/pipeline_supervisor_v5.sh` 的 SHA256 为
   `3ab5fe3ed6c42dc850b26ef3b3bc387104e773416e101e783a318321f4370572`。监督链只在
   metadata exit=`0` 后依次进入 document materialization、UNPROVEN contract queue 与
   12 票独立读回；任一阶段非零即停，不自动重启。
6. `2026-08-10 18:41:25+08` 首次进度读回：metadata 容器仍为 `running`，合法 marker
   仍为 `10/646`，`bisect_v5` 新读取件已由启动即刻的 `9` 增至 `93`，`errors=4` 未增，
   下游三阶段尚未启动。该状态表示当前仍在首待办证券的确定性定位读取中，不冒充 route 完成。
7. UTC+8 十五分钟只读监控已恢复为 `ACTIVE`。监控仅在实质进度、阶段切换、失败或全完成时
   回报；SSH 暂时不可达不得误判施工停止，也不得修改远端状态。

本节完成后，交付状态由“等待推送与远端续跑”更新为“v5 已启动并受只读监控”。E1 仍为
`OPEN_FAIL_CLOSED`；本单元仍未授权任何数据库或研究状态变更。
