# exp19 dividend_surprise 冻结与最小适配验收

日期：2026-08-06（UTC+8）  
停止点：行为验收；未生成 exp19 研究 manifest，未读取正式收益，未执行 §7，未 persist。

## 1. 授权与冻结

- 人的密封原文：`正，把握度60%`。唯一解释为主窗 `[0,+4]` 合并 signed、市场调整后
  CAR 方向为正；仅押方向，不押幅度或统计显著性。只绑定终版 PAP digest
  `4d5e6840f818c21dfd94a414e31133d79b0e83e8dc590a3b739cdf391e8b60b4`。
- 冻结与适配令：`dividend-surprise-freeze-adapt-order-2026-08-06.md`，F 条先行 commit
  `865add84498df6d260c3c22cf9d81dc5d49df5b2`；人另行明确批准推送后再施工。
- 冻结前 exp19=`registered`、结果三槽空、addendum=0、零 exp19 研究 manifest；台账
  `26=registered8/frozen2/done14/closed2`。终版文件 SHA、canonical 重算与令定 digest
  三者逐字相等。源级 snapshot375 三处 digest 均为
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，qbase 向量
  `dividend=17`，且无 taosha 半，身份确为源级锚。
- 使用 `taosha_app` 同连接单事务：`FOR UPDATE` 重断言 → 写入终版 canonical 原文 →
  `freeze(19)` → 一次 COMMIT。`frozen_at=2026-08-06 17:21:15.889471+08`；载荷
  MD5=`7e3a9aa7b182ac9799cf0106a8f15426`，parsed equality 成立；不可变探针被铁律④拒绝，
  回滚后 MD5 不变。台账恰迁一行至 `26=7/3/14/2`。

## 2. 最小适配触碰面与工程结构

施工 commit=`b623f6dbdd5c37c020b7ce94c94a0070db19450e`，7 文件、735 行新增；统计内核
`runner.py`、清洗内核、既有 reader/experiment、PAP schema 与全部 SQL 均未改。

- `compute/dividend_surprise_rules.py`（169 行）：纯函数、Decimal；实现 A1/B2-P1/C1/D1/E1、
  相邻财年、恰等 ±50% 入方向、三类基数异常分计、后续阶段零回填、重复事件键整组剔除、
  五条守恒与确定性 selection SHA。
- `reader/dividend_surprise.py`（56 行）：只读 snapshot 视图最小列面，从连接建立起注入
  `default_transaction_read_only=on`。
- `harness/run_dividend_surprise_study.py`（181 行）：PAP digest 三重绑定；11 个
  `engine_params` 键、4 个 `signed_ar` 键及 `axes.direction=[up,down]` 缺/多双向
  fail-closed；snapshot375 只允许 recon，正式模式拒绝冒充；台账身份水印只从 ledger 注入。
- `engine/report_dividend_surprise.py`（51 行）：真实 StudySnapshot 与 `llm/prescreen` 水印
  缺失即拒；通用 `report.py` 仅增加 7 行显式路由，既有路径缺键零变化。
- 两套攻击 fixture 分别 98/173 行。所有新增生产文件均不超过 200 行，职责单一。

## 3. 规则复现与确定性

专项 fixture 本地与阿里云钉版容器均为：规则 `13/13 PASS`、适配 `26/26 PASS`。攻击面覆盖：

- E1 初始行缺失/多行/flag1/仅后续阶段，实施值禁止回填；
- C1 `prior=0`、上年缺失、上年不可判与 `current=0 → -100%`；
- D1 Decimal 恰等 +50%/-50% 入 up/down；
- 非相邻年度禁止替代、B2-P1 起点、事件键重复/方向冲突整组剔除、乱序确定性；
- PAP/engine/signed/方向轴篡改、snapshot375 冒充、删除身份水印及递归 verdict 唯一。

snapshot375 两次只读 recon JSON 逐字节相同，SHA 均为
`a9591db0ceb250f8e15bc482d40d6fde4e6d0760a76386a067f049fef481bf7a`；selection SHA 为
`985e2312a7de4aca489a888647913e15fbff914899dd3f8459e5d489304a2e6b`。冻结参考精确复现：

- 视图输入126,900行 → 年度范围97,543行/52,027组 → E1严格初始26,467组；无初始
  25,560组，其中25,558组虽有后续值也零回填；
- 全期六分：up2,679/down3,436/inside8,596/zero_undefined6,501/
  missing_prior2,451/unresolvable_prior2,804，合计26,467；恰等边界698；
- B2-P1六分：up2,253/down2,802/inside7,089/zero_undefined5,491/
  missing_prior1,403/unresolvable_prior12；候选5,055；恰等边界574；
- 事件键重复0、方向冲突0，最终事件5,055（up2,253/down2,802）；五条恒等式全真。

## 4. 回归、启动期失败与停止线

- 本地 29 个离线验收入口全部通过，含全部既有实验 rules/adapter/engine、冻结不可覆写、
  三窗口与敏感性；阿里云数据库套件：状态机 `46/46`、PAP gate `23/23`、addendum
  `14/14`、镜像 `11/11`、血缘 `24/24`、StudySnapshot probes `19/19`、集成 `7/7`。
- 钉版镜像 `shuheng-quant:579a354`（image ID
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`）挂当前
  commit 只读运行，默认合成 e2e 双跑 result SHA 均为历史基线
  `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`。
- 三次非研究启动期失败均保留：首次直接脚本入口缺仓根模块路径；改模块入口后容器 localhost
  与宿主数据库隔离；快照探针的非 root 用户无权读只读挂载 `.env`。前两次均在首次数据库
  连接成功前停止，第三次在探针启动期停止；分别改用 `python -m`、Linux host network、仅探针
  容器 root 读取同一 `.env` 后通过。三次均未改代码、未产研究结果、未写数据库。
- 验收后 exp19 仍 `frozen`，冻结时间不变，`result_json/done_at` 为空；台账仍
  `26=7/3/14/2`；StudySnapshot 仍19行、max=375，集成测试复用既有 manifest，未新增行。
  零 exp19 研究 manifest、零正式收益、零 §7、零 persist。

## 5. 证据与结论

阿里云证据目录：`/root/s19freeze/` 与 `/root/s19adapt/`。适配包含冻结日志、两次 recon、
专项与数据库套件日志、合成 e2e、只读状态读回、秘密扫描和 SHA 清单；13 类秘密扫描
`TOTAL_HITS=0`，`SHA256SUMS -c` 全部通过。

冻结凭证、A1/B2-P1/C1/D1/E1 行为、signed 单判决适配、身份水印、snapshot375 对账、
确定性与零回归均通过。当前停在行为验收点；下一步只能在独立外审通过并获人另令后生成
exp19 自有研究 manifest 与执行 §7 单次正式运行。persist 继续单独授权。
