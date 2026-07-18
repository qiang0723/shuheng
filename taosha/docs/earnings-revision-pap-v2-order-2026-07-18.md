# exp20 终版 PAP 两阻断点回修令(2026-07-18 深夜三,人令原文即口径)

> 外部只读复核:终版 PAP 主体合格、范围与禁区合规;digest `94b9ba78…fa17` 暂不批准冻结,仅两个 PAP 文本阻断点。

## 人令原文

枢衡工地:
外部只读复核结论:exp20终版PAP主体合格,范围与禁区合规;但当前digest 94b9ba7821c3393e33123971f8b681e8f5d457e43c6f8bf39df9caa1f543fa17暂不批准冻结。仅有两个PAP文本阻断点。
一、flat阶段语义消歧
终版PAP须明确区分:
候选方向分类阶段:flat是合法分类结果,计入flat计数块后排除出主事件集;不得因存在flat候选而拒绝整次运行。
主事件流形成后:进入CAR及顶层verdict之前,direction必须严格属于{up,down};若flat/null/unknown或其他白名单外值泄漏进主事件流,才fail-closed拒绝运行。
同步修正event_def、diagnostic_dimensions.direction_fail_closed/note及相关报告承诺,避免"正常排除"与"整次拒跑"两种解释并存。
二、effect_alignment补成全定义函数
非verdict上下文字段冻结为:
权威ADJ-BMP统计量>0:ALIGNED
<0:REVERSED
=0:NEUTRAL
统计量不可得:UNAVAILABLE
四种状态均不得成为独立verdict或改变顶层四态判决。INSUFFICIENT/AMBIGUOUS等无可用ADJ-BMP的情形必须输出UNAVAILABLE,不得猜测方向。同步更新verdict_authority、reporting_commitments、字段角色及冻结后攻击fixture清单。
本单元范围:
只允许回修终版PAP、交付档和STATE;
不改代码、不读收益、不冻结、不建manifest、不写台账、不运行;
原PAP文件不覆盖,另建新版本并明确旧digest未冻结、已作废;
交付新canonical JSON、文件SHA/canonical digest、旧版→新版逐键diff、validate_pap及窗口解析结果;
新增攻击fixture计划至少覆盖:flat候选正常计数排除而不终止运行;
flat泄漏进主事件流时在CAR/verdict前拒绝;
ADJ-BMP正/负/零/不可得四分支;
四种alignment状态均不产生或改变verdict。

新PAP交回后再由人以新digest下冻结句并另写预判;当前digest及任何预判均不得平移。
