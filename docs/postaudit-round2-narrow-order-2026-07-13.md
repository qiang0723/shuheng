# 外审第二独立视角复审结论 + 窄补施工单（人转达原文留痕）

- 日期：2026-07-13
- 性质：裁决留痕（F 条）。本文为人转达的外部第二独立视角本轮复审结论与窄补施工单，**逐字留痕**，不改写不概括。
- 复审对象：外审五项修法窗口完工态 HEAD `c4ce3c8`（五份验收档 postaudit-item{1,2,3,4,5}-*）。
- 结论：**#2/#4/#5 通过；#1/#3 退回窄补**。窄补范围严格限定于下文三条缺口。
- 本轮窄补开工前 HEAD 锚：`c4ce3c8`（两台干净）。

---

## 施工单原文

外部第二独立视角本轮复审:#2/#4/#5通过,#1/#3退回窄补。范围严格限定在以下缺口,不得扩大,不新增制度或功能,只处理三条:

#1 · 策略引擎必须真正消费strategy_execution

drawdown_strategy.py须读取校验通过的strategy_execution字段并据此选择执行路径,不得静默走旧的"同刻成交"逻辑。
若某个execution_profile暂未实现(如preclose_to_tail真实模拟逻辑尚未就绪),驱动层必须显式fail-closed拒绝运行,不能通过校验后悄悄执行旧口径兜底。
preclose_to_tail改为结构化、可解析的时间字段,代码层强制断言decision_cutoff < fill_window_start,不能停留在字符串非空判断。在日内数据不足以支撑该profile真实执行前,不得宣称该模式"已可执行"。

#3 · source_anchor需严格schema,禁止空锚,且血缘需真正相容

定义source_anchor严格schema,拒绝{}及缺失关键字段的锚。
创建manifest时,比较派生批次的qbase源向量与manifest的qbase向量,不相容拒绝生成,不只检查"是否非NULL"。
seed阶段(如seed_market_return.py)改为绑定已发布的source snapshot ID/digest,从对应快照视图读取,禁止"先记录current/max批次为锚,再多次查询current视图"这种先记锚后读取的模式,消除并发回填下"稳定复现但血缘不一致"的窗口。

新增反向测试(四项),须全部拒绝方可提交验收:

合法close_to_next_open PAP冻结后,断言实际成交确实发生在次日开盘,而非旧的同刻收盘价;
构造decision_cutoff晚于fill_window起点的反向时间窗口,断言PAP冻结被拒;
构造source_anchor={} 空锚,断言manifest生成被拒;
构造source_anchor存在但与manifest qbase向量不匹配,断言manifest生成被拒。

范围禁令:仅限#1、#3两项及以上具体缺口,不得触碰已通过的#2/#4/#5实现,不得新增制度或重构无关代码。
完成后提交本轮验收实物(现状攻击路径复述/结构修法/正向控制/反向攻击测试/权限与验收实物,五要素照旧),并请附一份git diff --stat(本轮窄补开工前HEAD c4ce3c8 → 完工HEAD),供范围合规性核对。核对通过后再转回外部第二独立视角复核

---

## 执行注记（我方，非改写）

- 承接第一轮统一范围禁令：不碰闭卷 result_json / 密封卡数值；不用 reset/checkout 回退共享区。
- 验收实物五要素照旧 + 附 `git diff --stat c4ce3c8..<完工HEAD>` 供范围合规性核对。
- 核对通过后转回外部第二独立视角复核。
