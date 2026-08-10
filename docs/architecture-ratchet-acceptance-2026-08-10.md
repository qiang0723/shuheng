# 枢衡架构依赖棘轮验收

- 日期：2026-08-10（UTC+8 / Asia/Shanghai）
- 授权：`docs/architecture-ratchet-order-2026-08-10.md`
- 结论：PASS；只新增架构防线，零研究行为改动

## 一、落地规则

新增 `ops.verify_architecture`，扫描 `ops/qbase/taosha` 活跃 Python 模块并执行四类硬门：

1. 内部 import 图出现任何循环即失败；
2. `qbase` 反向 import `taosha` 即失败；
3. `taosha.compute/engine/reader` 反向 import `taosha.harness` 即失败；
4. 实验专属 `*_rules` 或 `run_*_study` 新增横向依赖即失败。

存量横向依赖以 `ops/runtime/architecture_baseline.json` 精确登记，仅两条：

- `taosha.compute.st_imposition_rules -> taosha.compute.st_removal_rules`
- `taosha.harness.run_st_imposition_study -> taosha.harness.run_st_removal_study`

实际边多于基线时拒绝新增；实际边少于基线时要求同步删除债务。基线无预留额度。

## 二、核验实数

- 隔离 self-test：PASS；覆盖新增横向依赖拒绝、精确基线放行、债务下降要求收紧、循环拒绝、
  `qbase→taosha` 层级倒置拒绝；
- 全仓实扫：PASS；活跃 Python 模块162、解析后内部依赖362、循环0、横向债务2；
- 原规模闸门：PASS；源码231文件/34,446行/992函数，存量债务仍20文件+50函数，零新增；
- 新 verifier 218行，所有函数≤50行，自身通过规模闸门；
- Docker 构建：两道闸门均在 `COPY` 后、切换非root用户前执行并通过；测试镜像
  `shuheng-quant:architecture-ratchet-test`，ID=
  `sha256:fae2b6f0b3f2a5478d610a547cc420ef2641abc7c43752d9cb6bed2e63efde03`；
- 无网络、只读根临时容器严格运行时：Python 3.14.4 与依赖锁21/21，ALL PASS。

F-first 中的“163模块/230边”来自开工前临时脚本：它未排除 docs，且只按 import 语句基础模块
计边。验收以正式闸门的活跃源码排除口径与解析后目标口径为准，故正式值为162/362；这是
测量口径收正，不是依赖实物变化。

## 三、触碰面与边界

触碰面只含：架构 verifier+精确基线、Dockerfile 接线、README 命令、授权/验收档与 STATE。
`qbase/taosha/web` 业务源码、研究 driver/fixture、统计内核、reader、数据库、PAP、实验状态、
StudySnapshot、manifest、result 均未改动。测试镜像只在本机用于验收，不替换任何正式部署。

## 四、后续纪律

- 新实验不得从另一个实验 driver 直接 import helper；公共逻辑应先下沉到明确公共模块；
- 当前两条 ST 对偶依赖只在自然触碰时下沉，并以既有 fixture/逐字节回归保护；
- `runner.py`、`report.py` 等热点不因本单元启动大拆分；仅在业务自然触碰时做行为等价小步拆分；
- 调整架构基线须人明确批准，不得随功能提交顺手放宽。
