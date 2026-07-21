# exp13 limit_down_open · PAP 冻结执行 + 最小适配行为验收档(2026-07-21 晚)

> 令原文档:`taosha/docs/limit-down-open-freeze-order-2026-07-21.md`(原文即口径,F 条留痕
> commit `b2aa593` 先于一切施工)。
> 绑定 digest:`583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42`(下称 `583c4c94…0c42`)。
> **预判(人令原文,仅绑本 digest)**:主窗[0,+4]市场调整后CAR为正,预计约+5%,即连续一字跌停
> 真正开板后出现超跌反弹;把握度70%。该预判仅绑定上述digest,不代表上涨概率或统计显著性。
> **冻结解释边界(人令原文)**:①τ0为自T+1起首个可交易日,[0,+4]为τ0起连续5个有效交易日观测点;
> ②N_MIN=2为准入下限,每段只取唯一最大饱和链,不截取子链;③Snapshot 121同批次向量下,交付档
> 既有漏斗必须确定性复现;若正式数据向量变化,停下报人,不追数、不改规则。
> 取证包 = AWS `~/shuheng/s13_adapt_delivery_2026-07-21/`(SHA256SUMS -c 全 OK,秘扫 0 命中);
> aliyun 原件 = `/root/s13freeze/` + `/root/s13adapt/`(600)。

## §1 冻结前只读确认(令项,执行写入前实测,全 PASS)

| # | 令项 | 实测 | 判 |
|---|------|------|----|
| 1 | exp13 status=registered | `13\|limit_down_open\|1\|连续一字跌停开板\|llm\|prescreen\|registered`(registered_at 2026-07-12) | PASS |
| 2 | 三结果槽为空 | frozen_at/result_json/done_at 全 NULL(closure_reason 亦 NULL) | PASS |
| 3 | 无 exp13 正式 manifest 或运行记录 | `study_snapshot` 全 8 行(1/2/38/40/74/87/121/166)逐行=硬化/exp4/exp8/exp20 链;content+note 对 `exp13`/`limit_down` 检索零命中;`experiment_addendum` exp_id=13 计 0 | PASS |
| 4 | 台账 25 行且分布 16/2/6/1 | 25 行 = registered 16 / frozen 2 / done 6 / closed 1 | PASS |
| 5 | 文件SHA==引擎canonical==本令digest 三者全等 | **两台**(AWS+aliyun,同 commit 树)实测三值全等 `583c4c94…0c42`;validate_pap PASS;parse_test_windows=(5,20,60) | PASS |
| 6 | 库内当前登记 PAP=未冻结占位载荷 | 11 键占位(cost/dual/pool/scope/window/holdout/cleaning/benchmark/direction/event_def/snapshot_batch_req),无 pap_schema_version | PASS |
| 7 | 冻结闸适用性 | exp13 ∈ pap_legacy_registry(legacy 事件版冻结路径);终版 PAP 带 pap_schema_version=2 + analysis_type='event' | PASS |

## §2 冻结执行(令项,既有状态机,单事务)

- 执行身份 = `taosha_app`(`ledger.connect()`,psycopg 非 autocommit);解释器
  `/opt/venvs/qbase-ingest/bin/python3`;脚本留档 aliyun `/root/s13freeze/freeze_exp13.py`(600),
  日志 `/root/s13freeze/freeze_exp13.log`(取证包同件)。
- 事务序(一次 COMMIT,承 exp20 先例):
  1. `SELECT … FOR UPDATE` 行锁内前置断言(registered/三槽空/台账 25 行=16-2-6-1)——全 PASS;
  2. `UPDATE pap_json = 终版 PAP 原文`(载荷=仓内 `limit-down-open-pap-final-2026-07-21.json`
     逐字节读入解析,无改写/无运行时补键;载荷预检 file_sha==canonical==令digest 先行);
  3. `ledger.freeze(13)`(既有状态机 registered→frozen,置 frozen_at;库侧冻结闸放行);
  4. COMMIT @ **2026-07-21 22:23:24.984414+08**。

## §3 冻结读回凭证(令项逐项,全 PASS)

