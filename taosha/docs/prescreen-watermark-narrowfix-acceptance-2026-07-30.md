# exp10/exp16 `llm/prescreen` 水印类缺陷窄修验收

日期：2026-07-30（UTC+8）  
授权令：`taosha/docs/prescreen-watermark-narrowfix-order-2026-07-30.md`  
授权原文：**“批准按上述收敛方案执行水印类缺陷窄修；不重跑研究、不覆盖原件、不修改既有result_json，exp10仅追加result-bound且不影响verdict的附注。”**

## 1. 结论

窄修完成，停止线内全部断言通过：

- exp16 的专属 driver/report 现从台账写入并 fail-closed 消费
  `audit.experiment_identity`，正式报告强制渲染 `llm/prescreen` 水印；
- exp16 v2 仅由已验收 v1 原件与冻结台账身份确定性生成，**没有进入
  ViewReader、runner、收益读取或事件选择路径**；v1 三件永久保留、零覆盖；
- exp10 已闭卷原 `result_json` 与原 result/report 文件均未修改，仅追加一条
  result-bound、`affects_verdict=false` 的附注；
- 样本、统计量、唯一顶层 verdict、PAP、manifest、ledger 状态均未改变；
- 本单元未执行研究重跑、正式运行或 persist。exp16 仍停在 `frozen` 取证点。

## 2. 代码触碰面

施工提交：

- `f06f84aa6445fd671b6e8f68cb609e2bf7aa5829`：专属 driver/report 与攻击 fixture；
- `c6d78edebf5d26b26b56048453127ab10ac728de`：fixture 输出收敛，不改断言语义。

触碰恰六个专属文件，共 `+85/-2`：

- `taosha/harness/run_volume_drought_study.py`；
- `taosha/engine/report_volume_drought.py`；
- `taosha/harness/verify_volume_drought_adapter.py`；
- `taosha/harness/run_yearend_strength_study.py`；
- `taosha/engine/report_yearend_strength.py`；
- `taosha/harness/verify_yearend_strength_adapter.py`。

无统计内核、清洗内核、reader、PAP schema、DDL 或通用报告框架改动。两个 driver
各新增单一职责 helper：身份值只取 ledger 行，字段固定为
`exp_id/family/family_trial/source_type/verdict_power`；已有身份拒绝覆盖，非
`llm/prescreen` 拒绝写入。两个报告模块缺身份或身份不完整即 fail-closed。

## 3. exp16 v2 产物

原始运行锚保持不变：

