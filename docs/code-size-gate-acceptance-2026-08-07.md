# 代码规模闸门验收（2026-08-07，UTC+8）

## 授权与范围

John 原文：`按照你的建议来`。

本单元只落实代码规模治理，不拆分存量研究逻辑，不触碰数据库、PAP、实验状态、manifest、
收益读取、正式运行或 persist。exp23 继续停在 NOT-FROZEN PAP 草案交验点，exp18 继续停原语义硬门。

## 落地规则

- 扫描 `ops/qbase/taosha/web` 的活跃 Python、SQL、TypeScript/JavaScript、CSS 与 shell 文件；
  排除文档、vendor、依赖与构建产物。
- 新文件最多 300 行，新 Python 函数最多 60 行。
- 存量超限项按实物建立精确基线：20 个文件、50 个函数，只减不增；缩小或删除后必须同步
  收紧基线，不允许重新长回。
- 基线上调必须由 John 明确批准，不得随普通施工顺手放宽。
- Docker 镜像构建强制执行 `python -m ops.verify_code_size`，超限即构建失败。
- `.dockerignore` 排除本地 Web 依赖与生成目录，防止量化镜像携带无关构建垃圾。

## 验收实物

- 本地隔离正反向自检：`verify_code_size self-test: PASS`；覆盖合规、61 行函数拒绝、301 行
  新文件拒绝、历史精确基线放行、基线继续增长拒绝。
- 本地全仓扫描：`PASS; files=208, lines=31179, functions=817, debt_files=20,
  debt_functions=50`。
- Docker 构建：规模闸门在构建阶段 PASS；构建上下文 6.26MB。
- 容器内隔离自检与全仓扫描均 PASS。
- 容器既有 strict 运行时：Python 3.14.4、依赖锁 21/21，ALL PASS。
- `git diff --check` PASS；本单元零研究运行与零数据库访问。

## 后续纪律

不单开大重构。新工作不得继续向存量热点增加规模；自然触碰超限文件或函数时，优先拆分并同步
下调基线。`runner.py`、`report.py` 与重复 driver 是首批自然拆分对象，但拆分必须保持行为等价并
沿用既有逐字节回归与专项 fixture。
