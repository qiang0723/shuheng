# exp568 `st_imposition` · manifest + §7 单次正式运行交付（2026-07-29）

## 结论

**§7 单次正式运行成功，现停在取证点。** 顶层判决=`SIG`：主窗`[0,+4]`
市场调整后CAAR=`-0.15929536336562053`（约`-15.93%`，N=`554`），唯一权威统计量
ADJ-BMP=`-5.522936355365047`；family trial 2 的双侧`alpha=0.025`下显著。

人的冻结预判原文为“负，把握度60%”，仅押主窗方向并绑定PAP digest
`56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`。
本次实测方向为负；正式开封对照与校准册入册留待persist终令，本交付点不改写预判、
不提前闭卷。效力仍为`llm/prescreen`，即使`SIG`也不得写成足额human/full结论。

## 1. 运行前硬闸

只读前置全部通过：

- exp568=`frozen`，`frozen_at=2026-07-29 19:23:34.970260+08`不变，结果双槽空；
  family=`delist_warning_financial`、trial=`2`、source=`llm`、power=`prescreen`；
- DB PAP canonical与令定digest逐字相等；台账26行=
  `registered 10 / frozen 3 / done 11 / closed 2`；零既有exp568正式manifest和运行进程；
- source snapshot 74三处digest均为
  `075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`；
- 完整向量为qbase八键
  `daily=6 / forecast=1 / trade_cal=10 / adj_factor=7 / namechange=7 /
  stock_basic=6 / stk_holdertrade=2 / holder_sell_predisclose=12`，taosha三键
  `market_return=88 / pool_b1=18 / pool_b1_return=18`；三派生批锚定source 74，
  `pool_b1_return=18`父池为`pool_b1=18`。

## 2. exp568自有研究manifest与选择硬闸

- 由source snapshot 74一次生成并发布manifest=`294`，创建时间
  `2026-07-29 23:33:11.518831+08`；
