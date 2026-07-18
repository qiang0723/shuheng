# exp20 终版 PAP 交付档(2026-07-18 深夜二,PAP 文本回修单元;深夜三 v2 回修补记)

> **⚠v2 补记(2026-07-18 深夜三)**:本档 §1 之 v1 digest `94b9ba78…fa17` 经外部复核**未批冻结、已作废**
> (标记档=`earnings-revision-pap-final-2026-07-18.NOT-FROZEN.md`);现行待复核版本见 §7(v2,digest `e1d18dc1…7fd5`)。
> §2-§5 的裁定映射与 fixture 清单对 v2 继续有效,v2 增量见 §7。

- **令源**:`taosha/docs/earnings-revision-pap-rulings-2026-07-18.md`(十项裁定+signed补强+终版要求,留痕 `ce48471`,原文即口径)。
- **本单元性质**:仅 PAP 文本回修。零代码/零收益·CAR·显著性读取/零冻结/零 manifest/零台账写/零运行。草案档未覆盖、原样保留。
- **⚠地位**:终版文本≠冻结。待人复核后以下方 digest 下冻结句并另写预判;旧草案不得直接冻结。

## 1. 终版实物

- 文件:`taosha/docs/earnings-revision-pap-final-2026-07-18.json`(canonical 串+末尾单换行的字节本体,19 顶层键)
- **文件 SHA256 = canonical digest = `94b9ba7821c3393e33123971f8b681e8f5d457e43c6f8bf39df9caa1f543fa17`**
  (引擎 `canonical_pap_sha256` 重算==文件 SHA256,当场断言 PASS)
- `validate_pap`:**PASS**(必备八键齐全非空/pap_schema_version=2/analysis_type=event)
- `parse_test_windows`:**(5, 20, 60)**(主窗[0,+4]唯一判决/次级[0,+19]/稳健[0,+59],runner 首=主、末=稳健既有语义)

## 2. 草案 → 终版逐键 diff

| 键 | 草案状态 | 终版 | 变更依据 |
|----|---------|------|---------|
| pap_schema_version / analysis_type | 2 / event | 不变 | — |
| event_def | 方向判定字段〔待拍§3-3〕;同日折叠〔待确认§3-9〕 | **p_change_min/max 窄闸显式口径落定**(中点/单边回退该单值/全空不可判/同链同日多行须全可判且标量一致否则fail-closed/大于up·小于down·等于flat/不改net_profit/不用type回退);同日多链同方向折叠为一市场事件+保留组成链审计清单;增"不能因对不上而修改冻结规则,对账异常即停报人" | 裁定一(方向字段)+裁定九(折叠)+终版要求(对账) |
| signed_ar.formula/estimand/single_verdict | 已落 | 不变 | — |
| signed_ar.application_level | 仅事件窗 raw_AR 先于聚合 | **补强**:direction_sign 并作用于估计期异常残差及所有方向相关统计输入;AAR/CAAR/BMP/ADJ-BMP/Corrado/日历法及聚集修正同一signed估计对象;秩方向/标准化残差方向/事件间相关符号按signed;raw AR只留诊断层;禁只改最终CAAR符号 | 令二 signed 补强逐字 |
| window | 〔待拍§3-4〕 | **"T+1起,后5/20/60日(T=公告日ann_date为日历锚,τ0=其后第一个交易所交易日…)"**,依据=短窗即时定价与中长期漂移分离,独立成立不引exp8 | 裁定三 |
| pool | universe〔待拍§3-5〕 | **全A股(排除北交所)**;source 不变(explore_reader_forecast 视图对=适配阶段新建注记保留) | 裁定四 |
| benchmark | 〔待拍§3-5〕 | **{market_hypothesis:全市场等权, note:benchmark_mode=market;池基准无冻结定义不采用}** | 裁定四 |
| cleaning | ST〔待拍§3-7〕/顺延〔待拍§3-8〕/含exp8式 event_day_anomaly | **st_policy=reject**(spec§5默认,不继承exp8例外,不增ST轴);**公告事件语义顺延**(ann_date=日历锚,不要求T有bar,周末节假日公告不因T无bar剔除,τ0=ann_date后第一个交易所交易日,自该日起缺bar/停牌/一字统一顺延≤5交易所交易日、第6日postpone剔);**删除"事件日T缺bar/停牌→event_day_anomaly"规则**(exp8价格形态事件专属);估计窗250~91/160/112门沿默认 | 裁定六/七/十 |
| cost | 四键冻结值 | 不变 | — |
| diagnostic_dimensions | display_basis raw〔待确认§3-6〕 | **raw 落定**(裁定五);direction_fail_closed/note/zero_survivor_status 实质不变;flat 仅计数块措辞保留 | 裁定五 |
| verdict_authority | 单双侧+三态verdict〔待拍§3-1/2〕 | **双侧ADJ-BMP,adj_bmp_main_only既有门槛,不新增单侧机构;SIG_ALIGNED/SIG_REVERSED枚举提案作废**——verdict维持既有SIG/NOT_SIG/INSUFFICIENT/AMBIGUOUS,双侧过阈仍记SIG;**新设非verdict上下文字段effect_alignment=ALIGNED/REVERSED**(以权威ADJ-BMP符号判定);SIG+ALIGNED=支持/SIG+REVERSED=显著证伪不得写成支持/NOT_SIG无论方向=未获统计支持;signed CAAR与ADJ-BMP符号不一致必须并列披露不得择一;field_roles 增 effect_alignment=CONTEXT | 裁定一·二(verdict条) |
| engine_params | 描述性占位字符串 | **结构化对象**(终版要求):{benchmark_mode:market, diagnostic_dims:[direction], direction_display:raw, direction_signed_main:true, effect_alignment_source:adj_bmp_sign, nfv_structured:true, postpone_policy:unified_announcement, st_policy:reject, strata_enabled:false, verdict_policy:adj_bmp_main_only, note:…新语义实现于适配阶段} | 终版要求+十项裁定汇总 |
| bias_statement | 照令 | 不变 | — |
| verdict_power_note | llm/prescreen | 不变 | — |
| holdout | 2024-07-01 三键 | 不变 | — |
| pap_digest_binding | 沿exp8先例(草案为描述句) | **结构化四键对象**(canonical_algorithm/caller_assert_rule/result_binding/report_anchor_rule,沿exp8 v3逐字范式) | 终版要求(去占位) |
| sample_gate | 30 | 不变(裁定十确认) | — |
| snapshot_batch_req | 描述句 | **结构化两键对象**(source/note),实质不变 | 终版要求(去占位) |
| reporting_commitments | ①-⑥ | 增:④折叠组成链审计清单入audit;⑥effect_alignment随主窗报告+signed CAAR与ADJ-BMP符号并列披露;①增"不能因对不上而修改冻结规则" | 裁定九+verdict条+终版要求 |
| (删除) | 草案顶层无删除键 | — | 三态verdict提案系§3清单项非草案键,直接不采 |

