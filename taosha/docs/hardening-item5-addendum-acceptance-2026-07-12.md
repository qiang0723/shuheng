# 硬化⑤ experiment_addendum 审计附属表 · 验收档(⑤ 关闭,2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ⑤。修法原文:新建 append-only 表(Experiment 审计附属对象),字段 exp_id / 原 result sha256 / 问题类别 / 附注正文 / 是否影响 verdict / created_at / 审批来源指针;同款触发器焊死(禁 UPDATE/DELETE);首批两条附注 (a)(b);原 result_json 一字不动。补充令:⑤ 拆两半,建表+附注(a) 随时可做,附注(b) 待 ③ diff 出数后补录,⑤ 整体关闭在 ③ 后。tie 人拍A(2026-07-12)追加:exp5 补附注(c),随 (b) 一并补录。

## 1. 前半(2026-07-12 午后):建表 + 附注(a)

- **007 迁移已 apply**(`taosha/sql/007_experiment_addendum.sql`,属主 postgres):字段齐(含 approval_ref/created_by 超出人令最小集,只加不减);append-only 同款焊死(`_freeze_appendonly` 行级 + `_no_truncate` 语句级);授权只收不扩(taosha_app SELECT+INSERT / taosha_engine 仅 SELECT)。
- **附注(a) 已入库**:addendum_id=1,exp_id=3,category=`strategy_version_qualification`,body=人批原文逐字("冻结口径下的不可执行诊断值,存在同刻成交前视与倾向乐观的偏置,不构成真实可交易表现证据"),affects_verdict=false,锚 `result_sha256=e3d2aef92bd47c6b…`(=exp3 台账 result_json sha256)。
- 自检 `taosha/experiment/verify_addendum.py` **8/8 PASS**(当时)。

## 2. 后半(2026-07-12 晚):附注(b)(c) 补录(③ diff 出数后)

执行 = scp+psql 文件法(附注(a) 先例),身份 taosha_app,单事务;**前置断言**(不过即中止):附注表现况恰 1 行(防重复补录)+ exp3/exp5 `result_json` sha256 与闭卷锚全等(防错锚)。三条 INSERT 全过,COMMIT 成功:

| addendum_id | exp_id | category | affects_verdict | result_sha256 锚 |
|---|---|---|---|---|
| 4 | 3 | cleaning_defect_st_row0 | false | `e3d2aef92bd47c6b…` |
| 5 | 5 | cleaning_defect_st_row0 | false | `c010ce9d4d235424…` |
| 6 | 5 | event_view_tie_break_defect | false | `c010ce9d4d235424…` |

(addendum_id 2/3 为自检探针回滚留下的 identity 序号空洞,与 item1 §7 同现象,登记不修。)

**附注正文(git 留痕,与库中逐字同;库为权威实物)**:

