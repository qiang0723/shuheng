# exp16 `yearend_strength` · PAP终版文本交付（2026-07-30）

## 终版实物

终版候选：`taosha/docs/yearend-strength-pap-final-2026-07-30.json`。

- 文件SHA256=`3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`；
- 引擎`canonical_pap_sha256()`同值；
- 18键，键集与草案相同；
- 本地与阿里云Python3.14.4均`validate_pap=PASS`；
- 两端`parse_test_windows=(5,20,60)`；
- `engine_params.st_policy=keep`；
- 终版本体为canonical紧凑JSON+末尾单换行。

本文件尚未冻结；须经外部复核与John另下绑定本digest的冻结句后方可进入数据库。

## 草案→终版键级diff

变动恰6键：

`benchmark / cleaning / engine_params / verdict_authority / verdict_power_note / window`

未变恰12键：

`analysis_type / bias_statement / cost / diagnostic_dimensions / event_def / holdout /
pap_digest_binding / pap_schema_version / pool / reporting_commitments / sample_gate /
snapshot_batch_req`

变化仅为将草案待确认项转为John 2026-07-30正式裁定：ST=`keep`；三窗5/20/60、
估计期250..91与覆盖门112/160、sample_gate=30、全市场等权benchmark、
`adj_bmp_main_only`唯一判决、无收益分层轴、cost四值仅审计，以及holdout、field roles、
digest binding与llm/prescreen效力按草案建议确认。事件公式、阈值、研究期、7,751对账参考和
selection SHA均未改变。

终版全文残留扫描：`NOT-FROZEN/草案/待终版/待人/建议/尚待/不得冻结/不冻结`均为0。

## 冻结身份边界

- 唯一实验对象=exp16，当前仍为`registered`；
- snapshot74/market_return88下7,751事件与selection SHA
  `057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`仅为冻结前对账参考，
  不是正式运行硬断言；
- ST事件保留，但不设置ST收益分层判决轴；
- 来源llm、效力prescreen；
- 人的方向与把握度尚未密封，须在本终版digest复核通过后另行绑定。

## 禁区与下一步

草案原件保持不变并已标NOT-FROZEN/SUPERSEDED。本单元零生产代码、零数据库写入、零冻结、
零manifest、零收益读取、零正式运行、零persist。

下一步仅为：外部复核终版digest与diff；通过后由John亲拟方向与把握度，并以本终版digest
另下冻结令。
