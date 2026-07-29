# exp568 `st_imposition` persist终令（2026-07-30）

> John 人令原文：**「批准 exp568 persist，并按上述固定读法正式闭卷。」**
> 唯一输入为已验收原件 `/root/s568run/result_exp568.json`。本令不授权重跑、改写
> result、敏感性分析或新实验登记。

## 一、前置只读断言

任一不符立即停止，不修补、不改写：

1. 三件原件SHA256必须分别为：
   - result=`6e96183c7cffd73261add0207899856b26ce5f783f3478bc49fbd2477a1c8afa`；
   - report=`a4c1cba0f2dd8b9018c78616f8534728d4435980eaa1eb388d98c3356aa04eff`；
   - log=`67f609be422e825e04243ac70d633fff6b22b41c11097666321d04fb9ff207a7`；
2. exp568仍为`frozen`，`frozen_at=2026-07-29 19:23:34.970260+08`不变，
   `result_json/done_at`为空；
3. DB PAP canonical=
   `56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`；
4. manifest 294权威行、qbase镜像、publication attestation三处digest均为
   `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
5. result关键值须逐字等于：顶层唯一verdict=`SIG`、事件=`765`、N_valid=`565`、
   主窗N=`554`、CAAR=`-0.15929536336562053`、ADJ-BMP=
   `-5.522936355365047`；选择审计=`646证券/带星560/不带星205`且两条恒等式为true；
   身份=`exp568/delist_warning_financial/trial2/llm/prescreen`，双侧alpha=`0.025`；
6. 台账必须仍为26行：`registered 10 / frozen 3 / done 11 / closed 2`。

## 二、persist执行

- 仅走既有状态机，由`taosha_app`同连接单事务执行
  `start_running(568) → finish(568, 已验收result原件) → 一次COMMIT`；
- 事务内`FOR UPDATE`后再次断言状态与PAP digest；
- result唯一来源为上述原件；零重跑、零改写、零旁路SQL、零新增台账行。

## 三、persist后核验

- exp568=`done`、`done_at`非空、顶层verdict=`SIG`；
- 库内result与原件`parsed_equal`，canonical双侧SHA一致，关键数值零删减零补写；
- 台账仍26行，分布应为`registered 10 / frozen 2 / done 12 / closed 2`，恰迁一行；
- PAP canonical、manifest 294三处digest、三件原始产物SHA均保持不变；
- 本地与阿里云HEAD同步、工作树干净。

## 四、闭卷固定读法

1. **校准册第八条**：冻结预判原文“负，把握度60%”，并逐字保留冻结限定：仅押主窗
   方向，不押幅度或统计显著性，绑定上述PAP digest。实测主窗CAAR为`-15.9295%`，
   因此只记**方向命中**；研究的独立统计终态为`SIG`，不得写成“预判命中且显著”。
   入册后方向读数为`4命中/4未命中`。
2. **执行边界**：本CAAR包含涨跌停及一字板价格观察，不等于可成交收益或可执行策略。
   既有正式报告τ0执行受限项为：一字板`383`、涨停`4`、跌停`64`，合计
   `451/565=79.82%`；该统计仅用于解释边界，不改判决、不改result。
3. **行业诊断边界**：industry unknown=`179/565=31.68%`，行业诊断在本实验实质不可用；
   但`benchmark_mode=market`、`strata_enabled=false`、`diagnostic_dims=[]`，该缺失不进入
   顶层判决链，亦不得表述为“行业中性已核过”。
4. **效力边界**：`llm/prescreen`的`SIG`不是human/full足额证据，不得写成发现alpha。
   它至多进入人工选题候选池，不自动登记、复验或升级效力。
5. 剔除率`26.14%`告警、Kish/KP以N_valid为基数、辅助三法与次级/稳健窗全部
   `NOT_FOR_VERDICT`，如实保留，不得择优扩写顶层结论。

完成后更新交付档与STATE，停工交终签；不再追加复核、重跑或敏感性分析。
