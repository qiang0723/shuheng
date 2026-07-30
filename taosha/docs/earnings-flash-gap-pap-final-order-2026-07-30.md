# exp17 `earnings_flash_gap` · PAP 终版文本收口令

日期：2026-07-30（UTC+8）

## 人裁来源

数据落地前，John 已裁：

> A1；ST reject；postpone_policy=unified_announcement，其他沿承项按草案建议确认。

数据前置交验后，施工方明确给出“若认可，回复 B1、C1；随后进入终版 PAP 收口”的建议，
John 回复原文：

> 继续执行

本令据此将该回复解释并登记为：**菜单 B=B1、菜单 C=C1，授权终版 PAP 文本收口**。

## 终版裁定

1. **A=A1**：预告基准固定为快报前最近一次公开且区间完整的预告；该值形成于 express
   全量数据落地前，不因样本数量改判；依数据施工令不重算 A2 供选口径。
2. **B=B1**：同票同期 `update_flag=0` 缺失、多条或字段冲突均整组 fail-closed；不得折叠、
   任取最早/最晚或使用 `update_flag=1` 回填。全量实物中该规则剔除 6/23,076 组。
3. **C=C1**：`express.n_income` 固定解释为归属于上市公司股东/母公司所有者的净利润（元），
   以 `n_income/10000` 与 forecast 归母净利润区间（万元）比较；公司公告抽核 5/5 一致。
4. ST=`reject`、`postpone_policy='unified_announcement'`，三窗、估计窗、sample gate、benchmark、
   ADJ-BMP 唯一判决、cost、holdout、field roles、digest binding、effect alignment、方向 NFV 与
   `llm/prescreen` 水印均按草案既有确认值，不新增运行时自由度。

## 文本收口与交付

1. 新建终版 PAP 文件，草案文件保持原样并标记 NOT-FROZEN/superseded；
2. 删除全部菜单、建议、待裁和数据前置未闭措辞，逐键落入 A1/B1/C1 与既有沿承裁定；
3. 写入数据身份：express 批 15、源级 snapshot 340 及完整 digest；340 仅为冻结前数据锚，
   不得冒充未来 exp17 研究 manifest；
4. 写入冻结前实测质量披露与 A1 漏斗参考：24,381 行、24,375 组、flag1=0、冲突 6 组、
   A1 方向事件 2,529（up 997/down 1,532）；这些是同数据锚参考，不构成正式运行硬断言；
5. 方向与把握度仍不得代填，待终版 digest 独立复核通过后由 John 另行密封；
6. 交付文件 SHA/canonical、schema/窗口校验、草案到终版键级 diff、残留态扫描和交付档。

## 边界

本单元只授权 PAP 文本收口。零生产代码、零数据库写入、零冻结、零 exp17 研究 manifest、
零收益读取、零正式运行、零 persist。完成即停交复核点。
