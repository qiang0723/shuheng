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
