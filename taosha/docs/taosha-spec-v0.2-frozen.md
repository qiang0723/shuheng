# 淘沙极简版 · 施工 spec v0.2(冻结版)

> 状态:**PAP 已冻结**(2026-07-05,人批总批复单⑨⑩⑪)。本版=v0.1+修订单R1+修订单R3 合稿,替换全部旧版。
> 服从:总纲 v1.2 + 数据资产宪法。部署:新机 quant/taosha/。对老平台库零访问,只吃 qbase 归一视图。

---

## 1. 定位与绝不做

淘沙极简版 = **事件研究引擎 + 假设台账**,没了。修正案三验收工具、第二引擎起步、Experiment 对象实体化。

**绝不做**:策略级组合回测/横截面因子IC分层/参数优化网格/自动调参/写回上游接口/LLM生成规则(极简版阶段)/LLM判断进历史回测/GARCH建模/bootstrap p值/BHAR长期检验/Web UI/消息队列——触发=有人批的新假设需要它们。

## 2. 五铁律结构化落法

| 铁律 | 落法 |
|---|---|
| ①分级判决效力 | source_type 强制非空(human/platform/literature/llm);llm→verdict_power=prescreen 触发器强制,报告水印 |
| ②统计纪律 | family_trial_count 触发器自增,门槛 α=0.05/n;holdout(2024-07-01)焊在 qbase explore_reader 视图 WHERE 里,探索代码结构上拿不到;事件数<30→INSUFFICIENT(合法终态);成本硬扣见 §6 |
| ③PAP 前置 | status 必须 frozen(pap_json+frozen_at)才许 running,引擎拒绝执行未冻结假设 |
| ④只证伪不优化 | pap_json 冻结后触发器禁 UPDATE;改参=INSERT 新行,family 继承计数+1 |
| ⑤用其手不引其忆 | LLM 仅四角色:PAP草稿翻译/变体登记/报告解读/台账管理;不定义事件、不选参数终值;报告无判断口吻 |

## 3. 目录结构(born-in-place)

```
quant/taosha/
├── CLAUDE.md
├── compute/    # 将来上交L2:纯函数零IO — car.py(ADJ-BMP在此)/costs.py/deflate.py/calendar_pf.py/rank_test.py
├── experiment/ # 永久自留:ledger.py/pap.py/gates.py
├── engine/     # 执行器(含A股清洗预处理)
├── reader/     # 唯一数据入口:qbase explore_reader 只读
└── sql/        # 台账schema(append-only触发器)
```
边界铁则:不 import 兄弟目录;唯一写入对象=台账;台账 append-only+双时戳+第一天入备份链。

## 4. 假设台账 schema(=六对象 Experiment 契约)

```sql
CREATE TABLE experiment (
  exp_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  family text NOT NULL, family_trial int NOT NULL,
  title text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN ('human','platform','literature','llm')),
  verdict_power text NOT NULL,           -- full/prescreen(llm强制prescreen)
  contamination_note text,
  pap_json jsonb NOT NULL,               -- 事件定义/窗口/池/基准/成本/holdout/清洗规则/数据快照批次要求
  status text NOT NULL DEFAULT 'registered',  -- registered→frozen→running→done
  registered_at timestamptz NOT NULL DEFAULT now(),
  frozen_at timestamptz,
  result_json jsonb,   -- CAR/各检验统计量/样本数/校正门槛/快照批次号/verdict(SIG|NOT_SIG|INSUFFICIENT|AMBIGUOUS)
  done_at timestamptz
);
-- BEFORE UPDATE 触发器:仅放行 status 单向推进与 result 一次性写入;pap_json 冻结后一律 RAISE;禁 DELETE/TRUNCATE。
```

## 5. 引擎与统计方法(R1 定稿)

**流程**:exp_id(须frozen)→ 从 pap_json 取事件定义 → explore_reader 拉数 → A股清洗 → compute → gates → deflate → result_json+体检报告。

**主检验:ADJ-BMP(Kolari–Pynnönen 2010)** = BMP × √[(1−ρ̄)/(1+(n−1)ρ̄)];对业绩预告类极端聚集事件,**ρ̄ 按行业内估计**。
**稳健性两道**:Corrado(1989) 秩检验;日历时间组合法。三法方向一致才确认效应。
**分歧裁决(写死)**:朴素 t 显著而 ADJ-BMP 不显著→聚集假阳性,以 ADJ-BMP 为准;日历时间法与截面法相反→查事件密集期(Loughran–Ritter),补事件加权;三法不一致→verdict=AMBIGUOUS,报告分歧,不许挑有利的。
**预期收益模型**:市场模型 + 等权超额(池内/全市场按假设);CH-3 留阶段2。报告注明联合检验属性。

