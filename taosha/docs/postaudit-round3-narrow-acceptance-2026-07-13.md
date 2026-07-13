# 外审第三轮窄补验收档(#1-a/#1-b/#3-a/#3-b,2026-07-13)

- 人令原文+人批注记+#1-b 代理规则拟冻结文本:`docs/postaudit-round3-narrow-order-2026-07-13.md`(留痕 commit `67150fb`)
- 范围禁令:仅 #1/#3 四条;#2/#4/#5 实现零触碰(§10 diff --stat 复核)
- 统一验收措辞(第三轮窄补口径):**"四条窄补反向攻击尝试全部被拒,正反向测试套件全部 PASS,合法再种链真实端到端跑通。"**

---

## §1 #1-a · fill 证据直接断言(五要素)

**攻击路径复述(施工前坐实):** E1 判据原文=`net = res["strategy_version"]["net"]["mean"]` 与
−0.07188319 比对(`verify_pap_gate.py` 旧 125-129 行)= 用聚合净收益反推成交价;result 无任何
事件级 fill 字段;报告无成交明细段。

**结构修法:**
- `compute/holding_path.py`:HoldingPath 增 `trigger_idx`(收盘确认决策 bar;从未触发的右删失
  =None)+ `fill_source`(值域 `FILL_SOURCES`={same_close, postponed_close, next_open,
  postponed_open, censored_close_mark};`censored_close_mark`=末端 close 截断,**标记非成交**,
  `__post_init__` 值域校验);全部 6 个构造点显式赋值,无默认兜底。
- `engine/drawdown_strategy.py`:result 新增 `strategy_version.fills` 块=事件级全量
  `records[{event_id, ts_code, entry_date, entry_price, signal_date, fill_date, fill_price,
  fill_source, right_censored}]` + `n` + `by_source` 计数 + 能力边界 note。
- `engine/report.py` render_strategy 新增〔成交明细〕段:**直接消费 fills 字段渲染**(样例 5 行
  +全量指针+by_source),非由净收益倒推展示。

**正向控制:** 引擎冒烟直接断言字段值(signal_date=dates[345]/fill_date=dates[346]/
fill_price==95.0/fill_source=='next_open'/entry 四值);pap_gate E1 改为**字段直接断言**
(净收益比对降为交叉项,不再是判据本体)。

**反向测试:** holding_path 自检 #1-a 段:same_close 域 trigger_idx/fill_source 四路径断言
(same_close/postponed_close/censored_close_mark×2、从未触发 trigger_idx=None);fill_source
非法值 `__post_init__` 拒。

**权限/迁移/回滚边界:** 纯代码件,无迁移;回滚=revert commit `750ef25` 对应段。

## §2 #1-b · next_open 可成交判定禁用日终信息 + 冻结代理规则(五要素)

**攻击路径复述(施工前坐实):** `holding_path.py` 旧 161-163 行 next_open 顺延判定调
`_sellable(limit_status[k], closes[k], closes[k-1])`——`limit_status`/`close` 均为日终字段=
决策使用决策时点之后信息。**真实数据量化:current 视图 15,098,一四行中,"收盘跌停但开盘不在
跌停位"= 119,532 行**(人令反例类,旧实现在这些日错误顺延);另"一字跌停⇒开盘在跌停位"违例
=0(一字跌停日开盘本就在跌停位,口径闭合自证)。

**结构修法:**
- **qbase 015 迁移**(两 prices 视图,current+_snap 同式,列尾增 `open_limit_status`):
  开盘时点口径=原始 open 恰在 `round(原始前收×(1±limit_pct),2)` 价位 →
  'open_at_down_limit'/'open_at_up_limit'/'none';**limit_pct 复用两视图既有口径**(主板 10%/
  ST 5%/创业板 2020-08-24 后 20%/科创板 20%,原始价分位取整;口径唯一,CTE 同一表达式)。
- 契约:PRICE_COLUMNS 末列增 open_limit_status(值域 OPEN_LIMIT_STATUS,PriceRow 校验;
  合成默认 'none'=既有语义零扰动);ViewReader SELECT 增列。
- `holding_path._sellable_at_open`(**冻结代理规则**,拟冻结文本=人令留痕档末节):
  R-open-1 opening print 存在(open 有值>0)+ R-open-2 开盘价不在跌停价位;两条均开盘时点
  可得;next_open 分支唯一可成交判定,~~日终 _sellable~~ 在该分支作废;`open_limit_status`
  缺失 → ValueError(fail-closed,防日终判定复燃)。same_close legacy 域语义一字不动。
- **能力边界声明(人令,不得夸大)**焊进三处:代理规则 docstring、result
  `execution.fill_feasibility_proxy_rule`、fills.note——"市场存在开盘成交/开盘价不在跌停位
  ≠ 我方委托单能排上队成交(排队优先级不可得);日线代理规则,非真实委托成交验证,不得表述
  为'已验证真实可成交'"。