## 3. 窄闸数字身份(令三重申)

候选 12,569 / 基准B可判 5,225 **仅是窄闸对账参考**,不是正式研究样本量,不得预写进未来结果。
正式数量由事件生成器采用**已裁 p_change 规则重实现**后,在研究期+flat 排除+全部 fail-closed 规则下重新确定,
并逐层归因对账;**不能因对不上而修改冻结规则**——对账异常即停报人。(已落 PAP `event_def` 末句+`reporting_commitments`①)

## 4. validate 与解析证据(本单元实测)

```
validate_pap: PASS
parse_test_windows: (5, 20, 60)
canonical digest : 94b9ba7821c3393e33123971f8b681e8f5d457e43c6f8bf39df9caa1f543fa17
file    sha256   : 94b9ba7821c3393e33123971f8b681e8f5d457e43c6f8bf39df9caa1f543fa17
digest == file sha256: PASS
```

## 5. 冻结后必须实施的攻击 fixture 清单(令三指定八组;适配阶段实现,本单元零代码)

1. **signed 同向归一**:构造 up 层正 raw AR 与 down 层负 raw AR 样本,经 signed 变换后主检验输入同为正。
2. **反向样本**:沿修正方向的反向价格反应(up 层负 AR / down 层正 AR)经 signed 后为负。
3. **SIG+REVERSED 措辞攻击**:ADJ-BMP 显著且 signed 效应为负时,报告/verdict_note 不得出现"支持"类措辞(零命中断言);effect_alignment 必须=REVERSED。
4. **公告日历锚**:周末/节假日公告(T 无个股 bar、T 非交易所交易日)不得被剔除,τ0 正确落于 ann_date 后第一个交易所交易日。
5. **顺延边界**:公告语义下顺延 1/5/6 日(缺 bar/停牌/一字混合)——5 日保留、第 6 日 postpone 剔除;逐例断言。
6. **方向判定全分支**:单边界回退该单值/两边界全空不可判 fail-closed/中点相等 flat 仅计数/同链同日多行标量不一致 fail-closed/白名单外方向值(空值/unknown/其他)进 CAR 前 fail-closed。
7. **raw 诊断层零判决**:direction 层递归扫描零 verdict/零显著性分类字段,计算路径结构上不调用判决函数(monkeypatch 计数=0 式攻击证明)。
8. **signed 输入实改证明**:估计期异常残差、秩方向、事件间相关符号等统计输入在 signed 口径下确实改变(与仅改展示值的假实现可区分),非只改最终 CAAR 符号。

