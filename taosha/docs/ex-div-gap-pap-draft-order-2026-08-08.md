# exp14 `ex_div_gap` · NOT-FROZEN PAP 草案令

日期：2026-08-08（UTC+8 / Asia/Shanghai）

## 一、外审结论

Fable 对 exp14 窄闸的限域复核结论为：

> A 级 0 / B 级 0 / C 级 2；二元结论成立：可进入 NOT-FROZEN PAP 草案，
> 当前不可冻结。

两项 C 级均默认不采：27个因子静态候选的成因不在本草案单元扩查；exp21人裁留痕不在
本次范围。窄闸的 Decimal、版本漏斗、复权收益语义、监管阶段与 A–E 菜单无需回修。

## 二、John 授权原文

> 批准 exp14 ex_div_gap 进入 NOT-FROZEN PAP 草案单元。草案须完整呈拍：A 因子变化资格门、B 多版本折叠规则、C 复权主CAR与 tau0=ex_date、D 监管阶段仅组成NFV或增加收益诊断、E 沿承项；其中 postpone_policy 不得机械沿承 unified_announcement。只列技术建议，不代裁。零生产代码、零数据库写入、零视图施工、零冻结、零StudySnapshot、零manifest、零收益读取、零运行、零persist。完成停交验点。

## 三、草案要求

1. 生成18键事件版 NOT-FROZEN PAP JSON；合并高送转除权事件集，只形成一个顶层
   `adj_bmp_main_only` verdict，不设置 `signed_ar`；
2. 菜单A完整呈拍 `adj_factor`变化硬门与保留27个静态候选两案；菜单B完整呈拍消费字段
   精确一致折叠与多行方案全剔两案；
3. 菜单C完整呈拍复权总回报、`tau0=ex_date`当日与停止后重登记不复权机械价格研究两案；
   不复权跳空不得进入主CAR；
4. 菜单D完整呈拍监管阶段仅事件数量/组成NFV与新增收益诊断两案；后者须明确板块历史映射、
   最小通用诊断轴及治理冻结条件，不得借用实验专属分层；
5. 菜单E逐项呈拍研究期、三窗口、估计期覆盖门、sample gate、market benchmark、cost、
   holdout、field roles、digest binding、身份水印、ST处置及 `postpone_policy`；
6. `postpone_policy` 必须与 `tau0=ex_date`同日语义相容，草案只可建议
   `missing_bar_only`，不得机械沿承公告事件的 `unified_announcement`；
7. 数据侧4,065/4,038、逐年分布、恰等1,083、snapshot375等只作冻结前同锚对账参考，
   不得写成正式运行硬断言或 selection SHA；
8. 输出文件SHA、canonical digest、`validate_pap`、窗口解析、键数、菜单映射与残留态扫描。

## 四、停止线

本单元仅生成文本并更新 STATE：零接口重探、零全量采集、零缓存入仓、零数据库写入、
零生产代码、零视图施工、零终版PAP、零冻结、零StudySnapshot/研究manifest、零收益读取、
零正式运行、零persist。完成即停交验点；exp18/exp23继续停既有语义硬门，exp21保持已裁草案
待数据闭合，不并行恢复。
