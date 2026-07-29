# exp10 `volume_drought_break` PAP 冻结 + 最小适配令（2026-07-29）

> 人裁原文即口径。F 条留痕先行；本令分段授权至行为验收点，正式 manifest、正式收益读取、正式运行与 persist 均未授权。

## 一、人裁冻结锚

- 终版 PAP：`taosha/docs/volume-drought-break-pap-final-2026-07-29.json`
- digest：`18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`
- 人冻结预判原文：**「正，把握度60%」**。
- 该原文在本实验中的唯一解释：主窗 `[0,+4]` 市场调整后 CAR 方向为正；仅押方向，不押幅度或统计显著性。仅绑定上述终版 digest，不继承、不平移任何旧版本表述。

## 二、冻结前只读断言

任一不符立即停止：

1. exp10=`registered`，`frozen_at/result_json/done_at`均空；
2. 无 exp10 正式 manifest、运行记录或遗留产物；
3. 终版文件 SHA、引擎 canonical 重算与本令 digest 三者逐字相等；
4. 数据库当前 PAP 仍为未冻结占位载荷；
5. 台账 25 行，分布 `registered 12 / frozen 2 / done 10 / closed 1`。

## 三、冻结执行

仅走既有状态机：`taosha_app` 同连接单事务，`FOR UPDATE` 重断言后将终版 canonical 原文写入 exp10 既有行，再执行 `ledger.freeze(10)`，一次 COMMIT。不得复制草案、补键或旁路改状态。提交后读回 `status/frozen_at/pap_json`，核对 parsed equality、数据库 canonical digest 与载荷 MD5。冻结后台账应为 `11/3/10/1`，总行数仍为 25。

## 四、冻结后最小适配授权

只实现本假设所需最小件：

1. 成交额事件只读视图对，holdout 与排北交所焊死；
2. `volume_drought_rules.py` 纯函数状态机，逐字实现 prior60、连续低量、首次放量终局、非收阳拒绝、停牌打断但 prior60 不清空及 Decimal 边界；
3. exp10 driver 逐字消费冻结 `engine_params`，支持只读 recon；正式模式必须使用 exp10 自有 manifest；
4. exp10 报告分支与 rules/adapter 攻击 fixture。报告须使用“事件后首个有真实bar的价格观察日”，终局拒绝组仅报几何计数、不得读取或展示收益。

攻击面至少覆盖：历史不足60根；prior60排当日且跨停牌保留；停牌/异常bar打断 low_run 与 armed；连续第5日武装；30%与100%严格边界；armed 中间带保持；首个放量收阳成事件、非收阳终结并重新蓄积；一阶段至多一事件；事件键唯一性 fail-closed；研究期边界；digest 与 engine_params 逐字消费；报告 NFV 与术语。

冻结漏斗按 daily6/trade_cal10 只读参考复现：研究期事件 `13,889`、selection SHA `3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`。同批次下不一致即停，不追数、不改冻结规则；不得读取事件日后收益。

## 五、停止线

完成冻结、最小适配、fixture、只读 recon 与零回归后停在行为验收点。仍禁止生成正式研究 manifest、正式收益读取、正式运行、persist 或结果写库。
