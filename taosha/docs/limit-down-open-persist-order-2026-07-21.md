# exp13 §7 取证验收通过+persist 终令(2026-07-21,人令原文即口径)

> 留痕纪律(F 条):人令留痕 commit 先于执行。本档为 2026-07-21 深夜人令逐字原文。

## 人令原文(逐字)

> exp13 §7单次运行取证验收通过,授权persist。
> persist唯一输入为已验收原件:
> /root/s13run/result_exp13.json
> SHA256=c71a696df5cd8803f34532220a0995cc87e638d497ae5cb592b08e9eba28b83e
> 执行前确认exp13仍frozen、结果槽为空、PAP digest为583c4c94…0c42、manifest 189三处digest一致、台账为15/3/6/1。
> 仅走既有状态机,以taosha_app同连接单事务执行start_running(13)→finish(13,result),一次COMMIT;零重跑、零改写、零旁路、零新增行。
> 闭卷留痕如实记录:
> 预判"主窗CAR约+5%、把握度70%"对实测−4.478%,方向未命中;ADJ-BMP不显著,终态NOT_SIG;
> NOT_SIG仅在冻结行业分组口径下成立,unknown组占26.8%,不作结果后敏感性重跑;
> 朴素t、Corrado、日历法名义显著及所有诊断/可交易口径均为NFV,不得改写顶层结论;
> 效力维持llm/prescreen。
> persist后核验exp13=done、库内result与原件解析全等、manifest不变、台账25行=registered 15 / frozen 2 / done 7 / closed 1、三件原始产物SHA不变、两台Git干净。完成后停工交终签。

## 执行边界(照令展开,先例=exp8/exp20 persist)

- 前置断言(只读):三件产物 SHA 不变(result `c71a696d…8b83e`/report `9ad456e9…77f8`/
  log `fc499797…405f`);exp13 frozen+结果槽空;DB PAP canonical==`583c4c94…0c42`;
  manifest 189 三处 digest==`21e9095e…efcd`;台账 25=15/3/6/1;result 原件锚定值逐项。
- 执行:taosha_app 同连接单事务,入事务前 FOR UPDATE 再断言→`ledger.start_running(13)`→
  `ledger.finish(13, result)`→一次 COMMIT;任一异常整笔回滚停止,零重跑零改写零旁路零新增行。
- 后核验(只读):done/verdict NOT_SIG/parsed_equal/canonical 双侧同/台账 25=15/2/7/1 恰迁一行/
  manifest 三处不变/三件 SHA 不变/frozen_at 既有值/两台 git 净。
- 闭卷留痕三件(如实记,原文永不改述)入交付档+STATE,随后停工交终签。
