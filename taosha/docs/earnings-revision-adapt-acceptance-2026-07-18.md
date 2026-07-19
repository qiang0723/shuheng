# exp20 适配施工行为验收档(2026-07-18 深夜,冻结令 2026-07-18 深夜六 令三)

> 令原文=`earnings-revision-freeze-order-2026-07-18.md`(原文即口径)。本单元=分段授权只到
> **行为验收**;冻结 PAP v2 digest=`e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`。
> **全程未动**:冻结 PAP/台账状态/manifest/正式收益读取/正式运行/persist(禁区声明见 §10)。

## 1. 单元范围与 commit 链

| 令三条目 | 实物 | commit |
|---|---|---|
| ① forecast 只读视图对 | `qbase/sql/018_forecast_reader.sql`(已 apply,§2) | `29c0e9f` |
| ① 事件生成器最小适配 | `taosha/compute/earnings_revision_rules.py` + `taosha/harness/run_earnings_revision_study.py` + `reader/view.py::forecast_rows` | `29c0e9f` |
| ② signed 统计路径/公告顺延/direction 轴参数化 | `engine/{runner,cleaning,survivors,report}.py`(默认值=既有行为零回归) | `29c0e9f` |
| ③ 14 组预注册攻击 fixture | `harness/verify_earnings_revision_{rules,engine,adapter}.py`(33+73+19=125 断言,§6) | `29c0e9f` |
| ⑤ 12,569/5,225 逐层对账 | recon-only 模式实跑+归因(§7) | `88d2cfe` |
| ④ 全家福+零回归 | 两台全绿+e2e `3116ba9b`(§8) | — |
| (随发现)R6 时点断言动态化 | `experiment/verify_pap_gate.py`(§9,非 exp20 语义) | `73ca1b1` |

## 2. 视图对 apply 验收(令三①)

- apply 身份=qbase_app(psql $QBASE_APP_DSN,ON_ERROR_STOP,单事务),视图属主=qbase_app;
- `explore_reader_forecast`(现值 max-batch)/`explore_reader_forecast_snap`(manifest GUC 路由)
  同口径:**最小列面**=链键(ts_code,end_date,first_ann_date)+事件锚 ann_date+判定字段
  p_change_min/max+snapshot_batch——**net_profit/type 不出列**(冻结口径明令禁用,结构防误用);
- 实测:行=127,166 / ann_date∈[1999-01-08, 2024-06-29] / **holdout+排北违例=0** /
  taosha_engine 视图 SELECT 通、底表 forecast_snap 拒(009 焊死维持)/ _snap 无 GUC fail-closed、
  GUC=74 路由通(127,166,forecast:1 已在源级快照向量);
- L1 忠实:不过滤不可判行,研究期下限属 L2 不焊视图(链基准可回看 2013 前公告)。

## 3. L2 规则件(冻结 PAP v2 event_def 逐字实现)

`compute/earnings_revision_rules.py` 纯函数零 I/O:L2 确定性折叠(L1 不动)→链锚分拣→时序
违例→研究期[2013-01-01, 2024-07-01)→同期多链侦测→逐(链,事件日):600856→孤儿→当前可判
→基准B(事件日前最近披露,非链首)→方向(中点/单边回退/全空不可判;>up/<down/=flat 两阶段)
→同日同向折叠(组成链审计)/方向冲突整事件拒。fail-closed 六类逐类逐年计数+600856 逐条留痕;
flat=合法分类入计数块排除出主事件集不拒跑。

## 4. 引擎参数化(默认值=既有行为零回归)

- `postpone_policy='unified_announcement'`(cleaning):ann_date 日历锚 bisect(须传 axis_dates,
  缺=fail-closed);周末/节假日公告不因 T 无 bar 剔;τ0=ann_date 后首个交易所交易日;自 τ 轴起
  缺 bar/停牌/一字统一顺延≤5 留、第 6 日剔 postpone;**无 event_day_anomaly**(exp8 专属,冻结
  原文明令不引入);锚日缺 bar 仅 ST 判定不可得留注,不构成剔除事由。
