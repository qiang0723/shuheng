# 外审第二轮窄补验收档(#1 执行消费 + #3 血缘严格化,2026-07-13)

- 施工单:`docs/postaudit-round2-narrow-order-2026-07-13.md`(人转达外部第二独立视角复审原文,F 条留痕 commit `b0bdebb`)
- 复审结论承接:#2/#4/#5 通过;**#1/#3 退回窄补**,范围三条钉死+四项反向测试。
- 开工前 HEAD 锚 `c4ce3c8`;施工 commit:`3c521c4`(窄补#1)/`4a2bfdd`(窄补#3);迁移 taosha `012`/`013` 已 apply(postgres 属主)。
- 范围禁令遵守声明:未触碰已通过的 #2/#4/#5 实现(qbase 014/taosha 008/009/010/011 零改动;011 的 `_pap_freeze_gate` 经 012 `CREATE OR REPLACE` 升级 preclose 分支属窄补令第 3 句直接辖区);不碰闭卷 result_json/密封卡数值;§10 附 `git diff --stat` 供范围合规性核对。

---

## 一、窄补#1:策略引擎必须真正消费 strategy_execution

### 1. 现状攻击路径复述(施工前探针坐实,全回滚零残留)

- **P-D(引擎静默旧口径)**:合法 close_to_next_open PAP 通过层①校验后实跑合成单事件,
  实际成交仍=触发日同刻收盘——net=−0.12073144(同刻口径),次日开盘口径应为 −0.07188319。
  根因:`run_strategy` 从头到尾未读 `pap["strategy_execution"]`,`simulate_holding_path`
  只有附录G 同刻 close 成交一条路径;校验(修法#1 第一轮)只挡冻结,不辖执行。
- **P-C(反向时间窗口可冻结)**:preclose_to_tail `decision_cutoff="15:00"` 晚于
  `fill_window.start="14:55"`,冻结**放行**(exp_id=77 探针,回滚)——011 的 gate 对
  preclose 字段停留在"字符串非空 + LIKE close_confirmed"判定,自由文本/反序时间全可过。

### 2. 结构修法

- **单一执行门** `engine/drawdown_strategy.resolve_execution(pap)`:读取并校验
  `strategy_execution`(复用层① `validate_strategy_execution`)→ 查
  `IMPLEMENTED_EXECUTION_PROFILES = {"close_to_next_open": "next_open"}` →
  白名单内但**未实现**(preclose_to_tail)→ `SystemExit` 显式拒,**不得静默旧口径兜底**。
  调用点两处=驱动层(`run_drawdown_strategy.py`,先于一切取数)+引擎(`run_strategy` 开头)
  ——双闸同一实现,无第二判定路径。
- **close_to_next_open 真实现**:`compute/holding_path.simulate_holding_path` 增
  `fill_mode` 参数(非法值 raise):
  - `'next_open'`=收盘确认决策(附录G 判据不变:成本×0.8 强平/收盘破 ma20 先到先出)
    → **次一 present-bar 后复权 open 成交**(fill_price=next_adjusted_open 冻结值);
    该 bar 不可成交(跌停/一字跌/open 缺)→ 顺延至首个可成交 bar 的 open,顺延天数自名义
    成交 bar(触发次日)起计、>20 交易日极端单列(G4 上限条款同式);触发后至样本末无可成交
    bar(含触发即末 bar)→ 末端 close 截断(G5 mark-to-market,非成交)。
  - `'same_close'`=附录G 原口径,**语义仅 legacy 域保留**(策略驱动对 legacy 一律拒,
    修法#1 层③)——生产不可达;既有 G1-G8 自检用例零改动=决策判据零回归。
- **preclose_to_tail 结构化时间字段**:python 层①(pap.py)+库层②(012 迁移
  `_pap_freeze_gate`)同则——`decision_cutoff` 须 `'HH:MM'`(正则,拒自由文本);
  `fill_window` 须 `{"start":"HH:MM","end":"HH:MM"}`;**代码层强制断言
  decision_cutoff < fill_window.start**(及 start < end);~~"字符串非空+LIKE
  close_confirmed"~~ 作废。该 profile 状态=**可冻结、不可执行**(pap.py 注记明示:
  日内数据足以支撑真实执行前不得宣称"已可执行";执行拒在 resolve_execution)。

### 3. 正向控制

- 引擎冒烟(合成单事件,idx345 收盘破 ma20 确认、idx346 open=95):成交=**95.0(次日
  后复权 open)≠ 90.0(旧同刻 close)**,net 手算逐位一致;基准 BH 跨度含成交日(H=16)
  手算一致;result 新增 `strategy_version.execution` 块(profile/decision/fill 显式留痕)。
- `verify_pap_gate` F3:结构化合法 preclose_to_tail(14:50 < 14:55 < 15:00)冻结照常放行
  (白名单地位不变);F2 合法 close_to_next_open 冻结放行。
- holding_path N1-N5 新用例:次日 open 成交/顺延 open/触发即末 bar 截断/open 缺顺延/
  >20 交易日极端标注;同序列 same_close 对照=触发日 close(两口径分流、决策判据同一)。

### 4. 反向攻击测试(窄补令四项之①②)

| 令定测试 | 实测 | 结果 |
|---|---|---|
| ① 合法 close_to_next_open PAP 冻结后,断言实际成交=次日开盘非旧同刻收盘 | `verify_pap_gate` **E1**:探针行 DB 冻结(层②真过闸)→读回冻结 pap_json→引擎实跑→net=−0.07188319==次日开盘口径,≠旧同刻 −0.12073144;profile 留痕核对 | **PASS(拒旧口径)** |
| ② decision_cutoff 晚于 fill_window 起点 → PAP 冻结拒 | **R8**:15:00 ≥ 14:55 冻结拒(库层②断言);python 层①同则自检拒;施工前 P-C 放行→施工后拒 | **PASS(全拒)** |

加测:E2=结构化合法 preclose_to_tail 实跑→`SystemExit("…未实现…fail-closed 拒运行")`
(证"校验通过≠可执行"、无兜底);R9=decision_cutoff 自由文本冻结拒;R10=fill_window
非结构化冻结拒;引擎冒烟内=缺 strategy_execution/白名单外 profile 全 raise。

### 5. 权限/迁移回滚边界/验收实物

- 权限零变更(012 仅 CREATE OR REPLACE 函数,属主 postgres 承 001-011)。
- 回滚边界:`_pap_freeze_gate` 重放 011 定义、DROP `_hhmm_minutes()`(012 文件头注明);
  既有 frozen 行不受扰(gate 仅辖 registered→frozen 迁移)。
- 实物:`verify_pap_gate` **21/21 PASS**(16→21;E1/E2/R8/R9/R10 新增)、
  `python -m taosha.experiment.pap` 层①自检(新增 4 反向)、holding_path/引擎冒烟全绿。

## 二、窄补#3:source_anchor 严格 schema + 血缘真相容 + seed 绑快照

### 1. 现状攻击路径复述(施工前探针坐实,全回滚零残留)

- **P-A(空锚)**:`source_anchor='{}'::jsonb` 批次 INSERT **放行**(batch_id=5 探针,回滚)
  ——010 的 `derived_batch_bi` 仅查 `IS NOT NULL`。
- **P-B(伪锚入 manifest)**:锚 qbase 向量全伪造(全键=999999)的批次落库后,引用它的
  manifest **生成放行**(snapshot_id=8 探针,回滚)——010 的 `_batch_lineage_trusted`
  仅查"锚是否非 NULL",从不比对向量。
- **代码面(seed 先记锚后读)**:三 seed 均"`collect_qbase_vector` 记 current/max 现值为锚
  → 再多次独立查询 current 视图取数"(seed_market_return 原 L206 记锚,L207/212/215 三次
  查 current 视图)——并发回填窗口下锚与实读数据可不一致("稳定复现但血缘不一致")。

### 2. 结构修法(013 迁移 + 三 seed)

- **严格 schema**(单一来源 `_anchor_schema_reason(jsonb)`,批次触发器与 manifest 双检共用):
  锚须为非空对象,含 `qbase`(非空源批次向量,值全为数值)+ `source_manifest{snapshot_id
  (数值), digest(64 位小写 hex)}`;`{}`/缺任一关键字段/类型不符 → 拒,原因逐字返回。
- **批次 INSERT 绑定真实性**(`derived_batch_bi` 升级):锚绑定的 `snapshot_id` 须在
  `study_snapshot` 在位、`digest` 与库内逐字一致(拒伪锚)、锚 `qbase` 向量 == 该 manifest
  的 qbase 半(锚必须=实际所读已发布快照向量);`pool_b1_return_batch` 另须
  `taosha_parent.pool_b1 == 行内 pool_batch_id`。
- **manifest 生成双检升级**(`study_snapshot_biu`,承 006/010 全检):三派生批各解析锚
  (行内 `source_anchor` 优先,历史批走 registry verified 锚;不可证→拒)→ 锚过严格
  schema(空锚经属主旁路也进不了 manifest)→ **qbase 向量逐键相容**:锚中每一源键须在
  `NEW.content->'qbase'` 在位且批次号相等,任一不等即 RAISE 拒生成——~~仅"是否非
  NULL"检查~~ 作废(`_batch_lineage_trusted` 已 DROP)。相容口径=锚键⊆manifest 键且值
  全等(manifest 多出的新源键不冲突;既有源刷新则旧派生批与新向量不相容→fail-closed,
  再种流程届时人令排产,不留后门)。
- **seed 绑定已发布快照**(三件全改,`--source-snapshot-id` 必填):
  `snapshot.read_published_snapshot` 读 qbase 权威镜像(mirror+**attestation** 双在,
  任一缺→拒,fail-closed)→ 锚={该快照 qbase 向量, source_manifest{id,digest}} →
  读径=同一连接 GUC `shuheng.study_snapshot_id` 路由:seed_market_return/
  seed_pool_b1_return 走 `explore_reader_{prices,calendar}_snap` 快照视图;seed_pool_b1
  直读底表处批次改 `study_snap_batch('daily'/'stock_basic')`(同一 manifest 钉死)。
  **锚与读取同源于同一已发布不可变快照**——"先记 current 锚、再查 current 视图"模式
  作废,并发回填窗口消除。taosha 父池批(pool_b1_membership)本就按显式 batch_id 读取
  (append-only 钉死、无 current 再查询窗口),保持并入锚 `taosha_parent`。

### 3. 正向控制

- **三 seed --dry 实测(绑定已发布 snapshot#1,digest 2a8a271f…;全部只读不落库)**:
  快照读径逐值复现各自在库 batch#1(qbase 零新批期,快照读径=当时 current 的钉死版,
  数据一致性实证)——
  - seed_market_return:8186 收益日 [1990-12-20..2024-06-28],双算闸 max|Δret|=6.523e-16
    /n 全等,硬闸过(==在库 market batch#1 8186 行);
  - seed_pool_b1_return:8066 收益日 [1991-06-10..2024-06-28],n_pool_stocks∈[1,1015]
    均 359.3,双算闸 max|Δret|=1.683e-16/n 全等(==在库 pool_b1_return batch#1,连双算闸
    数值 1.683e-16 与当时验收档同);
  - seed_pool_b1:池成员 2,948,735 行/8068 评估日/平均池 365.5/[1991-06-10..2024-06-28]
    (==在库 pool_b1 batch#1 逐值同)。
- 013 前置断言(焊进迁移):存量 4 历史批 registry 锚全过严格 schema 且与 manifest#1 向量
  逐键相容(不过即迁移中止,不带病上线)——apply 实测通过。
- `verify_manifest_lineage` F1(现值向量 manifest 生成放行,历史批经 registry)/
  F2(严格 schema 锚新批落库+manifest 引用放行)照常绿=合法路径未被误伤;
  `verify_integration` S1 manifest#2 幂等复用照常。

### 4. 反向攻击测试(窄补令四项之③④)

| 令定测试 | 实测 | 结果 |
|---|---|---|
| ③ source_anchor={} 空锚 → 拒 | 批次层:**R6** INSERT 拒(施工前 P-A 放行→施工后拒);manifest 层:**O1 属主旁路探针**=registry 植入 verified 空锚行(模拟历史残留)→ manifest 生成 RAISE"源锚非法——空锚"(psql 事务回滚,registry 4 行/manifest 2 行未扰) | **PASS(双层全拒)** |
| ④ 锚在位但与 manifest qbase 向量不匹配 → 生成拒 | **R10**:合法锚探针批(绑 manifest#1)+ 伪造 manifest 内容(daily→999999)→ RAISE"血缘不相容——market_return 批 15 的 qbase 源 daily 锚=6 ≠ manifest=999999(拒生成;非仅非NULL检查)";施工前 P-B 同型放行→施工后拒 | **PASS(全拒)** |

加测:R7=缺 source_manifest 锚拒;R8=伪 digest 锚拒;R9=锚向量≠所绑定 manifest 拒;
seed 反向=缺 `--source-snapshot-id` 拒/绑定未发布快照(id=99)`RuntimeError` 拒。

### 5. 权限/迁移回滚边界/验收实物

- 权限零变更(013 仅函数替换+DROP,表/授权未动;registry 写权仍=属主专责)。
- 回滚边界:`derived_batch_bi()`/`study_snapshot_biu()` 重放 010 定义、恢复 010
  `_batch_lineage_trusted()`、DROP 新增两函数(013 文件头注明);registry/批次行零变更。
- 实物:`verify_manifest_lineage` **17/17 PASS**(12→17;R6-R10 新增)。

## 三、回归全家福(施工后,aliyun 实测 2026-07-13)

| 套件 | 结果 |
|---|---|
| pap 层① / holding_path / drawdown_strategy 冒烟 | 全绿(冒烟含次日 open 断言) |
| verify_pap_gate | **21/21 PASS**(16→21) |
| verify_manifest_lineage | **17/17 PASS**(12→17) |
| verify_state_machine | 46/46 PASS |
| verify_addendum | 14/14 PASS |
| verify_snapshot_mirror | 11/11 PASS |
| verify_study_snapshot --mode probes | 19/19 PASS |
| verify_integration | **7/7 PASS,双跑 result sha `3bef1f81…` 同基线=读面零漂移** |
| 合成域零回归(run_ashare_study 双跑) | **sha `3116ba9b74f7c53b…` 逐字节同基线** |
| 台账/registry/manifest 存量 | 25 行/4 行/2 行,全程未扰(各探针回滚断言) |

## 四、统一验收措辞(窄补口径)

**四项反向攻击尝试全部被拒(①次日开盘实测成交、旧同刻口径不可达;②反向时间窗口冻结拒;
③空锚双层拒;④锚向量不匹配 manifest 生成拒),正反向测试套件全部 PASS。**

## 五、遗留注记(如实登记,非本轮范围)

- `seed_pool_b1_return --verify` 走引擎身份读 current 视图——引擎对 current 视图的 SELECT
  已于硬化②(012 视图迁移)收权,该验收工具需改 snap 范式(既有携带项,hardening-item2 §4
  已登记,本轮范围禁令不动)。
- qbase 既有源(如 daily)将来刷新批次时:旧派生批锚与新向量不相容 → 新 manifest 拒生成
  (fail-closed 正确方向);再种序(先发布过渡 manifest 供 seed 绑定)需人令排产,013 不留
  自动后门。新增源键(如 holder_sell 首载)不触发不相容(锚键⊆manifest 规则)。

## §10 git diff --stat(范围合规性核对)

开工前 HEAD `c4ce3c8` → 施工完 HEAD `4a2bfdd`(含裁决留痕 b0bdebb;本验收档 commit 仅增
docs+STATE,最终 HEAD 见 STATE):

```
 docs/postaudit-round2-narrow-order-2026-07-13.md |  43 +++++
 ops/STATE.md                                     |  17 +-
 taosha/compute/holding_path.py                   |  83 ++++++++-
 taosha/engine/drawdown_strategy.py               | 139 ++++++++++++---
 taosha/experiment/pap.py                         |  62 ++++++-
 taosha/experiment/snapshot.py                    |  18 ++
 taosha/experiment/verify_pap_gate.py             |  94 +++++++++-
 taosha/harness/run_drawdown_strategy.py          |   9 +-
 taosha/harness/verify_manifest_lineage.py        |  75 ++++++--
 taosha/ingest/seed_market_return.py              |  41 +++--
 taosha/ingest/seed_pool_b1.py                    |  58 ++++--
 taosha/ingest/seed_pool_b1_return.py             |  45 +++--
 taosha/sql/012_pap_preclose_structured.sql       | 122 +++++++++++++
 taosha/sql/013_source_anchor_strict.sql          | 213 +++++++++++++++++++++++
 14 files changed, 920 insertions(+), 99 deletions(-)
```

触碰面全部落在窄补令点名辖区:#1=pap/holding_path/drawdown_strategy/驱动/012+其自检;
#3=013/三 seed/snapshot 读取件+其自检;docs/STATE=留痕。**#2/#4/#5 已通过实现零触碰**
(qbase/sql/014、taosha/sql/008/009/010/011 文件均不在 diff 中;011 的 gate 函数经 012
迁移升级,函数替换属#1窄补令原文第 3 句辖区,011 文件本体未改)。
