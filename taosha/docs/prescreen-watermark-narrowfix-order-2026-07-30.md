# exp10 / exp16 `llm/prescreen` 水印类缺陷窄修令

日期：2026-07-30（UTC+8）

## F 条：人令原文

> 批准按上述收敛方案执行水印类缺陷窄修；不重跑研究、不覆盖原件、不修改既有result_json，exp10仅追加result-bound且不影响verdict的附注。

## 一、已确认缺陷

exp16 与已闭卷 exp10 的冻结 PAP 均要求正式 result/report 携带
`llm/prescreen` 效力水印；两案原始 result 均无台账实验身份，原始 report 均无水印。

- exp16 尚为 `frozen`，persist 暂停；
- exp10 已为 `done/NOT_SIG`，不得重开、重跑或改写既有 `result_json`。

## 二、代码窄修边界

仅修 exp10/exp16 专属 driver、专属 report 片段及对应 adapter fixture：

1. driver 从台账行写入 `audit.experiment_identity`，字段固定为
   `exp_id/family/family_trial/source_type/verdict_power`，不得从 PAP 或 CLI 取值；
2. report 对身份键 fail-closed，并渲染 `source=llm power=prescreen`；
3. 两套 fixture 均补身份删除攻击，缺键必须拒绝；
4. 不触碰 runner、cleaning、reader、统计判决、事件规则、PAP、manifest 或数据库 schema；
5. 不抽象通用平台，不顺手处理其他实验。

## 三、exp16 v2 产物规则

只允许读取：原始 v1 result、冻结台账身份、修后 report renderer。禁止进入
`ViewReader`、`runner`、收益读取或事件选择路径。

- 原始 v1 三件永久保留、SHA 不变；
- 新建 `result_exp16_v2.json` 与 `report_exp16_v2.txt`，不得覆盖 v1；
- v2 result 相对 v1 的结构差异必须恰为新增
  `audit.experiment_identity` 一键；删除该键并按原序列化规则重建后，须与 v1
  逐字节相等；
- v2 report 相对 v1 只允许新增一行实验身份水印；去掉该行后须与 v1 逐字节相等；
- 取证同时钉死原始运行 HEAD `b20a92b647b4846a816a22c31b884e22e7635b30`
  与镜像 `shuheng-quant:579a354` / image ID
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`，
  明确 v2 由后续修复 commit 渲染，不冒充单跑直出；
- 本单元不 persist。后续 persist 令须明确只允许 v2 入库，并同时断言 v1 三件
  SHA、v2 两件 SHA 与上述一键差异证明。

## 四、exp10 历史件处置

exp10 原 result/report 永久保留，数据库既有 `result_json` 一字不动；不生成竞争性的
替代 result，不改变 closed verdict。

仅以 `taosha_app` 同连接单事务追加一条 `experiment_addendum`：

- 必须绑定库内 exp10 当前 result canonical SHA；
- category 固定为 `prescreen_watermark_omission`；
- 正文明确：原 result/report 遗漏冻结件要求的效力水印，台账权威身份为
  `source_type=llm/verdict_power=prescreen`，缺陷只影响正式报告解读边界，
  不影响样本、统计量或 `NOT_SIG` verdict；
- `affects_verdict=false`；审批来源指向本令；
- 写入前后 exp10 result SHA、状态、verdict、manifest 与台账分布须不变；
- 失败整体回滚，不手工旁路。

## 五、停止线与交付

专项 fixture 与既有相关回归通过后，生成 exp16 v2、写入 exp10 附注并做只读验收；
证据包须含 v1/v2 SHA、结构与报告差异断言、附注行读回及原 result 不变证明。

完成后停在外部复核点。禁止研究重跑、exp16 persist、PAP/manifest 修改、既有产物覆盖
或任何结果后敏感性分析。