- `direction_signed_main=True`(runner):direction_sign(up=+1/down=−1)施加于**事件级、逐 τ、
  先于一切聚合与检验**,并作用于估计期异常残差(est_ar_by_date/秩输入序列)——SecurityEvent 即
  同一 signed 估计对象,AAR/CAAR/BMP/ADJ-BMP/Corrado/日历法/ρ̄ 全下游消费;est_ar_sd 数值不变
  (PAP 原文);raw AR 平行对象仅供诊断层。
- direction 二道闸(承 listing_age 先例):direction 轴或 signed 启用时,主事件流层键严格
  ∈{up,down},白名单与 PAP diagnostic_dimensions.axes.direction 逐项对账;flat/null/unknown
  等泄漏→**CAR 计算与顶层 _verdict 调用前** fail-closed。
- `direction_display='raw'`:诊断层消费未 signed 平行对象,display_basis 声明入块。
- `effect_alignment_source='adj_bmp_sign'`:四态全定义纯函数 `runner._effect_alignment`
  (>0 ALIGNED/<0 REVERSED/=0 NEUTRAL/不可得或 INSUFFICIENT·AMBIGUOUS=UNAVAILABLE);CONTEXT
  字段随主窗+field_roles 登记;SIG+REVERSED 强制证伪句;signed CAAR 与 ADJ-BMP 符号不一致
  →并列披露句;**四态不产生不改变顶层 verdict**。
- report:exp20 标题真锚(study_snapshot 缺席即 fail-closed,承 exp8 先例)+事件生成漏斗段
  (reporting①②③④)+effect_alignment 行(SIG+REVERSED 警示)。

## 5. driver 最小适配(`harness/run_earnings_revision_study.py`)

- engine_params **逐字消费冻结件**:键集(11 键,无 st_mode)不符=fail-closed,不留运行时选择;
- pap_sha256_assert 双保险(driver 先行断言+runner 权威重算);铁律③ status≠frozen 拒;
- `events_from_forecast`:L2 selection→EventRow(锚=市场事件 ann_date,layer=direction,
  event_id=ts:yyyymmdd);selection 全量漏斗+对账块入 audit;
- `--recon-only`(本单元唯一授权模式):现值 forecast 面,零收益/零 manifest/零引擎调用;
- 全量模式代码就绪但须 `--snapshot-id`(硬化②)——**本单元未运行,须外审后另令**。

## 6. 14 组预注册攻击 fixture 逐组映射(交付档 §5+§7.3;共 125 断言两台全绿)

| # | 组 | 位置 | 断言要点 |
|---|---|---|---|
| 1 | signed 同向归一 | engine | all-up signed==raw 逐项;all-down 逐τ AAR==−raw(事件级先于聚合) |
| 2 | 反向样本 | engine | all-down CAAR==−raw(raw 正→signed 负=逆修正方向);ADJ-BMP 同步翻转 |
| 3 | SIG+REVERSED 措辞 | engine | 报告"支持"零命中+证伪警示句在场(runner 层写入)+SIG+ALIGNED 对照 |
| 4 | 公告日历锚 | engine(cleaning 台架) | 周末公告不剔/τ0 正确/锚日缺 bar 不剔(vs unified=event_day_anomaly 对照)/无历史 history 剔/缺 axis_dates 拒 |
| 5 | 顺延边界 | engine(cleaning 台架) | 1/5 留 6 剔(缺 bar+一字+flag 混合);周末公告顺延自 τ 轴起计 |
| 6 | 方向判定全分支 | rules | 中点/单边回退/全空不可判/同日多行不一致 fail-closed/flat 仅计数 |
| 7 | raw 诊断层零判决 | engine | _verdict 计数=恰 1(顶层)/递归零 verdict·零显著性值/诊断块 signed 跑==raw 跑逐字节(raw 平行对象实证) |
| 8 | signed 输入实改 | engine | 混合方向 ρ̄≠raw(估计期残差实改)/秩统计∉{raw,−raw}(整序列重排)/CAAR∉{raw,−raw}(展示翻转不可及)/csar_sd 不变 |
| 9 | pap_sha256_assert | engine | 错误 digest 拒/正确放行结果逐字节同 |
| 10 | 对账结构断言 | adapter | selection_audit/recon 全键+恒等锚+差值算术+report 渲染消费 |
| 11 | flat 候选正常排除 | rules+adapter | 计数块入册/主事件集不含 flat/端到端运行不终止且产合法四态 |
| 12 | flat 泄漏拒跑 | engine | flat/null/unknown/空串/旧层名/混入单条→拒且 _verdict=0;PAP 白名单缺失/多 flat→拒;display 白名单外拒 |
| 13 | alignment 四分支 | engine | 单元 8 断言(含 NEUTRAL/INSUFFICIENT·AMBIGUOUS 禁猜)+集成 ALIGNED/REVERSED/UNAVAILABLE |
| 14 | 四态零判决影响 | engine | 三案例 alignment 开/关 verdict 逐字节同+关=零新键;字段角色 CONTEXT |

