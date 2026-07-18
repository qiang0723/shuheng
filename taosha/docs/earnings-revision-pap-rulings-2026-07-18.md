# exp20 十项参数裁定 + signed 统计口径补强 + 终版 PAP 文本回修令(2026-07-18 深夜二,人令原文即口径)

> 外部复核结论:PAP 草案单元范围合规、禁区全守;草案主体可用但暂不构成冻结文本。本档逐字收录人裁定原文。

## 人令原文

枢衡工地:
外部复核结论:exp20 PAP草案单元范围合规,禁区全部守住;草案主体可用,但暂不构成冻结文本。现作如下裁定。
一、十项参数裁定
主检验采用双侧ADJ-BMP,沿既有adj_bmp_main_only门槛,不新增单侧统计机构。
**不批准新增SIG_ALIGNED/SIG_REVERSED verdict枚举。**顶层继续使用既有SIG/NOT_SIG/INSUFFICIENT/AMBIGUOUS:ADJ-BMP双侧过阈仍记SIG;
另设非verdict上下文字段effect_alignment=ALIGNED/REVERSED,以权威ADJ-BMP符号判定;
SIG+ALIGNED表示支持方向假设;
SIG+REVERSED表示显著证伪,不得写成支持;
NOT_SIG无论方向均表示未获统计支持;
signed CAAR与ADJ-BMP符号若不一致,必须并列披露,不得择一解释。

方向字段采用p_change_min/p_change_max,维持07-17窄闸显式口径:两边界均在时取中点;
仅一个边界在时回退该单值;
两边界全空则不可判;
同链同日多行须全部可判且标量一致,否则fail-closed;
当前值相对事件日前最近公开值:大于=up、小于=down、等于=flat;
不改用net_profit,不使用type回退。

三窗裁定为5/20/60:主窗[0,+4]唯一判决;
次级窗[0,+19]仅报告;
稳健窗[0,+59]仅报告;
理由为修正公告短窗即时定价与中长期漂移观察分离,不引用exp8作为授权依据。

**研究池与基准:**全A股、排除北交所;全市场等权基准,benchmark_mode=market。
direction诊断层展示raw AR,保留上修、下修的实际方向和强度;全部结构化NOT_FOR_VERDICT。
ST按spec §5默认剔除,st_policy=reject;不继承exp8单点例外,不增加ST诊断轴。
采用统一顺延,但改为公告事件语义:公告日是日历锚,不要求公告日本身存在个股bar;
周末、节假日公告不得因T无bar被剔除;
τ=0从ann_date之后第一个交易所交易日开始;
自该日起,个股缺bar/停牌/一字不可交易统一计入顺延;
顺延不超过5个交易所交易日保留,第6日仍不可交易则以postpone剔除;
删除草案中的"事件日T缺bar/停牌→event_day_anomaly"规则,该规则只适用于exp8价格形态事件,不适用于exp20公告事件。

**同日多链同方向确认折叠为一个市场事件;**方向冲突继续整事件fail-closed。折叠仅在L2,L1不动,并保留组成链审计清单。
**估计窗、覆盖门和sample gate沿默认:**事件日前250至91交易日、160日窗口、有效日不少于112、sample_gate=30。
二、signed统计口径补强
最终PAP须明确:
direction_sign不仅作用于事件窗raw AR,还须作用于该事件对应的估计期异常残差及所有方向相关统计输入;
AAR、CAAR、BMP、ADJ-BMP、Corrado、日历时间法及聚集相关修正均针对同一signed估计对象;
标准差数值虽不因乘±1改变,但秩方向、标准化残差方向及事件间相关符号必须按signed口径处理;
raw AR只保留给direction诊断层,不得混入顶层判决;
禁止只给最终CAAR改符号。
三、终版PAP要求
本轮仍只授权PAP文本回修,不授权代码或运行。交付:
新建终版canonical PAP JSON,不覆盖草案;
engine_params必须为结构化对象,不得保留描述性占位字符串;
将上述十项及公告日T+1语义逐键落入PAP;
提交草案→终版逐键diff;
validate_pap与窗口解析结果;
文件SHA256与canonical digest;
明确12,569/5,225仍仅是窄闸对账参考;采用已裁p_change规则重实现后必须逐层归因,不能因对不上而修改冻结规则;
列出冻结后必须实施的攻击fixture,包括:up正AR与down负AR经signed后同为正;
反向样本经signed后为负;
SIG+REVERSED不得写成支持;
周末/节假日公告不因T无bar被剔除;
顺延1/5/6日边界;
单边界回退、全空、flat、同日不一致及白名单外方向;
raw诊断层零verdict;
signed相关修正输入确实改变而非只改展示值。

继续禁止:写代码、读取收益、冻结、生成manifest、写台账或正式运行。
终版PAP交回后,由人复核并以其新digest下冻结句,同时另写预判;旧草案不得直接冻结。
