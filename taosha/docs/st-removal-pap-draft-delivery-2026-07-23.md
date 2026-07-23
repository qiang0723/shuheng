# exp12 `st_removal` PAP 草案单元 · 交付档(2026-07-23)

> 授权依据 = 人裁定令(原文留痕 `taosha/docs/st-removal-pap-rulings-2026-07-23.md`,
> F 条 commit `f6e495c` 先于本单元施工)。
> **本单元产物全部为草案与只读对账,不构成冻结、不构成运行授权。** 禁区遵守实录见 §5。
> 交付三件(照令)= ①PAP 草案 ②裁决映射 ③样本漏斗复算。

## 1. PAP 草案

- 实物 = `taosha/docs/st-removal-pap-draft-2026-07-23.json`(canonical 字节本体:词典序排序键+
  紧凑分隔符+UTF-8+末尾单换行)。
- **文件 SHA256 == canonical digest == `12e8366de0c60ca33065e1a53ac10cd3d92cbd8214c23f2498266ab5ab4dcf41`**。
- **状态 = NOT-FROZEN**:digest 仅为草案 digest,未写库、未入冻结记录;冻结须人另下冻结令绑定
  终版 digest,方向+把握度预判由人届时亲拟(登记 direction=正 仅为登记令原文,预判以冻结时亲拟为准)。
- `validate_pap` PASS;`parse_test_windows` = (5, 20, 60);`pap_schema_version=2`,`analysis_type='event'`;
  18 键,键集与 exp13 冻结 PAP 同构,**差异 3 处**:benchmark 不含 `pool_hypothesis`(雷达股池与本假设
  无关,径用登记令全市场口径)、engine_params 无 `st_policy`/`st_mode`(事件本体=ST摘帽,前段 ST 为
  构造性事实,不设 st 分层)、diagnostic_dims=[](无收益分层诊断轴,裁定未及)。

## 2. 人裁条款 → PAP 键位映射

| 裁定条款 | 要点 | PAP 键位落点 |
|---|---|---|
| 一 | 研究期 2011-01-01≤ann_date<2024-07-01;2007—2010 公告日系统性缺失不进入,禁 start_date 回填 | `event_def` + `cleaning` + `diagnostic_dimensions.coverage_disclosure` + `bias_statement` |
| 二 | 事件=完整撤销(前段 ST 状态名→后段非 ST 非退市名);摘星未摘帽不计事件仅报数 | `event_def` + `diagnostic_dimensions.destar_audit` + `reporting_commitments` |
| 三 | ann_date 唯一事件日锚;start_date 仅生效日+状态校验 | `event_def`(锚定义+ann>start 校验 fail-closed) |
| 四 | 退市谓词双格式 `%退`+`退市%`;ST→退/退市整理不入事件集 | `event_def`(谓词原文+008 不可搬用警示) |
| 五 | τ0=ann_date 之后首个有真实 bar 可交易日;≤5 交易所交易日,第 6 日剔除留痕 | `window` + `cleaning`(postpone) + `engine_params.postpone_policy` |
| 六 | 事件键 (ts_code,ann_date);重复/同日冲突/状态不可判 fail-closed | `event_def` + `cleaning`(与 postpone 分别留痕) |
| 七 | 草案须如实记录公告日覆盖边界及剔除规则 | `diagnostic_dimensions.coverage_disclosure` + `reporting_commitments` + `bias_statement` |
| 八 | 本单元禁改码库/读收益/manifest/冻结/运行 | 非 PAP 键;§5 执行实录 + `snapshot_batch_req.note` |

**裁定未覆盖、草案沿既有冻结常量的键(请终版一并确认)**:检验窗 5/20/60(`window`)、
`cost` 四值、估计窗 250~91·160·112/160(`cleaning`)、`sample_gate=30`、`holdout` 三键、
`verdict_policy='adj_bmp_main_only'` + field_roles(`verdict_authority`/`engine_params`)、
`pap_digest_binding`(平台制度)——均沿 exp8/exp13 既有冻结口径,零自行改动。
**另一处沿承需人明示**:裁定五『可交易』判定,草案沿 S2-DEC3 unified 口径(缺 bar 停牌、一字板
均属不可交易);若人裁『有真实 bar 即为可交易』(裁定原文字面),则一字板日亦可为 τ0、顺延仅数停牌
——两读差异已在 `cleaning` 键内显式并列,终版择一。
**τ0 起点读法(照原文执行)**:『之后首个』= 严格晚于 ann_date 当日(ann_date 当日即使有 bar 亦不为 τ0)。