**正向控制:** 引擎冒烟断言 fill_feasibility_proxy_rule 在场含"非真实委托成交验证";
值域交叉断言 compute.OPEN_AT_DOWN_LIMIT ∈ reader.contract.OPEN_LIMIT_STATUS(口径唯一两处一致)。

**反向测试(人令统一验收要求逐条):**
- pap_gate **E3(人令反例)**:名义成交日 open=97 可成交(开盘时点字段 'none')而**收盘跌停**
  (limit_status='limit_down')→ 断言 fill_date=当日/fill_price=97.0/fill_source='next_open'
  =**不顺延**(旧实现误顺延将取次日 open=91.0,数值可分辨);
- pap_gate **E4**:开盘恰在跌停位('open_at_down_limit')→ 按代理规则顺延,
  fill_source='postponed_open';
- holding_path 自检 N2b(同反例纯函数层)+ next_open 缺 open_limit_status 拒;
- N2/N5 原"日终跌停顺延"样例按新代理规则改判为"开盘跌停位顺延"(期望值改判逐条归因=本节,
  非删自检,宪章⑦)。

**权限/迁移/回滚边界:** qbase 015=CREATE OR REPLACE 两视图列尾增列(既有列名/序/类型不变,
授权保留,taosha_engine 仅 _snap SELECT 不扩);回滚=重放 010/012 视图定义。apply 身份
qbase_app(属主链承 008/010/012)。

## §3 #1 回归全家福(施工后)

