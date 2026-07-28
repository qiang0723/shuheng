# exp24 sox_spillover · manifest + §7 单次正式运行交付（2026-07-28）

## 结论

**§7 单次正式运行成功，停在取证点。** 顶层判决为 `NOT_SIG`：主窗 `[0,+4]` signed CAAR=`0.0033051753367197385`（约 `+0.331%`，N=`13,656`），唯一权威统计量 ADJ-BMP=`0.5646755577681967`，双侧不显著。exp24 仍为 `frozen`，`result_json/done_at`为空；本轮未 persist。

## 1. 运行前阻塞与最小修复

人于本轮明确：**“你作为施工方，是有权修改代码的”**。据此，`sox-spillover-s7-json-key-blocker-2026-07-28.md` 所记正常施工授权疑义闭合；未扩大统计或事件口径。

manifest 248 recon 首次输出失败的根因为：`selection_audit.pool_members_by_event_date` 使用 `datetime.date` 字典键，`json.dump(default=str)`不能转换对象键。修复 commit=`f3819494ca51176450ba5e4df35f87bacffec924`：

- 只在 driver 的 JSON/报告审计边界把日期键确定性转换为 ISO `YYYY-MM-DD`；
- 核心 `sox_spillover_rules.py` 仍保留 `date` 键，事件、漏斗、统计与PAP零改动；
- 非 `date` 键 fail-closed；fixture 增加真实日期键转换与完整审计块 JSON 序列化攻击。

验收：exp24 rules=`23/23`、adapter=`34/34`；既有离线全家福全绿；合成 e2e SHA=`3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`，与历史基线逐字节一致。

生产镜像严格来自该 commit：`shuheng-quant:f381949`，image ID=`sha256:ebb3a1735660e86acf49c9da48acc3901fee33283f23dacb97e98ea87dc2185d`，`amd64`、用户=`shuheng`。

## 2. 钉批复现与研究 manifest

- snapshot 247 钉批复现：最终事件=`19,258`；selection SHA256=`7a7840e596b755746fe5f038928fad622e2df83a32ba64d6105e9a9513b2acee`；
- exp24 专属研究 manifest=`248`，由 source snapshot 247 一次生成，未重复建；
- digest=`c82d8a82eb69331799402ce9f025c35574a27ba8b3d6f2051dfaa1b8c881250a`；权威行、qbase镜像、publication attestation 三处一致；
- 七个实际消费键：`daily=6 / adj_factor=7 / stock_basic=6 / namechange=7 / trade_cal=10 / sox_daily=13 / sw_member=14`；
- `verify_manifest_lineage=24/24 PASS`，`verify_snapshot_mirror=11/11 PASS`；
- manifest 248 recon 成功完整落盘：SOX `3,395`行 → 触发`314`（up161/down153）→ 映射日`301` → D4碰撞`9`日剔`22`触发 → 存活触发日`292`（up150/down142）→ A股事件`19,258`，重复键0；日期审计键292项全部为ISO字符串。

## 3. §7 唯一一次正式运行

- 运行窗口：`2026-07-28 22:14:11+08` 至 `23:05:05+08`；
- 只启动一次，RC=`0`，未自动重跑；运行镜像与代码 commit 如§1；
- PAP digest断言：`be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`；
- 正式事件集=`19,258`，与停止线精确相等；有效存活 `N_valid=13,703`，剔除`5,555`，剔除率=`0.2885`，`>5%`告警如实报告；
- 相关折算：ρ̄=`0.006340770520612997`（行业内 `18,498,121` 对），Kish=`155.9263429006248`，KP=`154.9376497421735`；
- 主窗 `[0,+4]`：CAAR=`0.0033051753367197385`，N=`13,656`，ADJ-BMP=`0.5646755577681967`，`NOT_SIG`；
- 次级 `[0,+19]`：CAAR约`-0.00056`，ADJ-BMP约`-0.030`；稳健 `[0,+59]`：CAAR约`-0.00583`，ADJ-BMP约`-0.260`，均 `NOT_FOR_VERDICT`；
- 辅助方法：朴素t=`5.923`名义显著，但Corrado=`0.906`、日历t=`-0.916`不显著且日历方向相反；全部NFV，不改变顶层判决；
- `effect_alignment=ALIGNED`，角色=`CONTEXT`，不产生或改变判决；
- result递归唯一 `verdict` 键=1；bias_statement锚定冻结PAP digest；manifest 248锚在场。

