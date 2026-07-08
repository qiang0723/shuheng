# 切片3 · 步7 验收:#4 第一份真实体检报告(2026-07-08)

**结论:通过。** 台账 `exp_id=5`(`forecast_drift`/业绩预告漂移,status=frozen)在焊死的真实数据链
(explore_reader 三视图 · role `taosha_engine` · 全市场等权基准表)上端到端跑通,产出 #4 第一份真实
事件研究体检报告。**报告完成即交,不做解读**(开工令⑥:解读与密封开封对照是人的仪式,不是工地的活)。
合成回归两翼(约束③)已并列达成。跨机器重启 + 重跑三方**逐字节确定性一致**。

---

## 0. 报告本体(统计事实,无建议口吻 · 开工令⑤⑥)

| 项 | 值 |
|---|---|
| 假设 | `exp_id=5` forecast_drift / 业绩预告漂移(status=frozen,verdict_power=full)|
| 检验窗(从 pap 读) | 后 20/60 日 → 主窗 [0,+19] / 稳健窗 [0,+59](τ=0:=T+1,S2-DEC3)|
| 基准 | market(全市场等权,口径②)· **单跑不双跑**(#4 为全市场族)|
| 事件日锚 | first_ann_date(无 fallback)|
| 样本闸 | 30 → OK |
| 快照 | forecast_snap Q2 batch#1 |
| 冻结审计 | frozen_config=`b88a43ef…` / frozen_ashare=`c795b21e…`(对上)|
| **样本** | 事件总 **105584** · 有效 N_eff **67760** · 剔除 37824 · **剔除率 0.3582**(>5% 告警)|
| 估计窗覆盖 | 分母 160 · 门槛 112(70%) · 有效日 min/mean/max = 112/156.4/160 |
| 主窗 [0,+19] | CAAR=−0.00109 · BMP_CAR=6.089 · **ADJ-BMP_CAR=0.087**[不显著] |
| 稳健窗 [0,+59] | CAAR=−0.00377 · BMP_CAR=10.306 · ADJ-BMP_CAR=0.161 |
| Corrado 秩 | 主窗 t=−0.875 · 稳健窗 t=2.441 |
| 日历时间组合 | 主窗 t=−0.711(日历日 5759)· 稳健窗 t=−1.511(6003)|
| ρ̄(行业内,口径④) | 0.0732(4045567 对)|
| **verdict** | **`NOT_SIG`** |

**verdict 判据(报告原文)**:主窗双侧 α=0.05 临界 ±1.960——ADJ-BMP_CAR=0.087[不显著] / 朴素 t=−4.096 /
Corrado 秩 t=−0.875[dir−1] / 日历 t=−0.711[dir−1]。**朴素 t 显著而 ADJ-BMP 不显著 → 聚集假阳性,
以 ADJ-BMP 为准**(spec §6 三法一致规则)。

**剔除率按年份分解(item 7)**:1998–2024 全覆盖,主因 history(早年 6000 截断已重灌但估计窗覆盖不足)、
suspension(缺行=停牌)、coverage(估计窗<112)、st、postpone(一字板顺延)、**no_price(空价行剔除,2021–24
各 5/1/6/10 入账)**。2015/2016/2017 剔除率高(0.48/0.51/0.48),主因 suspension+coverage(2015 股灾停牌潮)。

**板块分层(item 8)**:main 有效 52871 / chinext 14191 / star 698 / **unknown 22(有效 0)** / ST 38(有效 0,已剔除层)。
创业板 regime 边界 2020-08-24:前(±10%)10468 / 后(±20%)3723。
**行业覆盖(口径④):'unknown' 残余组 5254/67760 = 0.078 ⚠升级上报(>5%)**。

**R5 删失诊断三件套(报告项 · 不进 verdict)**:①各 τ 逐日 AR(AAR+BMP/ADJ-BMP);②各 τ 一字板/涨停/跌停/停牌
计数占比;③板块四层分拆。全齐。

**偏差方向声明 + 口吻声明**:两固定段在报告内。剔除类处置(覆盖不足/停牌/ST/一字板顺延/无价行)均为保守处置,
方向倾向缩小可测异常收益(保守下界语义);报告只陈述统计事实,不含任何交易建议(铁律⑤)。

产物:`/tmp/s3step7/rerun_s4_report.txt`(9563B)+`rerun_s4_result.json`(40782B,`sha256 b48d2941…`)。

---

## 1. 跨机器确定性(三方逐字节一致)

真实域全事件票、真实市场基准,结果对随机性/机器/重启零依赖:

| 产物 | 来源 | sha256(result.json)|
|---|---|---|
| 本地基线备份 | 上一会话(2c/7.2G 机重启前)| `b48d2941…` |
| 阿里云首成功跑 | PID2313,14G 机,14:25 | `b48d2941…` |
| 阿里云干净 rerun | PID4058,14G 机,15:43 | `b48d2941…` |

`diff -q` report/json 逐字节一致。**跨机器重配(2c/7.2G→4c/15G)+ 重启 + 重跑,结果 sha 恒等。**

## 2. OOM 处置闭环(工程,非口径)

- **首跑 OOM(2c/7.2G)**:ViewReader 全事件票 5356 票 / 15,041,210 prices 行;根因=`by_sec` 1500万
  PriceRow 全物化(~5G)+ `sec_returns` 5356×8187 稠密展开(~1.4G)叠加 + swappiness=0。dmesg oom-killer 实证。
- **修复 commit `18835d5`(施工代码)**:runner 真实 market 域 `sec_returns` 惰性化——事件循环按票现算
  `returns_by_date`(单键缓存,events 按 ts_code 有序,内存 O(1票));`pool` 分支及合成域(SyntheticReader
  走 else)仍全物化 → **代码路径不变、数学等价(同函数同输入)、约束③合成逐字节零回归**。
- **人拍板 2026-07-08 = 调大机器实例 ≥16G**(否决"为迁就 2c/7.2G 做完整 by_sec 按票流式重构引擎核心"——
  升级零代码风险、正规军、未来真实假设都受益)。变配后 4c/15G(free 14G),OOM 彻底解决(swap 2G 全程未用,
  峰值 RSS 无致命叠加),惰性版正常退出。

## 3. 合成回归两翼(约束③ · 与真实 #4 并列交付硬项)

- **翼 A — 合成域确定性**:`run_ashare_study`(SyntheticReader 读 csv,pap 桩喂原短窗"后3/6日")双跑
  **逐字节一致 sha `7d5fddd…`**;关键量对齐切片2终签(verdict SIG / n_eff 35 / reject 0.2708 /
  主窗[0,+2] CAAR 0.0220 / ADJ-BMP 3.6577);新增 `industry_coverage`(unknown_n=0/escalate=False)=
  前置②受控 diff(仅新增该键)。
- **翼 B — logbench 对台 estudy2 0.10.0**:make_fixture→estudy2_ref.R→run_double,**ALL_PASS**——
  max_bmp_diff **7.1e-15**(<TOL 1e-5)/ rate 5e-17 / coef 4.2e-15 / ar 6e-17。compute 层
  (returns/market_model/abnormal_tests,步7 未改)零回归。运行在 aliyun /tmp/s2bench(非 git)。

## 4. 开工令逐项映射(六条 + 三约束)

| 令 | 要求 | 落地 |
|---|---|---|
| ① 入口项先清 | cleaning 按缺行+calendar 判停牌;coverage>1.0 归因 | ✓ 步5 cleaning 约束②;coverage>1.0=241 北交所(已排)+1 沪市 600018,"缺行=停牌"地基零威胁 |
| ② 事件源 | exp_id=5 pap 经 explore_reader_events 读;拒 status≠frozen | ✓ driver 读台账 exp_id5 校验 frozen;检验窗从 pap 读(20/60)|
| ③ 数据路径 | 全程 explore_reader 三视图,引擎 role 焊死 | ✓ ViewReader(taosha_engine),真实数据第一次入引擎;身份三组断言绿(步4)|
| ④ 全链口径 | 冻结配置,无运行时参数;三法互证 | ✓ frozen_config/frozen_ashare 审计对上;三法(ADJ-BMP/Corrado/日历)|
| ⑤ 产出 | 体检报告,无建议口吻:三法/N_eff/剔除率按年份/逐日 AR/板块/偏差声明 | ✓ 见 §0 报告本体 |
| ⑥ 报告完成即交,不解读 | — | ✓ 本档只陈述统计事实,不做效应解读、不对照密封卡 |
| 约束① | DSN 秘钥纪律 + 权限只收不扩 | ✓ .env 600 不进 git;taosha_engine 未加任何 GRANT |
| 约束② | 一字板=有 bar+触板 / 停牌=缺行,物理分离;杂交上报 | ✓ cleaning 分离两判据;无杂交样本上报 |
| 约束③ | 合成回归升格硬项(logbench 不回归)| ✓ 两翼见 §3 |

**体系原则(北交所全排除)**:三视图 WHERE `!~'\.BJ$'`(886c708);报告板块四层无北交所层;
事件宇宙=沪深(注记在报告口径)。

## 5. 携带项(登记,本轮不改)

- **report.py:36 标题硬编码"切片2 合成验收"**:共享渲染函数残留(合成域与真实域同用 `render()`)。
  真实 #4 报告标题因此显示"切片2 合成验收"。**本轮不改**:改共享渲染文本有打破合成域逐字节回归
  (sha `7d5fddd`)的风险,需专门评估。报告内容本身(快照批次/基准/审计/verdict)均为真实 #4 值,不误导。
- **off-calendar 携带项**(步3 已登记):explore_reader_prices 8189 distinct 交易日 > calendar 8187,
  市场基准已 ∩calendar 剔除;个股侧 ViewReader 亦 ∩calendar。qbase 数据质量携带项在案。

---

## 6. 复现指令

```
ssh aliyun-new
cd /opt/quant && git rev-parse HEAD   # 253d9283
set -a; . /opt/quant/.env; set +a; export PYTHONPATH=/opt/quant
/opt/venvs/qbase-ingest/bin/python -u -m taosha.harness.run_forecast_study \
  --exp-id 5 --json /tmp/s3step7/s4_result.json --report /tmp/s3step7/s4_report.txt
```

产物 sha256(result.json)= `b48d29411ccab7f7d7a07c14bd9932b65cea3891636a59c77b5b87510a9f7698`。

**HEAD `253d9283` · 两台一致 · git 干净。步7 = 切片3(#4 端到端·修正案三验收)最后一项,完成。**
