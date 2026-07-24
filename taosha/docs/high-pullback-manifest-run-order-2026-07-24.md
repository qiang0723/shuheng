# exp11 high_pullback 研究 manifest 生成 + §7 单次正式运行 · 人令原文留痕(2026-07-24 八)

> 人令下达 2026-07-24(同日第八令);原文即口径,一字不改。F 条留痕 commit 先行,与交付分单。
> 行为验收外部复核通过转授权;本令不授权代码修改、重跑或 persist;完成停取证点。

---

exp11行为验收外部复核通过。授权生成exp11自有研究manifest并执行§7单次正式运行。

一、manifest生成与发布:

生成前读回source snapshot的ID、digest及五键批次向量,必须为daily=6 / adj_factor=7 / stock_basic=6 / namechange=7 / trade_cal=10;任一变化立即停止,不生成manifest,读回入取证包;
绑定该源快照(--from-source-snapshot,沿全链血缘范式);
完成权威行、qbase镜像、publication attestation三处发布,digest一致;
不得使用snapshot 212或任何既有manifest冒充。

二、§7单次正式运行:

driver逐字消费冻结engine_params,传pap_sha256_assert=eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc,不一致fail-closed;
只允许一次执行;正式事件集必须等于42,784;不相等立即停止,不作运行后解释、不自动重跑;RC非零或任一锚定断言失败同停,停下报人;
运行后保持exp11为frozen、result_json与done_at为空、台账零写入(仍为13/3/8/1)。

三、取证(停点):

result/report/log三件原件+SHA256清单,传输前13类秘密扫描(命中不得改原件,停下报传输方案);
只读回报:source snapshot读回记录、manifest三处digest、exp11 status与frozen_at(冻结值不变)、台账基线、核心统计、生产git状态。

四、边界:
本令不授权代码修改、重跑或persist。完成后停在取证点,结果验收后另议。
