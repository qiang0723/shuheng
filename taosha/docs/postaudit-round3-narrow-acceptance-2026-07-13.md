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

**E2E 后全家福复跑(派生批换代+manifest 40 后)**:lineage **24/24**、集成 **7/7**(S1 幂等
复用 manifest 40=一致读向量)、探针 19/19、pap_gate 23/23、状态机 46/46、addendum 14/14、
镜像 11/11、合成 `3116ba9b` 不变。**集成双跑 result sha 受控漂移归因**:`3bef1f81`(第二轮
基线,manifest#2)→ `f145ac51`(本轮,manifest 40)——audit 块携带 snapshot_id/digest 随
E2E 再种换代而变;统计数据面零漂移之硬证=§5 第 11 行三组新旧批 0/0 逐行全等 + 合成 sha 不变。

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

**E2E 真实端到端实录(2026-07-13,aliyun,产物 /root/r3e2e/,日志 e2e.log):**

| # | 步骤 | 实测 |
|---|---|---|
| 1 | trade_cal 真实重拉(tushare,1990-2026 年片) | **fact_batch=8**,13,162 行;与批 5 业务列(exchange,cal_date,is_open,pretrade_date)双向差集 **0/0 逐行全等** → current 路由零行为变化,方准继续(不等即中止条款未触发) |
| 2 | 负半①:再种前研究 manifest `--create` | **拒**:`血缘不相容——market_return 批 2 的 qbase 源 trade_cal 锚=5 ≠ manifest=8`(死锁负半留档) |
| 3 | 源级快照发布 `--create-source` | **snapshot_id=38** digest `4aaadb65da9d…`,qbase 镜像+attestation 齐(经 qbase 016 分域;014 两半硬编码拒源级快照先坐实=P-B) |
| 4 | 引擎读源级快照(fail-closed 面) | run_drawdown_study --snapshot-id 38 → **拒**:`StudySnapshot manifest 38 缺 qbase/taosha 批次向量`(源级快照不可当研究 manifest 消费) |
| 5 | 再种 market_return(绑 38) | **market_batch=39**,8,186 行,双算闸 max\|Δret\|=6.5e-16,frozen_digest `b88a43ef…` 同 |
| 6 | 再种 pool_b1(绑 38)+ **真实并发①** | **pool_b1_batch=5**,2,948,735 行/8,068 评估日/均池 365.5;并发 trade_cal **批 9** 写入开始于 seed 运行中(CONC-T0 实录) |
| 7 | 再种 pool_b1_return(绑 38)+ **真实并发②(补强)** | **pool_b1_return_batch=5**,8,066 行,双算闸 1.68e-16,父池=5;并发 trade_cal **批 10** 的 **commit 落在 seed 运行窗口内**(CONC2-T1 实录 19:52:52 commit 时 seed 仍在跑,seed 19:55:32 结束) |
| 8 | 负半②(并发实测揪出):现值口径 manifest `--create` | **拒**:`market_return 批 39 的 qbase 源 trade_cal 锚=8 ≠ manifest=10`(并发新批推前现值向量→现值口径与锚不相容=fail-closed 正确)→ 补 `create(from_source_snapshot=N)`:研究 manifest 的 qbase 半=派生数据实际所出源向量(引擎一致读本义) |
| 9 | 研究 manifest `--create --from-source-snapshot 38` | **snapshot_id=40** digest `6691ba29d92d…` 生成+发布成功,content={qbase: 快照38向量(trade_cal=8), taosha: {market_return:39, pool_b1:5, pool_b1_return:5}} —— **新源快照发布→seed→新派生批→新研究 manifest 全链真实跑通** |
| 10 | 锚核对 | 三新批锚键集合==依赖集合不多不少(market/pret 5 键、pool 3 键,均无 forecast/stk_holdertrade),trade_cal=**8**(非并发批 9/10),绑定 snapshot_id=38;pret taosha_parent={pool_b1:5} |
| 11 | 数据全等(并发一致性判据) | market 批 2vs39=8186/8186 差集 **0/0**;pool 批 1vs5=2,948,735/2,948,735 差集 **0/0**;pool_return 批 1vs5=8066/8066 差集 **0/0** —— 并发批未泄漏进 seed 读径,血缘记录与实际读取数据在并发期间保持一致 |

配套修法(E2E 揪出,#3-b 题中之义):qbase 016(镜像触发器分域,源级快照可发布)、
`snapshot.create(from_source_snapshot=N)` + CLI、lineage F1/F2 与 verify_integration 幂等基准
改**一致读向量**(qbase 半=最新派生批绑定源快照之向量;现值口径在派生批换代后被正确拒,
套件在任意合法库态恒过)。

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
| #3-b 真实端到端(新快照发布→seed→新派生批→新 manifest),非静态 --dry | §5 E2E 实录:trade_cal 批 8→源快照 38→三批再种(39/5/5)→研究 manifest 40 全链真实成功 | **PASS** |
| 真实并发测试(seed 绑定快照期间并发写新 qbase 批次) | §5 E2E 并发①(批 9 写入始于 pool_b1 seed 运行中)+并发②(批 10 commit 落在 pool_b1_return seed 窗口内)+§5 第 10/11 行(锚=8 非 9/10;数据 0/0 全等) | **PASS** |

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
- `750ef25` #1 施工(#1-a fills + #1-b 代理规则 + qbase 015)
- `3a6b1cb` #3 施工(#3-a 依赖锚 + #3-b 源级快照 + taosha 014)
- `346475b` lineage 套件修(F5 三批探针/savepoint)
- `e172315`+`8fc4245` qbase 016 镜像分域(E2E Stage2b 坐实后配套)
- `53521ef` create(from_source_snapshot)(E2E 并发实测揪出)
- `b071e33` STATE 施工实况 + 验收档骨架
- `f46d4e8`+`4fc4663` lineage F1/F2 与 integration 幂等基准=一致读向量(套件环境无关化)
- 本验收档终稿 + STATE 收口(见 git log 末)

## §9 待人批项
- **#1-b 代理规则冻结文本**(留痕档末节〔#1-b 代理规则拟冻结文本〕)——实现与其逐字一致,
  随本验收档交人批冻结。

## §10 范围合规(diff --stat;**2026-07-13 外部复核后更正版**)

**完整实物 `8ea6b12..84f77c7`:18 文件 +1327/−96**(外部第二独立视角复核核对数,已复算全等)。

> **⚠️更正记录(改判纪律,原数作废):** 本节原记两数均误——
> ①原标题数"16 文件 +1180/−95"=`8ea6b12..4fc4663` **排除留痕档(docs/postaudit-round3-narrow-order)
> 与 ops/STATE 的代码面子口径**(已复算全等:`git diff --stat 8ea6b12..4fc4663 -- ':!ops/STATE.md'
> ':!docs/postaudit-round3-narrow-order*'` = 16 files, +1180/−95),但未标注排除口径,读作全量即误;
> ②原"全范围 18 文件 +1270/−96"统计时点=代码终 `4fc4663`,漏计终稿 commit `84f77c7` 自身
> (本验收档终稿+STATE 收口,2 文件 +67/−10)——验收档写就时无法包含它自己的终稿 commit,
> 属自引用盲区。此类"至代码终"口径此后作废:范围合规一律以**完整实物区间(基..最终 HEAD)**记数,
> 验收档自身行数变动照实计入,终稿后如需可另附增补更正(如本节)。

代码面(taosha+qbase,含本验收档;至 `4fc4663`,排除留痕档与 STATE 的子口径,仅供文件级归属阅读):16 文件 +1180/−95

```
 qbase/sql/015_explore_reader_open_limit.sql        | 198 +++++++  (#1-b 开盘时点列)
 qbase/sql/016_mirror_source_snapshot.sql           |  35 ++      (#3-b 镜像分域)
 taosha/compute/holding_path.py                     | 151 ++++--   (#1-a 字段+#1-b 代理规则)
 taosha/docs/postaudit-round3-narrow-acceptance-*.md| 180 ++++    (本验收档骨架)
 taosha/engine/drawdown_strategy.py                 |  53 ++-     (#1-a fills+代理声明)
 taosha/engine/report.py                            |  14 +       (#1-a 成交明细段)
 taosha/experiment/snapshot.py                      |  85 ++-     (#3-a 映射+#3-b 源级快照)
 taosha/experiment/verify_pap_gate.py               |  93 ++--    (E1 字段化+E3/E4)
 taosha/harness/verify_integration.py               |  19 +-      (一致读向量幂等)
 taosha/harness/verify_manifest_lineage.py          | 197 +++--   (T1/F5/F6/F7/R11-R13)
 taosha/ingest/seed_market_return.py                |   3 +-     (#3-a 依赖锚)
 taosha/ingest/seed_pool_b1.py                      |   4 +-     (#3-a 依赖锚)
 taosha/ingest/seed_pool_b1_return.py               |   3 +-     (#3-a 依赖锚)
 taosha/reader/contract.py                          |  15 +-     (#1-b 契约列)
 taosha/reader/view.py                              |   8 +-     (#1-b SELECT 列)
 taosha/sql/014_dep_anchor_source_snapshot.sql      | 217 ++++++  (#3-a/#3-b 迁移)
```

全范围含留痕档与 ops/STATE:完整实物 `8ea6b12..84f77c7` = **18 文件 +1327/−96**(~~原记
"18 文件 +1270/−96"作废:统计时点在代码终 `4fc4663`,漏计终稿 commit 自身 +67/−10,见上更正记录~~)。
**#2/#4/#5 实现零触碰**:未触碰文件包括 pap.py 执行门(011/012 迁移域)、008/009 出生态迁移、
007/009 addendum 锚定、014(qbase)镜像表结构与 attestation 流程本体、survivors 单一主干——
016 仅分域镜像触发器函数一处判断(研究 manifest 检查逐字保留)。无新增制度:源级快照复用
同表/同 digest/同发布机制;fills/open_limit_status 为人令四条的直接实现面。

---

## §11 判别力并发补测(外部复核回件令,2026-07-13;隔离验证环境)

> 人令原文=`docs/postaudit-round3-disc-order-2026-07-13.md`(留痕 commit `669c282`)。复核判点:
> §7 E2E 的并发批 9/10 与锚定批 8 业务内容逐行相同,"0/0 全等"对"seed 实际读了哪个批次"**无判别力**。
> 本节=可区分内容(水印)并发补测,直接证明实际读取数据内容来自批 8。**零生产代码改动、零生产库写入。**

### §11.1 隔离验证环境(实物)

- 库:`qbase_iso` / `taosha_iso` = 生产两库同机 `CREATE DATABASE … TEMPLATE` 全量克隆
  (2026-07-13 21:17,触发器/角色权限/快照 38 镜像+attestation/全部批次随库);水印批仅存 iso 库。
- 代码:`/root/r3disc/quant` = git clone,HEAD `669c282` 与生产 `/opt/quant` 逐字节同源(git 证),
  工作树干净;`.env` 仅 dbname token 改指 iso 库(QBASE_APP_DSN/TAOSHA_APP_DSN,秘钥不落日志)。
- 运行身份:seed 与水印写入均走 qbase_app/taosha_app 应用角色 = 与真实并发回填同权限路径。

### §11.2 水印设计(内容可区分,且若被误读必然改变产出)

水印批 = 批 8 全量拷贝(13,162 行)、仅 5 行 `is_open` 翻转:

| 探针日 | 批8 | 水印 | 误读水印的必然后果 |
|---|---|---|---|
| 2000-01-04 / 2015-06-15 / 2023-06-15 | 1 | **0** | 三日从日历视图消失 → 产出必缺这三行 |
| 1992-10-04 / 1993-01-03 | 0 | **1** | 两日在钉批价视图有真实 bar(1/2 根,实测)→ 产出必新增行 |

可区分性实录:`W1 EXCEPT 批8`=**5/5**(双向,逐行=上表)、`W2 EXCEPT 批8`=5/5;对照旧并发批
`批9 EXCEPT 批8`=**0/0**、`批10 EXCEPT 批8`=**0/0**(复核判点坐实=旧测无判别力的实录)。
holdout 前开市日数:批8=8187,水印=8186(−3+2)。

### §11.3 两跑实录(seed 绑快照 38〔trade_cal=8〕运行期间并发提交水印)

| | RUN1 `seed_market_return` | RUN2 `seed_pool_b1_return` |
|---|---|---|
| seed 运行窗(DB 钟) | 21:30:33.057 → 21:34:31.737 | 21:34:31.750 → 21:38:10.554 |
| 水印批 commit | **批 11**,21:32:02.066(窗内) | **批 12**,21:35:24.175(窗内) |
| commit 时点相位 | Python 主读相位开始后 0.16s(15M 行主读几乎全程在水印后) | Path A 聚合开始后 0.24s |
| SQL 独立复算相位起点 | 21:33:17.5(**全程在水印后**) | 21:36:39.5(**全程在水印后**) |
| rc / 落库 | 0 / 批 **64**,8,186 行 | 0 / 批 **12**,8,066 行(pool_batch=5) |
| 双算闸 | max\|Δret\|=6.523e-16,n 不一致=0 | max\|Δret\|=1.683e-16,n 不一致=0 |

### §11.4 直接证据①——实际读取的数据内容来自批 8(非水印)

- **翻关探针日行在且值全等**:RUN1 产出批 64 含 2000-01-04(ret=0.02771499487837608,n=911)/
  2015-06-15(−0.019313055336540538,2314)/2023-06-15(0.0031658463890428144,4976),
  与既有批 39 三日逐值全等(=True×3);若读水印,此三日不在日历,行**不可能存在**。
- **翻开探针日行缺**:批 64 在 1992-10-04/1993-01-03 行数=**0**;若读水印(is_open=1 且钉批价
  视图实测有 bar),此两日**必然出现**在产出。
- **全量内容**:批 64 EXCEPT 批 39 = **0/0**(8,186 行逐行,trade_date/ret_eqw/n_stocks);
  RUN2 批 12 EXCEPT 批 5 = **0/0**(8,066 行逐行),翻关三日值与批 5 全等(True×3)、翻开两日行数 0。
- **反事实通路实录**:两跑后 iso 库 max(trade_cal 批)=12=水印,探针日在 max 批上全为翻转值
  ——若 seed 走 current/max 路由(旧作废模式),读到的即水印内容;产出与批 8 全等、与水印矛盾
  = 实际读取源=批 8,判别力成立。

### §11.5 直接证据②——source_anchor 记录的确实是批 8

- RUN1 批 64 `source_anchor`:qbase 向量 `{daily:6, trade_cal:8, adj_factor:7, namechange:7,
  stock_basic:6}` + `source_manifest={snapshot_id:38, digest:4aaadb65…f72643}`(64 位全串在案)。
- RUN2 批 12 同向量 + `taosha_parent={pool_b1:5}` + 同 source_manifest。
- 两锚 trade_cal=8,**≠** 水印批 11/12;锚向量==快照 38 镜像向量(attestation 在案)。

### §11.6 复核"不接受"三条逐条对上

- ~~相同内容批次对照~~ → 水印与批 8 双向 EXCEPT 5/5(§11.2),批 9/10 的 0/0 已列为反面对照;
- ~~静态多次复现~~ → 两跑各自在运行窗内真实并发 commit(时间戳=DB 钟,§11.3),且 SQL 复算
  相位全程在水印之后仍与批 8 全等;
- ~~仅检查 anchor 字段~~ → §11.4 为产出数据内容级交叉验证(探针日行在/行缺+逐值全等+全量
  EXCEPT),§11.5 的 anchor 为第二证据而非唯一证据。

### §11.7 生产零触碰(令内约束核验)

生产 qbase trade_cal 批次清单跑后仍=`5,8,9,10`(无新批);生产 taosha market/pool_return max
批仍=39/5;生产 `/opt/quant` git porcelain=0 行。水印批 11/12 仅存 `qbase_iso`。

产物:`/root/r3disc/`(evidence.json + orchestrate.log + mret_seed.log/pret_seed.log 逐行时间戳
+ orchestrate.py 编排件);iso 两库暂留待外部复核质询,关窗后处置请人令。

**补测验收措辞:水印并发批在 seed 运行窗内提交且对 current/max 路由可见,seed 产出数据内容
逐行来自锚定批 8(探针日行在/行缺与逐值全等、全量 EXCEPT 0/0),source_anchor=批 8;
判别力并发补测通过。**