- 原始运行令 HEAD：`b20a92b647b4846a816a22c31b884e22e7635b30`；
- 原始镜像：`shuheng-quant:579a354`；
- image ID：`sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
- v1 result：`31b8115b47b9c69ee72bbd62a4849ec93dc180f6307cafcacd7ae2fba8156edb`；
- v1 report：`79ca36833f8c6a8e31c291b70506f28a1a7a8ad32eb51bbc1dc328d652440709`；
- v1 log：`e7bdfdd318317fc4ff0cb988825b3f5f8c8c904f62688d75db6b1e69e34b5b54`。

v2 实物：

- `result_exp16_v2.json`：
  `96cc24abe093e99fd4599193e51785655c48af7fedc9a2cbc580acd3a4de307b`；
- `report_exp16_v2.txt`：
  `aad35e96324b1b5947fde279b82c36195c7ec8cea74a64931ddf080cb403e68d`；
- 水印原文：`实验身份: exp16 family=yearend_strength trial=1 source=llm power=prescreen`。

程序化断言：

1. v1→v2 result 的结构差异恰为新增 `audit.experiment_identity` 一键；
2. 从 v2 删除该键后，序列化字节逐字还原 v1 result；
3. v2 report 删除唯一水印行后，字节逐字还原 v1 report；
4. v2 递归 `verdict` 键仍恰为 1；
5. exp16 仍为 `frozen`，`result_json/done_at` 为空；
6. v2 身份逐字段等于冻结台账实物，不接受 PAP 或 CLI 代填。

前两次未写库的失败尝试完整保留：attempt1 暴露 JSON 重载后的字典插入顺序会改变
报告字节；attempt2 进一步暴露 Python dict 展示键序差异。最终做法以当前 renderer 验证
水印内容，再把该唯一水印行插入 v1 报告，确保“去一行即逐字还原 v1”。失败与成功脚本、
日志、断言 JSON 均在 `/root/s16run/watermark_fix/`，未删除、未伪装为单跑直出。

## 4. exp10 result-bound 附注

原件锚：

- result 文件 SHA：
  `211b9f44ff4bd1b64cf0892c37c846d2d4f0b33b972064d9d117cd9b77349c51`；
- report 文件 SHA：
  `45dd146a6ef76fe1a7f072431ee4c592e3f1350ae1e32d5be9357f43699246ce`；
- 库内 `result_json::text` 绑定 SHA：
  `f96d5d2ddfe53cb24b04c6d174647e38b7b9f1fb24b9cd50d050666055c015e6`。

追加实物：

- `addendum_id=170`；
- `category=prescreen_watermark_omission`；
- `affects_verdict=false`；
- `created_at=2026-07-30 13:15:45.164794+08`；
- `approval_ref=taosha/docs/prescreen-watermark-narrowfix-order-2026-07-30.md §四`；
- body：`exp10原result/report遗漏冻结PAP强制要求的效力水印；台账权威身份为source_type=llm/verdict_power=prescreen。该缺陷仅影响正式报告解读边界，不影响样本、统计量或NOT_SIG verdict；原result_json保持不变。`

首次脚本因 `dict_row` 使用位置索引而在 INSERT 前 `KeyError` 停止，零库写；失败脚本与
日志保留。修正只把该只读计数改为具名列访问。正式事务在 INSERT 前后及 COMMIT 后均
断言：exp10 仍 `done/NOT_SIG`、result 解析对象不变、ledger 分布不变、manifest 271
三处不变、同类附注唯一。

## 5. 联合只读核验与回归

联合只读核验全部为真：

- exp10 库内 result 与原件 `parsed_equal`；附注唯一且 NFV；
- exp16 PAP canonical 仍为
  `3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- exp16 保持 `frozen`、结果双槽空；
- ledger 仍为 26 行：`registered 9 / frozen 3 / done 12 / closed 2`；
- manifest 271 与 317 的权威行、qbase 镜像、publication attestation 三处 digest
  均为 `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`。

专项与数据库硬门：

- exp10 rules `14/14`、adapter `22/22`；
- exp16 rules `14/14`、adapter `28/28`；
- addendum `14/14`、状态机 `46/46`、PAP gate `23/23`；
- snapshot mirror `11/11`、manifest lineage `24/24`、study snapshot probes
  `19/19`、integration `7/7`、three windows `5/5`。

其余离线全家福全部通过：earnings revision `24/73/33`、high pullback
`29/24`、holder sell `10/81`、limit down `34/48`、limit open `24/116/40`、
SOX `34/23`、ST imposition `23/16`、ST removal `43/42`、sensitivity `6/6`
及 frozen immutable。

证据目录：

- exp16：`/root/s16run/watermark_fix/`；
- exp10：`/root/s10watermark/`。

两处证据目录的递归 SHA 清单全部通过；新增文件 13 类秘密扫描均为
`TOTAL_HITS=0`。联合只读核验实物为
`/root/s10watermark/postverify_combined.json`。

## 6. 停止线

- exp10 继续维持已闭卷 `done/NOT_SIG`，不重开、不重跑、不改既有 result/report；
- exp16 统计结果仍为 `NOT_SIG`，但在 John 另下 persist 终令前继续保持 `frozen`；
- 本单元不做 exp16 密封开封对照与校准册入册；该动作只属于后续 persist；
- 外部复核范围只需核：六文件代码 diff、两套新增攻击 fixture、exp16 v1→v2
  恰一键/一行恒等、exp10 addendum_id 170 的 NFV 与 result 绑定。不得重开统计与漏斗审查。