| 令项 | 读回值 | 判 |
|------|--------|----|
| status | `frozen` | PASS |
| frozen_at | `2026-07-21 22:23:24.984414+08` | PASS |
| DB 载荷 canonical digest(库读回重算) | `583c4c94…0c42` == 令 digest == 文件 SHA | PASS |
| parsed_equal(DB jsonb 对象==文件解析对象) | `True` | PASS |
| 载荷 MD5(`md5(pap_json::text)`) | `b7339b4509c9c9568f3973270d72d599`(taosha_app 与 postgres 独立连接双侧同值) | PASS |
| 台账只迁 exp13 行不新增 | 25 行,分布 **registered 15 / frozen 3 / done 6 / closed 1** = 令预期 15/3/6/1,零新增零删除 | PASS |
| result_json/done_at 仍空 | 双 NULL(正式运行/persist 边界未触碰) | PASS |
| 冻结不可改探针 | taosha_app 真实改动(附加键)→ 触发器 RAISE `铁律④违反`,ROLLBACK 零残留,MD5 复核未变 | PASS |

- 独立复核:postgres 超级用户连接读回 status/frozen_at/md5/schema_version=2/analysis_type=event,
  与 taosha_app 读回全等。

## §4 最小适配施工面(令:仅授权到行为验收;不改统计内核和 qbase)

commit 链(留痕与施工分单):`b2aa593`(令留痕+STATE)→ `14116ca`(施工五件)→
`5230a00`(recon 流 namedtuple 契约面修正)→ `832fa66`(audit 补全链口径链长分布键)→ 本档+STATE。

| 件 | 路径 | 性质 |
|---|---|---|
| L2 冻结规则纯函数 | `taosha/compute/limit_down_rules.py` | 纯新增(N_MIN=2 冻结值/双条件成员判据/A 口径最大饱和链/令七.4 主漏斗七档互斥主原因/补充令1 正交标志/B 口径 NFV 镜像/真开板保留/ST 事件日 PIT 归层留痕/listing 三类 fail-closed) |
| driver | `taosha/harness/run_limit_down_study.py` | 纯新增(engine_params 9 键逐字消费 fail-closed;`--recon-only`=本单元唯一授权模式,SELECT 面零价格/收益列;正式模式须 `--snapshot-id`≠121——snapshot 121 冒充 exp13 正式 manifest 结构性 fail-closed) |
| report 显式分支 | `taosha/engine/report.py`(+11 行 elif) | 标题「exp13 一字跌停开板·事件版」+真实 StudySnapshot 锚,缺锚/present-but-None fail-closed;exp8/exp20 分支零触碰 |
| 攻击 fixture | `verify_limit_down_rules.py` + `verify_limit_down_adapter.py` | 纯新增(§5) |

- **统计内核零触碰**(runner/cleaning/abnormal_tests/returns/market_model 等零改动);
  **qbase 零触碰**;engine_params 值域全部为既有参数既有合法值(exp8 先例),引擎零新参数。

## §5 fixture 结果(交付档 §6 全 18 组落地)

- `verify_limit_down_rules.py` = **48/48 PASS(两台)**:F1~F18 逐组转录(N=1/N=2 门、禁子链、
  停牌不重置 A 链+B 拆段、真实 bar 断链、hijack 排除+audit 顺延结构、真开板保留、duplicate
  优先于 hijack 互斥主原因、listing 三类、ST 事件日 PIT 归层+不一致留痕、研究期上下界、star
  单行不成链、诊断层递归零 verdict(F12:audit 子树 verdict/verdict_note=0+零显著性分类值+
  NFV 三块在场+七档恒等)、右删失∧hijack 互斥+正交标志、纯右删失、停牌跨档开板保留(顺延
  计数零污染)、混合顺延结构分计(up/down/anom)、创业板改革边界 PIT 旗标、B 口径 NFV 不改
  主集)+确定性双跑/跨票聚合/空输入退化。
- `verify_limit_down_adapter.py` = **34/34 PASS(两台)**:①engine_params 逐字消费(真实冻结件,
  st 居首;缺键/多键 fail-closed;引擎白名单==冻结 PAP axes 逐项一致)②events_from_prices 映射
  (event_id/层键二值/listing fail-closed/hijack 留痕/B 开关/确定性)③selection_audit(七档恒等/
  hijack 分母显式/ST 轴恒等/B 对照差异/逐条五槽)④digest 不变量(文件 SHA==canonical==令 digest;
  _family_trial 不进 digest;改实质键必变)⑤report 分支合成域全流水线(缺锚+present-but-None
  fail-closed;真锚→exp13 专属标题+快照行;exp8/exp20 标题零命中;exp8 分支回归探针=真锚标题不变)。

