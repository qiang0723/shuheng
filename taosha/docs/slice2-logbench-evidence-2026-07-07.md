# 切片2 · 对数台架验收证据(2026-07-07)

> task 4 对台:compute 与 estudy2 0.10.0 同一合成 fixture 双跑,逐点比对 + ADJ-BMP 尺寸检验。
> 运行环境=aliyun-new(R 4.5.2 + estudy2 0.10.0)。凭实物:代码 `taosha/harness/`、fixture 确定性种子。
> 依据:核对单(item 2 改读后)+ 附录 E(S2-DOC1 裁定)+ 四口径拍板(冻结配置)。

## 0. fixture(确定性种子 20260707)

`make_fixture.py`:340 交易日 × 6 证券 + 市场指数。SIM 真结构 `r=α+β·rm+行业共同因子+ε`;
价格 `P_t=P_{t-1}·exp(r_t)`(对数收益可精确回收)。**S3 注停牌缺口**(索引130,连续3日 NA,落估计窗内)。
6 证券**共享同一事件日**(2023-02-27,聚集)、分**两行业**(银行 S1-3 / 地产 S4-6),事件日 τ=0 注入 **+3% 异常收益**。
窗口:估计窗 2022-03-14 至 2022-10-21(前250至前91=160日,spec §5);事件窗 τ=0..+5(2023-02-27 至 03-06)。

## 1. BMP 段对台(锚 estudy2 boehmer)——机器精度逐点对齐 ✅

`run_double.py` 我方 `returns → sim_fit → bmp_by_tau` vs estudy2 `get_rates → apply_market_model(sim) → boehmer`,
按到达日对齐(`rates[i]↔dates[i+1]`,跨缺口收益落恢复日)。**max|diff|**:

| 量 | max\|我方 − estudy2\| | 判定(tol) |
|---|---|---|
| 对数收益序列(含 S3 跨缺口) | **2.22e-16** | ✅ <1e-8 |
| SIM 系数 α/β | **4.22e-15** | ✅ <1e-7 |
| 事件窗异常收益 AR | **4.51e-17** | ✅ <1e-7 |
| BMP 统计量(boehmer) | **3.73e-14** | ✅ <1e-5 |

BMP@事件窗(我方≈estudy2 到 3.7e-14):τ=0 **12.176 \*\*\***(捕捉注入 +3% AR);τ=+1..+5 ≈ [0.99, 0.44, 0.61, −0.12, 0.92] 均不显著。

- **item 3(跨缺口对齐)**:S3 停牌3日,跨缺口对数收益落恢复日,rates 与 estudy2 差 2e-16;`delta=157=160−3`(覆盖计数正确扣缺口日)。
- **item 5(禁零填充)**:缺口处 rates/AR 恒 None,无零填充路径。
- **item 6(覆盖门槛)**:S3 delta=157 ≥112(=70%×160)合格;`frozen_config.coverage_ok` 焊死。

### 1a. 分歧逐笔归因(item 4)——已消解一处 estudy2 口径细节

首轮双跑 S3 的 BMP 差 ~3e-4(其余证券已 <1e-6)。**归因**:estudy2 `boehmer`(parametric_tests.R:897-908)
的预测误差修正 `√(1+1/L+(rm−x̄)²/Sxx)` 中,`x̄`/`Sxx` 取 **regressor 在估计窗内的全部非缺观测(na.rm)**,
而非 OLS 的 complete.cases 样本(L 仍=complete.cases delta=157)。无缺口证券二者相同,故仅 S3 受影响。
**处置**:`sim_fit` 的 x̄/Sxx 改从 market 估计窗观测计(commit 181d3c0),精确复现 estudy2 → BMP 差降至 3.7e-14。
(非我方错、非 estudy2 未决 issue,属其内部 L/Sxx 分母口径,已对齐并留痕。)

## 2. ADJ-BMP(KP2010)段——手算 + 蒙特卡洛尺寸检验 ✅

estudy2 0.10.0 无 KP 实现(附录 E1),ADJ-BMP 为我方扩展,验证两道:

### 2a. KP 因子手算复核
fixture:ρ̄=0.20697(同行业对估计窗 AR 平均 Pearson 相关,口径④ tushare industry),n=6 →
`√[(1−ρ̄)/(1+(n−1)ρ̄)]` 代码值=手算值=**0.62428**(差 <1e-12)。ADJ-BMP@τ=0=12.176×0.62428=**7.601**。

### 2b. 零假设蒙特卡洛尺寸检验(附录 E3;`mc_size_test.py`,种子 20260707)
无效应(真实 AR=0)+ 截面相关(行业共同因子,市场模型不回归 f → 残差保留)聚集样本,N=20、估计窗160、**2000 次**,
按 t_{0.975,19}=2.093024 双侧 α=0.05 判拒:

| 指标 | 值 | E3 要求 |
|---|---|---|
| ρ̄ 均值 | 0.2476 | (截面相关强度) |
| **朴素 BMP 拒绝率** | **0.461** | > α(假阳性复现)✅ |
| **ADJ-BMP 拒绝率** | **0.0475** | ≈ α ✅ |

**结论**:截面相关下朴素 BMP 假阳性率 46%(远超 5%),KP2010 校正后恢复到名义 4.75%≈α。ADJ-BMP 有效、"骗不了人"。

## 3. 核对单映射

| item | 证据 |
|---|---|
| 2 对数范围(改读·附录E) | BMP 段锚 estudy2(§1,3.7e-14);ADJ-BMP 段手算(§2a)+ 尺寸检验(§2b);聚集场景=fixture 6证券共享事件日 + MC 同行业簇 |
| 3 对数口径对齐 | §1 收益序列 2e-16;multi_day 跨缺口落恢复日 |
| 5 禁零填充 | §1 缺口恒 None |
| 6 覆盖门槛 112/160 | §1 S3 delta=157≥112;frozen_config 焊死 |
| 10 口径冻结只读 | frozen_config MappingProxyType,audit_digest=b88a43ef… |

## 4. 复现

```
# aliyun-new /opt/quant:
OUT=/tmp/s2bench
python3 -m taosha.harness.make_fixture --prices $OUT/prices.csv --meta $OUT/meta.json
Rscript taosha/harness/estudy2_ref.R $OUT/prices.csv $OUT/meta.json $OUT
python3 -m taosha.harness.run_double $OUT/prices.csv $OUT/meta.json $OUT $OUT/double_result.json   # ALL_PASS
python3 -m taosha.harness.mc_size_test --n-sim 2000 --out $OUT/mc_result.json                      # PASS
```
compute 四模块 `python -m taosha.compute.{frozen_config,returns,market_model,abnormal_tests}` 自检全绿。
