# exp17 `earnings_flash_gap` NOT-FROZEN PAP 草案令

日期：2026-07-30（UTC+8）  
授权人：John  
授权确认：**“已发”**

## 一、已闭合前置事实

显式 `fields=ts_code,ann_date,end_date,n_income,update_flag` 的 10 票探针已完成，
92/92 行返回 `update_flag=0`；证据=`/root/s17gate/update_flag_probe.log`，
SHA=`ff6bb4a3db3f806b149be0855b536bf79dded2e2a01cef92281c1e03b4cffd29`，
留痕 commit=`989833c`。不得重复探针。

草案以 `update_flag=0` 作为初始快报行识别基础；缺失、多条初始行或字段冲突的处置列入
人裁菜单，不代裁。

## 二、signed 硬约束

PAP 须显式包含 `diagnostic_dimensions.axes.direction={up,down}`，不得使用 exp24 专属
`direction_layers`，不得修改统计内核。

## 三、数据盲期锁定

草案须预先写明严格 up/down 判据、恰等边界不成事件、区间完整性、同日预告不算前置信息、
事件锚及研究期建议。express 全量落地后不得依据分布调整阈值、边界或方向判据；只能闭合
数据身份、初始/修订冲突及经 John 逐项裁定的结构性定义。

## 四、人裁菜单

完整呈交：

1. 首次预告或快报前最近预告；
2. 初始快报行缺失、重复或冲突的处置；
3. `n_income` 与预告区间的会计归属口径。

只列选项、实质影响和技术建议，不代填。

## 五、边界与交付

本单元只交 NOT-FROZEN PAP 草案、双口径 digest、schema/窗口验证、裁决映射、沿承建议和
盲期分类。零 express 全量采集、零落库、零生产代码、零数据库写入、零冻结、零 manifest、
零收益读取、零运行、零 persist。完成停交验点。
