# exp22 公告索引 v6 · `IncompleteRead` 网络重试窄修交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

本地窄修与攻击验收通过。生产行为变化只有两项：

1. `http.client.IncompleteRead` 进入 `cninfo._retry()` 既有三次整请求重试；残缺响应不解析、
   不保存、不进入双读集合。
2. 新运行布局由 `bisect_v5` 前移至 `bisect_v6`；v5 只读纳入 marker 自验与不覆盖攻击。

双读、日期二分、单日多页、结构性错误、重试次数、退避和串行限流均未改变。

## 二、失败锚与停止状态

v5 于 `2026-08-10 19:58:04+08` 在 `000155.SZ` 的
`2024-04-27..2024-04-29/pass_a` 请求读取过程中抛出
`IncompleteRead(13652 bytes read)`；该响应未写成原始页。容器 exit=`1`，监督日志为
`metadata_v5_exit=1`，停止点：

```text
valid_done = 17/646
bisect_v5_reads = 3469
errors = 5
downstream = 0
metadata_v5.log sha256 = 0001ff114d1936a7c3124265e1e9357cfc72ef495d64c94bf1263d60523df7b7
pipeline_supervisor_v5.log sha256 = a7c85fe9b6ded0ced06d2158531e8a0357460da10ce3090679e4a35aedf2ddfc
errors.jsonl sha256 = 81daeabf94632ae82bc4a3626dbefbccc1d8628f54ad4863a90d54a30c410ea5
```

监控已暂停，未自动重启；旧 v1/v2/v3/v4/v5 失败容器、页树、日志和 17 个合法 marker 保留。

## 三、攻击与回归

以仓内 Python 3.12.13 执行：

```text
verify_delist_warning_announcement_bisection    = 32/32 PASS
verify_delist_warning_announcement_localization = 6/6 PASS
verify_delist_warning_announcement_index        = 42/42 PASS
verify_delist_warning_routes                    = 6/6 PASS
verify_code_size = PASS; files=241, lines=35987, functions=1089,
                   debt_files=20, debt_functions=50
verify_architecture = PASS; modules=172, edges=377, cross_experiment_debts=2
py_compile = PASS
git diff --check = PASS
```

新增攻击让前两次调用抛 `IncompleteRead`、第三次返回完整响应；实测恰三次尝试、两次既有退避。
v5 失败页不覆盖和 v5 合法 marker 自验同时进入二分 fixture。

本机系统 `python3` 为 3.9，首次导入在既有 `X | None` 类型注解处退出；随后改用仓内 Python
3.12.13。该失败发生于测试导入期，零网络、零数据库、零远端状态变化，未据此修改生产代码。

## 四、提交与下一步

```text
d42f976 docs: authorize exp22 incomplete read retry
2338ade fix: retry incomplete cninfo responses
```

下一步已由同一授权覆盖：推送、阿里云精确 fast-forward、远端复验；启动前基线必须为
`routes646 / valid_done17 / first_pending 000155.SZ / v5_reads3469 / errors5`，随后以全新受限
v6 容器与监督链续跑。任一不符即停，不删除旧证据、不自动重启。

E1 继续为 `OPEN_FAIL_CLOSED`；零数据库写入及零研究状态变化。

## 五、GitHub 推送、远端复验与 v6 续跑

1. GitHub `origin/main` 已推进至
   `67a21660a872cbf26cc819c05d3af560ad0ce84d`；阿里云 `/opt/quant` 在先验干净后精确
   fast-forward 至同一提交并保持干净。
2. 远端钉版镜像 `shuheng-quant:579a354` 内重跑：二分 `32/32`、定位 `6/6`、索引
   `42/42`、路由 `6/6`，规模与架构通过。首次 `py_compile` 因只读 rootfs 无法写仓内
   `__pycache__` 而退出；未放宽只读保护，改用 `PYTHONPYCACHEPREFIX=/tmp/pycache` 指向
   tmpfs 后通过。
3. 新代码按 `1991-01-01..2024-06-30` 独立验证 marker：
   `routes=646 / valid_done=17 / first_pending=000155.SZ / layout=bisect_v6`；另读回
   `v5_reads=3469 / v6_reads=0 / errors=5`。全部命中才启动。
4. 新容器 `s22-ann-index-v6` 于 `2026-08-10 21:13:06+08` 启动，容器 ID 为
   `600b5dacca1f3a333f18e2114b8e9b68edd3ca29ac133b512f86130af44d363b`；钉版镜像、
   只读 rootfs/代码、证据目录唯一可写、`cap_drop=ALL`、零数据库凭据。
5. 监督 PID=`790687`；脚本
   `/root/s22announcement/pipeline_supervisor_v6.sh` SHA256=
   `f144d8c7a544442643a68e525b8d3a955509fc269c2d95226d8bfe10f33886e7`。只在 metadata
   exit=`0` 后依次启动 documents、UNPROVEN contract queue 与 12 票独立读回。
6. `21:13:19+08` 首读：v6 容器 `running`，合法 marker=`17/646`，v6 新读取件=`9`，
   v5=`3469`、errors=`5` 均未变化，下游零启动。
7. 十五分钟 UTC+8 heartbeat 已切换至 v6 并恢复 `ACTIVE`；仅在实质进度、阶段切换、失败
   或全完成时回报，任一非零即报告并暂停，禁止自动重启。

本节完成后，exp22 处于“v6 续跑中”；不作废 v1–v5 失败证据、17 个合法 marker 或原工程
停止线。
