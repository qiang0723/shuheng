# 切片3 · #2b(回撤反抽·b1池)步② 引擎接入 · 事件版第一份真实体检报告 · 验收档

日期:2026-07-09 · 台账 exp_id=3(drawdown_rebuy #2 = 「#2b」,frozen,verdict_power=full)
HEAD:见文末 commit · 报告完成即交、**不解读**(开工令⑥:统计事实陈述,判读留人)

---

## 0. 一句话

#2b 事件版(附录F-rev1 状态机生成事件 + b1 池 PIT 过滤 + **b1 池等权 PIT 活基准** SIM)第一份全A股真实
体检报告出炉:**verdict = `NOT_SIG`**。原始异常收益强负(主窗 CAAR=−0.031)、朴素 t/秩/日历三法均强负显著,
但截面相关 ρ̄=0.2197 极高(回撤反抽随大盘齐动、事件高度聚集)→ ADJ-BMP 校正后不显著(聚集假阳性),
以 ADJ-BMP 为准判 `NOT_SIG`。策略版(附录B 离场)=步③另跑。

---

## 1. 步②工程改造(engine 接入)· 约束③ #4 逐字节零回归

沿用 #4 流水线全套(删失诊断/板块分层/剔除分解/N_valid+折算 N_eff/可交易口径),额外 D1/D2/D3
事件生成诊断入报告;**三层(预喜/预亏/扭亏)不适用**(pap event_def 无 layers 维度)。

| 改动 | 文件 | 要点 |
|---|---|---|
| window 解析 | `experiment/pap.py` | 正则扩 `(?:后\|事件版)`,忠实读 exp3 冻结文本 `事件版20/60日;策略版按离场`→(20,60);"策略版按离场"半句不吃(归附录B步③域);#4/合成 `后X/Y日` 逐字节零回归 + 固定回归自检(人裁 2026-07-09,选项2,非①类) |
| 事件适配 | `engine/drawdown_events.py` | `DrawdownEventRow`(进场日→first_ann_date、event_type_layer=None)+ `to_event_rows` + `diagnostic_summary`(D1/D2/D3) |
| 执行器 | `engine/runner.py` | `benchmark_mode='pool_pit'`(读 `reader.pool_return` 活基准、sec_returns 惰性)+ `events` 事件源参数 + `strata_enabled` 开关 + D1/D2/D3 入 se_meta(仅 #2b)+ `drawdown_diagnostic` 聚合(仅 #2b 含此键)+ 可交易口径跳过 None 层 |
| 报告 | `engine/report.py` | #2b 专属横幅 + 三层不适用注 + D1/D2/D3 诊断段 |
| Reader | `reader/view.py` | `pool_return(dates)` 读 `pool_b1_return_current` |
| 驱动 | `harness/run_drawdown_study.py` | 读 exp3 冻结 pap→池宇宙→生成事件+池PIT过滤→run_study(pool_pit/events/strata关)→report;不改 ledger |

**约束③(合成域逐字节零回归)**:改动前后 `run_ashare_study`(#4 合成 fixture)result_json **sha256 = `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22` 前后同**(三次校验:改前基线 / 引擎改动后 / 可交易口径跳过None层修复后,均同 sha)。#4 台账事件(events=None、无 d1 属性)→ se_meta 不变、result 不含 drawdown_diagnostic 键、strata 默认 True → 既有路径逐字节不变。

---

## 2. b1 池等权 PIT 活基准(预置① · 骗不了人)

**预置①**:基准=b1 池等权 PIT 活基准——基准成分逐日=当日池快照(pool_b1_current[d]);
**验收硬项=任抽一日基准成分集合==当日池快照**;禁读静态 market_return。

- **004 表** `taosha/sql/004_pool_b1_return.sql`(apply 属主 postgres,COMMIT):`pool_b1_return`(ret_pool_eqw/n_pool_stocks)+ `pool_b1_return_batch`(**pool_batch_id 外键=成分来自哪批池快照血缘**)+ `pool_b1_return_current` max-batch 路由视图 + append-only 触发器焊死 + 授权 taosha_engine 只读/taosha_app 写。
- **口径**:ret_pool_eqw[d] = 当日池快照成员中【有 present bar 且有前序 present bar】的票 log(后复权 close_d/close_前序) 等权平均;收益核=冻结 `returns.py`(rates.cpp 复刻,跨缺口落恢复日);n_pool_stocks ⊆ 当日池快照。
- **seed** `taosha/ingest/seed_pool_b1_return.py` 落库 **batch=1、8066 行**、[1991-06-10..2024-06-28]、n_pool_stocks∈[1,1015] 均359.3、frozen_digest=`b88a43ef…`、pool_batch=1:
  - **双算闸**:Path A(冻结 returns.py)vs Path B(SQL 窗口 ln(close/lag)),均按 membership 门控 → **max|Δret|=1.683e-16、n_pool_stocks 不一致=0**;
  - **硬闸**:max_date=2024-06-28 < holdout 2024-07-01;
  - **✅ 验收硬项 --verify(引擎视角 taosha_engine 读 pool_b1_current)**:确定性抽 12 日(1991-06-10 … 2024-06-28),逐日从 pool_b1_current[d] 独立重算 ret 与库值机器精度一致(**max|Δ|=1.39e-17 < 1e-9**)、**成分逐日==当日池快照、有效分母全等**。末日 2024-06-28 池快照=1015=有效分母=n_pool_stocks(印证 n_pool_stocks≤快照、门控无误)。

---

## 3. #2b 事件版真实体检报告(统计事实 · 不解读)

产物:`/tmp/s3step2/drawdown_report.txt` + `drawdown_result.json`(aliyun;报告原文见附)。

- **样本**:池内进场事件(附录F-rev1)= **19638** 条;有效存活 **N_valid=17929**、剔除 1709、**剔除率=0.087**(>5%告警,主因 coverage 覆盖不足;2016/2018/2024 偏高〔2024=history 尾部数据不足 325〕)。
- **相关性折算有效 N**:ρ̄=**0.2197**(行业内,口径④)→ **Kish=4.6 / KP=3.6**(#2b 事件高度聚集,独立信息极少;ADJ-BMP 已内嵌此坍缩)。
- **主检验(verdict=`NOT_SIG`)**:主窗[0,+19] CAAR=**−0.03104**、BMP_CAR=−28.081、**ADJ-BMP_CAR=−0.411**(临界±2.241,**不显著**);稳健窗[0,+59] CAAR=−0.08170、ADJ-BMP_CAR=−0.587。朴素 t=**−34.096**(显著)/ Corrado 秩 t=**−8.149**(dir−1)/ 日历 t=**−13.028**(dir−1)。**判据**:朴素 t 显著而 ADJ-BMP 不显著 → 聚集假阳性,以 ADJ-BMP 为准 → `NOT_SIG`。
- **逐 τ**:AAR 各点均负(τ=0 −0.00287 … τ=59 −0.00137),持续负漂移;BMP 各点强负、ADJ-BMP 各点 |·|<0.2。
- **D1/D2/D3 事件生成诊断(F2;报告项·不进 verdict)**:池内生成 N=19638 → D1(进场前从未破 ma10)=**0.132**、D2(回撤触发→进场交易日)min2/中位23/mean25.4/max136、D3(进场前曾破 ma20)=**0.859**;清洗存活 N=17929 相近(D1=0.128/D3=0.863)。
- **板块分层**:main 有效15259 / chinext 2393(regime 前1016 后1377)/ star 277 / ST 已剔除层有效0;行业 unknown 残余 1192/17929=0.066(>5% 升级上报,报告项)。
- **删失诊断窗(R5)/ 剔除按年份×层**:齐(见报告原文 + result_json);三层不适用。
- **可交易口径(选项2;hold-to-window-end 净额,报告项·不改判决)**:合并主窗 N=17689 净均 −0.00584 胜率0.445 毛均 −0.00235;稳健 N=17596 净均 −0.00953 胜率0.404。(层分解不出:#2b 单信号无 layer 维度。)

**复现留痕(spec §9)**:audit.pool_snapshot 记 pool_b1_batch=1 / pool_return_batch=1;冻结审计 frozen_config=`b88a43ef…`/frozen_ashare=`c795b21e…`。

---

## 4. 结论与下一步

- **步②工程面完成**:pool_pit 活基准接入 + 事件版流水线 + D1/D2/D3 诊断 + 三层不适用;约束③ #4 逐字节零回归;池等权 PIT 基准双算闸+硬闸+**验收硬项(成分==当日池快照)全过**。
- **#2b 事件版统计结论(不解读=开工令⑥)**:`NOT_SIG`——原始强负漂移,但事件高度聚集(ρ̄0.2197/Kish 4.6),ADJ-BMP 校正后不显著。
- **下一步=步③策略版**(附录B:成本−20%强平 或 收盘破20日线先到先出,net 全额扣成本;事件版先跑毕、策略版解读前架构窗口交 R6 CPCV/PBO 调研不阻塞)→ 步④照 #4 先例(审计→终签→人开卡)。

〔携带项〕report.py 早年 carry-item「切片2合成验收」标题:#2b 路径已出专属横幅(据 drawdown_diagnostic 键),#4/合成横幅保持原样未动(约束③)。