reporting⑥ 增补:预注册种子 9 赋向 caar>0>adj_bmp → 并列披露句实证(engine)。

## 7. 12,569/5,225 逐层对账(令三⑤;冻结规则零改动)

实跑=aliyun `run_earnings_revision_study --recon-only`(钉版 venv python;digest 断言过;
现值面 batch1,行=127,166);**确定性双跑 sha 同=`6ba62da413251614…`**;产物
`/root/s20recon/recon_2026-07-18.json`+AWS 备份 `~/shuheng/s20_adapt_delivery_2026-07-18/`。

**漏斗(冻结规则)**:输入 127,166 →去重 −11,935 → 115,231 →缺链锚 88 →时序违例 10 →
全期候选 12,559 →研究期前 −4,378(后=0,视图焊死)→研究期候选 8,181(行=键=链日,去重后一一对应)
→fail-closed:孤儿 416/多链 0/数值不可判 2,587(当前 107+基准 2,479+不一致 1)/600856=3(逐条留痕)
→方向已判 4,892(up 2,054/down 2,838)+flat 283(逐年入计数块)→同日折叠 0/冲突 0 →
**主事件集 4,892**(未入引擎,本单元零运行)。

**候选层=精确恒等(Δ=+0)**:参考 12,569 = 全期候选 12,559 + 时序违例 10。SQL 独立复核:
视图上 `去重后 first 在场且 ann≠first` 行数=**12,569 恒等命中**(评估期口径=未加研究期筛、
未剔时序违例;非规则分歧)。

**可判层 Δ=−50,归因 −38+残差 −12(⚠交人裁)**:实测可判链日 5,175(=4,892+283 flat)。
SQL 变体探针:+35(孤儿链有前披且双侧可判——冻结规则孤儿整链 fail-closed 不得入)
+3(600856 可判——冻结规则单票 fail-closed)=5,213。**残差 +12 不可复现**:八变体
(含时序违例行/同日任一行规则/链首基准/全表含北交所/period 级链键/end_date 空容忍)
全部落 5,094~5,214,无一命中 5,225。原窄闸脚本未归档(人裁 2026-07-17 已留痕之已知风险,
终版 PAP 令原文:"5,225 脚本未归档,拍后重实现对账")。**未改冻结规则、未择优;残差报人裁定**
是否构成对账异常。

## 8. 全家福回归+默认路径零回归+特别验证七项(令三④)

- **两台全家福全绿**:aliyun(钉版 venv 3.14)=状态机 46/46/pap 硬门 23/23(§9 修正后)/
  addendum 14/14/镜像 11/11/血缘 24/24/冻结口径运行时探针 PASS/集成 7/7/运行时钉版 ALL PASS/
  三窗 5/5/holder 81/81+10/10/limit_open 116/116+40/40+24/24/敏感性 6/6/cleaning·rules 自检
  +**exp20 新三件 33/33+73/73+19/19**;AWS=非 DB 套件同清单全绿。
