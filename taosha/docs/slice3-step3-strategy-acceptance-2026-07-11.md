# 切片3 · #2b 步③ 策略版验收档(2026-07-11)

**范围**:#2b(`drawdown_rebuy#2`,台账 exp_id=3,frozen,family_trial=2)策略版 = 附录B B1 单事件
持有路径模拟 + 附录G 离场操作化 + ADJ-BMP 四件套检验 + DSR 常设报告项。事件版(步②)已于
2026-07-09 验收(NOT_SIG,`slice3-step2-drawdown-eventver-acceptance-2026-07-09.md`);
本档 = 步③施工令(人 2026-07-10)+ 附录G(人批冻结 2026-07-10,2026-07-11 转发入仓)全量落地。
**判决权归事件版(四件套④)**:本档所有策略版统计量为体检对照(附录B B2 互为体检),不产/不改台账 verdict。

---

## 1. 冻结口径审计

- pap(exp_id=3,frozen):`cost` 块 = commission 0.00025 / stamp_tax_sell 0.001 / slippage_oneway
  0.001(买费 **0.00125**/卖费 **0.00225**,与 #4 同率,复用 `engine/execution.py` 乘式净额单一来源);
  `window`="事件版20/60日;策略版按离场"(后半句=本步域)。**一个数未改(铁律④)。**
- digests:frozen_config `b88a43ef…` / frozen_ashare `c795b21e…`(与事件版一致,result.audit 对上)。
- 离场操作化 = **附录G**(`taosha-spec-appendix-G.md`,人批冻结 2026-07-10,与 spec 正文同等效力):
  G1 收盘确认 / G2 双触发双 flag 主因强平 / G3 触发日收盘成交 / **G4 顺延日收盘价出(改判,作废旧
  open 口径)+ >20 交易日极端标注** / G5 右删失 mark-to-market 不剔除 / G6 one_word close 对前收判向
  / G7 污染标注 / G8 固化回归三例。
- DSR V 口径 = **proxy**(人裁+追认 2026-07-10;BLdP 退化路径 Var[SR_hat];追认经转发已生效)。
- 四件套框架(人给,随附录G 执行指令):①超额=减 b1 池同跨度买入持有 ②标准化=估计窗日波动×√持有
  日数+KP ③BHAR 右偏附 skew-adjusted t 稳健项 ④判决权归事件版。

## 2. 实现物(commits)

| 件 | commit | 要点 |
|---|---|---|
| 附录G 入档 + STATE 改判留痕 | `3cbacc5` | 裁决留痕先行(F 条),作废旧 P3=open 条目 |
| `compute/holding_path.py` 修正 | `9579caa` | P3→顺延日 close(G4);双 flag(G2);postpone_days 交易日口径(`trade_day_idx`,停牌缺行 bar 差会低估)+extreme 标注;G8 回归三例自检绿 |
| `compute/bhar_tests.py` | `0223fe0` | SBHAR=BHAR/(σ_est·√H);截面 z=mean/sd·√N×KP2010(因子复用 abnormal_tests 单一来源);Hall 1992/LBT 1999 t_sa=√n(S+γ̂S²/3+γ̂²S³/27+γ̂/(6n)),γ̂=Σ(x−x̄)³/(n·s³);全手算自检绿 |
| `engine/drawdown_strategy.py` | `0223fe0` | 328 行(<500 红线);同源清洗与 runner 事件循环逐步同构;冒烟净收益/BHAR/H 手算绿 |
| `harness/run_drawdown_strategy.py` | `0223fe0`+`15df9ae` | driver(照 run_drawdown_study 形制;只算+dump 不改 ledger)+--report |
| `report.render_strategy` | `15df9ae` | 独立渲染(不碰共享 render → 约束③零回归) |

## 3. 同源一致性声明(步④硬项)

- 事件源 = **与事件版完全同一代码路径**(`drawdown_events.generate_events` + b1 池 PIT 过滤):
  真实跑池内进场事件 **19638 条 == 事件版 19638**。
- 清洗流水线与 runner 事件循环**逐步同构**(clean_event→sim_fit→coverage→robust 窗越界,同序同判据)
  → 同源存活 **17929 == 事件版 N_valid 17929**(同构造);剔除 1709 == 事件版剔除(19638−17929)。
- 策略版自身差集(建仓 open 缺 / 基准缺日 / 标准化不可得)= **0 / 0 / 0 —— 差集为空,
  消费集(17929)== 事件版 N_valid 全集**(声明"⊆"实现为"==",无需逐项归因表)。

## 4. 策略版结果(统计事实,不解读=开工令⑥)

产物:aliyun `/tmp/s3step3/strategy_{result.json,run.log}` + 报告;本地备份 `scratchpad/s3step3_backup/`。

- **事件级收益分布(N=17929,成本乘式)**:净收益 均值 **−0.00861** 中位 −0.03037 胜率 0.250
  sd 0.11489;毛收益 均值 −0.00513;池同跨度 BH 均值 +0.00048;**毛超额(毛−基准)均值 −0.00561**;
  净超额(净−基准)均值 **−0.00909** 中位 −0.02147 胜率 0.292 sd 0.09544。
- **四件套② SBHAR 截面 ADJ-BMP(主检验=毛超额、净额并报;人批补正 2026-07-11)**:
  ρ̄=0.21966(行业内 339,337 对,与事件版 0.2197 同函数同集一致;双侧 α=0.025 临界 ±2.241,
  family_trial=2)。**毛超额(主检验):adj_z=−0.553,NOT_SIG 标注**;净超额(并报):adj_z=−0.662。
  朴素 z 显著而 KP 校正(因子 0.014075)后不显著 = 与事件版同构的聚集假阳性形态(统计事实陈述)。
  **偏离留痕**:首跑(2026-07-11)实现将检验挂净超额,与四件套框架"检验挂毛超额、净额并报"不符;
  方向保守(净扣成本使超额更负);**人批补正(2026-07-11)**,现主检验=毛超额、净行降为并报
  (result 留 `test_object_note` 字段,报告显式打印)。
- **四件套③ 右偏稳健项(毛/净并列)**:毛超额 skew=+4.680,t_plain=−7.844 → **t_sa=−7.143**;
  净超额 skew=+4.669,t_plain=−12.749 → t_sa=−10.948(并报;Hall 变换右偏修正方向一致)。
- **开卡对照菜单(人指 2026-07-11;量纲:①②③=事件级简单收益均值〔小数,×100=%〕,④=净收益>0
  事件占比)**:
  | # | 项 | 值 |
  |---|---|---|
  | ① | 毛超额均值 | **−0.005610**(−0.561%) |
  | ② | 原始净额均值 | **−0.008610**(−0.861%) |
  | ③ | 净超额均值 | **−0.009088**(−0.909%) |
  | ④ | 胜率(净) | **0.2503**(25.0%) |
- **离场结构**:break_ma20 17910 / stop_loss 18 / right_censored 1;G2 同日双触发 12(双 flag
  记账,主因归强平);持有期 bars 中位 6(max 97)/日历交易日 中位 7(max 201)。
- **G4 交易日口径注记(人确认入档 2026-07-11)**:顺延天数按**日历交易日轴**计(`trade_day_idx`,
  engine 从 calendar 传入);停牌=缺行,present-bar 差会**低估**停牌顺延天数(G8 口径证例固化+
  真实数据 4 例实证,见下)。
- **G4 顺延**:n=920(中位 1 交易日,max 64);**极端(>20 交易日)4 例单列**(附录G 上限条款,不静默):
  000658.SZ:20011126(28日/24bar)、002680.SZ:20180711(33日/32bar)、300027.SZ:20150722(**57日/1bar**)、
  600565.SH:20150821(**64日/1bar**)——后两例=2015 停牌潮长停牌,present-bar 差仅 1、日历交易日差
  57/64,**实证 G4"交易日"须按日历轴计**(`trade_day_idx` 实现,G8 口径证例固化)。
- **G5 右删失(open_position)**:n=1(占比 0.006%),末端 mark-to-market 未实现净收益 +0.03391,
  不剔除(拒幸存偏差)。

## 5. DSR 常设报告项实物(施工令①;不进 verdict)

n=17929,N_trials=2(族内 trial 计数),v_mode=**proxy**(人裁+追认 2026-07-10):
SR̂=−0.07494(事件级净收益),skew=+5.120,kurt=59.776;V(proxy)=8.179e-05,SR*=+0.004700,
**PSR(vs 0)=5.8e-17,DSR=6.5e-19**(SR̂ 为负 → 概率量≈0,量纲自洽)。
**V 口径登记**:proxy = 单 SR 抽样方差 Var[SR_hat]=(1−γ̂₃SR+(γ̂₄−1)/4·SR²)/(n−1)(BLdP 退化路径,
mlfinlab 同做法);理由 = 单条冻结规则无可排序 trial-SR 集合,无试验间方差可估。备选 trial_var/given
参数化保留在 `compute/dsr.py`(留终裁位),不作 #2b 默认。

## 6. PBO 不适用之结构理由(施工令①要求)

PBO(Probability of Backtest Overfitting,BLdP CSCV 框架)需要**可排序的试验集合**(多组参数/策略变体
的组合式回测切分排名)。#2b 策略版 = **单条人批冻结规则**(pap 冻结后禁 UPDATE,改参数=新假设行):
无参数网格、无模型选择、无试验集合可排序 → CSCV 逻辑上无对象,PBO **结构性不适用**(非"未做")。
本体系对过拟合敌人的定价机制 = **族计数 α 递减**(family_trial 自增 → α=0.05/n,#2b 取 0.025):
与 PBO 同一敌人(多重尝试)的**序贯定价**,在登记时点即生效,不依赖事后组合切分。

## 7. CPCV 边界登记

当前 #2b 全流程**无训练/模型选择步骤**(事件定义、参数、离场规则均人批冻结,引擎只执行)→ CPCV
(Combinatorial Purged Cross-Validation)不适用。**边界**:未来任一假设引入训练/拟合/模型选择步骤
之日,overfitting 检验(CPCV/PBO 类)转**必需**,此登记为触发线(架构窗口 R6 调研档对接)。

## 8. 已知口径特征登记(附录G;显式不藏)

1. **G1**:−20% 强平收盘确认 → 盘中硬止损频率被低估,对策略版收益方向**保守**(附录G1 登记)。
2. **G3**:P1 收盘确认+P5 触发日收盘成交 = 同刻口径含轻微前视/乐观;与进场 τ=0 后复权 open
   不对称——正当性 = 各为其信息可得时点的**最早可执行价**(附录G3 原文,写入附则防审查)。
3. **基准端点粒度**:池基准为 close-to-close 日收益,τ=0 日按全日收益计(进场实为当日 open)
   ——ADJ-BMP 预置框架内读法,与事件版 CAR 自 τ=0 当日收益起算同法(登记,非新口径)。
4. **净 vs 基准不对称**:BHAR = 净收益(扣成本)− 池基准 BH(无成本概念)——成本为策略真实成本、
   基准为机会成本对照,方向上对策略版**保守**(登记)。

## 9. 合成回归(约束③)+ G8 固化回归

- **约束③ #4 合成逐字节零回归**:`run_ashare_study` result.json sha256 = `3116ba9b…` 与基线
  逐字节同,**两次实测**(模块③落地后 / report.render_strategy 增段后)。本轮 runner / 共享
  render() / compute 既有文件零改动(新增文件 + report.py 仅追加独立函数)。
- **G8 固化回归三例**(holding_path 自检永久用例):①P1/P2 同日双触发(双 flag、主因强平、数值同式)
  ②G4 顺延跌停连板 22 bar(可卖首日**收盘**出+极端标注)+ 停牌 25 交易日 present 仅隔 1 bar
  (trade_day_idx 口径证例)③G5 末端 mark-to-market。`python -m taosha.compute.holding_path` 绿。

## 10. 确定性验证 ✅

- 首跑:PID 70063(代码 `0223fe0`),产物 `/tmp/s3step3/strategy_result.json`(14,270 B)。
- 干净重跑:PID 70726(代码 `15df9ae`,driver 增 --report 后),产物 `rerun_strategy_result.json`。
- **diff = 逐字节一致;sha256 两跑全等 `918fda40aee71a935c117a704ef8ca166773a8a900c595dec35b1dba44f45ede`**
  (跨 commit 重跑同 sha:--report 增量不触统计路径的旁证)。产物+报告本地备份 `scratchpad/s3step3_backup/`。
- **人批补正跑(代码 `7d9f870`,产物 `gross_strategy_{result.json,report.txt}`)受控 diff vs 基线
  `918fda40`**:新增键=`bhar_gross`/`adj_bmp_bhar_gross`/`skew_adjusted_t_gross`/`anchor_menu`/
  `test_object_note`,移除 0;共有键仅两处受控变更(`adj_bmp_bhar` 子键 sig_state/sig_note 迁至毛行
  +framework 文案标"并报"、`skew_adjusted_t` framework 文案同);**全部数值键(净/毛/基准/净超额分布、
  ρ̄、净 adj_z、DSR、诊断)与基线逐字节同**(断言核对过)——补正=纯受控新增+归位,不动首跑统计事实。

## 11. 携带项

- `report.py:36` 标题"切片2合成验收"硬编码残留(旧 carry-item,不在本轮动)。
- 策略版 result 落台账 exp_id=3 的 persist 终态:**事件版+策略版两份结果一并写入**,待人验收
  开卡后走 persist 状态机(本 driver 不抢跑,与 #4 先例一致)。

## 12. 下一动作

交人验收(事件版 NOT_SIG + 策略版体检对照两封数;**不解读** = 开工令⑥)。人验收+开卡后:
result_json(事件版+策略版)walk persist 状态机写台账终态 → #2b 闭卷。
