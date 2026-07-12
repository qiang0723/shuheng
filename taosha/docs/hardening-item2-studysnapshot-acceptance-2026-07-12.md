# 硬化② StudySnapshot 快照锁定 · 验收档(2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ②。修法原文:受权角色(非 taosha_engine)生成一次性不可变 snapshot manifest;引擎经按 manifest 路由的受限视图读取,不扩底表权限;result.audit 同记 manifest ID 与 digest;fail-closed:无 manifest 拒运行,禁静默回退 `*_current`。

## 1. 修法实物

- **manifest 表 `taosha.study_snapshot`**(`taosha/sql/006_study_snapshot.sql`,apply 属主 postgres):不可变主键(identity)+ content(批次向量 jsonb)+ **digest 由 BEFORE INSERT 触发器权威计算** `sha256(content::text)`(jsonb 为 PG 规范化序列化,调用方传值被忽略)+ created_by/created_at;append-only 三触发器(UPDATE/DELETE 行级拒 + TRUNCATE 语句级拒);created_by=taosha_engine 直接拒(生成=受权角色专责,双保险:engine 亦无 INSERT 权)。
- **生成件 `taosha/experiment/snapshot.py`**:受权角色(TAOSHA_APP_DSN 写 + QBASE_APP_DSN 读批次表)采集两库批次现值向量(qbase: entity_batch/fact_batch 全源;taosha: market_return/pool_b1/pool_b1_return),必需键缺任一拒生成;CLI `--create/--show/--latest`。
- **路由视图**:
  - qbase 侧(`qbase/sql/012_study_snapshot_views.sql`,apply qbase_app):`explore_reader_{calendar,prices,events}_snap` = 008/010 定义逐字复制,仅 max(batch_id) 子查询替换为严格函数 `study_snap_batch(键)`(读会话 GUC `shuheng.study_batches` JSON;未设→PG 自然报错;缺键→RAISE);holdout/.BJ 焊法逐字保留。
  - taosha 侧(006):`market_return_snap`/`pool_b1_snap`/`pool_b1_return_snap`,严格函数 `study_snapshot_batch(键)` 经 GUC `shuheng.study_snapshot_id` 直读 manifest 行路由(manifest 不存在/缺键→RAISE)。
- **授权收敛(加固上报项,同① §5 模式)**:taosha_engine 对 `explore_reader_*`(qbase)与 `*_current` + 底表 `market_eqw_return`/`pool_b1_membership`/`pool_b1_return`(taosha)的 SELECT **全部收回**——引擎唯一读径=manifest 路由 `*_snap` + `study_snapshot`(路由键/audit 记账,非数据底表);未新增任何底表权限。`*_current` 与底表对 app/运维授权不变。
- **ViewReader fail-closed 改造**(`taosha/reader/view.py`):构造必须显式 `snapshot_id`(缺→RuntimeError,禁静默回退);init 即读 manifest(不存在→拒);连接工厂对每个连接注入路由 GUC;`snapshot_info` 供 audit。
- **三 driver**(run_forecast_study / run_drawdown_study / run_drawdown_strategy):`--snapshot-id` 必填;**result.audit 新增 `study_snapshot` = {manifest ID, digest, 批次向量}**;#2b 两驱动 audit.pool_snapshot 批次改从 manifest 取(原 `_batch_id` 直读底表 max 已删——engine 已无该权限)。

## 2. 验收实测(2026-07-12,aliyun)

**manifest #1**:snapshot_id=1,digest `2a8a271f2f7a52b5…`,向量 = qbase{daily 6/adj_factor 7/forecast 1/trade_cal 5/stock_basic 6/namechange 7/stk_holdertrade 2} + taosha{market_return 1/pool_b1 1/pool_b1_return 1}(与库中已知实物逐一吻合)。

