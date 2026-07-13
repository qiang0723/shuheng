# 外审修法 #1 验收档 · 新策略 PAP 可执行离场硬门 + 旧措辞修正(2026-07-13)

依据:`docs/postaudit-five-order-2026-07-13.md` #1(人终签 2026-07-13);施工序第 5 位(末位)。
边界遵守:#2b 已冻结计算载荷零触碰、不重跑旧判决(诊断跑零台账写入,见 §3)。

## 1. 现状攻击路径复述(外审描述确认)

旧 PAP 无 schema 版本与 analysis_type,策略版含否只能靠文本推断;策略执行时序(决策 vs
成交)无结构化约束——close_confirmed+same_close 类不可执行口径可再进入新 PAP 并冻结。
**施工前现场坐实(taosha_app,事务内探针+ROLLBACK)**:INSERT 携带
`decision_time=close_confirmed / fill_time=same_close` 的策略 PAP 并 registered→frozen
**被放行**(exp_id=57 status=frozen 返回,已回滚;identity 空洞在案语义)。
旧措辞坐实:`holding_path.py:24`"最早可执行价"、`drawdown_strategy.py:19-20,257-258`
"轻微前视/最早可执行价"仍作正当化表述,与已采纳 addendum_id=1 定性不一致。

## 2. 结构修法(三层 fail-closed,应用层单点校验不足够)

- **层①** `taosha/experiment/pap.py`:`PAP_SCHEMA_VERSION=2`、
  `analysis_type∈{event,strategy,event_and_strategy}`;`validate_pap()` 扩展(新 PAP 必含
  两键,含 strategy → `validate_strategy_execution()`);执行模式白名单:
  `close_to_next_open`(四字段须逐字冻结值 decision_time=close_confirmed/fill_time=next_open/
  fill_price=next_adjusted_open/slippage_rule=frozen_cost)与 `preclose_to_tail`
  (decision_cutoff/decision_price_source/fill_window/fill_price_rule/slippage_rule 必填,
  取值由人在冻结前选定、**代码零默认**);**信息时序禁组合**(决策时点必须严格早于成交窗口,
  时点记号序数化判定,close_confirmed+same_close 直接拒)。纯事件假设不要求该字段。
- **层②** `taosha/sql/011_pap_execution_gate.sql`(已 apply):registered→frozen 触发器
  (`experiment_bu` 承 005+008 全文重放 + `_pap_freeze_gate()` 调用)库内同则复刻上列全部检查。
- **层③** `taosha/harness/run_drawdown_strategy.py`:启动校验先于一切取数——legacy 一律拒
  (**含 --diagnostic**);`analysis_type` 不含 strategy 拒(不靠文本推断);
  `strategy_execution` 白名单校验。`ledger.is_legacy()` 为唯一判据查询口。
- **legacy registry 物化**:`pap_legacy_registry`(append-only 焊死,taosha_app/引擎**零写权**,
  写只在 011 迁移物化一次)——收录迁移时刻缺 `pap_schema_version` 的**全部 25 存量实验**
  (确认点②:含 frozen 3/done 3/closed 1,`status_at_migration` 注明;断言 25/25 焊进迁移)。
  判据=此表本身,不认调用方传 legacy 字段/可伪造 registered_at;迁移后新增实验不可能进入
  (append-only+零写权+一次性物化);升级 schema 仅 registered 态经人确认补元数据,
  且升级后仍限 `analysis_type=event`(策略研究须 INSERT 新实验行)。
- **旧措辞修正**(commit `70fd0ab`,数值路径零触碰):`holding_path.py` G3 条目+PIT 注、
  `drawdown_strategy.py` 头注+`known_caliber_features` G3 字符串,统一改为已采纳
  addendum_id=1 定性逐字——"**冻结口径下的不可执行诊断值,存在同刻成交前视与倾向乐观的
  偏置,不构成真实可交易表现证据**";"轻微前视/最早可执行价"表述显式作废(改判纪律:
  模块内以删除线注记作废原文,产物字符串零残留)。

