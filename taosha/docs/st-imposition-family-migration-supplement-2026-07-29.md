# exp15 `st_imposition` · family不可变迁移补充裁定（2026-07-29）

## 一、首次事务失败与回滚

首次迁移事务在`ledger.register`调用`validate_pap`时被既有执行schema硬门拒绝：旧exp15登记载荷为legacy 11键PAP，新登记行必须显式包含`pap_schema_version`。异常发生于COMMIT前，事务已整体回滚；只读复核确认exp15/exp22身份、状态、四槽及台账`25=registered 11 / frozen 2 / done 11 / closed 1`均未变化。

失败日志与脚本原件保留于阿里云`/root/s15migrate/`，不得删除或改写。

## 二、人补充授权

施工方向人报告唯一阻塞，并提出最小修正：新承接行的登记PAP仅在旧载荷上增加`pap_schema_version=2`与`analysis_type="event"`，其余11键逐字不变；后续仍在registered态按正常PAP流程完善，冻结前另行复核。

人授权原文：`批准`。

## 三、修正执行边界

1. 修正事务前重新执行原迁移令全部只读断言；
2. 关闭旧exp15的原因原文不变；
3. 新行family仍为`delist_warning_financial`，`family_trial`仍只允许数据库触发器生成，必须为2；
4. 新行PAP须满足：旧exp15载荷11键逐键解析相等，新增键集恰为`pap_schema_version`与`analysis_type`，值分别为`2`与`event`；不得增加、删除或修改其他键；
5. 仍为同连接单事务、一次COMMIT；失败即回滚停止，不自动作第三次尝试；
6. 其余后核验、台账守恒和禁止项沿原迁移令不变。
