# exp14 `ex_div_gap` 冻结与最小适配行为验收

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 代码 commit：`146eea50993725f31f2a6f62a52c2bea00f9f7e8`
- 停止点：行为验收；未生成 exp14 研究 manifest，未读取正式收益，未执行 §7，未 persist。

## 一、冻结身份与代码身份

- 终版 PAP digest：`a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；
  密封原文：`正，把握度60%`。冻结事务与实现说明见
  `ex-div-gap-freeze-adapt-implementation-2026-08-09.md`。
- GitHub 推送成功后，阿里云 `/opt/quant` 由 `a980543` fast-forward 至 `146eea5`，工作树干净。
- 验收使用既有钉版镜像 `shuheng-quant:579a354`，image ID=
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
  当前代码树只读挂载并以 `PYTHONPATH=/workspace` 消费，未重建或替换镜像。

## 二、snapshot375 冻结态 recon

同一命令独立运行两次，两件 JSON 字节级相同，SHA256 均为
`2d981a3ca5d10803494347b9dd3da637e59c46da5cfe6081789f74666bffbb15`。

- `mode=recon_only`、PAP digest 精确命中；source snapshot=`375`，三处既有 digest 身份为
  `2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`；
- current/snapshot 全量选择结果精确一致；六条选择恒等式全部为真；
- 最终事件 `4,035`、Decimal 恰等边界 `1,083`、selection SHA=
  `ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`，与冻结前同锚参考精确一致；
- 事件分年合计与监管三分 `2,688+664+683=4,035` 均守恒；
- A1 因子门：变化 `4,035`、静态 `26`、缺失/无效/冲突均为0；因子比 NFV 审计
  `min=1.003508776586567429613447966`、`mean=1.880281225213487030626024586`、`max=4.011`；
- `raw_price_enters_car=false`、主价格口径=`adjusted_total_return_close`。raw 跳空与因子比只作
  NOT_FOR_VERDICT 机械审计，不进入选择、CAR 或判决。

## 三、行为、攻击面与回归

阿里云数据库常设套件全部通过：

- 状态机 `46/46`；PAP gate `23/23`；addendum `14/14`；
- StudySnapshot fail-closed probes `19/19`；镜像 `11/11`；血缘 `24/24`；集成 `7/7`。

exp14 专项在阿里云当前代码树通过：规则 `14/14`、adapter `38/38`。攻击面覆盖 PAP digest
三重绑定、8键参数缺/多、`tau0=ex_date当日` 三处冻结文本、`tau0_on_anchor` 不设 CLI 自由入口、
拒绝 signed 旁路、source375 不得冒充正式 manifest、身份水印删除、结构化 NFV/执行限制审计删除、
递归 verdict 唯一。其余31个离线 rules/adapter/engine/冻结不可变/三窗口/敏感性入口全部通过。

规模闸门通过：`223 files / 33,242 lines / 922 functions`，存量债务仍为20文件/50函数，零新增；
新增与修改的 exp14 文件均未越过300行/60行函数上限，`report.py` 的存量棘轮未上升。

两次启动期失败如实保留：第一次遗漏 `verify_study_snapshot --mode`，argparse 在数据库连接前拒绝；
第二次非 root 容器无法读取只读挂载 `.env`，同样在数据库连接前拒绝。随后仅对该历史探针以容器
root 读取同一 `.env`，19/19 通过；未改代码、未删除失败痕迹、未造成数据库写入。

## 四、后核验与停止线

行为验收后只读实测：

- exp14=`frozen`，`frozen_at=2026-08-09 14:33:15.200827+08` 不变；
  `result_json/done_at` 仍为空，PAP MD5仍为 `46ecfcac84fd79e904731b05ca4ba115`；
- 台账仍为26行：`registered6/frozen3/done15/closed2`；exp14 addendum=0；
- StudySnapshot仍20行、max=`398`；血缘和集成套件只使用事务回滚探针或复用既有 manifest，未新增行；
- `/root/s14adapt/recon1.json` 与 `recon2.json` 为本单元两件新增证据；13类敏感词扫描0命中。

结论：冻结身份、A1/B1/C1/D1 规则适配、同日 tau0、复权主 CAR 边界、身份水印、确定性、
数据库硬门、零回归与规模闸门全部通过。当前停在行为验收点；下一步只能在独立复核通过并获人另令后，
生成 exp14 自有研究 manifest 并执行 §7 单次正式运行。persist 继续单独授权。
