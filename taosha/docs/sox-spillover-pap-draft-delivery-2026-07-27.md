# exp24 sox_spillover PAP 草案单元 · 交付档(2026-07-27)

> 人令留痕:`taosha/docs/sox-spillover-pap-draft-order-2026-07-27.md`。窄闸报告=
> `sox-spillover-narrow-gate-report-2026-07-26.md`(有条件通过:可进入 PAP 草案,不据此冻结或生产施工)。
> 本单元=PAP 草案文本+裁决映射+五项人裁菜单;**零采集、零入库、零冻结、零 manifest、零收益读取、零运行**。
> **草案=NOT-FROZEN**:`taosha/docs/sox-spillover-pap-draft-2026-07-27.json`,18 键事件版结构
> (蓝本=high-pullback-pap-draft-2026-07-24.json 逐键对偶;signed 单判决沿 exp20 `direction_signed_main` 产线路径,语义逐字沿承)。
> **候选 digest=文件 SHA256==canonical 重算==`d369e04faad3a7a2505a7d8f0c5995b379d4529ac9476ddd9d08e944dd849b2c`**;
> validate_pap PASS;parse_test_windows=(5,20,60)。
> ⚠草案含五处【待人裁A–E】占位标记,人拍后按裁定原文替换、终版另出、digest 必变;本候选 digest 仅锚定草案文本本身。

## 1. 两条注记落实(人令 2026-07-27)

**注记①(措辞精确化)**:窄闸报告§结论中「A股侧数据齐备」精确化为
「**A股行情与日历齐备,半导体历史成分尚未进入qbase**」。已落实于:本交付档(此节)、
草案 JSON `pool.source` 与 `snapshot_batch_req.note`(原文引用)、窄闸报告文末注记块(带日期与令指针)、STATE。
旧措辞不再单独引用,引用窄闸结论时以精确化口径为准。

**注记②(Nasdaq 官方渠道补核)**:核验限文档与元数据探针(共 12 次小窗/页面请求,单窗≤5 日,零批量采集、零落库),2026-07-27 实测:

| 项 | 实测结论 |
|---|---|
| 官方页面 | `indexes.nasdaq.com/Index/Overview/sox` 在线,含 SOX 实时值/历史图/方法论与 factsheet 文档(methodology_SOX.pdf 等) |
| **程序化端点(匿名)** | `POST https://indexes.nasdaq.com/Index/HistoryData`(参数 id=SOX/startDate/endDate/timeOfDay=EOD),**匿名 HTTP 200**,JSON 结构化字段(TimeStamp/Value/High/Low/NetChange/Divisor/MarketValue/Constituents=30/Currency=USD 等);另有 `/Index/ExportHistory/SOX?startDate=&endDate=` 导出通道(同参数族)。⚠该端点为站点内部 AJAX,非公开承诺 API,版式可变 |
| 稳定性 | 12 次探针全部 200、无限流迹象(对照:东财数次探针即限流);响应即时 |
| **准确性交叉** | 2026-07-24 官方 Value=**11818.88530208787**,与窄闸三源交叉值(Yahoo 11818.886/东财 11818.89/新浪 11818.8853)一致——官方数值权威锚成立 |
| **历史深度(匿名)** | 实测有数据窗:2005-07-18 起各年抽窗均 5 行;空窗:2004-07-16 及更早(2001/1996/1994/1993 均空)→ **匿名深度边界在 2004-07~2005-07 之间(约 21 年)**;1993-12 基期与 1994-05 全史匿名不可得。**覆盖研究范围(2011 起+250 日估计窗)充分** |
| 授权通道 | GIW Web Services API(spec v3.4,username/password POST,`indexes.nasdaqomx.com/reports2/*.ashx`)、GIFFD SFTP、GIDS 实时——均为订阅/entitlement 制(「weights/components/corporate actions/historical data 请联系 Nasdaq Index Sales」),非免费开放 API |
| 公开使用条款 | 站点 Disclaimer 页(`/Home/Disclaimer`)为免责声明(无担保/非投资建议),**未见明文允许或禁止匿名程序化抓取 EOD 历史**;GIW spec 含 AS-IS 无担保条款;SEDOL/CUSIP 字段注明 fee-liable(本假设不需该两字段)。条款上处于灰区:内部研究小量拉取属低风险,但「官方且授权明确」需订阅通道 |

**结论(进裁定A菜单,不预断)**:官方渠道**存在且匿名程序化可用**——「无一官方免费源」的窄闸小结须修正为
「**官方匿名 Web 端点可用(深度约 21 年、非承诺 API、条款灰区);官方授权 API 需订阅**」。

## 2. 登记原文 → 草案键位映射

