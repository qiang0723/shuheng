# 外审五项修法施工单(人终签 2026-07-13)

> **F 条留痕:人令原文即口径,逐字存档,不得善意改写。**
> 来源:外部第二独立视角复审意见(对象=8b36eeb 总表锚 + d545c2a 批复留痕 + 7bd246a §8-bis)经人分拣转化为本施工单。
> 终签措辞:**"可以,先这么做"(2026-07-13)** —— 批复对象 = 五项原文 + 我方评审 4 确认点 + 施工序 #4→#5→#3→#2→#1 全批。
> 效力:可信度硬化窗口冻结令对本单五项解除;范围禁令见文末。

---

## 人令原文(逐字)

### #1 · 新策略PAP可执行离场硬门

边界:不修改#2b已冻结计算载荷,不重跑旧判决。
结构修法(三层焊死,应用层单点校验不足够):

新PAP引入pap_schema_version与analysis_type=event|strategy|event_and_strategy,不得靠文本推断是否含策略版。
analysis_type含strategy时,必须具备结构化strategy_execution,采用执行模式白名单,保留原裁定允许的两类合法执行方式:

- execution_profile=close_to_next_open:decision_time=close_confirmed、fill_time=next_open、fill_price=next_adjusted_open、slippage_rule=frozen_cost;
- execution_profile=preclose_to_tail:决策必须发生在成交之前,必须结构化填写decision_cutoff、decision_price_source、fill_window、fill_price_rule与slippage_rule。具体截止时点和代理价规则必须由人在PAP冻结前选定,代码不得自行默认。

禁止组合由信息时序判定:成交价所依赖的信息不得晚于决策时点,决策时点必须早于成交窗口。close_confirmed + same_close等组合直接拒绝。
校验须同时落在三层,任一层不满足即fail-closed:①Python validate_pap();②registered→frozen数据库迁移触发器;③策略驱动启动校验。
纯事件假设不要求该字段。

旧代码修正:holding_path.py/drawdown_strategy.py的诊断标识与报告措辞,统一改为与已采纳的addendum定性一致(不可执行诊断值/倾向乐观偏置),不再使用"轻微前视""最早可执行价"等措辞。
文本修正与旧SHA的边界:修改known_caliber_features等结果文本后,未来重跑JSON的SHA会变化(数值未变)。验收口径——不修改数据库中已闭卷result_json,不重跑不改判;代码修正仅影响此后生成的诊断产物与报告文本。验收方式:数值字段逐项零差异断言,定性文本做显式语义diff,不再要求整份新产物与旧策略SHA相等。
schema生效边界(legacy-event白名单必须物化):迁移执行时,将当时已经存在、缺少新schema字段的registered实验exp_id,物化写入数据库只读的append-only legacy registry;taosha_app与引擎均无写权限。legacy实验只允许事件版冻结与运行,所有策略驱动一律拒绝。不得仅依据调用方传入的legacy字段或可伪造的registered_at判断——判据是这张迁移时刻写入的登记表本身。迁移完成后新增实验不可能进入registry。如需将legacy实验升级schema,只能在registered态经人确认补充元数据。

反向测试:
- 构造close_confirmed + same_close等禁止组合的PAP,断言冻结被拒绝;
- 构造preclose_to_tail但缺失decision_cutoff/decision_price_source等必填结构字段的PAP,断言被拒绝;
- 旧#2b报告输出断言不再出现旧措辞;
- taosha_app权限下尝试写入legacy registry,断言被拒(权限验证)。

正向控制:
- 既有registered纯事件实验(已物化入legacy registry者)仍能合法冻结并运行事件版;
- 新登记实验删除pap_schema_version或伪称legacy时被拒;
- 合法的close_to_next_open与preclose_to_tail两类PAP均能正常冻结。

### #2 · qbase快照路由伪造防护

边界:qbase侧改为查询受权角色落库的权威manifest映射表,引擎只传snapshot_id,不得自报任何形式的批次向量或token。禁止把"完整JSON"换成另一种仍由引擎自报的token——权威映射必须落库,由受权角色写入,引擎侧无写入权限。
权威映射表:至少包含snapshot_id/content/digest/created_at,append-only,受权角色写入,其digest必须与taosha manifest一致。
发布机制(append-only,不通过UPDATE改变发布状态):

- ①受权角色创建taosha manifest;
- ②在qbase写入相同snapshot_id/content/digest的不可变镜像;
- ③受权角色校验两库内容与digest一致后,另行INSERT一条append-only的publication attestation(不是修改镜像行的状态字段)。
- 路由视图只接受存在有效publication attestation的snapshot_id。
- 任一步中断留下的半成品均不可消费,可留作审计记录,不改不删。
- 两库canonical digest算法必须一致,并以实测向量验证。
- 引擎对映射表和发布凭证均只有SELECT权限。

反向测试:
- 旧shuheng.study_batches完整伪造JSON读取被拒;
- 不存在的snapshot ID被拒;
- 两库同ID但digest不一致被拒;
- 已授权且digest一致的snapshot正常读取(正向控制)。