## 3. 措辞修正与旧 SHA 边界的验收(人令口径:数值零差异断言 + 语义 diff,不再要求 SHA 相等)

措辞修正 commit 后、层③硬门安装**前**,对 exp3 策略版执行一次 `--diagnostic --snapshot-id 1`
只读诊断跑(③通路规矩:零台账写入、事由入产物与 STATE 登记;**本跑为硬门安装前最后一次
legacy 策略诊断跑**)。产物 `/root/s5item1/c2s_wording.json`(sha256 `336fef56…`)
vs item3 基线 `b2s_eventday.json`(norm 7dbd9006,备份同目录),剔除 diagnostic 运行元数据块后:
- **数值字段差异 = 0;结构差异 = 0**(逐项递归断言,n_consumed 17827/净均值 −0.008667/
  adj_z(毛) −0.5517 等全部逐位同);
- **定性文本差异恰 1 处** = `strategy_version.known_caliber_features[1]`(G3 措辞,旧→新
  显式语义 diff 全文留档于比对输出);
- 新产物旧措辞残留 = **无**;含 addendum 定性"不可执行诊断值" = **True**。
- 数据库中已闭卷 result_json 零触碰(集成回归 S7 台账 25 行前后全等再证)。

## 4. 正向控制 + 反向攻击测试

新常设自检 `taosha/experiment/verify_pap_gate.py`,**16/16 PASS**:
- 正向:F1 既有 registered 纯事件 legacy(exp8)事件版冻结放行;F2/F3 两类合法执行方式
  (close_to_next_open / preclose_to_tail)均正常冻结;F4 新纯事件 schema 冻结放行。
- 反向(施工单四条全覆盖):R2 close_confirmed+same_close 禁组合冻结拒(信息时序报错);
  R3 preclose_to_tail 缺必填拒;R1/R5 删除 pap_schema_version / 伪称 legacy 均拒;
  R7 taosha_app 写 legacy registry → permission denied;R4 白名单外 profile 拒;
  R6 legacy 升级为 strategy 拒;**L1 层③子进程实测:策略驱动对 exp3(legacy)一律拒
  (含 --diagnostic)**;§3 = "旧 #2b 报告输出不再出现旧措辞"断言实测。
- 层① 自检:`python -m taosha.experiment.pap` 修法#1 段全绿(白名单放行/六类非法全拒)。
- **回归全绿**:状态机 46/46、addendum 14/14、**合成基线 sha `3116ba9b` 双跑逐字节不变**
  (synth_pap 补 schema 键零扰动实证)、集成回归 7/7(S6 sha 3bef1f81 同基线)。

## 5. 权限身份 + 迁移与回滚边界 + 验收实物

- **权限身份**:011 以 **postgres 属主** apply;registry 对 taosha_app/引擎仅 SELECT
  (写只在迁移物化一次);全部探针与套件以 **taosha_app** 跑,层③以驱动真实身份子进程跑。
- **迁移边界**:新表(25 行物化)+ `_pap_freeze_gate()` + `experiment_bu()` 替换;
  台账 25 行数据零触碰(Z1 断言);#2b/#4 闭卷 result_json/密封卡数值零触碰。
- **回滚边界**:`experiment_bu()` 重放 005+008 定义(去 gate 调用)、DROP `_pap_freeze_gate()`;
  registry 为 append-only 审计实物,回滚保留不删;Python 件随 git revert。
- **验收实物**:措辞 commit **`70fd0ab`** + 硬门 commit **`dcf3ac1`**,push + aliyun ff 两台干净;
  比对产物 `/root/s5item1/`(新产物+基线备份+比对脚本输出);套件 **16/16 + 46/46 + 14/14 +
  3116ba9b + 7/7 全 PASS**;本项攻击尝试(禁组合冻结/缺必填/伪称 legacy/越权写 registry/
  legacy 策略驱动)**全部被拒**,正反向测试套件**全部 PASS**。
