# exp19 `dividend_surprise` · manifest + §7 单次正式运行交付

日期：2026-08-06（UTC+8 / Asia/Shanghai）

结论：**唯一一次正式运行 RC=0，顶层 verdict=`NOT_SIG`。** 已停在取证点，未 persist。

## 1. 授权与运行前硬闸

- John 授权生成 exp19 自有研究 manifest 并执行 §7 单次正式运行；F-first 运行令为
  `dividend-surprise-s7-order-2026-08-06.md`，commit=`a9a4e94`；
- 首次启动前置脚本时误用不存在的 `/usr/local/bin/python3`，在数据库连接前即停止；
  失败日志原样保留，不构成研究运行或数据库写入。改用既有
  `/opt/venvs/qbase-ingest/bin/python` 后，preflight=`33/33 PASS`；
- exp19=`frozen`，`frozen_at=2026-08-06 17:21:15.889471+08`不变，
  `result_json/done_at`为空；身份为
  `exp19/dividend_surprise/trial1/llm/prescreen`；
- PAP canonical=
  `4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`；
  台账26行=`registered7/frozen3/done14/closed2`；零既有 exp19 正式 manifest；
- source snapshot375 三处 digest 均为
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；
  qbase 键集恰为13项：
  `adj_factor=7/daily=6/dividend=17/express=15/fina_audit=16/forecast=1/`
  `holder_sell_predisclose=12/namechange=7/sox_daily=13/stk_holdertrade=2/`
  `stock_basic=6/sw_member=14/trade_cal=10`；taosha 三键为
  `market_return=88/pool_b1=18/pool_b1_return=18`，血缘与父池关系全部通过。

## 2. exp19 自有研究 manifest

以 `--create --from-source-snapshot 375` 一次生成并发布：

- StudySnapshot=`398`；
- digest=`94ee4a5e88a6a6927506d902260f75fcf88a979be97569e8056fd9705bebd0be`；
- 完整键集恰为上述13个 qbase 键与3个 taosha 键，共16键；
- taosha 权威行、qbase 镜像、publication attestation 三处 content/digest 一致；
- 血缘自检=`24/24 PASS`，镜像自检=`11/11 PASS`，manifest 后只读核验=
  `14/14 PASS`；StudySnapshot 恰增一行至20行、max=`398`，experiment ledger
  未写入。

## 3. 收益前选择硬闸

在构造 `ViewReader` 和读取正式收益前，manifest398 下独立复算：

- 最终 signed 事件=`5,055`，其中 `up=2,253/down=2,802`；
- selection SHA256=
  `985e2312a7de4aca489a888647913e15fbff914899dd3f8459e5d489304a2e6b`；
- 冻结六类分类、五条恒等式、实现阶段值零回填及 manifest 16键精确断言全部通过。

上述硬闸在 driver 正式路径中再次执行后，才进入正式收益读取。

## 4. §7 唯一一次正式运行

- 运行代码 HEAD=`b623f6dbdd5c37c020b7ce94c94a0070db19450e`且净；镜像=
  `shuheng-quant:579a354`，image ID=
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
  Python=`3.14.4`，锁定依赖=`21/21 PASS`；
- 运行时间=`2026-08-06 19:25:05+08`至`19:27:10+08`；只执行一次，RC=`0`，
  未自动重跑；
- driver 逐字消费冻结11个 `engine_params`、4个 `signed_ar`与
  `axes.direction=[up,down]`，PAP/manifest/选择硬闸及身份水印全部通过。

核心结果：

- 事件总数=`5,055`，N_valid=`3,810`，剔除=`1,245`，剔除率=`24.6291%`
  （告警）；逐年剔除为2021=`5`、2022=`6`、2023=`2`、2024=`1,232`；其中
  2024 年 `history=1,230`，来自60日稳健窗触及冻结 holdout/数据右界。该结果按冻结规则
  如实保留，不追数、不改规则、不重跑；
- 主窗 `[0,+4]`：N=`3,805`，signed CAAR=
  `-0.002804575188488496`（`-0.2805%`），ADJ-BMP=
  `-0.21553616523859276`，双侧不显著，顶层 `NOT_SIG`；
- 主窗逐 τ N=`3810/3810/3809/3805/3806`；N_valid 与完整主窗差=`5`，逐 τ
  缺失=`0/0/1/5/4`，并集5落在 `[max=5,sum=10]` 内；
- 主窗辅助统计：朴素 t=`-2.569503526040695`、Corrado=
  `-2.1898676110472217`，两者名义显著；日历法=`-1.876205597301981`不显著；
  三者均为 `NOT_FOR_VERDICT`，不得改写唯一判决；
- 次级 `[0,+19]`：N=`3,787`，CAAR=`-0.008183342590585415`，ADJ-BMP=
  `-0.3495144711961279`；稳健 `[0,+59]`：N=`3,759`，CAAR=
  `-0.032459804658179305`，ADJ-BMP=`-0.8483544772097485`；均为
  `NOT_FOR_VERDICT`；
- rho_bar=`0.02998195801586874`，Kish N_eff=`33.07254974439924`，KP N_eff=
  `32.08096994648493`；行业 unknown=`62/3810=1.6273%`，未触5%升级线；
- effect alignment=`REVERSED`；up/down raw 方向层、cost 与可交易口径输出均只作
  NFV 诊断，不进入顶层判决；效力保持 `llm/prescreen`。

人的密封原文“正，把握度60%”仍逐字封存。本次实测主窗方向为负；开封对照与校准册
入册留待 persist 终令，本交付点不提前入册、不改写密封原文。

## 5. 运行后状态与取证

运行后只读核验=`30/30 PASS`：

- exp19 仍为 `frozen`，`frozen_at`不变，`result_json/done_at`仍空；
- 台账仍26行=`7/3/14/2`，experiment ledger 零写入；
- manifest398 三处 content/digest 与16键向量不变；正式研究进程零残留，远端 Git 净；
- 13类秘密扫描=`TOTAL_HITS=0`，原始产物未修改；证据目录=`/root/s19run/`，
  34件 `SHA256SUMS -c` 全部通过。

三件原始产物 SHA256：

- result：`a3ecc0f7f47283a6c642f8e34b31a3487e1b03695ec1d32fb5a8dd3c603c2389`；
- report：`cff1b183c84c38ad1084126cc02e78a06ce537e2c99dff0014547089053134ae`；
- log：`96b1a362fd36f050de3726cf2cf06b644a074909922ca67b6946bba6a8c2a4fd`。

## 6. 停止线

已停在取证点。本令未授权 persist；结果经独立复核后，只能由 John 另行授权 persist。
未令不写入结果槽、不重跑、不追加敏感性分析。
