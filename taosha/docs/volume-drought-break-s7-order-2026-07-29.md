# exp10 `volume_drought_break` manifest + §7 单次正式运行令（2026-07-29）

> John 人令原文：**「批准执行，自动执行即可」**。该原文承接本令全部修订条款；本令由 John 签发，Fable 仅作独立复核，施工方不得自授权。本令不授权代码修改、自动重跑或 persist。

## 一、运行前只读硬闸

1. exp10仍为`frozen`，`result_json/done_at`为空；PAP canonical必须为`18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`；
2. source snapshot必须为74，digest必须为`075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`；
3. 完整manifest向量**键集必须恰等**于下列十一项，多一键或少一键即停：
   - qbase：`daily=6 / forecast=1 / trade_cal=10 / adj_factor=7 / namechange=7 / stock_basic=6 / stk_holdertrade=2 / holder_sell_predisclose=12`；
   - taosha：`market_return=88 / pool_b1=18 / pool_b1_return=18`；
4. `market_return=88`、`pool_b1=18`、`pool_b1_return=18`的source anchor必须指向snapshot 74；`pool_b1_return=18`的父池必须为`pool_b1=18`；
5. 行情研究读视图与`market_return=88`覆盖末日均须为`2024-06-28`；缺基准必须传递为`None`并使对应异常收益不可得，严禁零填充；
6. 任一不符立即停止，不生成manifest、不运行。台账须仍为`25=registered 11/frozen 3/done 10/closed 1`。

## 二、manifest

- 以`--from-source-snapshot 74`生成exp10自有研究manifest；
- 完成权威行、qbase镜像、publication attestation三处发布并核对digest一致；
- 不得使用snapshot 248或其他既有manifest冒充；
- 只授权manifest相关表写入，不授权experiment ledger写入。

## 三、§7 单次正式运行

- 必须传`--pap-sha256-assert=18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`；
- `--snapshot-id`必须为本令新建的exp10 manifest；
- 正式事件集必须为`13,889`；selection SHA必须为`3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`；三条漏斗恒等式必须全部为真；
- 只运行一次；任一断言失败或RC非零即停，不修改代码、不追数、不自动重跑。

## 四、运行后边界

- exp10保持`frozen`，`result_json/done_at`保持空；
- experiment ledger零写入，台账保持`11/3/10/1`；
- 不授权persist。

## 五、取证与停止线

回报完整十一键向量、source snapshot 74原文、三个派生批血缘锚、两侧覆盖区间、缺基准传递实证、manifest ID与三处digest、运行命令及时间窗、事件数、selection SHA、三条恒等式、核心统计和运行后状态；封存result/report/log及SHA256清单。完成后停在取证点交Fable复核。