## §6 Snapshot 121 同向量漏斗逐层复现(令:确定性复现,任何不符即停)

- **向量前置核对**:current 各表 max(batch_id) = daily 6 / adj_factor 7 / stock_basic 6 /
  namechange 7 / trade_cal 10,与 manifest 121 qbase 五键逐项相等 → 未触发停报线。
- **执行**:driver `--recon-only --recon-snapshot-id 121`(digest 断言过;正式 ViewReader 语义=
  会话 GUC + prices_snap JOIN calendar_snap USING(trade_date);SELECT 面=ts_code/trade_date/
  limit_status/open_limit_status/board/is_st,**零价格收益列**);**双跑 JSON SHA 同值
  `bec5407f…a0db`**(run 日志唯一差异=输出路径行);零 manifest 生成/零引擎调用/零库写。
- **主漏斗逐档 == 交付档权威数字(逐项精确相等)**:

| 档 | 本次 driver 复现 | 交付档权威(令一) |
|---|---|---|
| 输入行(钉批∩日历) | 15,099,011 | 15,099,011 |
| 成员行 | 18,106 | 18,106 |
| 原始最大链(A) | 3,323 | 3,323 |
| 右删失 | 47 | 47 |
| pre2007 / post | 456 / 0 | 456 / 0 |
| listing 异常 / duplicate | 0 / 0 | 0 / 0 |
| reversal_hijack | 26 | 26 |
| **最终主事件集** | **2,794** | **2,794** |
| ST / 非 ST | 1,480 / 1,314 | 1,480 / 1,314 |
| recent_listing / seasoned | 29 / 2,765 | 29 / 2,765 |
| hijack 占比 | 26/2,820=0.922%;26/3,323=0.782% | 同 |

- **深度对账 = `s13_compare.py` 33/33 PASS**(vs PAP 草案单元权威 recon 实物
  `s13recon_result.run1.json`,SHA `ecc915b5…260f` 双跑件):A/B 漏斗逐档(B=3,366/50/463/0/
  99 碰撞链·49 碰撞日/26/2,728)、hijack 26 条**逐条集合相等**(ts/链首尾/链长/事件日/顺延
  up·down)、A vs B 主事件集差异 **66/0 逐条相等**、ST 链起点 vs 事件日不一致 **74 条逐条相等**、
  右删失∧hijack 正交=0、链长全链口径分布(∑=3,323)、年度/board/事件日形态/开盘位/聚集
  top10/共享日 500 全部逐键相等。

## §7 全家福 + 既有路径零回归

- **两台全家福全绿**:aliyun(钉版 venv)=状态机 46/46 / pap 硬门 23/23 / addendum 14/14 /
  镜像 11/11 / 血缘 24/24 / 集成 7/7 / 冻结口径运行时探针 PASS / 三窗 5/5 / 敏感性 6/6 /
  holder 81+10 / limit_open 40+24+116 / earnings_revision 33+73+24 / **limit_down 新两件 48+34**;
  AWS=非 DB 套件同清单全绿。
- **e2e 合成基线**:AWS 双跑+aliyun 双跑全=`3116ba9b74f7c53b…`==历史基线,逐字节零回归。
- **既有报告实物零回归(真实产物)**:新 report.py 重渲染 exp8 已验收 result →
  `5fb87ebf…d914` == 封存 `report_exp8.corrected.txt`;重渲染 exp20 闭卷 result →
  `3b5de3c4…a030e` == 封存 `report_exp20.txt`;**双双逐字节相等**。

## §8 禁区遵守声明 + 停交验点

- **零新建正式 manifest**(study_snapshot 仍 8 行零新增);**零真实收益读取**(recon SELECT 面
  零价格收益列;正式 ViewReader.prices 全列流未在本单元执行);**零正式运行**(2,794 事件仅
  转译计数,未入引擎);**零 persist/零台账写**(exp13=frozen,result/done 槽空;台账 25=15/3/6/1
  为冻结令内唯一写入);冻结载荷自 COMMIT 后零触碰(不可改探针为 ROLLBACK 事务)。
- **▶停在行为验收点**:等人验收冻结凭证+适配行为面;正式 manifest 生成、真实收益读取、
  正式运行、persist 均待另令;未令不动。开工首动作=读 ops/STATE.md+查库。
