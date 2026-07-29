# exp568（旧exp15）`st_imposition` · 冻结与最小适配令（2026-07-29）

批准冻结终版PAP：`digest=56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`。

人的密封预判原文：`负，把握度60%`。唯一解释：主窗[0,+4]市场调整后CAR方向为负；仅押方向，不押幅度或统计显著性，仅绑定上述digest。

## 冻结

冻结前只读确认：exp568=`delist_warning_financial/trial 2/registered`且四槽空；旧exp15=closed、exp22=trial1 registered；零exp568 manifest/运行记录；终版文件SHA、canonical重算与令digest三者一致；数据库现载荷仍为13键登记PAP；台账26=`registered 11 / frozen 2 / done 11 / closed 2`。任一不符即停。

以`taosha_app`同连接单事务：`FOR UPDATE`重做断言→数据库载荷更新为终版canonical原文→`ledger.freeze(568)`→一次COMMIT。读回PAP canonical/parsed equality/MD5与状态；台账应为26=`registered 10 / frozen 3 / done 11 / closed 2`。

## 冻结后最小适配（至行为验收止）

仅实现普通→ST反向事件规则、exp568 driver、专属报告分支与两件fixture；复用019 namechange视图、现有事件引擎与`missing_bar_only`，统计内核/qbase零改动。代码须保持小函数与明确模块边界，不复制整份exp12 driver形成平行大文件。

攻击面至少覆盖：普通→ST与普通→*ST入集；ST→ST、ST→普通、普通→退市、退市→ST排除；同票多轮独立事件；锚缺失/冲突/ann>start/状态混合/重复键fail-closed；带星/不带星仅数量NFV、递归零verdict；engine_params与digest逐字消费；family_trial必须从台账读为2并使族内α=0.025，不得由PAP或driver覆盖。

recon按batch7冻结规则复现，765事件/646票仅参考；差异按血缘归因，不追数、不改规则。全家福与既有默认路径零回归。

仍禁止：exp568正式manifest、真实收益正式运行、persist。完成后停行为验收点。
