# exp21 `goodwill_impair` · NOT-FROZEN PAP 草案令

日期：2026-08-07（UTC+8 / Asia/Shanghai）

> John 授权原文：
>
> 批准 exp21 goodwill_impair 进入 NOT-FROZEN PAP 草案单元。草案须完整呈拍净资产定义、区间金额阈值、非正或缺失分母、Decimal >=5%边界、组合金额处理、首次合格披露载体及研究期/版本规则七项菜单，并显式登记五项冻结数据硬门；只列技术建议，不代裁。零全量采集、零落库、零生产代码、零冻结、零 StudySnapshot、零 manifest、零收益读取、零运行、零 persist。完成停交验点。

## 一、草案范围

1. 生成18键事件版 NOT-FROZEN PAP JSON；
2. 分子、分母、首次合格披露与 `>=5%` 仅按窄闸可表达规则起草，不填入正式候选数；
3. 七项口径以完整菜单、实质影响和技术建议呈拍，施工方不得代裁；
4. 五项冻结数据硬门全部落入 `snapshot_batch_req`、事件定义、数据质量披露与交付档。

## 二、判决形态

1. 合并商誉减值首次合格披露事件集，单一顶层 `adj_bmp_main_only` 判决；
2. 不设置 `signed_ar`、金额分层判决轴或多个顶层 verdict；
3. 短窗负向与中窗“出清”只登记为待人密封问题，本单元不读取任何收益；
4. `llm/prescreen`身份、水印、field roles与canonical digest约束沿既有事件版范式起草。

## 三、停止线

本单元零接口重探、零全量采集、零缓存入仓、零数据库写入、零生产代码、零冻结、零
StudySnapshot、零研究 manifest、零收益读取、零正式运行、零 persist。草案必须标记
NOT-FROZEN；完成交付档、STATE与机械校验后停交验点。
