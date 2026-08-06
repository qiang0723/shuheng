# exp19 `dividend_surprise` persist 终令

日期：2026-08-06（UTC+8 / Asia/Shanghai）

> John 授权原文：
>
> 批准 exp19 dividend_surprise persist 并闭卷。前置断言按 Fable 终稿执行，三件原件
> SHA 全值分别为：
> result=a3ecc0f7f47283a6c642f8e34b31a3487e1b03695ec1d32fb5a8dd3c603c2389；
> report=cff1b183c84c38ad1084126cc02e78a06ce537e2c99dff0014547089053134ae；
> log=96b1a362fd36f050de3726cf2cf06b644a074909922ca67b6946bba6a8c2a4fd。
> 使用 taosha_app 同连接单事务，FOR UPDATE复核后执行
> start_running(19)→finish(19,已验收result原件)→一次COMMIT。persist后应为
> done/NOT_SIG，台账26=7/2/15/2。
> 校准册第十一条固定为：密封原文「正，把握度60%」→实测方向为负，方向未命中；累计
> 5命中/6未命中。闭卷读法及2024右界、辅助统计NFV两项按Fable复核意见执行。完成停交验点，
> 不重跑、不追加敏感性分析。

Fable 对 §7 交付的限域复核结论为：`A级0 / B级0 / C级2 → 通过，可进入 persist`。

## 一、事务前只读断言

任一不符立即停止，不写库、不修补：

1. 三件原件 SHA256 与授权原文全值逐字相等；
2. exp19 仍为 `frozen`，`frozen_at=2026-08-06 17:21:15.889471+08`不变，
   `result_json/done_at`为空；
3. 数据库 PAP canonical=
   `4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`；
4. manifest398 权威行、qbase 镜像、publication attestation 三处 digest 均为
   `94ee4a5e88a6a6927506d902260f75fcf88a979be97569e8056fd9705bebd0be`，
   完整16键向量不变；
5. result 顶层 verdict=`NOT_SIG`，事件=`5,055`、N_valid=`3,810`、主窗N=`3,805`、
   signed CAAR=`-0.002804575188488496`、ADJ-BMP=`-0.21553616523859276`；身份、
   PAP、manifest与selection SHA锚均正确，递归 verdict 恰一个；
6. 台账26行，分布=`registered7/frozen3/done14/closed2`。

## 二、persist 执行

使用 `taosha_app` 同连接、同一事务：

1. `FOR UPDATE` 锁定 exp19 后重验 frozen、双槽空与 PAP canonical；
2. 仅走既有状态机 `ledger.start_running(19)`；
3. 仅以已验收 result 原件解析对象调用 `ledger.finish(19, result)`；
4. 一次 `COMMIT`；任一异常整笔回滚。

禁止研究重跑、原件改写、PAP或manifest改写、旁路SQL、新增experiment行及敏感性分析。

## 三、persist 后核验

1. exp19=`done/NOT_SIG`，库内 result 与原件 `parsed_equal`，canonical 双侧一致；
2. `frozen_at`、PAP canonical、manifest398三处digest与三件原件SHA均不变；
3. 台账仍26行，分布恰为 `registered7/frozen2/done15/closed2`；
4. 身份水印、PAP锚、manifest锚、selection SHA与递归唯一 verdict 均不变。

## 四、校准册第十一条

密封原文逐字为“正，把握度60%”，仅押主窗 `[0,+4]` signed 市场调整后 CAR 方向，
绑定上述 PAP digest，不押幅度或统计显著性。实测 signed CAAR 为负，故方向未命中；
校准累计为 `5命中/6未命中`。

## 五、闭卷固定读法

1. 顶层=`NOT_SIG`，不得认定分红意外存在正向或负向效应；
2. 朴素 t=`-2.570`与 Corrado=`-2.190`虽名义显著，与日历法同为
   `NOT_FOR_VERDICT`，不得引作效应证据；
3. 剔除率24.63%集中于2024研究期尾部，系冻结60日稳健窗与数据右界交互所致，
   不构成年度效应或事件质量差异；
4. `current=0→-100%`离散规则及其他冻结口径不得事后调整；效力保持
   `llm/prescreen`；τ0仅为价格观察，不得读作可执行策略。

## 六、停止线

完成 persist、后核验、取证、交付档与 STATE 后停工；不得追加复核、重跑、参数调整或
敏感性分析。
