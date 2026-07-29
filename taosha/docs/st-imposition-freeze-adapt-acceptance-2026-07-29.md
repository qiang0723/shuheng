# exp568 `st_imposition` 冻结与最小适配验收（2026-07-29）

## 1. 结论与停止线

exp568（`delist_warning_financial` trial 2）冻结及最小适配通过，停在行为验收点。
PAP digest=`56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`；
人的密封预判原文为“负，把握度60%”，仅押主窗方向。

本单元未生成 exp568 正式研究 manifest，未读取正式收益，未执行正式事件研究，未
persist。下一步须经外部只读复核后另行授权 manifest 与 §7 单次正式运行。

## 2. 冻结凭证

- 冻结前 exp568=`registered`、结果槽空、零 manifest；终版文件 SHA、canonical 重算与
  人令 digest 三者一致。
- `taosha_app` 同连接单事务更新终版载荷并执行 `ledger.freeze(568)`，一次 COMMIT；
  `frozen_at=2026-07-29 19:23:34.970260+08`。
- 冻结后 DB canonical 与文件一致，`parsed_equal=True`，载荷 MD5=
  `cb7fbc6dad74fad0432376e2df9f4497`；台账 26 行由 `11/2/11/2` 恰迁为
  `registered 10 / frozen 3 / done 11 / closed 2`。
- 冻结证据在阿里云 `/root/s568freeze/`，独立回执见
  `st-imposition-freeze-receipt-2026-07-29.md`。

## 3. 最小适配与代码边界

生产触碰面：

- `compute/st_imposition_rules.py`：154 行纯函数，复用 exp12 名称定级、段折叠和聚合，
  仅实现普通→ST反向事件规则；
- `harness/run_st_imposition_study.py`：223 行 driver，PAP 全键消费、exp568/family/trial2
  身份 fail-closed、recon 与正式模式分离；
- `engine/report_st_imposition.py`：48 行专属报告模块；`report.py` 仅接入标题和选择审计
  两个分支，避免继续放大单文件；
- `run_st_removal_study.py` 仅把 namechange recon reader 改为公共函数名，exp12 行为不变；
- 两件专项 fixture；统计内核、清洗、收益计算、qbase 视图及数据库 schema 零改动。

提交链：`1b6c265`（最小适配）→`efd6d63`（事件/证券双口径审计）→`f1118d1`
（PAP gate 零残留断言动态化）。最后一笔只修测试可靠性：旧 Z1 把台账总行数写死为 25，
合规迁移后实数为 26；现改为测试前后行数相等，不改变生产判据。

family trial 纪律：driver 只接受 exp568、`family=delist_warning_financial`、
`family_trial=2`；trial 由冻结台账注入且不进 PAP digest，runner 实测双侧 α=`0.025`。
PAP、CLI 与 driver 均无覆盖入口。

## 4. 攻击 fixture

本地 Python 3.12 与阿里云钉版 Python 3.14 均通过：

- `verify_st_imposition_rules`：`16/16 PASS`。覆盖普通→带星/不带星 ST、所有反向或退市
  非目标转换、mixed 孪生段、锚缺失/冲突、ann>start、研究期两端、重复事件键全剔、
  漏斗与组成双恒等式、确定性双跑；
- `verify_st_imposition_adapter`：`23/23 PASS`。覆盖终版 digest、运行时 trial 键不进 digest、
  engine_params 缺/多/篡改拒绝、EventRow、trial2 α、llm/prescreen 水印、exp568 标题、
  NFV 组成审计及 exp12 报告分支零回归；
- exp12 同源回归：rules `42/42`、adapter `43/43`。

## 5. batch7 recon

阿里云冻结身份下只读 current namechange 视图双跑，两个完整 JSON 逐字节一致，SHA256=
`9bc67f1f8434725847357a38d22bbe2e0521f33ca069090dd7e2624c3bc5f871`。

漏斗精确复现：

`18,868 输入行 → 17,133 段 → 11,601 有前段转换 → 1,277 普通→ST候选 →`
`状态不可判 1 / 锚缺失 510 / 期外 1 → 765 事件 / 646 证券`。

锚冲突、ann>start、重复事件键均为 0；漏斗恒等式成立。组成审计为带星 ST
`560/765=73.20%`、不带星 ST `205/765=26.80%`，组成恒等式成立，全部结构化
`NOT_FOR_VERDICT`，没有分层 CAR、显著性或 verdict 字段。所有参考差额均为 0。

## 6. 全家福、零回归与最终状态

- 阿里云数据库套件：状态机 `46/46`、PAP gate `23/23`、addendum `14/14`、
  snapshot probes `19/19`、镜像 `11/11`、血缘 `24/24`、集成 `7/7`；
- 其余离线全家福全部通过，包括 exp8/10/11/12/13/20/24 及 holder 系列；
- 合成 e2e 在本地只读挂载 Docker（`shuheng-quant:local`）与阿里云钉版 Python 各双跑，
  四份 result SHA256 均为历史基线
  `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`。
  macOS 系统外的临时 Python 3.12 数值序列化不作为生产字节基线；Docker/Python 3.14
  才是权威运行环境。
- 最终只读读回：exp568 仍 `frozen`、`frozen_at` 不变、`result_json/done_at` 为空；
  台账仍 26=`10/3/11/2`；当前 14 个 StudySnapshot note 中无 exp568/st_imposition
  研究 manifest；行为代码基线=`f1118d1`，验收档提交前本地与阿里云工作树均净。

适配证据包在阿里云 `/root/s568adapt/`（47 件，`SHA256SUMS -c` 全通过）。
