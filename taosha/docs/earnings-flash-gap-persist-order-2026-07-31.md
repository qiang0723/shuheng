# exp17 `earnings_flash_gap` persist 终令

日期：2026-07-31（UTC+8）  
授权人：John  
授权原文：

> 批准 exp17 persist，并按“校准册第十条、方向命中但不显著、累计5命中/5未命中”的固定读法正式闭卷。

## 一、授权对象与边界

唯一 persist 输入为已验收的单次正式运行原件：

- result：`/root/s17run/delivery/result_exp17.json`，SHA256=
  `a5249ec4554aff2476bc33b33b2e2600dd7cdcba01a0c98fb04e27a382394db7`；
- report SHA256=
  `cb29f575f9ef4a607852df518c44e8db8c542b60e63613fe51c90a3bd6878745`；
- log SHA256=
  `daa31bb87e072d73678baf0d5e51f5af757d6ced0737ce6e9d750f3babc7b489`。

禁止研究重跑、收益重读、原件改写、PAP 改写、manifest 重建、旁路 SQL、新增
experiment 行或敏感性分析。本令只授权既有状态机单事务 persist、只读后核验与闭卷留痕。

## 二、Fable 复核项闭合

1. 主窗 τ=0..4 的 N 为 `1841/1837/1835/1831/1829`，相对
   `N_valid=1841` 的缺失数为 `0/4/6/10/12`；主窗完整样本差
   `1841−1822=19` 落逐 τ 缺失并集界 `[12,32]`，且交集
   `1822≤min(N_tau)=1829`，守恒成立。
2. `rho_bar=0.009815666688264883`；按顶层 `N_valid=1841` 复算
   Kish=`96.58552739379029`、KP=`95.63747604998257`，与 result 全精度逐位相等。
   `n_eff_rho` 是 `NOT_FOR_VERDICT` 诊断；主窗 ADJ-BMP 另按主窗完整样本
   `N=1822` 计算，两者无混用。
3. 只读补证 JSON=`/root/s17run/b_followup_readback.json`，SHA256=
   `386759c2fec7a6a5a7bdff9f365a8eae6c522a81e828a7aad32d4278481824c2`；
   result 原件补证前后 SHA 不变。Fable 更新结论为 `A0/B0/C1`；C 项默认不采。

## 三、事务前只读断言

任一不符立即停止，不修补、不自动重跑：

1. 上述 result/report/log 与补证 JSON 的 SHA256 全值逐字相等；
2. exp17 仍为 `frozen`，
   `frozen_at=2026-07-30 22:36:24.132972+08`，`result_json/done_at` 为空；
3. 数据库 PAP canonical=
   `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`；
4. manifest 363 权威行、qbase 镜像、publication attestation 三处 digest 均为
   `2e6f25863fb2f41b3f781c971c325456fe045a4602d1e9175a03828e4d70380b`；
5. result 关键值：递归 `verdict` 恰一个且顶层为 `NOT_SIG`；事件 `2,529`、
   `N_valid=1,841`、主窗 `N=1,822`、signed CAAR=
   `0.001648578486047189`、ADJ-BMP=`0.2783298113335189`；
6. result 身份恰为
   `exp_id=17/family=earnings_flash_gap/family_trial=1/source_type=llm/verdict_power=prescreen`，
   PAP 与 manifest 锚逐字正确；
7. selection SHA=
   `cd1433f0e9cc5d60dea807dc7f4f7b26fbcf324392602205c466aa7be5bb05ac`，
   事件组成 `up=997/down=1532`，三条选择恒等式全真；
8. ledger 共 26 行，分布为
   `registered 8 / frozen 3 / done 13 / closed 2`。

## 四、persist 执行

使用 `taosha_app` 同一连接、同一事务：

1. 完成全部事务前只读断言；
2. `FOR UPDATE` 锁 exp17 行后，再断言 `status=frozen`、结果双槽空、PAP canonical
   未变；
3. 仅走既有状态机 `ledger.start_running(17)`；
4. 仅以已验收 result 原件的解析对象调用 `ledger.finish(17, result)`；
5. 一次 `COMMIT`。

禁止修改冻结 PAP、result/report/log、补证 JSON、manifest 或 result 内容。

## 五、persist 后只读核验

1. exp17=`done`、`done_at` 非空、顶层 verdict=`NOT_SIG`；
2. 库内 `result_json` 与 result 原件 `parsed_equal`，canonical 序列化 SHA 双侧一致；
3. 库内身份水印、PAP 锚、manifest 锚与原件逐字段相等，递归 verdict 仍恰一个；
4. `frozen_at` 与 PAP canonical 不变；
5. ledger 仍为 26 行，分布恰为
   `registered 8 / frozen 2 / done 14 / closed 2`；
6. manifest 363 三处 digest 不变，result/report/log 与补证 JSON SHA 不变；
7. 本地、GitHub、阿里云代码同步且工作区干净。

## 六、闭卷固定读法

1. 密封预判原文：**“正，把握度80%”**。该预判仅押主窗 signed 市场调整后 CAR
   方向，不押幅度或统计显著性，绑定 PAP digest
   `92eec90123e53981e4752bd129b0113c1fbd8c5f18845cd885ebf93ad9a62f97`。
2. 实测主窗 signed CAAR=`+0.1649%`，方向命中；ADJ-BMP=`+0.278` 双侧不显著，
   终态 `NOT_SIG`。固定表述为**“方向命中但不显著”**，不得合写成“预判命中且显著”。
3. 校准册据实登记为**第十条**，累计方向读数为**5命中/5未命中**。
4. 不得认定存在可靠的业绩快报超预期或低预期效应；朴素 t、Corrado、日历法、
   次级窗、稳健窗、raw direction 与可交易口径均为 `NOT_FOR_VERDICT`，不得改写顶层判决。
5. 剔除率 `27.20%` 与行业 unknown `173/1841=9.40%` 告警如实保留；效力维持
   `llm/prescreen`，不得写成 human/full 或足额判决证据。

## 七、停止线

完成 persist、后核验、取证归档、闭卷交付档与 STATE 后停工。不得追加重跑、
敏感性分析、参数调整或无关施工。