- taosha权威行、qbase镜像、publication attestation三处digest全为
  `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
- `verify_manifest_lineage=24/24 PASS`，`verify_snapshot_mirror=11/11 PASS`；
- 在读取收益和调用正式引擎之前，以manifest 294独立执行选择硬闸：输入18,868行，
  精确得到`765事件 / 646证券 / 带星560 / 不带星205`，漏斗与组成恒等式均为true，
  所有参考差额为0。

## 3. §7唯一一次正式运行

- 运行代码为只读挂载的精确HEAD=
  `2a5d819b9d72fc675a60cb313bb26cb18e12c2b4`；运行时镜像=
  `shuheng-quant:579a354`，image ID=
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
  Python=`3.14.4`、锁定依赖`21/21 PASS`。重新构建同依赖层因下载长期无进展而在正式
  运行前终止，未生成新镜像、未消耗单跑；完整说明见取证包runtime note；
- 容器根文件系统和`/opt/quant`代码挂载均只读，仅证据目录可写；
- 运行时间=`2026-07-29 23:56:58+08`至`23:57:52+08`，仅启动一次，RC=`0`；
- `--pap-sha256-assert`逐字等于冻结digest；manifest=`294`；
- 正式选择审计再次精确得到`765/646/560/205`，两条恒等式为true；
- experiment identity=`exp568/delist_warning_financial/trial2/llm/prescreen`，报告明确
  `alpha=0.025`，result递归`verdict`键恰1个。

核心统计：

- N_valid=`565`，剔除=`200`，剔除率=`26.14%`，告警如实保留；主窗完整N=`554`；
  主窗逐tau N=`565/563/564/560/559`，完整五日面板交集形成N=`554`；
- 相关折算：rho_bar=`0.042969464364672125`，Kish N_eff=`22.38973539618494`，
  KP N_eff=`21.427660458944132`；
- 主窗`[0,+4]`：CAAR=`-0.15929536336562053`，ADJ-BMP=
  `-5.522936355365047`，`SIG`；
- 次级`[0,+19]`：CAAR=`-0.21998470014767832`、ADJ-BMP=
  `-3.7785728243967167`；稳健`[0,+59]`：CAAR=`-0.17835753215884548`、
  ADJ-BMP=`-2.296288246245026`，均`NOT_FOR_VERDICT`；
- 朴素t=`-29.597774310383052`、Corrado秩t=`-12.348316673134182`、日历t=
  `-22.542378119077203`，全部仅为`NOT_FOR_VERDICT`，不得替代或扩写唯一判决；
- 行业unknown残余=`179/565=31.68%`，升级上报；名称带星/不带星组成仍只报数量，
  零分层CAR、显著性和verdict。

## 4. 运行后状态与取证

只读后核验全部通过：

- exp568仍为`frozen`，`frozen_at`不变，`result_json/done_at`为空；
- experiment台账仍26行=`10/3/11/2`，ledger零写入；
- manifest 294三处digest与完整十一键向量不变；阿里云HEAD为`2a5d819`且工作树净；
- 13类秘密扫描`TOTAL_HITS=0`，原始产物零修改；取证目录=`/root/s568run/`，
  `SHA256SUMS -c`全通过。

三件原始产物SHA256：

- `result_exp568.json`：
  `6e96183c7cffd73261add0207899856b26ce5f783f3478bc49fbd2477a1c8afa`
- `report_exp568.txt`：
  `a4c1cba0f2dd8b9018c78616f8534728d4435980eaa1eb388d98c3356aa04eff`
- `run568.log`：
  `67f609be422e825e04243ac70d633fff6b22b41c11097666321d04fb9ff207a7`

## 5. 停止线

**本轮不授权、也未执行persist。** 结果原件、manifest和运行后冻结状态先交人验收并供
Fable作GitHub侧独立复核；persist须由John另行明确授权。

## 6. persist与正式闭卷（2026-07-30）

John随后明确授权：“批准 exp568 persist，并按上述固定读法正式闭卷。”终令见
`taosha/docs/st-imposition-persist-order-2026-07-30.md`。

- persist前只读断言`28/28 PASS`；三件原件SHA、exp568冻结状态、PAP canonical、
  manifest 294三处digest、result关键值与台账`10/3/11/2`全部符合终令；
- `taosha_app`同连接单事务执行
  `start_running(568) → finish(568, 已验收result原件) → 一次COMMIT`，
  `done_at=2026-07-30 00:36:07.188912+08`；零重跑、零改写、零旁路、零新增行；
- persist后只读核验`17/17 PASS`：exp568=`done/SIG`，库内result与原件
  `parsed_equal=True`，canonical双侧SHA=
  `3aa01a38045171624fa03d311e3e5fa3ab1803a457ebf787b890edb54ae52f35`；
  台账26行=`registered 10 / frozen 2 / done 12 / closed 2`，恰迁一行；PAP、
  manifest 294三处digest与三件原始产物SHA均未改变；
- persist证据目录=`/root/s568persist/`，三件脚本、三件日志及`SHA256SUMS`自检全通过。

闭卷固定读法：冻结预判原文“负，把握度60%”仅押主窗方向，不押幅度或统计显著性；
实测主窗CAAR为`-15.9295%`，故校准册第八条只记**方向命中**，研究的独立统计终态为
`SIG`，不得合写为“预判命中且显著”。方向校准累计为`4命中/4未命中`。

本CAAR包含一字板与涨跌停价格观察；正式结果已有τ0执行受限披露：一字板`383`、涨停
`4`、跌停`64`，合计`451/565=79.82%`，不得读作可成交收益或可执行策略。industry
unknown=`179/565=31.68%`，行业诊断在本实验实质不可用，但不进入market benchmark顶层
判决；不得表述为行业中性已核过。效力保持`llm/prescreen`，本次`SIG`不构成human/full
足额证据，不自动登记、复验或升级效力。剔除率、N_eff口径、辅助三法及次级/稳健窗
全部按正式result原样保留且`NOT_FOR_VERDICT`。

**exp568至此正式闭卷，不再追加复核、重跑或敏感性分析。**