- **(b)·exp3(id=4)**:ST rows[0] 缺陷登记(人令⑤(b)原文:exp_id=3/5 ST rows[0] 缺陷登记,影响以③diff实测为准〔不影响 verdict,理由随 diff 补录〕)。缺陷=清洗段 ST 剔除按估计窗首行 rows[0](≈事件日前250交易日的陈旧标签)而非事件日行 is_st 判定。③ diff 实测(2026-07-12,修复=st_mode event_day,commit b14872a;产物 /root/s3hard3/diff_2e.json、diff_2s.json):事件版 st 剔除 4→144(+140),n_valid 17929→17827(−102),剔除率 0.08703→0.09222,主窗[0,+19] ADJ-BMP −0.410848→−0.410839,稳健[0,+59] −0.58660→−0.58339,verdict NOT_SIG 不变;策略版消费 17929→17827(同源差集仍 0),exits break_ma20 17910→17808(stop 18/censored 1 不变),adj_z 毛 −0.55271→−0.55172 / 净 −0.66205→−0.66075(NOT_SIG 标注不变,判决权归事件版),net.mean −0.008610→−0.008667。不影响 verdict 之理由(实测):修复臂各统计口径判定均不变;post-ST 新基线 norm_sha 事件版 b7d0879eeadcbcd1…/策略版 7dbd9006b354c94b…(登记档 hardening-item3 §6)。原 result_json 一字不动,闭卷 sha 永久保留。
- **(b)·exp5(id=5)**:同缺陷登记。③ diff 实测(旧臂 vs 修复臂=ST 效应,对照基=013 tie 钉死后旧臂;闭卷与旧臂差异另归 tie 缺陷见附注(c);产物 /root/s3hard3/diff_4.json,n_diffs=135):st 剔除 30→4239(+4209),n_valid 67765→64033(−3732,−5.51%),剔除率 0.35823→0.39357,剔除原因重分配 coverage 7929→7482/postpone 27→11/suspension 9020→9007/history 20797→20796,三层 n_valid good 34664→34435/bad 26996→24661/turnaround 6105→4937,主窗[0,+19] ADJ-BMP 0.08744→0.07147(CAAR −0.001094→−0.002007),稳健[0,+59] 0.16043→0.13076(CAAR −0.003776→−0.006238),ρ̄ 0.07322→0.07768。三臂 verdict 均 NOT_SIG,判决不变。不影响 verdict 之理由(实测):判定不变;post-ST 新基线 norm_sha eb6f01d43dcbec7f…。原 result_json 一字不动,闭卷 sha 永久保留。
- **(c)·exp5(id=6)**:事件视图 DISTINCT ON tie-break 缺陷登记(tie 人拍A 2026-07-12:工程钉死次级键 id ASC〔qbase/sql/013〕,"任意但永远同一行"不宣称语义;#4 闭卷不动,补附注)。缺陷=008/012 事件视图 DISTINCT ON 最早 ann_date 并列 11689 对无确定性次级序(②验收实测总数可漂 105584↔105587;存在可漂 19 对/层可漂 62 对);013 钉死后恒 105590。③ diff 实测(闭卷 vs 013 钉死后旧臂=tie 钉死效应;diff_4.json n_diffs=35):n_events_total 105584→105590(+6:main+3/chinext+2/star+1),n_valid 67760→67765(+5),剔除 +1(suspension 9019→9020),三层 good+10/bad−7/turnaround+2,主窗 ADJ-BMP 0.08745616→0.08744020(Δ≈−1.6e-5),稳健 0.16056→0.16043,verdict NOT_SIG 不变。exp3 不消费事件视图:closed vs 旧臂 n_diffs=0,tie 不适用实测得证,故仅 exp5 登记本附注。不影响 verdict 之理由(实测):差异量级 1e-5 且判定不变。原 result_json 一字不动,闭卷 sha 永久保留。

## 3. 补录后验收(2026-07-12 晚实测)

- 自检 `verify_addendum` 重跑 **8/8 PASS**(S1 触发器在位 / F1 INSERT 放行〔探针回滚零残留〕/ R1–R3 UPDATE·DELETE 全拒 / R4 外键拒 / Z1 原 result_json 一字未动〔exp3/5 sha 前后同〕/ Z2 零残留)。
- **原 result 一字不动终验**:补录后 exp3 `e3d2aef92bd47c6b…` / exp5 `c010ce9d4d235424…` 与闭卷锚逐字全等;experiment 台账仍 25 行=registered18/frozen3/running0/done3/closed1。
- 表实物 = 4 行(1/4/5/6),全 affects_verdict=false,created_by=taosha_app。

## 4. 结论

⑤ 两半齐:建表焊死 + 附注(a)(b)(c) 全入库(b/c 含 ③ diff 实测数字,verdict 判定登记为不受影响且理由随附),原 result_json 一字不动实测得证。**⑤ 关闭,实物(表 4 行)入硬化验收包;待架构窗口终审时随包复审。**
