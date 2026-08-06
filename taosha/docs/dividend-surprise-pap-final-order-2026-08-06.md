# exp19 `dividend_surprise` · PAP 终版文本收口令

- 日期：2026-08-06（UTC+8 / Asia/Shanghai）
- 草案 digest：`b61c1a00e58181d6756b7ea8d06b15638104d5f2c267c3986ecc1252dcf47c9b`
- 数据闭合提交：`846820772af0ea90c06db0990ead6ea53b77b602`

## 一、人裁来源

数据落地前，John 逐字裁定：

> 菜单A=A1；菜单B=B2，精确研究期起点待全量覆盖报告后由我另裁，不得代填；菜单C=C1；菜单D=D1；菜单E=E1；st_policy=keep；postpone_policy=unified_announcement；其余沿承项按草案建议确认。随后另令数据闭合，当前草案digest不得冻结。

数据闭合外审 `A0/B0/C3 → 通过` 后，John 逐字裁定：

> 选择B2-P1

该裁定已落 `dividend-surprise-research-period-ruling-2026-08-06.md`，正式研究期起点为
`2021-01-01`。本窗口明确告知下一步须另令终版 PAP 收口后，John 回复原文：

> 继续

本令仅将该回复解释为授权当前唯一下一步——终版 PAP 文本收口；不解释为方向密封、冻结、
manifest、收益读取、运行或 persist 授权。

## 二、终版裁定

1. A=A1：只使用初始预案税前现金每股分红 `cash_div_tax`；送股、转增与税后值不进公式。
2. B=B2-P1：研究期固定为
   `2021-01-01 <= current_initial_ann_date < 2024-07-01`。
3. C=C1：纯百分比；prior=0、上年缺失、上年不可判分计并排除，current=0且prior>0按−100%。
4. D=D1：Decimal 精确比较 50% 闭区间，`>=+50%` 为 up，`<=-50%` 为 down。
5. E=E1：同票同期须恰一条 `div_proc=预案 AND update_flag=0` 初始行；异常整组 fail-closed。
6. `st_policy=keep`、`postpone_policy=unified_announcement`；三窗、估计窗、sample gate、
   benchmark、ADJ-BMP 唯一判决、cost、holdout、field roles、digest binding、signed 估计、
   direction NFV 与 `llm/prescreen` 水印均按已确认值落位。

## 三、文本收口与交付

1. 新建终版 PAP 文件，草案本体保持原样并另立 NOT-FROZEN/SUPERSEDED 标记；
2. 删除全部菜单、建议、待裁及数据未闭措辞，逐键落入 A1/B2-P1/C1/D1/E1；
3. 写入事实批 `dividend=17`、源级 snapshot 375 及完整 digest；375 不得冒充研究 manifest；
4. 写入全量画像、B2-P1 机械参考及公告原件抽核，全部标明 NFV/非正式运行硬断言；
5. 方向与把握度不得代填，须在终版 digest 独立复核通过后由 John 另行密封；
6. 交付文件 SHA/canonical、schema/窗口、草案到终版键级 diff、残留态扫描与交付档。

## 四、边界

本单元仅授权 PAP 文本收口。零生产代码、零数据库写入、零冻结、零 exp19 研究 manifest、
零收益读取、零正式运行、零 persist。完成即停终版候选复核点。
