# exp12 `st_removal` 冻结 + 最小适配 · 行为验收档(2026-07-23)

> 授权依据 = 人冻结令+最小适配授权令 2026-07-23(原文留痕 `st-removal-freeze-order-2026-07-23.md`,
> F 条 commit `93c0a5a` 先行)。施工 commit `b0229ef`(与留痕分单),两台 HEAD 净。
> **本令不授权 manifest/真实收益/正式运行/persist/result_json 写入——全部未触碰(§7)。**
> 完成停行为验收点。

## 1. 冻结前只读确认(令一;10/10 PASS)

实录 = aliyun `/root/s12freeze/preflight_exp12.log`(取证包镜像,SHA `80af9f94…0161`):
exp12 registered/三槽空 ✓;台账 25 行、分布 15/2/7/1 ✓;study_snapshot 9 行零 exp12/
st_removal 关联 ✓(无正式 manifest 无运行记录);库内当前 PAP=未冻结占位(canonical
`3cb99c73…` ≠ 终版 digest)✓;终版文件 SHA==引擎 canonical 重算==令 digest
`62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353` 三者逐字相等 ✓;
validate_pap PASS+检验窗 (5,20,60) ✓。

## 2. 冻结执行(令二;既有状态机单事务)

实录 = `/root/s12freeze/freeze_exp12.log`(镜像 SHA `3dc38509…e03c`;脚本承 exp13/exp20 先例):
taosha_app 同连接单事务 = FOR UPDATE 行锁内再断言(registered/三槽空/25 行 15-2-7-1)→
UPDATE pap_json=终版 canonical 原文(仓内冻结件逐字节读入,零改写零补键)→
`ledger.freeze(12)` → 一次 COMMIT。

- **frozen_at = 2026-07-23 19:45:23.251569+08**;读回 status=frozen。
- 读回 DB 载荷 canonical == 令 digest `62a387a2…4353`;**parsed_equal=True**;
  载荷 md5(pap_json::text)=`c102063f7153d95352bd6c936fc3244d`。
- 台账 25 行,分布 **14/3/7/1**(恰迁一行,零新增)==令预期。
- **预判绑定(人令原文,F 条留痕档§预判登记)**:主窗[0,+4]市场调整后 CAR 为正,预计上涨
  约 5%,把握度 70%;仅绑上述终版 digest,不预判统计显著性,不得改述或平移。

## 3. 最小适配施工清单(令三授权面;commit `b0229ef`)

| 授权项 | 实物 |
|---|---|
| 只读视图接入 | `qbase/sql/019_namechange_reader.sql` 已 apply(qbase_app):`explore_reader_namechange(_snap)` 视图对,holdout 焊死 `(ann IS NULL OR ann<2024-07-01)`(锚=ann_date,NULL 行忠实传递=锚缺失属 L2 留痕)、排北交所、最小列面(无 end_date=冻结口径明令不信任)、taosha_engine 最小 SELECT;+`ViewReader.namechange_rows()`(_snap 面,holdout 双保险) |
| 事件生成器 | `taosha/compute/st_removal_rules.py`(L2 纯函数):段位折叠(孪生 GROUP BY+LEAD 边界)/名称谓词(ST 变体·退市双谓词 `%退`+`退市%`·优先级退市>ST>普通)/完整撤销判定/fail-closed 六类/主漏斗十一档+恒等式/摘星·戴星·ST→退市 NFV 报数 |
| 引擎 `missing_bar_only` | `engine/cleaning.py`+`survivors.py`+`runner.py`:显式值域收编;公告日历锚(同 unified_announcement 族);**仅停牌/缺 bar 计入顺延**(≤5 保留,第 6 日仍无真实 bar 剔 postpone);一字涨停或跌停有真实 bar 即取为 τ0 进入 CAR、不作顺延、不计入顺延计数;τ0 日一字板留痕注记;无 event_day_anomaly;既有值域(legacy/unified/unified_announcement)行为零触碰 |
| driver | `harness/run_st_removal_study.py`:冻结件 7 键逐字消费(缺/多键、postpone 篡改均 fail-closed,不映射不回退);digest 双保险断言;`--recon-only`=本单元唯一授权模式(零收益/零 manifest/零引擎);正式模式须 `--snapshot-id`(exp12 自有 manifest,另令) |
| 报告分支 | `engine/report.py`:`st_removal_selection` 真锚标题(缺 study_snapshot 锚 fail-closed,禁回退)+事件生成漏斗段+NFV 报数段+**一字板执行限制段(execution_limit_audit,NFV,强制在场缺则 fail-closed;含"cost 仅 schema/执行审计、不得表述为可成交策略证据"口径句)** |

**⚠ driver 定值一项报人确认(非 PAP 键)**:冻结 PAP engine_params 无 st_mode/st_policy 键
(engine_params.note 原文:"本假设无st诊断轴(事件本体=ST摘帽,前段ST为构造性事实,不设分层)")。
引擎签名须传值,driver 定值 `st_mode='event_day'`(生产唯一合法值,硬化③)、
`st_policy='keep'`——论证:事件锚日(撤销公告日)事件票名称仍属 ST 状态,若 'reject' 则
全部事件被 ST 剔除=归谬,与冻结 event_def 不相容;'keep' 且 diagnostic_dims=[](照冻结件)
不设 ST 分层。fixture 专项验证(锚日 is_st=True 不剔);**此读法请人于本验收点确认**。

## 4. 攻击 fixture(令三清单全覆盖;两台全绿)