## 3. 样本漏斗复算(只读;权威=qbase entity_alias 最新 namechange 批 batch_id=7)

复算件 = AWS scratchpad `exp12_funnel.sql`,aliyun 双跑输出逐字节一致
(sha256 `5b6220aa3b63855f9f5bcdb024d6c0e50f80c3bd4b582c123814e135536ecfb1`);
会话强制 `default_transaction_read_only=on`,零价格/收益列、零库写、零 manifest。
档序=互斥主原因固定顺序(与 `reporting_commitments` 承诺一致):

| 档 | 计数 | 说明 |
|---|---|---|
| 入库行(最新批 name) | 20,005 | append-only 快照,含源孪生 |
| − start_date 缺失 | 0 | |
| = 段(折叠孪生) | 18,113 | GROUP BY (ts_code,start_date)+LEAD 划界 |
| = 有前段转换 | 12,253 | 首段 5,860 无前段不计 |
| = 完整摘帽候选(前段 ST→本段普通) | 1,063 | 双格式退市谓词;旧后缀谓词会虚增 61(46 退市前缀泄漏+15 前段误判) |
| − fail 状态不可判(段内 ST/非ST 混名) | 0 | 裁定六,实测零 |
| − 锚缺失(ann 全空,留痕) | 296 | 全部为 2010 年及以前段=覆盖边界(裁定一) |
| − fail 锚冲突(段内多 ann) | 0 | 裁定六,实测零 |
| − fail 校验 ann>start | 0 | 裁定三,实测零 |
| − 研究期外(ann<2011-01-01 或 ≥2024-07-01) | 126 | 含 2010 年 5 例+2024-07 后 |
| − fail 事件键重复 (ts_code,ann_date) | 0 | 裁定六,实测零 |
| = **最终候选事件集** | **641** | 恒等式 1,063−0−296−0−0−126−0=641 ✓ |

逐年分布(ann_date 年):2011:35 / 2012:68 / 2013:73 / 2014:45 / 2015:32 / 2016:42 / 2017:50 /
2018:37 / 2019:21 / 2020:18 / 2021:92 / 2022:62 / 2023:40 / 2024H1:26(∑=641;年际起伏为
监管周期事实,如实报告不调参)。锚→生效日差:gap0=2 / 1–3 日=583 / 4–10 日=56 / >10=0。
**NFV 报数(裁定二)**:摘星未摘帽(*ST→ST)全史 458、研究期内锚干净 222;戴星(ST→*ST)全史 419;
ST→退市 143(不入事件集);以上正式运行按钉批快照重算对账。
**τ0 顺延剔除(postpone)本单元不可算**(需 bar 存在性=行情表,裁定八禁读收益):预登记为运行期
漏斗第 12 档,位于事件键重复之后,逐条留痕。**样本闸参照**:641≥sample_gate 30;若 postpone
剔除后任一窗存活<30,输出 INSUFFICIENT(合法终态)。

## 4. 台账对账(只读)

exp_id=12,family=`st_removal`,trial=1,status=**registered(本单元零写入)**,source_type=llm,
verdict_power=prescreen;登记 pap_json 之 holdout/universe/benchmark/dual(st_imposition)/
data_note 与本草案一致或经窄闸修正(data_note『is_st PIT 现成』→修正为:段位法现成,但事件识别
谓词须双格式,008 视图谓词不可原样搬用)。

## 5. 禁区遵守实录(裁定八)

- 生产代码零改动:本单元新增文件仅 `taosha/docs/` 三件(rulings/draft.json/本档)+ `ops/STATE.md` 更新。
- 数据库零写入:全部查询经 `PGOPTIONS='-c default_transaction_read_only=on'`;台账 exp12 行未动。
- 零收益读取:只读 entity_batch/entity_alias(+台账元数据);未触 bar_daily/adj_factor/收益视图。
- 零 manifest、零冻结、零运行。
- 完成后停交验点,等人对草案(含 §2 沿承键清单与 unified 两读)逐项裁决→冻结令。