### #3 · manifest批次血缘一致性

边界:验收标准是血缘相容性,不是所有批次号相等。至少强制pool_b1_return.pool_batch_id == manifest.pool_b1;派生批次须锚定其qbase源向量或源manifest digest。
历史批次处理(不加NOT NULL,不批量补猜):

- 不对现有派生批次直接加NOT NULL约束(会导致现有snapshot失效);
- 不批量补猜来源(制造伪血缘);
- 唯一路径:可由既有审计实物证明的历史批次,用独立append-only lineage registry登记并附审批来源;无法证明的批次标记legacy-unverified,不允许其生成新的正式研究manifest;
- 新派生批次从ingest起强制写入源manifest ID/digest。

反向测试:
- 构造pool_b1_return依赖批次与manifest.pool_b1不一致的场景,断言manifest生成被拒;
- 构造派生批次缺失源锚定的场景,断言被拒。

### #4 · 状态机出生即frozen旁路

边界:常规INSERT路径只允许生成status='registered'。历史导入需求走独立高权限迁移程序,不复用taosha_app常规写路径。
反向测试:
- taosha_app权限下尝试INSERT status='frozen'并同时写frozen_at,断言被拒;
- 补充44/44自检未覆盖的"INSERT frozen+frozen_at"这一具体变体。

### #5 · addendum result_sha256锚定

边界:hash由数据库从对应result_json自动计算,不留"忽略或拒绝"二选一。

- 调用方可不传result_sha256,由数据库自动计算填写;
- 调用方如显式传入,必须与数据库计算值一致,否则拒绝;
- 对应experiment无result_json时,拒绝创建result-bound addendum;
- 既有正确附注行原样保留;
- 新增格式约束:SHA-256必须为64位小写十六进制。

反向测试:
- INSERT时传入错误/占位hash(如现有自检用的'probe'),断言被数据库拒绝而非成功写入;
- 补充"hash与result_json不一致"反向用例到verify_addendum.py。

### 统一交付格式

每项须交付以下5要素,缺一不接受为完成:

1. 现状攻击路径复述(确认理解外审描述的旁路)
2. 结构修法(具体改动:哪个文件/哪张表/哪个约束)
3. 正向控制(合法路径仍正常工作的证据)
4. 反向攻击测试(非法路径被拒的证据,新增测试用例)
5. 权限身份说明 + 迁移与回滚边界 + 验收实物(commit sha/测试输出)

### 统一验收措辞

五种攻击尝试全部被拒,正反向测试套件全部PASS。

### 范围禁令

仅此5项,不得借机重构无关代码,不得新增本单未列的功能,不得触碰#2b/#4已闭卷的result_json/密封卡数值。发现超范围需求立即停工上报,不得自行夹带施工。不得使用reset/checkout等方式回退共享工作区中的用户改动。

---

## 我方评审 4 确认点(随终签一并批复,2026-07-13)

评审前提:五项攻击路径已逐项在实物上核实坐实——#1 措辞在 `holding_path.py:24`/`drawdown_strategy.py:19-20,257-258`;#2 = qbase `012 study_snap_batch()` 读引擎自报 GUC `shuheng.study_batches` 完整 JSON(taosha 侧 006 按 snapshot_id 查权威表,无此洞);#3 = `pool_b1_return.pool_batch_id` ingest 层有 FK 血缘但 manifest 生成处无交叉校验;#4 = `005` 出生白名单含 `frozen` 且要求配套 `frozen_at`;#5 = `007` `result_sha256` 裸 text 列库侧零校验。

1. **#2 存量回填**:既有 manifest#1(digest 2a8a271f)/#2(f660d76b)须在迁移时由受权角色回填镜像+attestation(回填本身留审计记录),否则 verify_integration 与一切既有 snapshot 读取全线 fail-closed 砖死。
2. **#1 legacy registry 收录范围扩为全部存量缺 schema 实验(含 frozen/done/closed,注明物化时 status)**,不只 registered——判据单一、普查显式;尤其 exp4(#3 holder_sell,frozen)是窗口关闭后第一个排产对象,不落规则缝。
3. **#5 用 BEFORE INSERT 触发器实现而非表 CHECK**(免追溯砸既有 probe 行 id2/3/7);施工第一步先实测存量正确锚(e3d2aef9/c010ce9d 等)与库算 digest 全等再上约束,digest 口径沿 007 注释既有约定 = sha256(result_json jsonb::text 规范化);不等则停工上报,不静默两套口径并存。
4. **施工序 #4→#5→#3→#2→#1**(小→大;#3 与 #2 代码相邻连做;#1 最大独立)。

## 流程位

本单 = 外审意见架构窗口分拣产物;终签即解除冻结令(仅限本单五项)。五项全毕、统一验收措辞成立("五种攻击尝试全部被拒,正反向测试套件全部PASS")后交人,随后按既定流程窗口关闭、恢复检验排产(#3 排产另下)。