- **e2e 合成基线**:AWS 三跑+aliyun 双跑全=`3116ba9b74f7c53b…`==历史基线,逐字节零回归。
- **特别验证七项**:①flat 计数排除不终止=fixture#11 ②flat 泄漏 CAR·verdict 前拒=#12
  (_verdict=0)③signed 真作用估计期残差·秩·修正输入=#8 ④alignment 四分支=#13
  ⑤direction 层递归零 verdict 零显著性=#7 ⑥SIG+REVERSED 禁支持性措辞=#3 ⑦旧路径逐字节
  零回归=e2e 基线+默认路径零新键(effect_alignment/diagnostic_dimensions/premend_params 递归 0)
  +默认渲染零 exp20 段落+既有套件全绿。

## 9. 随发现修正:verify_pap_gate R6 时点断言(非 exp20 语义,commit `73ca1b1`)

全家福首跑 pap 硬门 22/23:R6 零残留断言硬编码负对照标本 `exp8==('frozen',True,True)`
——s8 窄修(07-18)时点态;exp8 已于 07-18 深夜二**人令 persist 闭卷(done)**,断言时点性假红。
最小修复=断言动态化(标本非 registered+回滚前后逐项等值,不锚具体终态);判据/攻击路径/负对照
逻辑零改动,证据四条语义不变。修后 23/23。属测试路径边界内自决,此处留痕供审。

## 10. 禁区遵守声明+git 实物

- **零正式收益读取**(recon 只读 forecast 元数据列面,无 prices/收益消费);**零 manifest 生成**;
  **零正式运行**(4,892 事件仅转译计数,未入引擎);**零 persist/零台账写**(exp20 仍 frozen,
  result/done 槽空;台账 25=16/3/5/1 未动);冻结 PAP 载荷零触碰。
- commit 链:`29c0e9f`(施工+fixture)→`73ca1b1`(R6 动态化)→`88d2cfe`(对账归因)→本档+STATE;
  两台 HEAD 同、git 净。
- **停交验点**:等外部只读复核;通过后另行授权 manifest+单次正式运行(令三尾款)。
  待人裁一项=§7 可判层残差 +12。

## 11. 外审结论+残差裁定落档(2026-07-19 人令,provenance 异常留档;令原文=`earnings-revision-narrowfix-order-2026-07-19.md`)

- **外审结论**:适配主体通过(有条件);manifest 与正式运行仍未授权,待三处窄修+复核闭合后另令。
- **残差 −12 裁定(§7 待人裁项闭合)**:−50 中 −38 已归因;剩 −12 **认定为历史参考数血缘缺口**
  (5,225 原窄闸脚本未归档不可重放,**丧失硬基线证据资格**),非冻结规则或适配代码异常。
  - **provenance 异常留档(本节即档)**:参考数 5,225 之产生脚本未持久归档,血缘断裂,不可重放复核;
    此为 07-17 人已留痕之已知风险的终局裁定。
  - **报告注记义务(永续)**:后续一切报告保留注记 **"不可归因旧口径差额 −12"**,不得写成 5,225 已复现。
  - **唯一权威**:正式样本 4,892(可判 5,175)以冻结规则实现为唯一权威;5,225 降格为无证据资格的历史参考。
- **三处窄修施工(commit `00cf8c1`,零生产逻辑)**:①driver `reference_reconciliation` docstring
  参考层锚定口径改与实现一致(候选 12,569 ↔ 全期候选+时序违例恒等锚,只改说明不动计算)
  ②`verify_pap_gate` R6 台账行数断言 `==25` 改前后相等(不绑字面行数)③R6 证据③输出文案同步
  ("状态及结果槽前后不变、且状态非registered")。修后 pap_gate aliyun 带 DSN 重跑 **23/23 PASS**
  (证据③实测 25→25/exp8 done 前后不变);exp20 三件 fixture 两台 33/73/19 全绿。
- **版本纪律**:行为代码基线止于 `4eb404d`;本单元三 commit(`ad9870c` 留痕/`00cf8c1` 窄修/回执)
  均为文档/测试面。禁区维持=零收益/零 manifest/零运行/零 persist。
