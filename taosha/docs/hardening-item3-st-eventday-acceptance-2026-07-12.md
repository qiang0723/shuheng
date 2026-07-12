# 硬化③ 事件日 ST 修复 + 全量受控 diff · 验收档(2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ③。修法原文:cleaning 的 ST 剔除改按事件日行 is_st 判定(现取 rows[0])。验收原文:对 #4/#2b 全量重算清洗段,旧实现 vs 修复版做受控语义 diff(事件计数/剔除计数/板块分层归属逐项),影响以 diff 实测陈述,禁止以修复前计数预判影响;diff 产物即 post-ST 新基线(sha 登记)。旧闭卷 sha 永久保留,不被取代;已闭卷两案走 ⑤ 附注,不重跑不改判。
> 运行通路依据:⚖③ 通路预裁(人 2026-07-12,STATE〈可信度硬化窗口〉留痕):只读诊断模式 --diagnostic;零台账写入零状态迁移(铁律③辖产判决之运行,诊断不产判决);产物落 diff 专用目录绝不写 result 槽;与台账唯一连接=addendum 附注经人批补录;DIAGNOSTIC 水印;每次诊断跑 STATE 登记事由。

## 1. 修法实物(commit `b14872a` + diff 件 `43bbdee`/`73ba918`)

- **cleaning ST 判定源**:`clean_event` 的 ST 剔除从估计窗首行 `rows[0]`(≈事件前 250 交易日的陈旧标签)改为**事件日行 `is_st`**;新参数 `st_mode ∈ {event_day, legacy_row0}`,`event_day`=生产唯一默认,`legacy_row0` 仅诊断域可用(**双闸**:非 --diagnostic 传 legacy_row0 即拒),自检新旧对照用例固化(cleaning 自检 R7–R10)。
- **穿透**:runner / drawdown_strategy 穿 `st_mode`;三 driver(run_forecast_study / run_drawdown_study / run_drawdown_strategy)增只读诊断模式:`--diagnostic` + `--reason` 必填 + 终端 DIAGNOSTIC 水印 + `result.diagnostic` 块;另 run_ashare_study 增 `--st-mode`(合成域对照用)。
- **合成域实测**(commit b14872a 当次):legacy_row0 逐字节复现旧合成基线 sha `3116ba9b`(参数化零扰动证);event_day 同 sha(合成夹具 ST 恒定 → 合成域 ST 效应=0 实测)。
- **diff 分析件** `taosha/harness/diff_post_st.py`:受控语义焦点面(事件计数 / 剔除原因×年份 / 板块分层 / 统计事实〔事件版 car+verdict;策略版 net/gross/BHAR/adj_z/DSR/exits/postpone/同源一致性〕)+ 三方归因协议(**闭卷 vs 旧臂 = 013 tie 钉死效应;旧臂 vs 修复臂 = ST 效应**;#2b 不消费事件视图 → tie 不适用);两提取器已对 exp3/exp5 闭卷实物校准(commit 73ba918)。

## 2. 运行环境合规(①② 焊死 + 通路预裁,硬前置)

- **①② 已过架构窗口(人 2026-07-12)后才跑**:九跑全部 `--diagnostic --snapshot-id 1`,manifest #1 digest `2a8a271f2f7a52b53fce966fbd094f11803f9f6f06a87e86a028a1589625cdf6`;产物 audit 实测记账(b4_eventday.json 摘录):`study_snapshot={snapshot_id:1, digest:2a8a271f…, content:{qbase:{daily 6/adj_factor 7/forecast 1/trade_cal 5/stock_basic 6/namechange 7/stk_holdertrade 2}, taosha:{market_return 1/pool_b1 1/pool_b1_return 1}}}`。
- **DIAGNOSTIC 水印实测**(产物 `diagnostic` 块摘录):`{"diagnostic": true, "reason": "硬化③受控diff(ST事件日修复与013tie钉死分开归因;人令+通路预裁2026-07-12)·#4修复臂", "st_mode": "event_day", "exp_status_at_run": "done", "note": "只读诊断: 零台账写入、不产判决(通路预裁 2026-07-12);产物不得作 result 槽载荷"}`。
- **台账零写入实测**(跑毕查库 2026-07-12):experiment 仍 **25 行 = registered18/frozen3/running0/done3/closed1**;`experiment_addendum` 跑毕时仍仅 1 行(附注(a));闭卷载荷 sha256(`sha256(result_json::text)`)与锚全等——exp3 `e3d2aef92bd47c6b28c460d1847a3b63226bd72c2bdd936d4efbcdf761216332`(==附注(a) 锚)、exp5 `c010ce9d4d235424eb34548c5647b8381db0758fd68e52a355ad079787241c8f`。
- **事由登记**:STATE〈诊断跑批事由〉先行留痕(commit `f73aa1c`→`6dc5429`)。

## 3. 九连跑实录(aliyun `/root/s3hard3_runner.sh` 串行 + `/root/s3hard3_post.sh` 守护)

| # | 跑名 | 案/臂 | 起—止(2026-07-12) | rc |
|---|------|-------|--------------------|----|
| 1 | a4_legacy | #4 旧臂(legacy_row0) | 17:29:45–17:55:53 | 0 |
| 2 | b4_eventday | #4 修复臂(event_day) | 17:55:53–18:19:05 | 0 |
| 3 | b4_r2 | #4 修复臂重跑(确定性) | 18:19:05–18:42:06 | 0 |
| 4 | a2e_legacy | #2b 事件版旧臂 | 18:42:06–18:47:58 | 0 |
| 5 | b2e_eventday | #2b 事件版修复臂 | 18:47:58–18:53:50 | 0 |
| 6 | b2e_r2 | #2b 事件版修复臂重跑 | 18:53:50–18:59:40 | 0 |
| 7 | a2s_legacy | #2b 策略版旧臂 | 18:59:40–19:04:43 | 0 |
| 8 | b2s_eventday | #2b 策略版修复臂 | 19:04:43–19:09:47 | 0 |
| 9 | b2s_r2 | #2b 策略版修复臂重跑 | 19:09:47–19:14:52 | 0 |

九跑全 rc=0,ALL DONE 19:14:52;post 守护 19:15 自动执行三对 diff(`diff_post_st --closed-exp 5/3/3`,策略对加 `--strategy`)+ sha 登记 + 备份,diff 全 rc=0。

## 4. 归因一:013 tie 钉死效应(闭卷 vs 旧臂;与 ST 修复分开归因=人拍 A)

- **#4(diff_4.json,n_diffs=35)**:n_events_total **105,584→105,590(+6)**(板块分解:main +3 / chinext +2 / star +1;②验收预测"存在可漂 19 对"中实际落 6,以实测为准);n_valid **67,760→67,765(+5)**;剔除 +1(suspension 9,019→9,020;年份重分配 2014 −1/2016 +1/2022 +1);三层 n_valid:good +10 / bad −7 / turnaround +2;主窗 ADJ-BMP 0.08745616→0.08744020(Δ≈−1.6e-5)、CAAR −0.00109434→−0.00109362;稳健窗 ADJ-BMP 0.16056→0.16043;ρ̄ 0.0732199→0.0732237;**verdict NOT_SIG 不变**。
- **#2b 事件版(diff_2e.json):closed vs 旧臂 n_diffs=0**;**#2b 策略版(diff_2s.json):closed vs 旧臂 n_diffs=0**——#2b 不消费事件视图,tie 不适用**实测得证**;且闭卷记录在 ①②(manifest 路由 + 013 钉死后视图)+ legacy st_mode 环境下**逐字节复现**,同时构成闭卷可复现性硬证。

## 5. 归因二:ST 效应(旧臂 vs 修复臂;影响以实测陈述)

- **#4(n_diffs=135)**:st 剔除 **30→4,239(+4,209)**;n_valid **67,765→64,033(−3,732,−5.51%)**;剔除率 0.35823→0.39357;剔除原因重分配(同一事件被更早剔除原因截获的次序转移):coverage 7,929→7,482(−447)、postpone 27→11、suspension 9,020→9,007、history 20,797→20,796;板块 ST 层 38→4,239;三层 n_valid:good 34,664→34,435(−229)/ bad 26,996→24,661(−2,335)/ turnaround 6,105→4,937(−1,168)(ST 剔除集中于预亏/扭亏层——结构陈述,非解读);主窗 ADJ-BMP 0.08744→**0.07147**、CAAR −0.001094→−0.002007;稳健窗 ADJ-BMP 0.16043→**0.13076**、CAAR −0.003776→−0.006238;ρ̄ 0.07322→0.07768;Kish 13.65→12.87 / KP 12.65→11.87;**三臂 verdict 均 NOT_SIG,判决不变**。
- **#2b 事件版(n_diffs=87)**:st 剔除 **4→144(+140)**;n_valid **17,929→17,827(−102)**;剔除率 0.08703→0.09222;主窗 ADJ-BMP −0.410848→−0.410839、CAAR −0.031036→−0.031159;稳健窗 ADJ-BMP −0.58660→−0.58339;ρ̄ 0.21966→0.22103;**verdict NOT_SIG 不变**。
- **#2b 策略版(n_diffs=121)**:消费 17,929→**17,827**(同源差集仍 0:`n_survivors_sourced==n_consumed`,"⊆"实现仍为"==");exits:break_ma20 17,910→17,808(stop 18 / censored 1 不变);adj_z 毛 −0.55271→−0.55172 / 净 −0.66205→−0.66075(**NOT_SIG 标注不变**,判决权归事件版);net.mean −0.008610→−0.008667;BHAR −0.009088→−0.009117 / 毛 BHAR −0.005610→−0.005640;skew-adj t(毛)−7.1431→−7.2579;DSR proxy 6.45e-19→2.59e-19;postpone 920→896、极端案例 4→3(000658.SZ:20011126 退出样本)。

## 6. 确定性硬项 + post-ST 新基线 sha 登记

**规范化规则**:`norm_sha256` = 产物 JSON 剔 `diagnostic` 块后的 sha256(diagnostic.reason 为各跑自由文案,B 臂与 r2 文案不同乃预期;其余全部键参与摘要)。raw_sha256 并记。

**确定性硬项:三对修复臂 B 臂 vs r2 双跑 norm_sha256 全等 = {#4: True, #2b事件版: True, #2b策略版: True}**。

| 跑 | norm_sha256(剔 diagnostic) | raw_sha256 |
|----|---------------------------|------------|
| a4_legacy | `0b720c911260b541a820f147a799838bebb7c63374f3b787c06ba3fcfa0d1412` | `ccd033e5…` |
| **b4_eventday(=post-ST 新基线 #4)** | **`eb6f01d43dcbec7f5ccaa99a3b96c4b09a80b024524bb67067c2e160601e190c`** | `11ba52e8…` |
| b4_eventday_r2 | 同上(全等) | `005a8cba…` |
| a2e_legacy | `716e715c05fca1399c854de887e355c91c26b33c800a5082f25971bfa30248a8` | `de8d1700…` |
| **b2e_eventday(=post-ST 新基线 #2b 事件版)** | **`b7d0879eeadcbcd182931d64a58da6dcb6c721d46974b67e443603def4c9450a`** | `479e47b5…` |
| b2e_eventday_r2 | 同上(全等) | `0c72ce0b…` |
| a2s_legacy | `5395f80dbc254c4007a27dc38a011795b160a6bef1b9d3db47bd239c9cec4175` | `d787e4ab…` |
| **b2s_eventday(=post-ST 新基线 #2b 策略版)** | **`7dbd9006b354c94b3e411526bd6ef579125f5733f41e2acf621a1a13c0ad4a4b`** | `eacc1607…` |
| b2s_eventday_r2 | 同上(全等) | `eb229875…` |

**旧闭卷 sha 永久保留、不被取代**:#4 = 闭卷产物 result.json sha `b48d2941…` / 台账 exp5 result_json sha `c010ce9d4d235424eb34548c5647b8381db0758fd68e52a355ad079787241c8f`;#2b = 事件版产物 `0565b11520672acb…` / 策略版产物 `fbf4d829222b2e44…` / 台账 exp3 result_json sha `e3d2aef92bd47c6b…`。已闭卷两案不重跑不改判,缺陷登记走 ⑤ 附注(b)(c)(`hardening-item5-addendum-acceptance-2026-07-12.md`)。

## 7. 产物与备份

- 持久盘 `/root/s3hard3/`:九跑 `*.json` + `*.log` + `progress.log` + `diff_4/2e/2s.json(.log)` + `baseline_shas.json` + `post.log`;备份 `/root/s3hard3_backup/`。
- 跑批脚本 `/root/s3hard3_runner.sh`(串行+flock 单例)+ post 守护 `/root/s3hard3_post.sh`(盯 ALL DONE 自动 diff/sha/备份)。

## 8. 结论

③ 验收标准逐项达成:全量重算清洗段(#4/#2b 三份)、旧 vs 修复受控语义 diff 逐项(事件计数/剔除计数×原因×年份/板块分层/统计事实)、影响以实测陈述(§4/§5,未以预判代实测)、diff 产物即 post-ST 新基线且 sha 已登记(§6,确定性双跑硬项过)、旧闭卷 sha 永久保留(§6)、tie 钉死效应与 ST 效应分开归因(§4/§5,人拍 A)。**待架构窗口验收;④ 共享主干施工的验收基线 = §6 三份 post-ST 新基线(逐字节)。**
