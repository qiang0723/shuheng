# 硬化④ 共享存活样本主干 · 验收档(2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ④。修法原文:提取"事件存活样本构造"单一主干(clean_event→sim_fit→coverage→robust 边界),事件版 runner 与策略版共同调用,平行链消除——不是拆短函数,是消灭第二条实现。验收原文:重构后与 ③ 的 post-ST 新基线逐字节一致(#4 合成 / #2b 事件版 / #2b 策略版三份);验收标准=平行链消失(代码层单一调用点),非行数达标。#3 检验接入的前置。人开令(2026-07-12,③⑤过窗后)重申同三条。

## 1. 修法实物(commit `fae0dcd`)

- **新件 `taosha/engine/survivors.py`(73 行)= `iter_survivors` 流式生成器**:clean_event → SIM 拟合(估计窗 mask)→ coverage 门槛(70%×160)→ robust 检验窗右端越界(history),同序同判据的**唯一实现**。逐事件 yield `(ce, survivor|None)`、不物化 fit 全集——#4 六万存活若齐持 SimFit.abnormal 稠密列即内存灾难,流式=与提取前 runner 事件循环内存轮廓等价。
- **两侧原有差异以参数盖**(侦查结论=平行链仅差此两处):`sec_returns` 预物化(pool/合成域)| 惰性单键缓存(真实域,events 按 ts_code 有序、内存 O(1票));`reject_notes` 剔除文案(事件版 True=既有文案逐字落 ce.notes,策略版 False=既有行为不落)。
- **消费端各留各**:runner(582 行,净减 32)迭代生成器,存活侧保留 SecurityEvent 构造/删失诊断/可交易口径捕获/rank·cal 输入;drawdown_strategy(343 行,净减 30)收集 survivors 后走持有路径。**result 内字符串一字未动**(source_consistency 注记、notes 文案、各 note 键均原文)。
- 生产链依赖方向不变(compute←engine←driver,宪章第 1 条);survivors 只 import compute(frozen_config/market_model)+engine(benchmark/cleaning)。

## 2. 平行链消失证据(验收标准=代码层单一调用点)

`grep -rn "clean_event(\|sim_fit(" taosha/engine/ taosha/harness/` 全仓实测:
- **生产研究链上 `clean_event`/`sim_fit` 调用点唯一 = `survivors.py:33/:49`**;
- 其余命中均非生产链:`engine/cleaning.py` 13 处=自检 `__main__` 用例(R1–R10);`harness/mc_size_test.py`/`harness/run_double.py` 各 1 处=切片2 对台 estudy2/MC 尺寸检验台架(logbench 证据件,不产研究 result);
- runner.py/drawdown_strategy.py 中两函数 import 已移除,静态上无法再各自成链。

## 3. 随件自检 + 合成域零回归(提交前,本地 AWS + aliyun 双跑)

- **survivors 随件自检**(`python -m taosha.engine.survivors`,宪章第 7 条只增不删):R1 预物化 vs 惰性两分支逐值等价(fit.est_ar_sd/delta/x_bar/sxx + est_ar_by_date 全等);R2 reject_notes 只加文案不改判定(剔除序列全等);R3 coverage 门槛剔除(估计窗挖 60 日 delta<112);R4 robust 越界=history 同判据。绿。
- cleaning 自检(约束②+硬化③ R7–R10)、drawdown_strategy 冒烟(净收益/BHAR 手算一致/同源差集空)全绿。
- **约束③ 合成域零回归**:`run_ashare_study`(#4 合成 fixture,seed 20260707)重构后双跑 sha256 = **`3116ba9b74f7c53b…` 与既有基线逐字节同**(预物化分支+reject_notes=True 象限实证)。

## 4. 验收硬项:三份 post-ST 新基线逐字节比对(真实域,aliyun)

跑批 `/root/s3hard4_runner.sh`(2026-07-12 21:03:18–21:37:12 串行三跑全 rc=0;只读诊断=--diagnostic --snapshot-id 1〔manifest #1 digest 2a8a271f…〕,DIAGNOSTIC 水印+diagnostic 块在产物实测,事由已登记 STATE=通路预裁硬项;惰性分支×事件版/策略版两消费端全覆盖):

| 跑(重构后) | norm_sha256(剔 diagnostic,同③规则) | ③ post-ST 新基线(item3 §6) | match |
|---|---|---|---|
| c4_eventday(#4) | `eb6f01d43dcbec7f…` | `eb6f01d43dcbec7f…` | **true** |
| c2e_eventday(#2b 事件版) | `b7d0879eeadcbcd1…` | `b7d0879eeadcbcd1…` | **true** |
| c2s_eventday(#2b 策略版) | `7dbd9006b354c94b…` | `7dbd9006b354c94b…` | **true** |

**ALL_MATCH=True**(`/root/s3hard4/verify_vs_baseline.json`,全 64 位比对;raw 差异仅 diagnostic.reason 各跑事由文案,与③确定性硬项同规则)。三份逐字节达成:#4 合成(§3 `3116ba9b`)/#2b 事件版/#2b 策略版——注:施工单"三份"中 #4 合成基线由 §3 合成域 sha 覆盖,#4 真实域为本表加严项(合成+真实双证)。

**跑毕台账零写入复核**:experiment 仍 25 行、experiment_addendum 仍 4 行、exp3 `e3d2aef9…`/exp5 `c010ce9d…` result sha 与闭卷锚全等。

## 5. 产物与备份

`/root/s3hard4/`(三 result.json + 三 run.log + progress.log + verify_vs_baseline.json);备份 `/root/s3hard4_backup/`。commit 链:裁决留痕 `99242b1`(④开令)→ 施工 `fae0dcd` → 事由登记 `24634b2` → 本验收档。

## 6. 结论

④ 验收标准逐项达成:第二条实现已消灭(生产链单一调用点,§2,非行数标准)、重构后与 ③ post-ST 新基线三份逐字节一致(§3 合成 + §4 真实域 ALL_MATCH)、行为等价零功能增量(result 字符串一字未动)、#3 检验接入前置就位(下一假设复用 iter_survivors 走适配器,宪章第 5 条首检点)。**待架构窗口验收;过窗后 ⑥ 端到端集成回归收官(消费 ②④ 终态)+ 硬化验收包总表(含「#2b 闭卷可复现性硬证」单列,人点名 2026-07-12)。**
