# exp15 `st_imposition` · family迁移最终执行补充令（2026-07-29）

## 一、第二次失败与零残留

补充裁定后的v2事务已通过PAP执行schema校验并完成事务内INSERT，但迁移脚本把连接级`row_factory`设为`dict_row`，导致既有`ledger.register()`按元组解包返回值时取得字符串键名`"exp_id"`；随后的事务内查询据此失败。异常发生于COMMIT前，事务整体回滚。

独立只读读回再次确认：exp15与exp22身份、状态及结果槽均未变化，台账仍为`25=registered 11 / frozen 2 / done 11 / closed 1`。两次失败脚本、日志与读回证据均保留于阿里云`/root/s15migrate/`。

## 二、人最终执行授权

施工方报告唯一修正：数据库连接恢复psycopg默认元组返回；仅审计查询游标显式使用`dict_row`。不修改生产代码、PAP变换、状态机步骤、关闭原因或任何断言。

人授权原文：`执行`。

## 三、执行边界

1. 执行前第三次重跑原只读硬闸；
2. 新登记PAP仍严格等于旧11键加`pap_schema_version=2`、`analysis_type="event"`；
3. `ledger.register()`必须使用默认元组连接，family trial仍由数据库触发器生成；
4. 前两次回滚可能消耗identity序列值，新exp_id允许非连续，以本次数据库实际返回值为唯一权威；
5. 只允许本次最终执行；异常即整体回滚并停报，不再自动尝试；
6. 其余断言、一次COMMIT、后核验与禁止项沿前两份迁移令不变。
