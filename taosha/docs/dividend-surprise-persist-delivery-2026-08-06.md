# exp19 `dividend_surprise` persist 与正式闭卷交付

日期：2026-08-06（UTC+8 / Asia/Shanghai）

结论：**exp19 已按既有状态机单事务 persist，终态=`done/NOT_SIG`，正式闭卷。**

## 1. 授权与前置断言

- John persist 终令=`dividend-surprise-persist-order-2026-08-06.md`，F-first commit=
  `644cc46`；
- 事务前只读断言=`49/49 PASS`：三件原件 SHA、exp19冻结状态、PAP canonical、
  manifest398三处digest与16键向量、result关键值、selection SHA及台账
  `26=7/3/14/2`全部精确符合终令；
- 前置时间=`2026-08-06 21:22:31+08`，任一停止线均未触发。

## 2. 唯一写事务

- `taosha_app`同连接，事务内 `FOR UPDATE` 与结果断言=`44/44 PASS`；
- 仅走既有状态机
  `ledger.start_running(19) → ledger.finish(19, 已验收result原件) → 一次COMMIT`；
- 事务窗口=`2026-08-06 21:22:46+08`至`21:22:47+08`，
  `done_at=2026-08-06 21:22:47.003057+08`；
- 零研究重跑、零原件改写、零旁路SQL、零新增experiment行、零敏感性分析。

## 3. persist 后核验

后核验=`53/53 PASS`：

- exp19=`done/NOT_SIG`，`frozen_at=2026-08-06 17:21:15.889471+08`不变；
- 库内 result 与原件 `parsed_equal=True`；canonical result SHA256 双侧均为
  `85a71163b4eb59ccb84133bae36569a95da183b255d42815ea0e32bc746230c2`，
  库侧 result MD5=`40fd715ec896af4c5beb400ca326c6f6`；
- 台账仍26行，分布恰迁为 `registered7/frozen2/done15/closed2`；
- PAP、manifest398三处digest、16键向量、selection SHA、身份水印与递归唯一 verdict
  均不变；
- 三件正式运行原件 SHA 保持：result=`a3ecc0f7…c2389`、report=
  `cff1b183…134ae`、log=`96b1a362…2a4fd`；
- 阿里云代码 HEAD=`b623f6dbdd5c37c020b7ce94c94a0070db19450e`，工作树净。

## 4. 校准册第十一条

密封原文为“正，把握度60%”，仅押主窗 `[0,+4]` signed 市场调整后 CAR 方向，
不押幅度或统计显著性，绑定 PAP digest
`4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`。
实测主窗 signed CAAR=`-0.002804575188488496`，故**方向未命中**；累计校准为
**5命中/6未命中**。

## 5. 闭卷固定读法

1. 顶层=`NOT_SIG`，不得认定分红意外存在可靠的正向或负向效应；
2. 朴素 t=`-2.570`与 Corrado=`-2.190`虽名义显著，与日历法同为
   `NOT_FOR_VERDICT`，不得引作效应证据；
3. 剔除率24.63%集中于2024研究期尾部，系冻结60日稳健窗与数据右界交互所致，
   不构成年度效应或事件质量差异；
4. `current=0→-100%`及其他冻结口径不得事后调整；效力保持 `llm/prescreen`；
   τ0仅为价格观察，不得读作可执行策略。

## 6. 取证与停止线

- 取证目录=`/root/s19persist/`；14件纳入 `SHA256SUMS`，清单 SHA256=
  `de61fcabf10172ab5728da7ae5a86106f8e4733b874832ad2c642b4d8cd85ecd`，
  `sha256sum -c`全过；
- 13类秘密扫描=`TOTAL_HITS=0`；persist脚本 SHA256=
  `38b0fece2cb3f7d07ffb4c1ffde635bf14d54a61c5e6bcad1bedc1bf15c8cc99`。

exp19 至此正式闭卷，不再追加复核、重跑、参数调整或敏感性分析。exp18 继续停在既有
首次披露语义硬门。
