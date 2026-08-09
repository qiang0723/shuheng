# exp14 `ex_div_gap` · persist 与正式闭卷终令

日期：2026-08-09（UTC+8 / Asia/Shanghai）

> John 在 §7 独立复核通过后亲自授权：
>
> 批准 exp14 ex_div_gap persist 并正式闭卷。以前置只读断言确认 PAP、manifest432及三件原件不变；
> result=5ef3a3137b769092bc09b9f0b7cefd0ebc8480f98b4b74193babd9f05ac51a33，
> report=8e36af391d33f448e256d614692a88fc6a7d2e66ab1f541d998f777002620a0c，
> log=cc5a51cf3f3fe20e3e8b4b07653c684740808111bc777c4ac99e362cf384d730。
> 使用 taosha_app 同连接单事务执行 start_running(14)→finish(14,已验收result原件)→一次COMMIT；
> persist 后应为 done/NOT_SIG，台账26=6/2/16/2。校准册第十二条固定为：密封原文
> 「正，把握度60%」→实测方向为负，方向未命中；累计5命中/7未命中。闭卷读法按Fable意见执行，
> 包含辅助三法NFV及两处报告文字注记。不重跑、不覆盖原件、不追加敏感性分析。完成停交验点。

Fable §7 复核结论：`A级0 / B级1(记Fable账上) / C级2 → 运行通过，两处文字错位均不阻塞
persist`。两项 C 级按建议只进入闭卷固定读法，不开代码或报告重渲染单元。

## 一、事务前只读断言

任一不符立即停止，不写数据库：

1. exp14 身份须为 `ex_div_gap/trial1/llm/prescreen`，状态仍为 `frozen`，
   `frozen_at=2026-08-09 14:33:15.200827+08`不变，`result_json/done_at`为空，addendum=0；
2. 库内 PAP canonical 须为
   `a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；
3. manifest432 在 taosha 权威行、qbase mirror 与 publication attestation 三处 digest 均为
   `94ee4a5e88a6a6927506d902260f75fcf88a979be97569e8056fd9705bebd0be`；content 键集恰等
   13个 qbase 键与3个 taosha 键，值与 §7 运行令一致；
4. `/root/s14run/` 三件原件 SHA256 须分别为：
   - result `5ef3a3137b769092bc09b9f0b7cefd0ebc8480f98b4b74193babd9f05ac51a33`；
   - report `8e36af391d33f448e256d614692a88fc6a7d2e66ab1f541d998f777002620a0c`；
   - log `cc5a51cf3f3fe20e3e8b4b07653c684740808111bc777c4ac99e362cf384d730`；
   `SHA256SUMS -c`须全过；
5. result 原件须为顶层 `verdict=NOT_SIG`，递归 `verdict` 恰一处；PAP、manifest、台账身份水印、
   选择 `4,035/1,083/ef9529b1…7f2f` 均命中；主窗 CAAR=
   `-0.018488168100005337`、ADJ-BMP=`-0.9132553766202723`；
6. 台账须为26行，分布 `registered=6/frozen=3/done=15/closed=2`。

## 二、唯一写事务

只允许 `taosha_app` 同一连接、同一事务：

1. `SELECT ... FOR UPDATE` 锁定 exp14，并在事务内重新执行第一节全部数据库与原件断言；
2. 调用既有 `ledger.start_running(14)`；
3. 调用既有 `ledger.finish(14, 已验收 result.json 解析对象)`；
4. 一次 COMMIT。

禁止手写旁路 UPDATE、触碰其他实验、修改 PAP/manifest/addendum、重跑研究、重渲染报告、覆盖原件或
追加敏感性分析。任一事务内断言失败则整体 ROLLBACK 并停止，不自动重试。

## 三、事务后核验

- exp14=`done`、顶层 verdict=`NOT_SIG`，`done_at`落在事务时间窗内；`frozen_at`与 PAP 不变；
- 库内 `result_json` 与 result 原件解析全等，canonical 双侧一致；身份水印与递归 verdict 唯一；
- 台账26=`registered6/frozen2/done16/closed2`，恰迁一行；
- manifest432 三处 digest/content、三件原件 SHA、证据目录均不变。

## 四、校准册第十二条与闭卷固定读法

1. 密封原文逐字为「正，把握度60%」，只押主窗复权市场调整 CAR 方向，不押幅度或显著性；实测主窗
   CAAR 为负，故记“方向未命中”；累计 `5命中/7未命中`；
2. 顶层 `NOT_SIG`：不得认定实际高送转除权存在可靠正向或负向异常收益；朴素t、Corrado、日历法
   虽同向负且名义显著，全部为 NOT_FOR_VERDICT，不得引作效应证据；簇日相关正是 ADJ-BMP 为唯一
   判决权威的理由；
3. snapshot375 三值原为冻结前参考，但已由本次 §7 令与 driver 升格为收益前双层硬闸并两度通过；
4. 通用删失标题“ST=已剔除层”是静态旧措辞；exp14 实际 `st_policy=keep`，ST有效24个事件在主样本内；
5. 主 CAR 使用复权总回报；不得把本结果读作“不复权名义价格幻觉已证实”，raw 跳空与因子比仅为NFV
   机械审计；一字板/涨跌停为价格观察，不得读作可成交收益或策略；
6. 效力为 `llm/prescreen`，不因任何统计结果升级；行业unknown、21.61%剔除率、N_eff坍缩与2024
   全剔如实保留。

完成事务、后核验、校准册与闭卷档后停止，不追加复核循环。
