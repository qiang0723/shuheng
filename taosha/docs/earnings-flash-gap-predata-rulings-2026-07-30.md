# exp17 `earnings_flash_gap` 数据前置前口径裁定

日期：2026-07-30（UTC+8）

授权人：John

## 人裁原文

> A1；ST reject；postpone_policy=unified_announcement，其他沿承项按草案建议确认。

## 逐项效力

1. **预告基准=A1**：采用快报前最近一次公开且区间完整的预告。该裁定形成于 express 全量
   数据落地及 A1/A2 全量数量对照之前；后续并算只作数据质量披露，不得据数量改判。
2. **ST=`reject`**：ST 事件按草案建议剔除，不设置 ST 收益分层判决轴。
3. **`postpone_policy='unified_announcement'`**：初始快报 `ann_date` 为日历锚，τ0从其后第一个
   交易所交易日开始；个股缺 bar、停牌及一字不可交易统一顺延不超过5个交易所交易日，第6日仍
   不可交易则剔除。
4. **其他沿承项确认**：三窗 5/20/60、估计期前250至前91日与覆盖门112/160、
   `sample_gate=30`、全市场等权 benchmark、`adj_bmp_main_only` 唯一判决、cost四值仅schema与
   执行审计、holdout/field roles/digest binding/effect alignment、direction raw NFV诊断及
   `llm/prescreen`水印，均按草案建议确认。

## 尚未裁定且不得代填

- **菜单B**：`update_flag=0` 初始快报缺失、重复或冲突组的具体处置；须待全量实物量化异常形态。
- **菜单C**：`express.n_income` 与 forecast 净利润区间的会计归属同一性；须待公司公告原文抽核。

上述两项未闭合前，不得生成可冻结终版PAP。正式适配时须显式验收台账身份水印：driver写入
`audit.experiment_identity`，report缺身份fail-closed，fixture包含删除身份攻击用例；该项本轮
仅登记，不授权代码施工。

## 本令边界

本令只确认冻结前口径并授权留痕，不授权 express 全量采集、落库、生产代码、数据库写入、
终版冻结、manifest、收益读取、正式运行或 persist。