**A股清洗(engine 预处理,动作落 result_json 可审计)**:估计期=事件日前250至前91交易日;不足者剔;ST 剔除;一字板事件日标注+事件窗顺延;停牌缺失按 modified_rank 口径;**可交易时点=事件日 T+1 开盘,CAR 窗口起点=T+1**(盘后披露前视规避)。

**报告**:只陈述统计事实,无建议口吻;头部水印(llm来源/AMBIGUOUS/警示);**自动警示规则**:方向与文献基准相反或幅度超基准一倍以上→强制打"首先怀疑管道错误"+核对清单(SUE构造/事件日对齐/一字板/ST噪声/增减持混淆/实施日错位/截面相关未校正)。

## 6. 创始五条 · PAP 冻结记录(人批 2026-07-05)

**通用(冻结)**:成本=佣金万2.5+卖出印花税千1+滑点单边千1,一字板日不可成交;基准=池内假设用雷达股池等权、全市场假设用全市场等权;holdout_start=2024-07-01(动用须人批,每假设一次);样本量闸=30。
**污染标注(全局)**:3/4/5 惯例参数由 LLM 按文献惯例拟定、人批、未接触样本数据;#2 全参数来自人的事前直觉。

| # | family | 事件定义(冻结) | 窗口 | source/效力 | 数据源 |
|---|---|---|---|---|---|
| 1 | radar_heat | heat_signal 升温标记(沿雷达A7口径) | A7口径 | platform/full | v_signal_radar |
| 2 | drawdown_rebuy | 雷达股池(PIT)内收盘自60日高点回撤≥10%后,站上10日线且连续3日不破=进场;破20日线=失效。策略版离场:成本−20%强平或收盘破20日线,先到先出 | 事件版20/60日;策略版按离场 | human/full | qbase行情+雷达股池 |
| 3 | holder_sell | **减持计划首次预披露公告**(巨潮自建采集,announcementTime 为时间戳金标准),减持比例≥总股本1%;2024新规前历史样本用当时口径首次公告日。stk_holdertrade 仅作实施结果辅助表(按 ts_code+ann_date 聚合,无公告ID局限入 pap_json) | 后5/20/60日 | literature+platform/full | 巨潮预披露采集(Q2)+stk_holdertrade |
| 4 | forecast_drift | 业绩预告,**valid_time=first_ann_date**(非ann_date);修正公告(ann_date≠first_ann_date)不进本假设;分预喜/预亏/扭亏三层 | T+1起,后20/60日 | literature/full | qbase forecast 快照(Q2) |
| 5 | rv_resonance | 观象节点日度 resonance 进全池当日分布前10% | 卡面horizon_days | platform(确定性函数)/full | v_judgment_rv |

**文献基准(密封预判锚,非真值)**:#4 极端组约+6%、持续3–4月、正漂移;#3 负漂移非反转,实控人>大小非>高管,高管约50日修复。**人须在切片3跑真实数据前密封写下对#4的方向与幅度预判。** 预期声明:#5 大概率 INSUFFICIENT(故意,验证样本量闸)。

## 7. 任务切片与验收

- **切片1·台账**:sql+ledger+pap+触发器。验收=五条登记冻结、UPDATE被拒实测证据。
- **切片2·引擎**:reader+compute(ADJ-BMP/秩/日历组合)+gates+deflate+清洗+报告。验收=合成数据跑通,且**同数据在 R estudy2(含KP实现)并行跑,Python 结果对数一致(±数值误差)**;成本与门槛校正人工核对。
- **切片3·假设#4端到端=修正案三验收**:真实数据(qbase Q2 快照批次)体检报告一份,人签收。前置:人的密封预判已封存。
- 里程碑:切片3过=立柱验收;前50条假设=淘沙首金复盘(复盘前人密封预判)。

## 8. 验收即停

切片3后建设冻结,转假设消耗模式。任何"顺便增强引擎"=红灯律适用对象。

## 9. 数据依赖(qbase 侧,详见施工清单 v0.2)

explore_reader 视图族(holdout 焊死)/forecast+stk_holdertrade append-only 快照(自打 observed_time,禁 upsert)/巨潮预披露公告采集(雷达 cninfo 代码复制落位)/三层核对协议为 Q2 验收/result 须记快照批次号(可复现)。
