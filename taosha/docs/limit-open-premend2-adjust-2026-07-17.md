# exp8 冻结前回修二次执行令 · 中途调整裁决(人 2026-07-17,原文即口径,F 条留痕)

> 上承 `limit-open-premend2-order-2026-07-17.md`。人已验收:状态闸与撤回留痕通过
> (exp8 确为 registered;未冻结/未 manifest/未运行/未写 result;原 PAP、原预判及原验收结论
> 已显式作废;commit `92bff23` 处置正确)。允许继续冻结前回修;**被拦下的 _assemble 编辑
> 不得原样恢复,按下文要求调整**。

---

以下为人令原文,逐字:

---

状态闸与撤回留痕验收通过:
exp8确为registered;
未冻结、未生成manifest、未运行、未写result;
原PAP、原预判及原验收结论已显式作废;
commit 92bff23的处置正确。
允许继续冻结前回修,但刚才被拦下的_assemble编辑不得原样恢复,先按以下要求调整。

一、C1方案维持
postpone_policy显式参数化方向正确:
默认legacy保持既有实验逐字节行为;
exp8使用unified;
unified下,从T+1起纯停牌、一字板及混合状态统一顺延;
1日、5日保留,6日以postpone剔除;
T事件日本身缺行或异常状态单列event_day_anomaly并fail-closed。
同步修正文案及审计字段:
unified路径的notes不得继续只写"一字板顺延",应写"不可交易状态顺延"并列明停牌/一字数量;
result audit须记录实际postpone_policy;
默认legacy输出不得新增键或改变旧notes。

二、bias_statement不得成为可自由覆盖的函数参数
P1-4要求正式报告消费冻结PAP,不是让driver再传一份可能不同的文字。
因此:
权威来源唯一为pap["bias_statement"];
runner/result直接从PAP读取并原样携带;
report直接消费result中已锚定的该字段;
不得允许调用方通过独立bias_statement=参数覆盖PAP;
如工程上保留该参数,只能用于逐字相等断言;与PAP不等立即fail-closed,不能作为第二来源;
exp8新策略启用但PAP缺bias_statement时必须拒绝运行;
默认旧路径继续渲染原固定段并保持逐字节不变。

三、诊断层不得在内部计算影子verdict
仅删除sig_state_report_only输出还不够。如果诊断路径仍调用_verdict(),只是把影子判决算完后藏起来,仍不符合C6。
要求:
exp8两个诊断维度的计算路径不得调用_verdict();
不得产生SIG、NOT_SIG、AMBIGUOUS、INSUFFICIENT等分类;
只计算并报告预注册统计量、样本数和剔除分解;
_stats_for_subset()若仍服务既有实验,可保留旧默认行为;
exp8诊断必须使用独立的report-only统计路径,或显式compute_verdict=False且结构上证明未调用判决函数;
fixture须通过monkeypatch或等价攻击证明:诊断路径调用_verdict()即失败。

四、"两个正交维度"是两条独立轴,不是四格交叉实验
本轮只要求:
listing-age轴:recent_listing / seasoned
ST轴:ST / non-ST
要求:
两轴分别报告;
不自动扩成recent×ST四格交叉统计;
不产生四个额外样本检验或隐性多重比较;
如audit需要可记录二维计数矩阵,但只能是计数核对,不计算CAR、显著性或判决;
不复用forecast的type_strata文案、标签或"正负漂移抵消"解释。
exp8应关闭forecast专属type_strata消费,再由新diagnostic_dimensions输出两条独立诊断轴。若使用strata_enabled=False,其注记不得写成"#2b单信号事件",应参数化为与exp8一致的中性说明。

五、零存活状态必须按真实原因命名
不能把所有空层都写成UNESTIMABLE_BY_FROZEN_COVERAGE。
按以下规则:
n_events_total=0:输出NO_EVENTS_IN_LAYER;
n_events_total>0、n_valid=0,且确因冻结覆盖/历史门槛无法估计:输出
UNESTIMABLE_BY_FROZEN_COVERAGE;
若零存活由listing异常、停牌、顺延超限或多种清洗原因共同造成:输出
UNESTIMABLE_AFTER_FROZEN_CLEANING,并给出逐因、逐年分解;
n_valid>0:输出统计块,不产生任何状态判决。
recent_listing即使零事件或零存活,块也必须在场,但状态名称不得虚假归因。

六、field_roles必须完整覆盖,不只列几个字段
主窗唯一判决权为adj_bmp_car。字段角色元数据须至少明确:
adj_bmp_car:VERDICT_AUTHORITY
naive_t、bmp_car、caar及辅助统计:NOT_FOR_VERDICT
taus、n等:CONTEXT
要求:
角色映射与实际字段集合逐项对账;
出现未分类的新统计字段时fail-closed或测试失败;
不能只在结果末尾列一份块名清单;
report中非权威统计段也必须直接带NOT_FOR_VERDICT标记。

七、接下来的施工顺序
按以下顺序继续:
完成_assemble对新策略的实际消费;
result落diagnostic_dimensions、PAP来源的bias_statement、完整field_roles和审计参数;
report消费新偏差声明并渲染两个独立诊断轴;
重写C1错误fixture,新增纯停牌1/5/6及混合5/6;
新增C3三态fixture:有存活;
有事件但覆盖归零;
本层零事件;

新增C6攻击测试:诊断路径禁止调用_verdict();
result递归唯一顶层verdict;
零sig_state_report_only及等价判决字段;
field_roles无漏项;

新增P1-4报告对账:新声明逐字来自PAP;
旧保守下界措辞零命中;
默认旧报告逐字节不变;

生成新PAP版本文件、新digest及原新逐键diff;
跑专项测试及全家福;
更新验收档和STATE后停在交验点。

八、边界维持
继续禁止:
写driver;
读取收益、CAR或显著性正式结果;
生成manifest;
冻结exp8;
写台账;
正式运行;
修改原PAP文件;
重开C2、C4、C5或adj_bmp_main_only;
把诊断层扩成通用分层平台。
完成后只交新PAP、代码diff、fixture、报告样例和零回归实物,等待重新验收及新人冻结句。
