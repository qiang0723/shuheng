# exp12 `st_removal` 冻结令 + 预判绑定 + 最小适配授权令(原文留痕,2026-07-23)

> 人令下达于会话内(2026-07-23 二晚),本档为 F 条裁决留痕,**原文措辞即口径,不得善意改写**。
> 令性质:①批准以终版 digest 冻结 exp12 终版 PAP;②预判原文绑定该 digest;③冻结后仅授权
> 既定最小适配与行为验收。**不授权 manifest/真实收益/正式运行/persist/result_json 写入**;
> 完成后停行为验收点。

---

## 人令原文

**枢衡工地:**

批准冻结exp12 `st_removal`终版PAP:

`digest=62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`

**预判:主窗[0,+4]市场调整后CAR为正,预计上涨约5%,把握度70%。**
该预判仅绑定上述终版digest,不预判统计显著性,不得改述或平移至其他PAP版本。

**一、冻结前只读确认**

任一不符立即停止:

- exp12为`registered`,`frozen_at/result_json/done_at`为空;
- 无exp12正式manifest和运行记录;
- 台账25行,状态分布为15/2/7/1;
- 终版文件SHA、引擎canonical重算值、本令digest三者逐字相等;
- 数据库当前仍为未冻结占位PAP。

**二、执行冻结**

仅走既有状态机,以`taosha_app`同连接单事务执行`registered→frozen`:

- 冻结载荷为终版PAP canonical原文;
- 提交后读回status、frozen_at、PAP digest及载荷MD5;
- 只更新exp12既有行,不新增行;冻结后预期分布14/3/7/1。

**三、冻结后最小适配**

仅授权:

- exp12事件生成器、只读视图接入和driver;
- 引擎显式支持`postpone_policy='missing_bar_only'`:仅停牌/缺bar顺延,一字涨跌停有真实bar即进入CAR;
- exp12报告显式标题、PAP/manifest锚及一字板`NOT_FOR_VERDICT`执行限制段;
- 攻击fixture覆盖:缺bar顺延1/5/6日、一字涨跌停不顺延、退市双谓词、摘星排除、冲突与重复fail-closed、digest和engine_params逐字消费;
- 漏斗按冻结规则复现,641仅作batch 7参考数,差异按血缘归因,不追数、不改规则;
- 全家福及既有默认路径零回归。

完成后停在行为验收点。

**本令不授权**生成正式manifest、读取或计算真实收益、正式运行、persist或写入result_json。

---

## 预判登记(F 条,原文逐字;绑定关系照令)

> **主窗[0,+4]市场调整后CAR为正,预计上涨约5%,把握度70%。**
> 该预判仅绑定终版 digest `62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`,
> 不预判统计显著性,不得改述或平移至其他 PAP 版本。

(对照期=persist 阶段,届时原文对照、永不改述——沿 exp8/exp20/exp13 校准册纪律。)
