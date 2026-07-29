# exp568（旧exp15）`st_imposition` · PAP终版文本交付（2026-07-29）

## 终版实物

终版候选：`taosha/docs/st-imposition-pap-final-2026-07-29.json`。

- 文件SHA256=`56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`；
- 引擎`canonical_pap_sha256()`同值；
- 18键，键集与草案相同；
- `validate_pap=PASS`；
- `parse_test_windows=(5,20,60)`；
- 终版本体为canonical紧凑JSON+末尾单换行。

本文件尚未冻结；须经外部复核与John另下绑定本digest的冻结句后方可进入数据库。

## 草案→终版键级diff

变动恰9键：

`benchmark / cleaning / diagnostic_dimensions / engine_params / event_def / pool / snapshot_batch_req / verdict_authority / window`

未变恰9键：

`analysis_type / bias_statement / cost / holdout / pap_digest_binding / pap_schema_version / reporting_commitments / sample_gate / verdict_power_note`

变化仅为将交验清单六组提案转为John 2026-07-29确认的正式表述：2011起点、`missing_bar_only` τ0、5/20/60三窗、估计窗与门槛、benchmark/cost/holdout等沿承、带星/不带星仅做数量NFV审计。阈值、参考漏斗、family/trial/α、事件定义实质与草案一致。

终版全文残留扫描：`NOT-FROZEN/草案/待人/提案/建议/本草案/不得冻结/不冻结`均为0。

## 冻结身份边界

- 唯一实验对象=exp568；旧exp15已closed，不得复用；
- family=`delist_warning_financial`、family_trial=2，由数据库身份权威提供；
- 族内双侧α=0.025，不得由PAP或driver覆盖；
- batch7下765事件/646票与560/205构成仍仅为冻结前参考，不是运行硬断言；
- 来源llm、效力prescreen。

## 禁区与下一步

草案原件保持不变并已标NOT-FROZEN/SUPERSEDED。本单元零生产代码、零数据库写入、零冻结、零manifest、零收益读取、零正式运行、零persist。

下一步仅为：外部复核终版digest与diff；通过后由John亲拟方向与把握度，并以本终版digest另下冻结令。
