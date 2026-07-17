# exp8 冻结前回修二 · 交付验收档(2026-07-17 深夜三;人令=`limit-open-premend2-order-2026-07-17.md` + 中途调整令 `limit-open-premend2-adjust-2026-07-17.md`)

> 性质:冻结前回修交付,**非冻结令**。全程未写 driver、未读任何收益/CAR/显著性正式结果、
> 未生成 manifest、未冻结 exp8、台账 25 行零写入、未正式运行、原 PAP 文件未改。
> 按人令§九交验清单 12 项逐项对应如下。

## 1. 开工前数据库状态闸(只读实物,已人验收)

exp8 status=**registered**;frozen_at/done_at/result_json 全空;pap_json=2026-07-12 登记占位
(全"待冻结")→ 未执行过冻结迁移;pap_legacy_registry.status_at_migration=registered;
无 driver(harness 无 run_limit_open_*)/无 exp8 manifest(study_snapshot 最新 87=exp4、74=holder_sell 源)
/无正式运行记录;台账 25 行=registered18/frozen2/done4/closed1。→ 分支 1,保持 registered 施工。

## 2. 新 PAP JSON、SHA256、canonical digest、逐键 diff

- 实物 = `taosha/docs/limit-open-pap-final-v2-2026-07-17.json`(canonical:词典序紧凑分隔符+末尾单换行,与 v1 同式)。
- **文件 sha256 = `2611be36a37b89055a5e4c393f18c507492b36fa51db323db66d43be370b66b4`**
- canonical 串本体 sha256 = `af21ab718f8d911c63c5415e45e0957b4484317be45365a0693262faed694e1e`
- `validate_pap` PASS(schema v2/event);`parse_test_windows`=(5,20,60)。
- **v1(a6a2da9a,已作废)→ v2 逐键 diff**:
  - [CHANGED] `bias_statement` = 人令§六固定口径逐字("清洗剔除与listing fail-closed产生样本
    选择,偏差方向未知;估计对象仅限清洗存活样本,不得外推为全体一字涨停链事件的效应。"),
    旧含 C3 结构性预判的声明整体废除;
  - [CHANGED] `cleaning` = C1 统一顺延新口径(T 真实交易行 fail-closed event_day_anomaly/
    T+1 起停牌一字混合统一计数≤5/6 剔 postpone),旧"事件日T或T+1停牌剔(item7)"表述废除;
  - [CHANGED] `engine_params` = 冻结值八项:st_mode=event_day/st_policy=keep/
    verdict_policy=adj_bmp_main_only/nfv_structured=true/**postpone_policy=unified**/
    **diagnostic_dims=[listing_age,st]**/**strata_enabled=false**/benchmark_mode=market;
  - [ADDED] `diagnostic_dimensions` = 两条独立轴定义+零存活三态命名规则+C3 覆盖同门槛条款;
  - [REMOVED] `layers`(forecast 风格键废除,由 diagnostic_dimensions 取代);
  - [CHANGED] `verdict_authority` = 补字段级角色元数据条款(adj_bmp_car=VERDICT_AUTHORITY/
    辅助统计=NOT_FOR_VERDICT/taus·n=CONTEXT,逐项对账 fail-closed);
  - [CHANGED] `reporting_commitments` = 补两轴逐层报告义务(C3)+报告直接消费 bias_statement
    +旧措辞禁则指针(P1-4);
  - [SAME] analysis_type/benchmark/cost/event_def/holdout/pap_schema_version/pool/sample_gate/
    snapshot_batch_req/verdict_power_note/window(C2/C4/C5/事件定义/研究期/holdout 不重开)。
- 构内断言:新 PAP 全文零命中"结构性无CAR/适用域以seasoned为主/保守处置/保守下界/
  真实效应不小于报告值/倾向缩小效应/旧item7表述/改名旁路键名"。
- 新 digest **待人批**;不作预判(预判只能由人随新冻结批复写入)。

## 3. C1 fixture(纯停牌 1/5/6 + 混合 5/6;`verify_limit_open_engine` 76/76 之①段)

- unified:**纯停牌 1 日**(留,τ0=T+2)/**5 日**(留,τ0=T+6=上限)/**6 日**(剔 postpone)
  缺行判据+flag 行变体;**混合 5 日**(一字1+停牌4,留)/**混合 6 日**(一字1+停牌5,剔);
  一字 1/5/6 同证;未用混合替代纯停牌(人令§四)。
- T 缺行/停牌 flag → `event_day_anomaly` fail-closed,notes 单独留痕"不与 T+1 顺延混淆"。
- notes 文案(调整令一):unified 写"不可交易状态顺延 N 交易日(停牌x/一字y)"分计实测
  (纯停牌1=停牌1/一字0;混合5=停牌4/一字1;超限6=停牌6/一字0);legacy 旧"一字板顺延"
  文案逐字保留;audit.premend_params 记实际 postpone_policy。
- legacy 默认行为固化:T/T+1 停牌=item7 suspension、一字 1/5/6 边界原值——**明标"仅辖默认
  路径"**,不再充当 exp8 期望值(旧 fixture 固化错误行为已改写)。

## 4. C3 三态 fixture(同套件④段)

- **有存活**:recent_listing/seasoned 双层统计块在场(CAAR/ADJ-BMP/朴素t),**无状态判决键**;
- **有事件、覆盖归零**:n_events=1/n_valid=0、剔因={history} → `UNESTIMABLE_BY_FROZEN_COVERAGE`
  +逐因分解;
- **本层零事件**:块在场 → `NO_EVENTS_IN_LAYER`(不虚假归因覆盖门槛);
- 附加:清洗致零存活(event_day_anomaly+suspension 混合)→ `UNESTIMABLE_AFTER_FROZEN_CLEANING`
  +逐因逐年分解(2021/2022)。

## 5. P1-4 报告对账(同套件⑦段)

- result.bias_statement.text **逐字==pap['bias_statement']**(fixture 另与 PAP v2 实物文件对账);
- exp8 报告渲染新声明逐字+来源锚;
- 旧禁止措辞四项(保守处置/倾向缩小效应/真实效应不小于报告值/保守下界)exp8 报告**零命中**;
- 权威唯一性:`bias_statement_assert` 仅作逐字断言(不等 → fail-closed 实测);新策略启用而
  pap 缺键 → 拒绝运行实测;
- 默认旧路径:原固定偏差段在位、渲染零新增段/标记(见 §10)。

## 6. 两条独立诊断轴 JSON + 报告实物

- 合成域样例(SYNTHETIC 标注,非正式运行):
  `taosha/docs/limit-open-premend2-json-sample-2026-07-17.json`(diagnostic_dimensions 全树+
  bias_statement+field_roles+not_for_verdict_policy+audit.premend_params)、
  `taosha/docs/limit-open-premend2-report-sample-2026-07-17.txt`(渲染全文)。
- 两轴(listing_age、st)分别报告;无四格交叉统计;cross_counts=仅 n_events/n_valid 计数核对;
  不复用 forecast 文案(exp8 报告"预喜/预亏/扭亏"零命中实测);type_strata 注记中性无"#2b"。

## 7. 递归证明(同套件⑤段)

- 全 result 唯一 `verdict`/`verdict_note` 键=顶层(递归扫描 1/1);
- `sig_state_report_only`/`sig_state_note` 全文档 **0 命中**(改名旁路已从代码删除);
- 诊断子树无 SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT 分类值;
- **攻击测试(调整令三)**:monkeypatch 计数=全跑 `_verdict` 恰调用 **1 次**(顶层);
  `_verdict` 炸弹(调用即 raise)下诊断构建器照常工作=结构性零调用。

## 8. 非权威字段结构化角色检查(同套件⑥段)

- car.main_window.field_roles 与实际字段集合**逐项对账无漏项**(set 相等断言);
- adj_bmp_car=VERDICT_AUTHORITY;naive_t/bmp_car/caar/csar_mean/csar_sd/kp_factor=
  NOT_FOR_VERDICT;taus/n=CONTEXT;
- 未分类新统计字段 → fail-closed raise 实测;
- 报告非权威段**直接带 [NOT_FOR_VERDICT] 标记**(逐日AR/板块分层/稳健性/删失诊断/可交易/
  行业覆盖/robust_window/诊断轴逐层),非仅末尾块名清单。

## 9. 专项测试及全家福回归

- 专项:`verify_limit_open_rules` **40/40**(两台)/`verify_limit_open_engine` **76/76**(两台)。
- 全家福:aliyun(钉版 venv python)=状态机 46/46/pap 硬门 23/23/addendum 14/14/镜像 11/11/
  血缘 24/24/fail-closed 探针 19/19/**集成 7/7(S6 双跑 sha `63e2c9fc` 与回修前基线逐字节同)**/
  运行时钉版 ALL PASS/三窗 5/5/holder 规则 81/81/适配 10/10/敏感性 6/6/cleaning/pap 自检;
  AWS=非 DB 套件同清单全绿(AWS 无本地 PG,DB 套件历史即 aliyun 域)。

## 10. 既有默认路径零回归证明

- 合成 e2e(官方 harness):**改后两台四跑全=`3116ba9b74f7c53b…` 逐字节**(=历史基线);
- 默认路径双跑 result 逐字节相等;零新键递归扫描(not_for_verdict/premend_params/
  not_for_verdict_policy/diagnostic_dimensions/bias_statement/field_roles 全 0);
- 默认渲染:原固定偏差段在位、无"[NOT_FOR_VERDICT]"标记、无诊断轴段、无 NFV 水印段;
- 分层块 verdict 键在位、ST 注记原文、legacy notes 文案逐字。

## 11. git 实物

- commit 链:`92bff23`(撤回令留痕+作废登记)→ `7860dce`(中途调整令留痕)→
  `04bd096`(回修二施工+fixture+PAP v2)→ 本验收档+样例+STATE commit(见 git log)。
- `git diff --stat 7860dce..04bd096`:
  ```
  taosha/docs/limit-open-pap-final-v2-2026-07-17.json |   1 +
  taosha/engine/cleaning.py                           |  49 ++-
  taosha/engine/report.py                             |  80 ++++-
  taosha/engine/runner.py                             | 235 +++++++++++++-
  taosha/engine/survivors.py                          |   8 +-
  taosha/harness/verify_limit_open_engine.py          | 349 +++++++++++++++++----
  6 files changed, 627 insertions(+), 95 deletions(-)
  ```
- `--name-status`:A=PAP v2;M=cleaning/report/runner/survivors/verify_limit_open_engine。
  实际逐行 diff=git 仓内(两台可 `git show 04bd096`)。触碰面全部在人令§十允许范围内;
  qbase/台账/driver/manifest/原 PAP 文件零触碰。

## 12. 边界证明

未写 driver(harness 无新 driver 文件);未读收益/CAR/显著性正式结果(合成域样例已显式
SYNTHETIC 标注;真实库仅状态闸只读元数据查询);未生成 manifest(study_snapshot 无新行);
未冻结 exp8(状态闸后零台账写入,25 行未扰);未正式运行;原 PAP 文件 sha `a6a2da9a` 未变
(仅旁立 WITHDRAWN 标记档);C2/C4/C5/adj_bmp_main_only 未重开(fixture ②③段原样全绿);
诊断层未扩通用分层平台(_DIAG_DIM_SPECS 仅两轴,维度白名单 fail-closed)。

---

**本交付不构成冻结。停在交验点:等人重新审核新 PAP(digest `2611be36…`)→ 人以新 digest
重新下达冻结句并重新写入方向与把握度预判后,方可进入 driver 施工/manifest/正式运行。**