| 登记字段(库实物,2026-07-12) | 原文 | 落入键位 | 落法 |
|---|---|---|---|
| event_def | 「美股费城半导体指数(SOX)单日涨跌幅 ≥±3% → 次日 A 股半导体链=事件」 | `event_def` 首句 | **逐字沿承**;细化(触发算式/方向/无前视映射/展开/研究范围)为草案 NOT-FROZEN 文本,映射规则=窄闸§2.3 |
| direction=同向 | 同向 | `event_def`(2)+`engine_params.direction_signed_main` | signed 单判决:direction_sign=sign(SOX r_T),up=+1/down=−1,事件级逐τ翻转先于聚合(exp20 路径逐字沿承) |
| pool | 「A股半导体链(成分界定待冻结)」 | `pool.universe/source/pit_semantics` | 待冻结→【待人裁B+C】占位+申万 L2 最小自洽候选如实列出 |
| window | 待冻结 | `window` | 草案默认 τ0起后5/20/60(确认清单#2);τ0=映射日当日(确认清单#1) |
| benchmark | 待冻结 | `benchmark` | 草案默认 market 全市场等权(确认清单#3) |
| cost | 待冻结 | `cost` | §6 冻结常量四值沿承(确认清单#6;仅 schema 与执行审计,不控 CAR 取样) |
| cleaning | 待冻结 | `cleaning` | A股侧沿既有冻结常量(250~91/112(70%)/missing_bar_only≤5;确认清单#4);SOX 侧细则随裁定A |
| snapshot_batch_req | 待冻结 | `snapshot_batch_req` | qbase 既有视图+market_eqw_return+【随 A/C 新增】SOX 表+成分视图,全部经 StudySnapshot 路由 |
| data_note | 采集件排产时触发 | `pool.source`+`snapshot_batch_req` | 如实沿承;采集件=冻结前置工程件,本单元零施工 |
| crowding_note | crowding_prior=高 | `bias_statement`④+`verdict_power_note` | 聚集坍缩如实声明,连接裁定E |
| (登记外结构沿承) | — | `analysis_type`/`pap_schema_version`/`holdout`/`sample_gate`/`pap_digest_binding`/`diagnostic_dimensions`/`verdict_authority`/`reporting_commitments`/`bias_statement`/`verdict_power_note` | 沿 exp11 18 键范式逐键对偶;pap_digest_binding 逐字沿承 |

## 3. 五项人裁菜单(随草案呈拍;A/B=冻结前置)

### A. SOX 锚定源(含 Nasdaq 官方渠道补核结论)——冻结前置①
| 选项 | 内容 | 特性 |
|---|---|---|
| A1 | **Nasdaq 官方匿名 Web 端点**(`/Index/HistoryData`) | 官方数值权威;匿名深度~2005-07 起(覆盖研究范围);非承诺 API、条款灰区;实测稳定无限流 |
| A2 | **Yahoo `^SOX`** | 全史 1994-05-04 起;字段/时区元数据最明确(America/New_York 显式);非官方;AWS 出口可达 |
| A3 | 东财 251.SOX / 新浪 gb_sox | 国内出口可达;东财限流严重、新浪仅实时口径已证——仅宜作交叉校验源 |
| A4 | **组合:主锚+第二源交叉**(如 A1 主锚+A2 交叉,或 A2 主锚+A1 官方交叉) | 窄闸建议形态:单一锚定源+原始响应 SHA 留痕+第二源收盘交叉校验 |
| A5 | Nasdaq 订阅通道(GIW API/GIFFD) | 官方且授权明确;需订阅签约,成本与周期人裁 |

工地建议(仅供参考,人拍):**A4(A1 主锚+A2 深度与交叉备源)**——官方数值为锚、匿名深度足够研究范围、Yahoo 补全史与容灾;三源 07-24 收盘已证一致。

### B. 申万半导体 L2「半PIT」语义是否接受——冻结前置②
| 选项 | 内容 |
|---|---|
| B1 | 接受:池=申万半导体 L2(801081.SI)全体(含七 L3),成员进出按 in_date/out_date,半PIT 语义如实入 bias_statement(草案现文) |
| B2 | 接受但扩池:另加人指定的电子链环节(须人逐一点名,工地不代选) |
| B3 | 不接受:改为人另行指定的成分口径(如指数成分快照/自建清单),待人给出 |

### C. 成分数据落地路径(工程件,随 B 定)
| 选项 | 内容 |
|---|---|
| C1 | 老机 `md.index_member` 借阅 → qbase 归一视图扩(触碰老机数据借阅边界,须人准入;7,890 行 KB 级一次性) |
| C2 | 同源 tushare 重采直落 qbase(不触老机;依赖 tushare 接口可用性与口径一致性,落地后与老机行数抽验对账) |

### D. 中国长假多对一映射的合并规则(PAP 冻结项,冻结令定)
| 选项 | 内容 | 影响 |
|---|---|---|
| D1 | 各自成事件(同一 A 股首开日多事件并存) | 同日同股多事件键冲突,须另设去重规则,事件键唯一性复杂化 |
| D2 | 合并取累计(假期内 SOX 累计收益率对 ±3% 重判,方向=累计符号) | 语义自洽(「假期信息总量」);触发口径偏离登记单日原文,须人确认为细化而非改判 |
| D3 | 取末日(仅假期最后一个美国交易日的触发有效) | 简单;丢弃期内其余触发信息 |
| D4 | 整段剔除(多对一日不成事件,仅计数报告) | 最保守;春节/国庆样本结构性缺失 |

### E. N_eff≈事件日数的低功效知情确认(设计固有,非缺陷修补项)
市场级日期事件×全池展开→ADJ-BMP 聚集校正后 N_eff 坍缩至事件日数量级;
±3% 阈值下触发日数十年或仅数十至百余日(候选统计按令未算,待采集件落地补验)。
**E1=知情并照此设计推进 / E2=人另调设计(如改阈值须走改判/新假设流程,工地不代选)。**

## 4. 冻结前置显式登记(人令原文)

> **SOX 数据源闭合(裁定A)+ 半导体池语义闭合(裁定B),两项未闭不得冻结。**

配套工程最小件(人拍后、排产时施工,本单元零施工):①SOX 最小采集件(源随 A;原始响应 SHA 留痕+节流容错);
②成分归一视图(路径随 C);③exp24 事件生成 harness(SOX 阈值→方向→无前视映射→池展开→signed 事件流,复用 run_study,引擎零改动)。
裁定D 属 PAP 冻结内容随冻结令定;裁定E 为知情确认,冻结令前须留痕。

## 5. 待人终版确认清单(草案默认读法,非 A–E;人可一并批复或改裁)

1. **τ0 锚定=映射日当日**:SOX 收盘信息于 A 股开盘前已知(窄闸§2.3),A 股映射日当日即反应日,草案取 τ0=event_date 当日(有真实bar即为τ0;missing_bar_only 顺延≤5)。备选=次日起(exp11「事件后首日」惯例,将错过反应主日)。**请确认。**
2. **三窗 5/20/60 沿事件版惯例**(主窗=后5日)。**请确认。**
3. **benchmark=market 全市场等权**(pool 基准会吸收行业共同反应,仅可作诊断)。**请确认。**
4. **A股清洗常量沿承**:估计期 250~91(160 日)/覆盖门槛 112(70%)/missing_bar_only≤5/sample_gate=30。**请确认。**
5. **研究范围 2011-01-01≤event_date<2024-07-01**(沿 family 惯例;SOX 侧数据深度无论 A1 或 A2 均覆盖)。**请确认。**
6. **cost 四值沿承**(仅 schema 与执行审计不控 CAR 取样)+ **st_policy='reject' 沿 exp20 同款**。**请确认。**
7. **键结构说明**:令文=18 键,草案=18 键(exp11 蓝本);exp20 终版另有第 19 键 `signed_ar`(signed 语义专章)。本草案已将 exp20 signed 语义逐字要点并入 `engine_params.note`/`verdict_authority`/`event_def`(2);若人要求终版补设 `signed_ar` 独立键(与 exp20 完全同构),冻结稿补上、digest 必变。**请裁 18 键维持或 19 键补设。**
8. 确认后流程:人拍 A–E+批复本清单 → 工程件施工与 SOX 触发统计补验(另令)→ 人以终版 digest 下**冻结令**+方向与把握度预判 → 冻结后 manifest→单次正式运行→persist(各另令)。

## 6. 边界遵守声明

零采集(网络访问仅注记②文档与元数据探针:12 次小窗/页面请求,单窗≤5 日,响应仅记录字段与行数,探针文件已清理不落库不入仓);
零数据库写入(台账只读核对:exp24 仍 registered 三槽空,25=13/2/9/1);零冻结零 manifest(study_snapshot 未动);
零收益读取(未触任何 A 股事件后收益/CAR/显著性;SOX 侧亦零批量历史);零正式运行零 persist;零生产代码
(草案构建脚本=取证件,住 scratchpad/取证包,不入仓库代码路径;引擎/采集/视图零改动)。
仓库改动=令文留痕+草案 JSON+本交付档+窄闸报告文末注记块+STATE。

## 7. 取证

取证包=AWS `~/shuheng/s24_pap_delivery_2026-07-27/`(令文+草案 JSON+本交付档+构建脚本+SHA256SUMS);
aliyun 侧 pull 后以同脚本重算 canonical digest 复核(`canonical_check.txt` 记录)。

**▶停交验点待人:①拍 A–E 五项(A/B=冻结前置)②批复 §5 确认清单(含#7 键结构)③复核草案 JSON(候选 digest `d369e04f…9b2c`);人拍后按裁定原文出终版、以终版 digest 另下冻结令;未令不动。**