**(i) 无 manifest 启动被拒(fail-closed)— 探针 16/16 全拒**(`taosha/harness/verify_study_snapshot.py --mode probes`,taosha_engine 身份):
- 引擎读 `explore_reader_{prices,calendar,events}`(current 路由)→ permission denied ×3;
- 引擎读 `{market_return,pool_b1,pool_b1_return}_current` + 三底表 → permission denied ×6;
- snap 视图无 GUC(qbase/taosha 两侧)→ unrecognized configuration parameter ×2;
- 批次向量缺键 → RAISE 缺键;manifest 不存在(id=999999)→ RAISE 不存在;
- 引擎写 study_snapshot → permission denied;
- Python 层:ViewReader 无 snapshot_id / manifest 不存在 → RuntimeError ×2。

**(ii) 同一 manifest 双跑逐字节同(读面全量摘要)**:dump 覆盖 = 日历 8,187 行 + 事件全量 + 市场基准 8,186 非空 + 池基准 8,066 非空 + 池成员 2,948,735 行 + 定样本 20 票价格 132,437 行,规范化流式 sha256:
- 修 tie 前:dump1 == dump2 == dump3 = `5f9acf5187280328…`(三跑逐字节同);
- 修 tie 后参考(见 §3):dump4a == dump4b = `1afba7d356d0a75e…`(events=105,590)。

**(iii) 并发写入新批次时运行不受扰(实测)**:dump2 与 `seed_market_return` 全程并发(写侧计算窗口重叠);reseed 落 **market_return batch=2**(8,186 行,双算闸 max|Δ|=6.5e-16 过,与 batch1 同源同容);batch=2 COMMIT 后 dump3/dump4 照跑——**snap 读面 sha 不动**,而 max-batch 现值路由已移(max(market_batch)=2,batch2 行数 8186 实测)。锁定得证:current 会漂,manifest 钉住不漂。

## 3. 验收中发现的缺陷与人拍(留痕)

**008/012 事件视图 DISTINCT ON tie 不确定性(② dump 实测揪出)**:同 (ts_code, first_ann_date) 的最早 ann_date 并列多行共 **11,689 对**;其中 **19 对**并列行跨八类型线 → 事件存在性随执行计划漂(实测:current 视图 105,584 vs snap 视图 105,587,同批次);**62 对**并列行层归属可漂(good/bad/turnaround)。属潜伏可复现性缺陷,恰为本窗口猎物。
**人拍 A(2026-07-12)= 工程钉死次级键**:两视图 ORDER BY 追加 `f.id ASC`(代理键=采集落库序,append-only 批内永恒;"任意但永远同一行",不宣称语义)。`qbase/sql/013_events_deterministic_tiebreak.sql` 已 apply,两视图同口径。钉死后:current 视图三跑恒 **105,590**,snap 双跑 sha 全等(§2 dump4)。
**归因纪律**:钉死效应(105,584→105,590,+6 事件面变动)须在 ③ 全量 diff 中与 ST 修复**分开归因**;#4 已闭卷结果一字不动;**人拍:缺陷给 exp_id=5 补 addendum 附注(c),随附注(b) 一并补录(⑤,待 ③ diff 出数)**。

## 4. 携带项登记

- `seed_pool_b1_return --verify`(验收硬项)原以 engine 身份读 `pool_b1_current`——收权后该路径失效;**下次池种子跑时改**:落新批 → 生成新 manifest → 经 `pool_b1_snap` 验收(流程更硬,顺势归位)。本窗口不触池种子,不阻塞。
- 历史"引擎身份三组断言"(holdout/.BJ 泄漏测试直查 explore_reader_*)被本项收权取代:等效断言已并入 verify_study_snapshot probes(引擎无权读 current 视图,snap 视图继承同 DDL 焊法)。
- 自 #3 起新增数据源(holder_predisclose)落库后,其批次自动进 manifest 向量(snapshot.py 全源采集);消费视图接入时须走 snap 范式,禁新建 current 直连。

## 5. 结论

② 修法+三件验收(fail-closed 16/16/同 manifest 逐字节/并发不受扰)全过;tie 缺陷已按人拍 A 钉死并留痕。产物备份 `/root/s3hard2_backup/`(dump1-4 JSON)。**待架构窗口验收后与 ① 一并放行 ③。**