补充建议(非令内,采否由人定):9) pap_sha256_assert 逐字断言 fail-closed(沿 exp8 fixture ⑨先例);10) 对账产出=12,569/5,225 逐层归因表落 audit 的结构断言。

## 6. 交验点(v1,已被 §7 取代)

~~待人复核终版并以 digest `94b9ba78…fa17` 下冻结句~~——该 digest 未批冻结、已作废(v2 补记)。

## 7. v2 回修(2026-07-18 深夜三,令=`earnings-revision-pap-v2-order-2026-07-18.md`,留痕 `e8b5964`)

### 7.1 实物

- 新版本:`taosha/docs/earnings-revision-pap-final-v2-2026-07-18.json`(v1 未覆盖,SHA 复核仍 `94b9ba78…fa17`)
- **v2 文件 SHA256 = canonical digest = `e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`**(引擎重算==文件 SHA 当场断言 PASS)
- `validate_pap`:**PASS**;`parse_test_windows`:**(5, 20, 60)**(均对 v2 实测)

### 7.2 v1→v2 逐键 diff(程序化对账:键集不变,恰 4 键改、15 键逐字节相等)

| 键 | 变更 | 依据 |
|----|------|------|
| event_def | 增 flat 阶段语义段:候选方向分类阶段 flat=合法分类结果,计入 flat 计数块后排除出主事件集,不得因存在 flat 候选拒绝整次运行;主事件集仅由 up/down 构成;主事件流形成后、进 CAR 及顶层 verdict 前 direction 严格∈{up,down},flat/null/unknown 等白名单外值**泄漏进主事件流**才 fail-closed 拒跑 | 令一 |
| diagnostic_dimensions | `direction_fail_closed` 重写为两阶段语义(候选阶段正常排除≠拒跑;泄漏才拒);`note` 末句改"flat候选不在轴内、不入主事件集,仅入计数报告块(候选阶段正常排除,非拒跑事由)";axes/display_basis/zero_survivor_status 未动 | 令一 |
| verdict_authority | effect_alignment 补成全定义函数:权威 ADJ-BMP 统计量 >0=ALIGNED、<0=REVERSED、=0=NEUTRAL、不可得=UNAVAILABLE;INSUFFICIENT/AMBIGUOUS 等无可用 ADJ-BMP 必须输出 UNAVAILABLE 不得猜测方向;四态均不得成为独立 verdict 或改变顶层四态判决;SIG+ALIGNED/SIG+REVERSED/NOT_SIG 解释句及 field_roles(effect_alignment=CONTEXT)不变 | 令二 |
| reporting_commitments | ③改 flat 候选计数(正常排除不终止运行);⑥改 effect_alignment 四态全定义随主窗报告+无可用 ADJ-BMP 必须=UNAVAILABLE+四态不产生不改 verdict | 令一+二 |
| 其余 15 键 | pap_schema_version/analysis_type/signed_ar/window/pool/benchmark/cleaning/cost/engine_params/bias_statement/verdict_power_note/holdout/pap_digest_binding/sample_gate/snapshot_batch_req **逐字节相等**(生成器程序化断言) | — |

### 7.3 攻击 fixture 清单增补(令定四组,并入 §5 总清单为 11-14 号)

11. **flat 候选正常排除**:构造含 flat 候选的输入,断言运行不终止、flat 进计数块、主事件集不含 flat、主检验正常产出。
12. **flat 泄漏拒跑**:向已成形主事件流注入 flat/null/unknown/白名单外方向值,断言在 CAR 计算及顶层 verdict 调用前 fail-closed 拒绝(判决函数调用计数=0)。
13. **effect_alignment 四分支**:ADJ-BMP 正/负/零/不可得(含 INSUFFICIENT、AMBIGUOUS 终态)四分支逐一断言输出 ALIGNED/REVERSED/NEUTRAL/UNAVAILABLE;不可得分支不得猜测方向。
14. **四态零判决影响**:四种 alignment 状态下顶层 verdict 均由既有四态判决路径独立产生,alignment 不产生独立 verdict、不改变顶层判决(对照攻击:翻转 alignment 值,verdict 逐字节不变)。

### 7.4 交验点(现行)

v2 全毕,**停交验点**。待人复核 v2 并以 digest `e1d18dc1…7fd5` 下冻结句+另写预判;
旧 digest `94b9ba78…fa17` 及任何预判不得平移。未令不动代码/manifest/台账/运行。
