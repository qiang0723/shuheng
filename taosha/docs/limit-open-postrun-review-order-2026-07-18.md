# exp8 运行后外部复核裁决 + 两项窄修令(2026-07-18,原文即口径)

> 人转外部第二独立视角复核结论 + 本轮施工令。**统计结果及 NOT_SIG 判决已通过;persist 暂不授权。**
> 本档为令原文逐字留痕(F 条);对应验收档=`limit-open-postrun-narrowfix-acceptance-2026-07-18.md`。

---

## 令原文

外部第二独立视角已通过AWS跳板,对阿里云原始产物、数据库和两台代码实物完成独立只读复核。

已确认:

- 两台代码`HEAD=6f7bfd3`,工作区干净;
- `result_exp8.json` SHA256=`282bda4fdc404eed7cf409b2566a77ae94aa6d57954c0ed0b03c7f81d1018a10`;
- `report_exp8.txt` SHA256=`278456d5bad1e88055114b2dd3e83c36e3fca19d035383640185f781687c3e99`;
- `run8.log` SHA256=`d2940c311aecc045b5fc46219604b1362feb1e2bbeb8c52b6cf7fb31098e1c76`;
- 三件秘密扫描零命中;
- result全文只有一个顶层`verdict=NOT_SIG`;
- 主窗CAAR=`−0.014817818…`,ADJ-BMP=`−0.472587656…`,判决符合冻结口径;
- manifest 121权威行、镜像与publication attestation三处digest/content一致;
- exp8仍为`frozen`,`result_json`、`done_at`为空,台账25行,persist未触碰。

**统计结果及NOT_SIG判决已通过;persist暂不授权。**

本轮只处理以下两个验收问题,属于报告与测试证据修正,**不得重跑研究、重建manifest、修改原始result或触碰台账**。

### 一、正式报告标识修正

当前原始`report_exp8.txt`被直接核实存在两处错误:

1. 标题错误显示:`淘沙 · 事件研究体检报告(切片2 合成验收)`
2. "快照批次"错误打印PAP中的`snapshot_batch_req`需求字典,而非实际manifest 121。

要求:

1. 对`report.py`做最小参数化修正:
   - 当`result.audit.limit_open_selection`在场时,标题固定为:`淘沙 · 事件研究体检报告(exp8 一字涨停开板·事件版)`
   - 同一路径的快照行必须直接读取:`result.audit.study_snapshot.snapshot_id`、`result.audit.study_snapshot.digest`
   - 本案应显示实际`StudySnapshot=121`及digest:`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`
2. 若exp8结果缺`audit.limit_open_selection`、`audit.study_snapshot`、`snapshot_id`或`digest`,报告生成必须fail-closed,不得回退为合成标题或PAP需求字典。
3. 其他路径保持原行为:默认合成路径逐字节不变;#2b专属标题逐字节不变;不借本轮修正其他历史报告标题或无关carry-item。
4. 原始产物永久保留:`/root/s8run/report_exp8.txt`不得覆盖、删除或改写;原SHA `278456d5…`永久保留;新报告另存为:`/root/s8run/report_exp8.corrected.txt`
5. 新报告只能由已验收原始`result_exp8.json`确定性重新渲染:不重跑事件生成;不重跑收益/CAR/检验;不修改result;不修改manifest;不从日志手工拼接报告。
6. 提交原报告与更正版逐行diff。除标题行和快照展示行外,应逐字节相同;出现第三处差异立即停止上报。

### 二、PAP gate R6假绿灯修正

当前`verify_pap_gate.py`虽已将F1动态化,但R6仍硬编码`exp8`。

exp8已处于frozen,因此当前R6实际执行为:

- PAP升级UPDATE因`status='registered'`条件命中0行;
- 随后因改写既有`frozen_at`或状态约束产生数据库异常;
- 测试却把任意`psycopg.Error`记为"legacy策略升级被PAP gate拒绝"。

这不能证明R6声称的攻击路径,属于错误拒绝原因造成的假PASS。

修正要求:

1. R6动态选择真实满足以下条件的标本:当前`status='registered'`;在`pap_legacy_registry`中物化在册。
2. 可复用F1选出的动态标本,但必须在独立SAVEPOINT内执行。
3. PAP升级UPDATE后必须直接断言:`rowcount == 1`;标本当时仍为registered;注入后的PAP确实包含:`pap_schema_version=2`、`analysis_type='strategy'`、合法`close_to_next_open`结构。
4. 随后执行`registered→frozen`攻击,必须由`_pap_freeze_gate`拒绝。
5. PASS条件必须核对具体错误原因包含:`legacy 实验只允许事件版冻结与运行`。不接受以下错误代替:frozen_at不可改;status非法迁移;UPDATE命中0行;其他任意数据库异常。
6. 全过程SAVEPOINT回滚,结束后直接证明:标本状态和PAP恢复原值;台账总行数不变;exp8状态及结果槽不变;探针零残留。
7. 重跑`verify_pap_gate`并提交23项逐项输出,R6须同时展示:注入UPDATE命中1行;捕获到预期PAP gate错误文本;SAVEPOINT回滚后零残留。

### 三、攻击性验收

至少新增或补强以下断言:

1. exp8正式结果渲染为真实标题,不出现"切片2合成验收";
2. exp8报告直接显示manifest 121及真实digest,不出现`snapshot_batch_req`字典;
3. exp8缺真实`audit.study_snapshot`时报告fail-closed;
4. 默认合成报告在修改前后逐字节一致;
5. #2b专属报告标题在修改前后逐字节一致;
6. R6的PAP注入真实命中1行;
7. R6只接受预期`_pap_freeze_gate`拒绝原因;
8. 任意其他数据库错误不得被记作R6 PASS。

### 四、回归与范围

本轮允许触碰:`taosha/engine/report.py`、`taosha/experiment/verify_pap_gate.py`、对应专项fixture、本轮裁决、验收档及`ops/STATE.md`。

禁止触碰:`result_exp8.json`、原始`report_exp8.txt`、`run8.log`、manifest 121、PAP v3、exp8冻结载荷、qbase/taosha生产事实及批次、台账状态、result槽、addendum、其他实验结果、任何收益、CAR或显著性计算代码。

必须提交:`git diff --stat 6f7bfd3..HEAD`、`git diff --name-status 6f7bfd3..HEAD`、完整实际diff、报告专项测试、R6逐项攻击输出、默认合成路径逐字节零回归证明、#2b标题零回归证明、两台HEAD、工作区状态及同步凭证。

### 五、重新取证

完成修正后提交:

1. 原始`result_exp8.json`,SHA必须仍为`282bda4f…`;
2. 原始`report_exp8.txt`,SHA必须仍为`278456d5…`;
3. 更正版`report_exp8.corrected.txt`及新SHA;
4. 原始`run8.log`,SHA必须仍为`d2940c31…`;
5. 新旧报告逐行diff;
6. manifest 121权威/镜像/attestation读回;
7. exp8仍为frozen、result_json/done_at为空;
8. 台账仍25行;
9. 全部交付件秘密扫描结果和新SHA256清单。

完成后停在交验点。**不得persist。**

外部复核只需核对本轮两个窄修及更正后的证据包;通过后另行下达persist令。
