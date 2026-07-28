# exp24 sox_spillover persist 终令 · 人令留痕（2026-07-28）

> 人在 §7 结果与外部复核意见交验后明示：**“执行”**。本令授权范围仅为将已验收 result 原件经既有状态机单事务 persist，并完成闭卷核验与留痕；不授权重跑、改写结果或追加敏感性分析。

## 唯一输入与前置断言

- result 原件：`/root/s24run/out/result_exp24.json`，SHA256=`991016a0c43b26639498e2f377d8597b2ea1e4589efb7de118c150e50dc4fdb8`；
- exp24 仍为 `frozen`，`frozen_at=2026-07-28 19:43:43.332816+08`，`result_json/done_at`为空；
- DB PAP canonical=`be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`；
- manifest 248 权威行、qbase 镜像、publication attestation 三处 digest 均为 `c82d8a82eb69331799402ce9f025c35574a27ba8b3d6f2051dfaa1b8c881250a`；
- result 关键值：顶层唯一 verdict=`NOT_SIG`、事件 `19,258`、`N_valid=13,703`、主窗 `N=13,656`、signed CAAR=`0.0033051753367197385`、ADJ-BMP=`0.5646755577681967`；
- 主窗 N 与 N_valid 差 47 的既有披露位置：`result.per_tau.by_tau` 与正式报告逐日 AR 段；完整主窗按 `_car_test` 既有口径，任一 τ 缺失即不进入 CAR 截面，不作新计算或补写；
- 台账 25 行，分布应为 `registered 12 / frozen 3 / done 9 / closed 1`。

任一不符立即停止，不修补、不重跑。

## 执行与闭卷

仅以 `taosha_app` 同连接单事务执行 `start_running(24)→finish(24, 已验收result原件)→一次COMMIT`；零重跑、零改写、零旁路 SQL、零新增行。

persist 后只读核验：exp24=`done/NOT_SIG`；库内 result 与原件 `parsed_equal` 且 canonical 双侧一致；台账仍 25 行、分布应为 `12/2/10/1`；manifest 248 三处 digest、PAP canonical 与三件产物 SHA 均不变。

闭卷固定读法：人的冻结预判原文“同向，把握度60%”仅绑定上述 PAP digest；实测主窗 signed CAAR 为正，方向命中，但 ADJ-BMP 不显著，终态 `NOT_SIG`。不得据此认定存在可靠的 SOX→A股半导体链传导效应；朴素 t/Corrado/日历法均为 NOT_FOR_VERDICT。效力保持 `human/full`，半 PIT 成分语义与剔除率告警如实保留。

完成后更新交付档与 STATE，提交并同步，停工交终签；不再追加重跑或敏感性分析。