人的冻结预判原文为“同向，把握度60%”。实测主窗 signed CAAR 为正，但ADJ-BMP不显著；正式密封开封对照与校准册入册留待 persist 终令，本交付点不改写预判原文、不提前闭卷。

## 4. 取证与停止线

阿里云内部证据包：`/root/s24run/delivery/`，`SHA256SUMS -c`全过。三件原件：

- `result_exp24.json`：`991016a0c43b26639498e2f377d8597b2ea1e4589efb7de118c150e50dc4fdb8`
- `report_exp24.txt`：`3e04751c24ebb3f2829d52009942ec53837556174c35eea5f3759980381239b8`
- `run24.log`：`28ab31228f27023b6821978f1ba760d4e05856435e440f3c023bdb2b80c750ef`

13类秘密扫描 `TOTAL_HITS=0`，原件未修改。运行后只读核验：

- exp24=`frozen`，`frozen_at=2026-07-28 19:43:43.332816+08`不变，`result_json/done_at`为空；
- 台账25行=`registered 12 / frozen 3 / done 9 / closed 1`；
- study_snapshot共13行、max=248；manifest 248三处digest不变；
- 生产代码与本地代码同步，工作树净。

**停止线：本轮不授权、也未执行 persist。** 取证交人和Fable复核后，persist须另行终令。

## 5. Fable 外审范围

按分级一次出清：

1. 核 `f381949` 是否严格止于审计 JSON 日期键边界及fixture；
2. 核交付档内 manifest 248、漏斗、result关键值与三件SHA的自洽性；
3. A级（改变判决/样本/血缘/正式产物）才阻塞persist；B级表述项一次列清，C级默认不扩施工。

## 6. persist 闭卷（2026-07-28）

人于取证与Fable复核完成后明示“执行”，终令留痕见 `sox-spillover-persist-order-2026-07-28.md`。

外审唯一B级项已在既有产物内指认闭合：`result.n_valid=13,703`、`result.car.main_window.n=13,656`；`result.per_tau.by_tau`及正式报告逐日AR段已披露τ0–τ4样本量依次为`13,703/13,690/13,689/13,680/13,674`。完整主窗沿既有 `_car_test` 口径，任一τ缺失即不进入CAR截面；不同τ缺失事件的并集形成完整主窗差额47。未新增计算、未改result、未重跑。

执行前只读断言`22/22 PASS`。第一次操作脚本在数据库连接前因把 `audit.study_snapshot` 误断言为“只能含snapshot_id/digest两键”而停止；原件还含合法`content`向量。失败脚本与日志原样保留，随后再次执行同一套前置只读断言仍为`22/22 PASS`，证明数据库与产物零变化。断言仅收窄为逐字段核对snapshot ID和digest后，事务内`FOR UPDATE`断言`7/7 PASS`。

实际数据库写事务只有一笔：以`taosha_app`同连接执行`start_running(24)→finish(24,已验收result原件)→一次COMMIT`，`done_at=2026-07-28 23:25:53.284244+08`；零研究重跑、零result改写、零旁路SQL、零新增行。

persist后只读核验`15/15 PASS`：

- exp24=`done`，顶层 verdict=`NOT_SIG`，`frozen_at`保持`2026-07-28 19:43:43.332816+08`；
- 库内result与原件`parsed_equal=True`，canonical双侧SHA256=`3204cdbccb9b318c47179f944af9b2745dcad43d53eef4eb2233146d64859446`，库侧`jsonb::text` MD5=`fe01d0ae4998c318ce7446412f3ac639`；
- 台账仍25行，分布=`registered 12 / frozen 2 / done 10 / closed 1`，恰迁exp24一行；
- PAP canonical、manifest 248三处digest、result/report/log三件原件SHA全部不变；
- persist脚本与日志已镜像进`/root/s24run/delivery/`，独立`SHA256SUMS.persist -c`全过；第一次失败痕迹未覆盖、未删除。

闭卷固定读法：人的冻结预判原文“同向，把握度60%”仅绑定PAP digest `be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`；实测主窗signed CAAR=`+0.3305%`，方向命中，但ADJ-BMP=`+0.565`不显著，终态`NOT_SIG`。校准册第六条据此记为方向命中，六条方向读数为3命中/3未命中。不得认定存在可靠传导效应；朴素t/Corrado/日历法均为NOT_FOR_VERDICT。效力保持`human/full`，半PIT成分语义、剔除率28.85%告警和低功效预注册边界如实保留。

**exp24正式闭卷；不再追加复核、重跑或敏感性分析。**
