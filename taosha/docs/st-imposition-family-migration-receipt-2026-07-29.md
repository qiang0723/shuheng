# exp15 `st_imposition` · family迁移回执（2026-07-29）

## 结论

迁移已按最终补充令完成并独立只读复核：旧exp15关闭；新承接行为**exp568**，身份=`delist_warning_financial/family_trial 2`、状态=`registered`。exp22保持`delist_warning_financial/trial 1/registered`不变。

## 执行与回滚留痕

1. 首次事务：旧legacy PAP复制至新登记行时，被`pap_schema_version`硬门拒绝，COMMIT前回滚；
2. v2事务：PAP schema已合法，但连接级`dict_row`破坏`ledger.register()`元组返回契约，COMMIT前回滚；
3. v3事务：连接恢复默认元组返回，仅审计查询使用字典游标；前置断言通过后一次COMMIT成功。

三轮间均以独立只读读回确认数据库保持原状态；失败脚本与日志未删除、未覆盖。identity序列因回滚事务产生跳号，新承接行实际ID由数据库返回为568；台账仅新增一行，不以ID连续性冒充行数。

## 后核验

- 旧exp15=`closed`，关闭原因逐字等于迁移令固定原文，`result_json`为空；
- exp568=`registered`，`frozen_at/result_json/done_at/closure_reason`全空；
- exp568相对旧exp15：title/source/verdict/contamination/data_class/crowding_prior逐字段相等；PAP旧11键逐键相等，新增键集恰为`analysis_type="event"`与`pap_schema_version=2`；
- exp22仍为trial 1 registered；
- 台账26行=`registered 11 / frozen 2 / done 11 / closed 2`；
- 零PAP冻结、零manifest、零收益读取、零正式运行、零persist。

## 证据

阿里云证据目录：`/root/s15migrate/`。脚本、三轮日志、读回与`SHA256SUMS`均在场并通过`sha256sum -c`；清单文件SHA256=`bc3e39c91555d8a2bb015dd1b35f93370d4cac4c2d4eb4ef24b2c52acad03d85`，最终v3脚本SHA256=`016b7c285255f6dbb7de56da23fc9eb277ba6ba447391b81aee4ab9782b36f89`。

## 下一停止线

后续PAP草案仅以exp568为对象，并明确“旧exp15/新承接行exp568”。本回执不授权冻结、适配、manifest、收益读取、正式运行或persist。
