# 硬化⑥ 环境钉死 + 端到端集成回归 · 验收档(2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ⑥ + 人后半开令(2026-07-12,④过窗后):集成回归入常设自检=manifest 生成→路由读取→清洗(survivors 主干)→检验→报告一条龙,小样本即可,要点=全链在焊死环境下走通且可重复,入 python -m 可独立运行的自检家族。

## 1. 前半(即刻半,2026-07-12 午后,commit `cf6f198`,存档引用)

Python 钉版 **3.14**(两台实况 3.14.4;施工单括注 3.11/3.12 按人令"以两台实况为准"条款修正)+ 生产 venv 依赖锁 `ops/runtime/requirements-qbase-ingest.lock` + `ops/verify_runtime.py` 常设自检(生产 strict **21/21 ALL PASS**;开发机=解释器钉版+通报模式)。新 PAP 模板硬门随 v1.6 入档(下一条含策略版假设起生效)。

## 2. 后半:端到端集成回归常设自检(`taosha/harness/verify_integration.py`)

**一条龙覆盖**:S1 manifest 生成(**幂等**:批次向量与现值同→复用同行,不同→真实生成 append-only 新行)→ S2 ViewReader fail-closed 双探针(缺 snapshot_id 拒/manifest 不存在拒)→ S3 路由读取小样本(事件票排序首 6 只/事件 225/日历轴读面实测 max<holdout)→ S4 清洗(**survivors 单一主干**经 runner)→检验 → S5 报告渲染 → S6 **可重复=同 manifest 双跑 result sha 逐字节同+报告文本同** → S7 零台账写入(experiment 行数前后断言全等)。自检域先例=verify_study_snapshot/verify_runtime:result 只在内存断言即弃、不产判决不落槽;pap 用桩(转录 #4 检验窗"T+1起,后20/60日",与台账状态解耦)。

**aliyun 生产环境实测(2026-07-12 晚)= 7/7 PASS**:S1 snapshot_id=2 digest `f660d76b…`(二次运行=复用,幂等实证);S2 双拒;S3 6 票/225 事件;S4 n_valid=107 verdict=NOT_SIG(仅走通性,不作研究结论);S5 报告 7,285 字;S6 双跑 sha `3bef1f81…` 逐字节同;S7 台账 25 行前后全等。

**"合成小样本"操作化登记(待人追认)**:焊死环境腿(manifest 路由+触发器)只能用真实库读面——合成数据不入库(红线),故此腿=**真实小样本**(首 6 事件票,秒级);**合成腿**=既有合成域全链(SyntheticReader→survivors→runner→report,`run_ashare_study` 基线 sha `3116ba9b` 双跑,item4 §3)。两腿合起来=清洗→检验→报告在合成与真实读面双覆盖、manifest→路由在焊死库覆盖。

**实物登记:manifest #2 由本自检幂等生成**(append-only 合法新行,note="硬化⑥端到端集成回归自检(幂等生成)";与 #1 的批次向量差=market_return 2〔硬化② 并发验收所落 batch,双算闸过〕;此后自检重跑在批次不变期恒复用 #2,不增行)。

修复链:`93fde66`(施工)→`1e8fdd8`(::jsonb cast)→`40dabc4`(snapshot_info property)。

## 3. 自检家族总清单(python -m 可独立运行,常设)

| 件 | 覆盖 | 现况 |
|---|---|---|
| taosha.experiment.verify_state_machine | ① 台账状态机 a反向30拒+b正向10通 | 44/44 |
| taosha.harness.verify_study_snapshot | ② fail-closed 探针+读面 | 16/16 全拒 |
| taosha.experiment.verify_addendum | ⑤ append-only+原 result 不动 | 8/8 |
| ops/verify_runtime.py | ⑥ 解释器钉版+依赖锁 | strict 21/21 |
| **taosha.harness.verify_integration** | **⑥ 端到端一条龙(本件)** | **7/7** |
| taosha.engine.survivors / cleaning / drawdown_strategy `__main__` | ④③ 随件回归 | 绿 |
| taosha.harness.run_ashare_study(合成 fixture) | 合成域全链零回归 | sha `3116ba9b` |

## 4. 结论

⑥ 两半齐:环境钉死(前半)+ 端到端集成回归入自检家族(后半,焊死环境走通+可重复实证)。**⑥ 施工完毕;硬化验收包总表见 `docs/hardening-acceptance-package-2026-07-12.md`(总表交付=硬化窗口施工全毕,待外审+人终签)。**