- `verify_st_removal_rules.py` = **42/42**:退市双谓词(前缀退市名在仅后缀谓词下的假事件
  攻击被拒)/摘星排除(全史+窗内锚干净分计)/戴星/ST→退双格式/孪生折叠/start 缺失/锚缺失/
  锚冲突/状态不可判(前后段混名)/ann>start/研究期四边界(2011-01-01 含·2024-07-01 不含)/
  事件键重复全剔不择一/恒等式/确定性双跑。
- `verify_st_removal_adapter.py` = **43/43**:冻结件逐字消费(缺键/多键/postpone 篡改
  fail-closed)/digest 不变量/EventRow 映射+行序无关确定性/**缺 bar 顺延 1/5/6 日、
  一字涨停不顺延、一字跌停不顺延、混合(缺bar2+一字=τ0)**/τ0 一字板留痕/ST 锚日 keep
  不剔/unified 零回归探针(一字板照旧阻塞)/缺 axis·bogus 值拒/report 分支五面
  (缺锚·present-but-None·缺 execution_limit_audit 三 fail-closed;真锚标题;exp8/13/20
  零命中;exp13 分支回归探针)/execution_limit_audit 消费口/参考数对账块结构。

## 5. 漏斗按冻结规则复现(令三;aliyun 双跑逐字节一致)

recon 双跑 JSON SHA 同 = `00e2b498f8c5d61e3beb8b6234612e1147c4aabb9253ab13477aa1514ab63cc0`
(`/root/s12adapt/recon1.json`==`recon2.json`;AWS 取证包镜像);现值面=batch7(唯一批次)。

| 档 | 本复现(019 视图面) | batch 7 参考(草案原始表面) | Δ | 血缘归因 |
|---|---|---|---|---|
| 入库行 | 18,868 | 20,005 | −1,137 | 视图 holdout 焊死(ann≥2024-07-01 段不可见)+北交所排除 |
| 段 | 17,133 | 18,113 | −980 | 同上 |
| 有前段转换 | 11,601 | 12,253 | −652 | 同上 |
| 完整摘帽候选 | 944 | 1,063 | −119 | −121 期外候选不可见 +2 不可判候选新表面(下行) |
| 状态不可判 | **2** | 0 | +2 | 本实现 fail-closed 面更宽:mixed 段潜在候选**计入候选并剔除留痕**(草案 SQL 段级 bool_or 折叠下此二例结构上不成候选、不可见);逐条=000995.SZ 皇台(孪生 ST皇台/皇台酒业 混名+锚冲突 12-09/12-15)、002680.SZ 长生退(孪生 '长生退'/'长生退(退市)',后者全角尾缀不中双谓词);**两例均不入最终集,处置=裁定六不合并不择一** |
| 锚缺失 | 296 | 296 | 0 | 精确一致 |
| 锚冲突 / ann>start / 键重复 | 0/0/0 | 0/0/0 | 0 | 一致 |
| 研究期外 | 5 | 126 | −121 | 2024-07 后候选已被视图 holdout 焊死(仅余 2010:5) |
| **最终事件集** | **641** | **641** | **0** | **精确一致** |

恒等式 OK;**逐年分布 14 年逐字一致**(2011:35…2024H1:26,∑=641);gap 分布 0:2/1-3:583/
4-10:56 一致;NFV:**窗内锚干净摘星=222 精确一致**;全史摘星 429(参考 458)/戴星 361(419)/
ST→退市 110(143)——Δ 全部=视图 holdout+排北面(全史含 2024-07 后段,视图不可见;NFV 仅报数)。
**641 仅 batch 7 参考数,非硬断言;未追数未改规则**(冻结令三节)。

## 6. 全家福 + 零回归(两台全绿)

- aliyun(DB 全清单):st_removal 新二件 42+43 / limit_down 34+48 / limit_open 24+116+40 /
  earnings_revision 24+73+33 / holder 10+81 / frozen_immutable / sensitivity 6 / 三窗 5 /
  集成 7 / 血缘 24 / 镜像 11 / snapshot 探针 19 —— 全 PASS。
- AWS(非 DB 同清单)全 PASS;pap 自检两条 PASS。
- **e2e 合成基线:AWS 双跑+aliyun 双跑全=`3116ba9b74f7c53b…`==历史基线,逐字节零回归**
  (引擎收编 missing_bar_only 后既有默认路径零变化)。

## 7. 禁区遵守实录(令尾)+运行后核验

零正式 manifest(study_snapshot 仍 9 行)/零真实收益读取(recon 面=namechange 名称段元数据,
无价格收益列)/零正式运行/零 persist/零 result_json 写入。运行后读回:exp12 仍 frozen
(frozen_at 不变)、result_json/done_at 空、台账 25=14/3/7/1、两台 git 净(HEAD 同)。
取证包 = AWS `~/shuheng/s12_adapt_delivery_2026-07-23/`(recon1.json+preflight/freeze 双 log,
SHA256SUMS 在包,秘扫 0 命中);aliyun 原件 `/root/s12freeze/`+`/root/s12adapt/`。

## 8. 停行为验收点 · 待人

1. 验收冻结凭证(§1/§2)+适配行为面(§3–§6);**§3 driver 定值(st_policy='keep')读法确认**;
   §5 状态不可判 +2 逐条处置确认(fail-closed 面更宽,最终集不受影响)。
2. 下一步(须另令)= exp12 自有研究 manifest 生成 → 单次正式运行 → persist;未令不动。
