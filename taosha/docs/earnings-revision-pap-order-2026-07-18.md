# exp20(earnings_revision)判决形态裁定与 PAP 草案排产令(2026-07-18 深夜,人令原文即口径)

> 留痕纪律:人令原文逐字收录,不改写、不概括。本单元交付仅限 PAP 草案、逐项裁决映射、待人拍参数清单;非冻结令。

## 人令原文

枢衡工地:
exp20(earnings_revision)判决形态裁定与PAP草案排产令。
一、判决形态(人裁:方案1)
唯一主检验采用signed abnormal return:
上修事件direction_sign=+1;
下修事件direction_sign=-1;
事件级、逐τ定义为
signed_AR(i,τ)=direction_sign(i)×raw_AR(i,τ);
符号变换必须发生在事件级AR进入AAR、CAAR、BMP、ADJ-BMP等聚合与检验之前,不得仅对最终CAAR或报告展示值改符号;
正signed效应表示价格沿修正方向反应,负signed效应表示价格逆修正方向反应。
合并signed事件集只产生一个主窗ADJ-BMP顶层verdict,不因方向诊断层分拆α。
PAP草案必须明确提交以下待人确认项,不得由施工侧静默决定:
主检验采用单侧还是既有双侧门槛;
若ADJ-BMP达到显著门槛但signed效应为负,顶层verdict及"支持/证伪"应如何对应;
不得把"统计显著但方向相反"解读为支持原假设。
二、方向诊断层
上修、下修分别作为结构化NOT_FOR_VERDICT诊断轴:
白名单严格为up/down;
主事件集出现空值、flat、unknown或其他值必须在进入CAR及顶层判决前fail-closed;
可报告事件数、存活数、逐因逐年剔除、raw CAAR和ADJ-BMP数值;
PAP须明确诊断层展示的是raw AR还是signed AR;建议使用raw AR,以保留上修和下修的实际方向及强度;
诊断层零verdict、零显著性分类字段,不调用判决函数,不改变顶层判决;
不引入上修/下修双检验、多重比较或总判决规则。
三、既裁数据口径重申
以下2026-07-17窄闸裁定继续有效:
方向基准B:相对事件日前最近一次公开披露;
链键=(ts_code,end_date,first_ann_date);
事件键=(ts_code,ann_date);
同日逐字段重复行仅在L2确定性折叠,L1原始行不动;
孤儿修正、ann_date<first_ann_date、同期多链归属不明、基准或当前数值不可判、同日方向冲突全部fail-closed;
不使用type文字回退;
flat不进入方向判决,仅计数报告;
不设修正幅度门;
研究期为2013-01-01≤ann_date<2024-07-01;
事件轴自公告日后T+1开始;
600856.SH单位疑点fail-closed并留痕;
效力保持llm/prescreen,不得写成full。
四、窄闸数字的正确身份
窄闸数字:
候选事件面12,569;
基准B可判5,225。
以上仅作为规则实现的对账参考,不是正式研究样本量,不得预写进未来结果作为n_events_total。正式数量必须在应用研究期、flat排除及全部fail-closed规则后由事件生成器重新确定,并逐层对账差异。
五、本单元仅授权PAP草案
PAP草案须逐字提出并等待人复核:
signed AR公式、施加层级与估计对象;
检验单双侧及显著反向结果的解释规则;
事件方向、不可判、flat和异常样本处置;
exp20自身的主窗、次级窗、稳健窗及选择依据——不得把exp8的5/20/60写成既裁先例;
全市场或其他研究池、基准口径及其依据——当前尚未冻结;
ADJ-BMP唯一权威及辅助方法边界;
direction诊断轴的raw/signed展示口径和NFV结构;
bias statement:大量不可判与fail-closed造成样本选择,偏差方向未知,估计对象仅限2013年后可形成合法修正链且数值可判的存活样本;
engine_params冻结值;
PAP canonical digest及运行时绑定规则;
sample gate、StudySnapshot依赖与报告承诺。
六、禁区与后续顺序
本单元不构成冻结令:
不写代码;
不读取任何收益、CAR或显著性结果;
不修改台账;
不冻结PAP;
不生成manifest;
不运行研究。
交付仅限:PAP草案、逐项裁决映射、尚待人拍的参数清单。
后续顺序固定为:
PAP草案交人复核 → 人批准最终PAP并在冻结句内嵌预判 → 最小适配器与攻击fixture → StudySnapshot绑定 → 单次正式运行 → 取证 → 外审 → persist。
