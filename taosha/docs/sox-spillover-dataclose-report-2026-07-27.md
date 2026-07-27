# exp24 sox_spillover 数据前置闭合单元 · 交付报告(2026-07-27)

> 人令留痕:`sox-spillover-dataclose-order-2026-07-27.md`(草案通过+裁定 A4/B1/C2/D4/E1+
> 确认清单批复〔#1–6 默认、#7=19 键 signed_ar、#8 流程〕+施工授权)。
> 边界:范围限 SOX 与 801081.SI;零通用美股/跨市场平台;仍禁终版 PAP、冻结、研究 manifest、
> 正式运行、persist;禁读 A 股事件后收益。

## 0. 开工核对(全符后才动工)

exp24=registered 三槽空 ✓;台账 25=13/2/9/1 ✓;tushare `index_member_all` 先验可用
(184 现役+24 已出=208 行,与老机 `md.index_member` 窄闸计数逐项一致)✓;
Nasdaq 端点阿里云出口可达(HTTP 200)✓。

## 1. 施工产物(全部落库/落仓)

| 件 | 实物 | 说明 |
|---|---|---|
| DDL | `qbase/sql/020_sox_sw_member.sql` | `sox_daily_snap`+`sw_member_snap`(007 范式:append-only 触发器焊死+双时戳+fact_batch lineage)+最新批读取视图 `sox_daily`/`sw_member`;apply=qbase_app |
| SOX 采集件 | `qbase/ingest/seed_sox.py` | 主锚=Nasdaq GIW 站点内部端点(裁定 A4;**非官方授权API**,如实标注);节流+退避,三败即停报;源非交易日占位行(Value=null,如 2012-10-29 飓风休市)剔除留痕 |
| SOX 批 | **fact_batch 13**=`nasdaq_giw:sox_daily`,**3,395 行,2010-12-30..2024-06-27** | 范围推定(人令:不因 A 股估计窗扩大):T0=2010-12-31(首个映射≥2011 年首交易日 2011-01-04 的触发候选日)→载入起点=其前一 SOX 交易日 **2010-12-30**;T_end=**2024-06-27**(最后映射≤2024-06-28<holdout 的 T);日历缓冲行 7 只存证据包不落库 |
| 成分采集件 | `qbase/ingest/seed_sw_member.py` | 源=tushare `index_member_all`(裁定 C2;接口失败即停报,零老机回退);半PIT 语义如实照落(裁定 B1) |
| 成分批 | **fact_batch 14**=`tushare:sw_member`,**208 行**(184 现役+24 已出,in_date 1998-09-24..2026-07-10) | 与老机窄闸计数(208/24)完全对账;L3 七子行业齐 |
| 交叉件 | `qbase/ingest/sox_cross_check.py` | Yahoo `^SOX`(AWS 出口);原始响应+SHA **仅存内部证据包**(裁定 A4 原文),不入库不入仓 |
| 发布 | **源级快照 snapshot_id=247**,digest=`4a0dbd9e93e931422584036a50d0c522108f4c1cf8b481193133c4bc9fe1f450` | qbase 镜像+publication attestation 已核(attested=t);向量含 sox_daily=13/sw_member=14;**未生成任何 exp24 研究 manifest**(令文禁令;源级快照结构上不可被引擎当研究 manifest 消费) |

## 2. 第二源交叉校验(Yahoo ^SOX;数据质量事实,不改主锚)

- **交易日集合完全一致**:共同 3,395 日;仅主锚有=0;仅 Yahoo 有=0(占位行剔除口径与
  Yahoo 交易日自证互证)。
- **收盘一致性**:3,350/3,395(98.7%)两位小数一致;差≥0.1 仅 **1 日**(2015-02-02,
  主锚 655.187 vs Yahoo 653.140,Δ2.05≈0.031%);其余全部 <0.01。
- 主锚不因差异回改;差异清单在证据包 `cross_check_report.txt`,正式报告作 NOT_FOR_VERDICT
  数据质量披露。

## 3. 落地后只读触发报告(双跑 SHA 一致=`b9c752d1d48346aa…711079`;Decimal 闭区间)

**±3% 触发**:总数=**314**(up **161** / down **153**);恰等 3% 边界命中=**0**。
触发日逐年(美东 T):2011=32 2012=10 2013=4 2014=5 2015=11 2016=14 2017=3 2018=25
2019=17 2020=49 2021=32 2022=**73** 2023=24 2024H1=15。

**无前视映射**(T→北京历日 T+1 起首个 A 股交易日):触发映射日=**301**。
**D4 碰撞整段剔除**(仅计数,禁改累计):碰撞映射日 **9** 个,剔除触发 **22** 个——全部为
长假窗(2011 国庆、2020 春节/五一/国庆、2022 春节/五一/端午/国庆、2023 春节);
最重一例 2011-10-10 吞 4 个触发(±方向混杂,佐证 D4 保守剔除的合理性,不代裁)。
**D4 后存活事件日=292**(up **150** / down **142**);逐年(A 股映射日):2011=28 2012=10
2013=4 2014=5 2015=11 2016=14 2017=3 2018=25 2019=17 2020=43 2021=32 2022=63 2023=22
2024H1=15。

**成分覆盖质量**(801081.SI 半PIT,批 14):存活事件日在池成员数 min=**17**(2011-10-25)
→ max=**157**(2024-06-25),mean=66.2,**零成员日=0**;逐年均值 2011=18 → 2024=155。
早年池窄(2011–2013 约 18 只)如实报告;半PIT 语义(现行 2021 版体系回溯+历史进出日期)
已在草案 bias_statement 承诺披露。

**低功效预警落数**(裁定 E1 知情基础):事件日数上限=292 → 正式运行 N_eff 折算后约为该
量级或更低;正式结果将强制报告触发事件日数、ρ̄ 与 N_eff(草案 reporting_commitments 已载),
不因此调整阈值。

## 4. 边界遵守声明

采集限 SOX(单指数,3,395 行)与 801081.SI(单成分,208 行),零通用平台;
qbase 写入=fact_batch 13/14+两 snap 表(append-only 触发器焊死)+020 视图,零 UPDATE/DELETE;
taosha 写入=源级快照 247 一行(既有机制,受权角色);**零 exp24 研究 manifest、零冻结、
零终版 PAP、零正式运行、零 persist**;触发报告全程未触 A 股价格/收益表
(仅 sox_daily_snap/sw_member_snap/trade_cal_snap);台账未动(exp24 仍 registered 三槽空)。
Yahoo/Nasdaq 原始响应+SHA 仅存内部证据包(aliyun `/root/s24dataclose/`+AWS 交付包 evidence/),
不入库不入仓。

## 5. 取证

- aliyun `/root/s24dataclose/`:nasdaq_raw/(15 窗原始响应+fetch_manifest+fetch_log)、
  tushare_raw/(原始 CSV+SHA)、trigger_report_run1/2.txt(双跑一致)、s24_trigger_scan.py(取证件)。
- AWS `~/shuheng/s24_dataclose_delivery_2026-07-27/`:令文+DDL+采集件三份+触发报告+
  evidence/(sox_batch13.csv、yahoo 原始+SHA、cross_check_report.txt)+SHA256SUMS。

**▶停交验点待人:①验收数据前置闭合(冻结前置 A 源+B 池语义两项据此闭合与否由人认定)
②复核触发报告与交叉校验 ③另令=终版 PAP(19 键含 signed_ar,携五裁定原文)→冻结令。未令不动。**
