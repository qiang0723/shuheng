# exp17 `earnings_flash_gap` · persist 闭卷交付

日期：2026-07-31（UTC+8）

结论：exp17 已经既有状态机单事务 persist，终态为 **`done/NOT_SIG`**；正式闭卷。
零研究重跑、零原件改写、零旁路 SQL、零新增 experiment 行。

## 1. 授权与前置

John 授权原文：

> 批准 exp17 persist，并按“校准册第十条、方向命中但不显著、累计5命中/5未命中”的固定读法正式闭卷。

F-first 终令=`earnings-flash-gap-persist-order-2026-07-31.md`，commit `719817b`。

事务前只读断言 `30/30 PASS`：

- result/report/log SHA256 分别为
  `a5249ec4554aff2476bc33b33b2e2600dd7cdcba01a0c98fb04e27a382394db7`、
  `cb29f575f9ef4a607852df518c44e8db8c542b60e63613fe51c90a3bd6878745`、
  `daa31bb87e072d73678baf0d5e51f5af757d6ced0737ce6e9d750f3babc7b489`；
- Fable B 项补证 JSON SHA256=
  `386759c2fec7a6a5a7bdff9f365a8eae6c522a81e828a7aad32d4278481824c2`；
- exp17=`frozen`，`frozen_at=2026-07-30 22:36:24.132972+08`，结果双槽空；
- PAP canonical=
  `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`；
- manifest363 三处 digest=
  `2e6f25863fb2f41b3f781c971c325456fe045a4602d1e9175a03828e4d70380b`；
- result 的唯一 verdict、身份水印、2,529事件、up997/down1532、selection SHA、
  主窗全精度值、逐 τ 守恒与 N_eff 全精度全部命中；
- 台账26=`registered8/frozen3/done13/closed2`。

前置环境 attempt1/2 均因容器用户无权读取新建的 root 取证目录而在 Python 启动前退出，
未连数据库、零写入；失败痕迹保留。后续仅以 host root 读取取证目录，数据库身份仍为
`taosha_app`/只读身份，正式前置通过后才进入事务。

## 2. 单事务 persist

时间：`2026-07-31T00:14:21.458502836+08:00`至
`2026-07-31T00:14:22.144945464+08:00`。

在 `taosha_app` 同一连接、同一事务内：

1. `FOR UPDATE` 锁 exp17 行并再次断言 frozen、结果双槽空、PAP/manifest/台账不变；
2. `ledger.start_running(17)`；
3. `ledger.finish(17, 已验收result原件)`；
4. 一次 `COMMIT`。

persist phase 只执行一次，无失败事务、无自动重试。

## 3. persist 后只读核验

后核验 `18/18 PASS`：

- exp17=`done/NOT_SIG`，
  `done_at=2026-07-31 00:14:22.058089+08`；
- 库内 result 与原件 `parsed_equal=True`；canonical result SHA 双侧同为
  `5435e212d0cd9a6976548d1201a7306c9f863142efd9a7cf6ab3b90edae42b7b`；
- 身份仍为
  `exp17/earnings_flash_gap/trial1/llm/prescreen`，递归 verdict 恰一个；
- `frozen_at`、PAP canonical、manifest363 三处 digest 均不变；
- 台账仍26行，恰迁一行为
  `registered8/frozen2/done14/closed2`；
- result/report/log 与补证 JSON 的 SHA 全部不变。

取证目录=`/root/s17persist/`；12项 `SHA256SUMS -c` 全部通过，13类秘密扫描
`TOTAL_HITS=0`。preassert/persist/postverify 日志 SHA256 分别为
`736509dcc3284498d405ae73df8ba4f252c0661dc00e8da4085479082b8d3603`、
`5298f31d2babcb9fdffd9e13e0766255c318439c276da6dac45df746523e57be`、
`a27579edaaff3f2d3135c273c684211e10c83b8f00eb142daca9fa4d891658e5`。

## 4. 校准册第十条与固定读法

密封预判原文为**“正，把握度80%”**，仅押主窗 signed 市场调整后 CAR 方向，
不押幅度或统计显著性，绑定上述 PAP digest。

实测主窗 signed CAAR=`+0.1649%`，方向命中；ADJ-BMP=`+0.278` 双侧不显著，
顶层 `NOT_SIG`。闭卷固定表述为：**方向命中但不显著**，不得合写为“预判命中且显著”。

校准册据实登记为**第十条**，累计方向读数为**5命中/5未命中**：

- 命中：exp8、exp12、exp24、exp568、exp17；
- 未命中：exp20、exp13、exp11、exp10、exp16。

不得认定存在可靠的业绩快报超预期或低预期效应；朴素 t、Corrado、日历法、次级窗、
稳健窗、raw direction 与可交易口径全部是 `NOT_FOR_VERDICT`。剔除率27.20%、行业
unknown 9.40% 告警如实保留。效力维持 `llm/prescreen`，不得写成 human/full 或足额证据。

## 5. 终止线

exp17 全链行政与技术闭卷。不再追加重跑、敏感性分析、参数调整或施工；下一研究任务
另行排产。
