# 六周期期末复盘底稿 v1 · 验证记录

验证时间：2026-08-12（Asia/Shanghai，UTC+8）。

## 结论

**DRAFT / NOT-FINAL，已达到外审交验质量。** 数据、算术、来源、notebook、artifact、HTML 结构、桌面/窄屏显示与治理闸门均通过。2026-08-25 仍须做一次新的连接级只读增量核对后才能签为最终期末复盘。

## 数据与算术

- 2026-08-12 08:32:43+08 独立只读读回确认 `transaction_read_only=on`；台账 26 行 = registered 6 / frozen 2 / done 16 / closed 2；
- `done=16` 剔除 exp7 `synthetic_smoke` 后，正式真实 `done=15`；exp18 / exp21 / exp22 / exp23 均仍为 `registered`；最新 `done_at` 仍为 2026-08-09 的 exp14；
- 校准 CSV 12 行、实验 ID 唯一；方向由 CAAR 符号重新推导后为 5 命中 / 7 未命中，零错标；每行 `main_n <= n_valid <= n_events`；
- 5/12 的 Wilson 95% 区间约为 19.3%–68.0%；
- 正式真实研究唯一 `SIG` 为 exp568，效力为 `llm/prescreen`；真实 `full` 研究 4 条，`SIG=0`；
- 硬门守恒：exp18=`12+10=22`；exp21=`1+21+1=23`；exp23=`15+13=28`；exp22=`51<=646` 且身份为 route progress，不作抽核通过率；
- exp22 失败链 v1–v8 恰 8 行、版本连续、outcome 全为 `FAIL`，每行权威来源路径在仓可解析。

## 计数差异闭合

旧 STATE 的“判决闭卷14条”是 exp14 persist 后未同步递增的滚动叙述，不是另一套总体定义。底稿将口径固定为：

1. 台账 `done` 16 条；
2. 正式真实 `done` 15 条；
3. 方向校准 12 条，5 命中 / 7 未命中；
4. exp3 / exp4 / exp5 是未进入当前方向校准序列的三条早期正式 `full` 研究。

## Notebook

- `cycle_end_review_analysis.ipynb` 共 16 个单元，其中 5 个代码单元；
- 代码单元执行序号严格为 1–5，错误输出为 0；
- 输出含 `Ledger and calibration checks: PASS`、`Evidence-gate checks: PASS`、`Formal-real SIG: 1/15`、`Full-power SIG: 0/4`；
- 使用临时 `/tmp` 隔离依赖与临时 kernelspec 完成执行，未在仓内增加虚拟环境或依赖文件。

## Artifact 与 HTML

- 统一 portable builder：validation=`passed`、package=`passed`、verification=`structural_only`；结构包含 17 blocks / 6 metrics / 1 chart / 2 tables；
- builder 环境未安装 Chromium headless-shell，故其自动浏览器验证仅到 `structural_only`；未把该状态冒充视觉通过；
- 另用应用内浏览器完成显示层复核：
  - 桌面 1440×900：`scrollWidth=clientWidth=1440`，6 张指标卡、3 张表、Recharts 主图在 DOM；
  - 窄屏 390×844：`scrollWidth=clientWidth=390`，6 张指标卡、3 张表，响应式静态摘要替代交互图且无横向溢出；
  - 两宽度均命中 Executive Summary、15 条正式真实 done、5/7、trial 2 临界值 2.241 与 DRAFT 标记；console warning/error 为 0。

## 治理与边界

- `python3 -m ops.verify_code_size`：PASS，243 文件 / 36,211 行 / 1,099 函数，债务 20 文件 + 50 函数未增；
- `python3 -m ops.verify_architecture`：PASS，173 模块 / 378 边 / 跨实验债务 2 未增；
- `git diff --check`：PASS；
- 本单元零数据库写入、零实验状态迁移、零 PAP、零冻结、零 StudySnapshot、零研究 manifest、零收益读取、零研究运行、零 persist、零 Web 页面修改、零部署。

## 产物 SHA256

```text
calibration_results.csv          680bf1153d583045c386717b86a1331973bb00eea9e84736fb1f630989795018
ledger_snapshot.csv              8586b83de23bdb728a57ebad4604e9e586e65ccce9d7ee0898b629e2df4585b1
evidence_bottlenecks.csv         442ba6b165f01b15fceb277cb1546cad3b98ee89fd6b72d1021880f285240053
exp22_failure_chain.csv          98be5bb392fa5c02c877fa5e7d9cb352cbcd78f3ff09deddf2c4b3d92ad57b1c
extract.sql                      28ccfecbb8840997577f1841fb4287a513aa73302ebae63856e22a863e91c18b
current-readback-2026-08-12.md   9e4724dfd825cd64e8d467a9b55043f9b5ca128e3f89df6c7f22492b69f1e497
build_notebook.py                65917512acd2d44b180f1a6aa3540a10c4ff3d4031110fc55be3aef743de915f
cycle_end_review_analysis.ipynb  397fc6941f7e669ae4c911e4b63900c44eb3034b79219b9bd4bea46c5e85d9d5
build_report_artifact.py         809f596562c99772e5d479e714f023ae8d321552036ee92ab5c1b9fc7496dd48
artifact.json                    efbd58a33567f581eca8a2e0843c355320190ef14ee9d1e7fe64c2b6872a4c59
cycle_end_review_report.html     1226257710a39621c86284c8f89989825db9fddeb914ba079ce9534711863283
```

## 复现入口

- `build_notebook.py`：生成并执行 notebook；
- `build_report_artifact.py`：由 CSV 与 SQL 生成规范 `artifact.json`；
- `artifact.json`：portable HTML 的唯一结构化源；
- `cycle_end_review_report.html`：便携、自包含的底稿报告。
