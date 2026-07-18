# exp8 运行后外审两窄修 · 验收档(2026-07-18)

- **令源**:`taosha/docs/limit-open-postrun-review-order-2026-07-18.md`(原文即口径,留痕 commit `854e25a`);施工基线=外审确认的两台 HEAD `6f7bfd3`。
- **本轮性质**:报告与测试证据修正。**未重跑研究、未重建 manifest、未修改原始 result、未触碰台账**;完成后停交验点,**未 persist**。
- **施工 commit**:`6c64849`(report.py + verify_pap_gate.py + verify_limit_open_engine.py,三文件 +162/−10)。

## 1. 窄修一:正式报告标识修正(`taosha/engine/report.py`)

最小参数化,只动 `render()` 横幅/快照两行的分支逻辑:

- `result.audit` 含 `limit_open_selection` 键(**在场=键在场**;present-but-None 同走 exp8 路径撞 fail-closed,不得静默落回合成)→ 标题固定
  `淘沙 · 事件研究体检报告(exp8 一字涨停开板·事件版)`,快照行直读
  `audit.study_snapshot.snapshot_id` + `audit.study_snapshot.digest` 真锚。
- 缺 `study_snapshot`/非 dict/缺 `snapshot_id`/缺或空 `digest` → `SystemExit` fail-closed,禁回退合成标题或 PAP 需求字典。
- 其余路径(默认合成/#2b 专属)分支原文原样保留,渲染逐字节不变(证据 §5)。

## 2. 更正版报告(aliyun `/root/s8run/`)

- **原始产物零触碰**:`report_exp8.txt` 未覆盖未删除,SHA256 仍 `278456d5bad1e88055114b2dd3e83c36e3fca19d035383640185f781687c3e99`;`result_exp8.json` 仍 `282bda4f…18a10`;`run8.log` 仍 `d2940c31…98c76`。
- **更正版生成方式**:仅由已验收 `result_exp8.json` 经 `report.render()` **确定性重渲染**(双渲染逐字节一致实证);不重跑事件生成/收益/CAR/检验,不改 result,不改 manifest,不从日志拼接。
- 落盘 `/root/s8run/report_exp8.corrected.txt`,SHA256 = `5fb87ebfc9a69d33cf5d701e4e434db87968c76149ed62a854bba15d65d2f914`。
- **逐行 diff 程序化断言**:两文件同 170 行,差异行号恰=**{1(标题行), 2(快照展示行)}**,其余 168 行逐字节相同,**零第三处差异**(第三处差异即停的闸未触发)。行 2 现显示
  `快照批次: StudySnapshot=121 digest=21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd  |  基准口径: market(口径②)`。
- 全文 diff 见交付包 `report_exp8.diff`。

## 3. 窄修二:PAP gate R6 假绿灯修正(`taosha/experiment/verify_pap_gate.py`)

**旧假绿灯机理(坐实)**:R6 硬编码 exp8;exp8 真冻结后,升级 UPDATE 因 `status='registered'` 命中 **0 行**(空打),随后冻结 UPDATE 撞 `硬化①: frozen_at 仅可随 registered→frozen 迁移一次性写入` 类无关异常,任意 `psycopg.Error` 均被记 PASS——错误拒绝原因,证不了声称的攻击路径。

**修正后 R6(aliyun 实测,动态标本=exp9)**:

1. 动态标本=当前 `status='registered'` ∧ `pap_legacy_registry` 物化在册(复用 F1 选取逻辑),独立 `SAVEPOINT r6`;标本缺失时 fail-closed(不得空转计 PASS)。
2. **证据①注入**:升级 UPDATE 命中=**1 行**;注入后标本仍 `registered`;PAP 实含 `pap_schema_version=2` + `analysis_type='strategy'` + 合法 `close_to_next_open` 结构(逐字段==SE_C2N)→ 全 True。
3. **证据② registered→frozen 攻击**:被 `_pap_freeze_gate` 拒,拒绝原文=
   `修法#1: legacy 实验只允许事件版冻结与运行(升级 schema 后 analysis_type 须=event;策略须 INSERT 新实验行)`。
   **PASS 判据=错误文本必须包含「legacy 实验只允许事件版冻结与运行」**;frozen_at 不可改/status 非法迁移/命中 0 行/其他任意库异常均不算 PASS(判据代码化=`_r6_accept`)。
4. **证据③回滚零残留(直接证明)**:ROLLBACK 后标本 status/PAP 逐字段==原值(True/True);台账总行数 25→25;exp8 `(status, result_json IS NULL, done_at IS NULL)` = `('frozen', True, True)` 前后不变;探针零残留(Z1 另证 probe=0/total=25)。
5. **证据④负对照(旧假绿灯路径逐字重放,SAVEPOINT 回滚零副作用)**:对 exp8 的升级 UPDATE 命中=**0**(坐实旧探针空打);随后异常原文=`硬化①: frozen_at 仅可随…`,**被新判据拒绝**(`_r6_accept`=False)→ 证明"任意其他数据库错误不得被记作 R6 PASS"。
- 全套 23 项逐项输出=交付包 `verify_pap_gate_23items_aliyun.txt`,**23/23 PASS**(R6 四条证据行随项打印)。

## 4. 攻击性验收八断言 → 实测映射

| # | 断言 | 落点 | 实测 |
|---|------|------|------|
| 1 | exp8 正式结果渲染真实标题,零"切片2合成验收" | engine 证⑪ | PASS(标题逐字节断言+零命中) |
| 2 | 报告直接显示 manifest 121+真实 digest,零 `snapshot_batch` 需求字典 | engine 证⑪ | PASS(快照行逐字节断言+需求字典零渲染) |
| 3 | 缺真实 `audit.study_snapshot` → fail-closed | engine 证⑪ | PASS(缺块/非dict/缺id/空digest/present-but-None 五路全 SystemExit) |
| 4 | 默认合成报告修改前后逐字节一致 | engine 证⑪+e2e | PASS(标题+快照行逐字节断言;e2e 两台四跑 sha `3116ba9b…` ==历史基线) |
| 5 | #2b 专属标题修改前后逐字节一致 | engine 证⑪ | PASS(标题+快照行逐字节断言) |
| 6 | R6 PAP 注入真实命中 1 行 | pap_gate R6 证据① | PASS(rowcount==1 直接断言) |
| 7 | R6 只接受预期 `_pap_freeze_gate` 拒绝原因 | pap_gate R6 判据+证据② | PASS(`_r6_accept` 文本包含判据) |
| 8 | 任意其他数据库错误不得记作 R6 PASS | pap_gate R6 证据④负对照 | PASS(旧假绿灯错误文本被判据拒) |

另加结构性断言:exp8 路径除标题行+快照行外与既有渲染**逐行相同**(改动面=恰两行,窄修一要求 6 的 fixture 级保证)。

## 5. 回归(两台)

- `verify_limit_open_engine`:102→**116/116**(证⑪ +14)两台;`verify_limit_open_rules` 40/40;`verify_limit_open_adapter` 24/24;三窗 5/5;holder 规则 81/81;适配 10/10;敏感性 6/6(两台)。
- aliyun DB 套件:状态机 46/46;**pap 硬门 23/23**;addendum 14/14;镜像 11/11;血缘 24/24;冻结口径运行时探针 PASS;集成 7/7(**S6 双跑 sha `63e2c9fc…` ==基线**)。
- 合成 e2e 官方 harness:AWS 双跑+aliyun 双跑全=**`3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`** ==历史基线 → 默认合成路径**逐字节零回归实证**。
- 改动面=`git diff --stat 6f7bfd3..HEAD`(见交付包):仅 report.py/verify_pap_gate.py/verify_limit_open_engine.py+本轮文档,无任何收益/CAR/显著性代码。

## 6. 重新取证九件(交付包 `~/shuheng/s8_narrowfix_delivery_2026-07-18/`,AWS)

1. `result_exp8.json` SHA 仍 `282bda4f…`✅ 2. `report_exp8.txt` SHA 仍 `278456d5…`✅ 3. `report_exp8.corrected.txt` SHA `5fb87ebf…`✅ 4. `run8.log` SHA 仍 `d2940c31…`✅ 5. `report_exp8.diff` 逐行 diff✅ 6. manifest 121 三处读回=`db_readonly_queries.txt`:权威(taosha.study_snapshot 121)/镜像(qbase.study_snapshot_mirror 121)/发布凭证(qbase.study_snapshot_publication pub_id=25 attested)三处 digest 全=`21e9095e…3efcd`,两侧 content md5 均 `aa940b61…`✅ 7. exp8 仍 frozen、result 槽空、done_at 空✅ 8. 台账仍 25 行(registered 17/frozen 3/done 4/closed 1)✅〔勘误 2026-07-18 深夜:原误写 18/3/3/1,该分布属 `pap_legacy_registry.status_at_migration` 历史迁移分布,非当前台账;详见 §10〕 9. 秘密扫描 13 类全部交付件 TOTAL_HITS=0 + `SHA256SUMS` 全清单(传输后 AWS 侧 `sha256sum -c` 全 OK)✅。

## 7. 范围声明

- 触碰:`taosha/engine/report.py`、`taosha/experiment/verify_pap_gate.py`、专项 fixture `taosha/harness/verify_limit_open_engine.py`、本验收档、`ops/STATE.md`、aliyun 新增 `/root/s8run/report_exp8.corrected.txt` 与证据目录 `/root/s8nf_evidence_2026-07-18/`(均为新文件)。
- 未触碰:`result_exp8.json`/原 `report_exp8.txt`/`run8.log`/manifest 121/PAP v3/exp8 冻结载荷/qbase·taosha 生产事实与批次/台账状态·result 槽·addendum/其他实验结果/任何收益、CAR、显著性计算代码。DB 访问全部只读(R6 探针在 SAVEPOINT 内、回滚零残留有直接证明)。

## 8. 观察记录(不修,留痕)

- `verify_pap_vs_spec` 以 `KeyError: 'synthetic_smoke'` 退出(exp7=SMOKE 家族不在其 SPEC6 对照表)——**既有行为**,该件不在全家福清单,本轮零触碰;是否补 SMOKE 豁免待人裁,不借本轮顺手修。

## 9. 交验点

两窄修+攻击性验收+回归+重新取证全毕,**停交验点,未 persist**。待外审核对本证据包后另行下达 persist 令。

## 10. 勘误(2026-07-18 深夜,外审指正):台账状态分布留痕错误

- **性质**:纯事实留痕勘误。零代码 / 零重跑 / 零重渲染 / 零 DB 写 / 原始 result·report·log 零触碰;原证据包及 `SHA256SUMS`、`SHA256SUMS.all` 不改不作废。
- **错误**:多处将 **18/3/3/1**(registered 18/frozen 3/done 3/closed 1)写成当前台账分布。该分布实为 **`public.pap_legacy_registry.status_at_migration`(legacy registry 历史迁移分布)**;当前 **`public.experiment`** 台账正确分布 = **registered 17 / frozen 3 / done 4 / closed 1**(共 25 行,外审直接只读查询与我方 2026-07-18 22:33 复核一致)。
- **错误位置**:①`ops/STATE.md` 07-18 傍晚条目(已改正+作废标注);②本档 §6 第 8 件(已改正);③交付包 `README.txt` 第 18 行与 ④`db_readonly_queries.txt` [3] 节标题预期文字——二者为封存原件(在 SHA 清单内)**不改动**,以勘误附页为准;⚠该文件 [3] 节**原始 SQL 输出本身正确**(17/3/4/1),错的只是标题预期文字。
- **原因**:取证文字预期值误从 legacy registry 迁移分布取数,未与同文件 SQL 实际输出逐字核对,README/验收档/STATE 照抄同源扩散。
- **交付索引更新**:交付包新增两件——**`ERRATA_ledger_status_distribution_2026-07-18.txt`**(勘误附页:错误位置/原因/正确 SQL 结果/两种分布表名对照,SHA256=`1ab84bb67e54d33e500df805d1d99d649d4cfc738d8b52dc95d75f1dabbcda85`)+ **`SHA256SUMS.errata`**(仅覆盖新增勘误件)。README 九件对照第 8 条以勘误附页为准。勘误后原包 `sha256sum -c SHA256SUMS.all` 复核仍全 OK。

## 11. persist 闭卷(2026-07-18 深夜,人正式批准令原文即口径)

外部复核确认勘误闭合+两窄修及运行结果验收全部通过后,人正式批准 exp8 persist,按令四节边界执行完毕:

- **前置断言(只读,任一不符即停)全 PASS**:exp8 仍 frozen、result_json 与 done_at 空;台账 25 行=17/3/4/1;唯一结果来源 `/root/s8run/result_exp8.json` SHA256=`282bda4f…18a10` 全等;原报告 `278456d5…`/修正版 `5fb87ebf…`/run8.log `d2940c31…` 全等;manifest 121 权威·镜像·publication attestation(pub_id=25)三处 digest 全=`21e9095e…3efcd`;冻结 PAP canonical digest(引擎 `canonical_pap_sha256` 对 DB pap_json 重算)=`afd8443a…addb`;result 内顶层唯一 verdict=NOT_SIG、事件 6,005、N_valid 3,742、audit.study_snapshot=121+digest、bias_statement.pap_sha256==PAP digest。
- **执行**:仅既有状态机 `ledger.start_running(8)`→`ledger.finish(8, result)`,同连接同事务末尾一次 COMMIT,身份 taosha_app;result 唯一来源=上述已验收原文件;零重跑/零重生成/零改写/零补键/零旁路 SQL;不新增 experiment 行。脚本+日志留档 aliyun `/root/s8persist/persist_exp8.py`+`.log`。**COMMIT @2026-07-18 22:47:22+08**。
- **persist 后核验(只读)全 PASS**:exp8=done,done_at=2026-07-18 22:47:22.536829+08,顶层 verdict=NOT_SIG;库内 result_json 与原文件 **parsed_equal=True**,canonical SHA(排序紧凑 JSON)双侧同=`671ab272ea00c509397ffd8087c63d61dcd281bc1704430e43f8b22e61b2d436`,库侧 jsonb::text SHA=`a96beb30fcc3d4fa6e7122d741816b7ddf840b983eaf431f9a445f819ba7a856`;结构完整=manifest 121/事件 6,005/N_valid 3,742/三窗(main[0,+4] CAAR −0.014818、secondary[0,+19] 带不判决注记、robust[0,+59])/诊断双轴 diagnostic_dimensions.dims={st:{ST,non_ST}, listing_age:{seasoned,recent_listing}}/NOT_FOR_VERDICT 块 17 处全标注/**顶层外 verdict 键=0(唯一判决在顶层)**;台账 25 行,分布严格=**registered 17 / frozen 2 / done 5 / closed 1**;manifest 121 三处 digest 不变;四件产物 SHA 不变;两台生产 git 无代码改动、工作区净。
- **终态解读边界(闭卷结论固定,人令原文)**:exp8 一字涨停开板事件版判决为 NOT_SIG。主窗市场调整后 CAR 方向为负,与冻结前预判同向,但唯一权威判据 ADJ-BMP 不显著。朴素 t、Corrado、日历时间法的负向名义显著及次级、稳健窗负值均属 NOT_FOR_VERDICT,不得改读为显著结论。该实验效力仍为 llm/prescreen,不得写成 full 证据。
- **密封开封对照(令第九条,首条校准读数入册;预判原文不得修改、重述或替换)**:冻结前预判原文=**"主窗市场调整后CAR为负,把握度60%"**,绑定 PAP v3 digest `afd8443a…addb`;实测主窗 CAAR=**−1.482%,方向命中**,但 ADJ-BMP **−0.473 不显著**,终态=**NOT_SIG**。
- **exp8 正式闭卷,不再追加复核、重跑或施工。**修正版报告作为独立验收产物保留,未写入、未反向改造 result_json。