| 套件 | 结果 |
|---|---|
| verify_pap_gate(E1 字段化+E3/E4 新增) | **23/23 PASS** |
| verify_state_machine | 46/46 |
| verify_addendum | 14/14 |
| verify_snapshot_mirror | 11/11 |
| verify_study_snapshot --mode probes | 19/19 |
| verify_manifest_lineage | 17/17(#3 施工前)→ **24/24**(#3 施工后) |
| verify_integration(双跑 sha) | 7/7 |
| 合成域零回归(make_ashare_fixture→run_ashare_study 双跑) | **sha `3116ba9b74f7c53b…` 逐字节同基线** |
| holding_path / drawdown_strategy / cleaning 模块自检 | 全绿 |

## §4 #3-a · 派生批锚=实际依赖键集合(五要素)

**攻击路径复述(施工前坐实):** 三 seed 锚=`{"qbase": snap_content["qbase"]}` 整向量
(seed_market_return.py:218 等);013 derived_batch_bi:83 要求锚==manifest qbase 半**全向量
全等**→ 与派生批无依赖的源(forecast/stk_holdertrade)刷新即令批次"不相容"。施工前探针
P-A:全向量锚批 INSERT 在 013 下**放行坐实**(batch_id=23,回滚)。

**结构修法(依赖键映射表=本节交付物):**

| 派生批次表 | 实际 qbase 依赖键(不多不少) | 依据(seed 实际读径) |
|---|---|---|
| market_batch | adj_factor, daily, namechange, stock_basic, trade_cal | explore_reader_prices_snap(bar_daily×adj_factor×entity_master×entity_alias 四源内联)+ calendar_snap(trade_cal) |
| pool_b1_batch | daily, stock_basic, trade_cal | bar_daily_snap.amount(原始额不复权,无 adj_factor)+ entity_master 上市界 + calendar_snap;不读 namechange |
| pool_b1_return_batch | adj_factor, daily, namechange, stock_basic, trade_cal | 同 market 读径;taosha 父池批走 taosha_parent 锚(非 qbase 键) |
| (非依赖,不入锚) | forecast, stk_holdertrade | 三派生批均不读;其刷新不得使派生批"不相容"(F5 实证) |

- 映射双权威镜像:python `snapshot.DERIVED_BATCH_QBASE_DEPS` ↔ SQL `_derived_qbase_deps()`
  (taosha 014),lineage T1 逐键交叉断言。
- taosha 014 `derived_batch_bi`:锚 qbase 键集合==依赖集合**不多不少**(多键=过锚/少键=依赖
  不可证均拒)+ 逐键与所绑快照相等(**快照可含更多键**=人令"不要求全量 qbase 向量相等");
  ~~013 全向量全等~~作废。承 013:严格 schema/绑定库内真实快照/digest 逐字/pool 父批锚行一致。
- manifest 生成双检(study_snapshot_biu)沿 013 逐键相容(锚键⊆manifest 且值等)——锚瘦身后
  语义自动收敛为"只比对该批次实际依赖的键"(人令验收点,F5 实证)。
- 三 seed 锚改 `snapshot.anchor_qbase_deps(<table>, snap_qbase)`(缺依赖键 fail-closed)。

**注记(历史锚不改写):** 存量 registry 4 verified 锚=全向量式**历史事实**(当时确实绑读了
整个快照向量),append-only 不改写;manifest 双检只查所引批次的锚,#3-b 真实再种后最新批
换代为依赖键锚(F5 用依赖锚探针证换代后语义;F7 反证换代前 fail-closed 未弱化)。

**正向控制:** lineage F2(依赖键锚批落库+入 manifest)/F5(**无依赖源 stk_holdertrade 刷新
→manifest 放行**=#3-a 验收点)/T1 映射交叉断言。

**反向测试:** R11 全向量锚(含 forecast/stk_holdertrade)拒=施工前 P-A 反转;R12 少键锚
(缺 trade_cal)拒;R9 依赖键值≠所绑快照值拒;R6/R7/R8/R10 承前轮全保留。

**权限/迁移/回滚边界:** taosha 014 apply 身份=postgres(承 001-013);前置断言=registry 4 锚
过 schema 且与 manifest#1 逐键相容(不过即中止);回滚=重放 013 两触发器+DROP _derived_qbase_deps。

## §5 #3-b · 合法再种路径实测跑通(五要素)

**攻击路径复述(施工前坐实=循环死锁):** 013:18 自认"刷新既有源批次→新 manifest 拒生成";
而 seed 必须绑**已发布**快照(read_published_snapshot fail-closed),发布=生成 manifest 又被
013 拒 → 死锁。施工前探针 P-B:源级快照(仅 qbase 半)INSERT 在 013 下**被拒坐实**
("content 须含 qbase 与 taosha 两半批次向量")。

**结构修法:** 源级快照解耦(taosha 014 分域+qbase 016 镜像分域+snapshot.create_source/
`--create-source`)——同表同 digest 同发布机制(镜像+attestation),content 仅 qbase 半=源级
快照标识;研究 manifest 的 013 全检逐字保留;引擎消费面 fail-closed(ViewReader 拒缺 taosha
半,E2E 实测)。合法链=刷新源→源级快照→三 seed 绑之再种→研究 manifest。

**E2E 真实端到端实录(2026-07-13,aliyun,产物 /root/r3e2e/):**
<!-- E2E_RESULTS -->

**权限/迁移/回滚边界:** qbase 016=CREATE OR REPLACE 镜像触发器函数(apply 身份=postgres,
镜像防拆链属主,qbase_app 实测被拒);回滚=重放 014 定义。E2E 产生的新批次/快照全部
append-only 落库,是真实生产事实,不回退(trade_cal 批 8 与批 5 逐行全等已核=路由零行为变化)。

## §6 #3 反向测试与正向套件映射(统一验收要求逐条)

| 人令要求 | 实物 | 结果 |
|---|---|---|
| #1-a/#1-b 新增测试直接断言 fill_date/fill_price 字段值 | pap_gate E1(字段断言)+引擎冒烟+holding_path #1-a 段 | PASS |
| "当天 open 可成交但收盘跌停"反例正确处理(不顺延) | pap_gate E3 + holding_path N2b(fill=当日@97,fill_source=next_open) | PASS |
| #3-a 依赖键映射表交付 | §4 表 + DERIVED_BATCH_QBASE_DEPS↔_derived_qbase_deps(T1) | PASS |
| manifest 只比对该批实际依赖键,不要求全量向量相等 | lineage F5(stk_holdertrade 刷新放行)+R11(全向量锚拒) | PASS |
| #3-b 真实端到端(新快照发布→seed→新派生批→新 manifest),非静态 --dry | §5 E2E 实录(真实 trade_cal 批 8→源快照 38→三批再种→研究 manifest) | <!-- E2E_STATUS --> |
| 真实并发测试(seed 绑定快照期间并发写新 qbase 批次) | §5 E2E 并发段(pool_b1 再种中真实写入 trade_cal 新批) | <!-- CONC_STATUS --> |

## §7 施工前探针 → 施工后反转(fail-closed 方向证明)

| 探针 | 施工前(013/旧代码) | 施工后 |
|---|---|---|
| P-A 全向量锚批 INSERT | 放行(batch_id=23,坐实) | R11 拒 |
| P-B 源级快照 INSERT | 拒(死锁坐实) | F6/E2E 放行+发布 |
| 反例类(收盘跌停开盘可成交) | 旧 _sellable 顺延(前视) | E3/N2b 当日 open 成交 |
| 源刷新后研究 manifest | 拒(负半留档:trade_cal 锚=5≠manifest=8) | 再种后放行(E2E) |
| 源刷新后只种一批 | — | F7 仍拒(fail-closed 未弱化) |

## §8 commit 链
- `67150fb` 裁决留痕(人令原文+人批注记+代理规则拟冻结文本)
- `750ef25` #1 施工(#1-a fills+#1-b 代理规则+qbase 015)
- `3a6b1cb` #3 施工(#3-a 依赖锚+#3-b 源级快照+taosha 014)
- lineage 套件修 + qbase 016 镜像分域 + 本验收档(见 git log)

## §9 待人批项
- **#1-b 代理规则冻结文本**(留痕档末节〔#1-b 代理规则拟冻结文本〕)——实现与其逐字一致,
  随本验收档交人批冻结。

## §10 范围合规(diff --stat)
<!-- DIFFSTAT -->
