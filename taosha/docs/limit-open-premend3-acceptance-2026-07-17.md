# exp8 回修三验收档(2026-07-17 深夜四;执行令=`limit-open-premend3-order-2026-07-17.md`)

> 范围=人转外部复核令退回的**两个窄阻塞**,不扩大:①P1-4 来源锚改真锚;②listing-age
> 白名单外值 fail-closed。回修二其余结论主体通过、本轮不重开。
> 禁区遵守:零 driver/零 manifest/零冻结/零收益读取/零正式运行/零台账写入(25 行未扰)。

## 1. 窄阻塞一:P1-4 真锚(施工实物)

- **canonical 算法单一口径** = `taosha/experiment/pap.py::canonical_pap_sha256()`:
  canonical 串 = 实质键(顶层剔除 `_` 前缀运行时键,`_family_trial` 等非 PAP 字段不进
  digest)按**词典序排序键 + 紧凑分隔符(`,`/`:`)+ UTF-8(ensure_ascii=False)**序列化;
  digest = `sha256(canonical串 + 末尾单换行)`。与 PAP 文件对账:冻结 PAP 文件即
  canonical 串+末尾单换行的字节本体,**引擎重算值 == 文件 SHA256**(v2/v3 均实测相等)。
- **digest 唯一权威=引擎重算**:`runner.run_study()` 对实收 pap 内容调用
  `canonical_pap_sha256()` 重算;调用方不得填写。新参数 `pap_sha256_assert` **仅作与
  引擎重算值逐字断言**,不一致立即 fail-closed raise(错误值实测拒)。
- **result 真锚三元组**:`result["bias_statement"] = {pap_sha256, key="bias_statement",
  text原文, source_anchor(串内含实际 digest)}`;旧描述性占位串
  `"pap['bias_statement'](...)"` 已废,全文零残留。
- **报告来源锚直接显示实际 digest**:`report.render()` 渲染
  `来源锚: pap_sha256=<64hex> key=bias_statement(引擎自实收冻结 PAP 内容重算…)`。

## 2. 窄阻塞二:listing-age fail-closed(施工实物)

- **主校验**(`runner.run_study()`,事件源构造后、**任何清洗/CAR 计算及顶层 `_verdict()`
  调用之前**):启用 `listing_age` 诊断时——
  ① 白名单与 PAP `diagnostic_dimensions.axes.listing_age` **逐项一致对账**(缺失/不一致
  → fail-closed 拒,PAP 缺该键实测拒);
  ② 全部事件层键严格 ∈ {recent_listing, seasoned};None/空串/unknown/forecast 旧层名及
  任何白名单外值 → fail-closed 拒绝运行,违例逐值计数入异常文本。
- **兜底**:`_diagnostic_dimensions()` 观测到白名单外层 → raise(原"意外层如实上报"
  追加行为**已删除**;意外层不得追加入报告后继续研究)。
- 引擎白名单 `_DIAG_DIM_SPECS['listing_age'].layers` 与 PAP v2/v3 axes 逐项一致(fixture
  实物对账)。

## 3. 攻击测试两组(`verify_limit_open_engine.py`,76→**102/102 PASS** 两台)

- **⑨ P1-4 四证**(人令定点):
  - PAP v2 实物重算得 `2611be36…` == 文件 sha256(canonical 与文件对账);
  - 修改任一实质字段(window/bias_statement/event_def 三例)→ digest 改变;
  - 仅添加 `_family_trial` → digest 不变;
  - 错误 digest 断言拒(fail-closed)/正确断言放行且结果逐字节同;
  - result 三元组 pap_sha256==引擎重算值;报告串内实际 digest 在场、描述性占位零命中。
- **⑩ listing-age 五证**(每证=拒绝运行 + **攻击下 `_verdict()` 调用次数=0** 双断言,
  monkeypatch 计数):
  - 全事件标 unknown 拒;缺失层(None)拒;空字符串层拒;forecast 旧层名("预喜")拒;
    合法样本混入单条非法层拒;
  - 合法 recent/seasoned 全体放行(顶层判决在场+两层诊断块);
  - PAP 缺 axes.listing_age(白名单不逐项一致)拒;构建器兜底 raise 实测。

## 4. PAP v3 与 v2 标记

- **PAP v3** = `limit-open-pap-final-v3-2026-07-17.json`,单行 canonical JSON+末尾单换行
  (7,683 字节):
  - **文件 SHA256 = canonical digest = `afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb`**
    (引擎 `canonical_pap_sha256()` 重算实测相等);canonical 串本体 sha256 =
    `e298615434cda4261acc52c0bfc1f02e0254d68f4204183374c03217527302fb`;
    `validate_pap` PASS;`parse_test_windows` = (5,20,60) 不变。
- **v2→v3 逐键 diff**(程序化比对):
  - ADD 顶层 `pap_digest_binding`(digest 绑定四规则:result 三元组/canonical 算法与文件
    对账/调用方 digest 仅逐字断言 fail-closed/报告直接显示实际 digest——措辞取自人令原文);
  - MOD `diagnostic_dimensions`:仅 sub-ADD `listing_age_fail_closed`(白名单外值全
    fail-closed/意外层禁追加/与 axes 逐项一致/CAR 及顶层 `_verdict()` 前完成校验);
  - 其余 **16 键逐字未动**(analysis_type/benchmark/**bias_statement**/cleaning/cost/
    **engine_params**/**event_def**/holdout/pap_schema_version/pool/reporting_commitments/
    sample_gate/snapshot_batch_req/verdict_authority/verdict_power_note/**window**)——
    实质研究内容零改动。
- **v2 标记档** = `limit-open-pap-final-v2-2026-07-17.NOT-FROZEN.md`:v2(digest
  `2611be36…`)标记"**外部复核未通过、未冻结**",原 JSON 不覆盖不删除(循 v1 WITHDRAWN
  标记档先例);v3 在人签发冻结句前同样未冻结。

## 5. result/report 样例中的真实 PAP digest(SYNTHETIC 合成域)

- `limit-open-premend3-json-sample-2026-07-17.json` + `…-report-sample-2026-07-17.txt`
  (顶部 SYNTHETIC 标注):result `bias_statement` 三元组 pap_sha256 =
  `57d4ff6a…`(=引擎对该合成 pap 重算的**真实** canonical digest,非占位);报告行
  `来源锚: pap_sha256=57d4ff6a… key=bias_statement(引擎自实收冻结 PAP 内容重算…)`。
- 真实 exp8 运行时该值将 = 冻结 PAP v3 digest(`afd8443a…`),以人签发冻结句为准
  (样例内 `_SYNTHETIC_SAMPLE_NOTE` 已注明)。

## 6. 专项套件与默认路径零回归

- 专项:`verify_limit_open_engine` **102/102**、`verify_limit_open_rules` **40/40**(两台)。
- 合成 e2e(官方 harness):双跑均 = **`3116ba9b74f7c53b…` 逐字节 == 历史基线**
  (默认路径:pap 无 bias_statement/未启用诊断 → pap_sha256 不计算、result 零新键、
  报告固定偏差段逐字不变)。
- 全家福:AWS 非 DB 套件=三窗 5/5、holder 规则 81/81、适配 10/10、敏感性 6/6、运行时钉版
  ALL PASS;aliyun(钉版 venv)=状态机 46/46、pap 硬门 23/23、addendum 14/14、镜像 11/11、
  血缘 24/24、探针 19/19、集成 7/7(S6 双跑 sha `63e2c9fc` 同基线)、pap_vs_spec
  (DB 套件历史即 aliyun 域;实测记录见 §8 两台核验)。

## 7. 完整 diff 与边界证明

- 代码面(`git diff --stat`,施工 commit 实物):
  ```
  taosha/engine/report.py                    |   8 ++-
  taosha/engine/runner.py                    |  68 ++++++++++++++----
  taosha/experiment/pap.py                   |  17 +++++
  taosha/harness/verify_limit_open_engine.py | 109 ++++++++++++++++++++++++++++-
  ```
  新增文件=PAP v3/v2 标记档/两样例/本验收档(+STATE)。
- 触碰面全部在执行令注记 3 允许范围(runner/report/fixture/pap.py canonical 函数/新 PAP v3
  +标记档/留痕/验收档/STATE);**qbase/台账/driver/manifest/原 PAP v1·v2 文件/收益路径零触碰**;
  已裁项(C1/C2/C4/C5/P1-1 等)零重开。
- 状态闸(接令核,只读):exp8=registered/frozen_at 空/result 空;台账 25 行
  =registered18/frozen2/done4/closed1;无 exp8 manifest。

## 8. 两台核验(交付 commit 后补记)

- commit 链:`f659c82`(回修三令留痕)→ 施工 commit → 交付 commit(本档);两台 HEAD 一致、
  `git status` 净;aliyun 全家福实测结果照跑照录。

## 9. 停交验点

本单元完成后**停在交验点**:等人重审 PAP v3(digest `afd8443a…`)→ 人以新 digest 重新
签发冻结句+新预判 → 才可 driver/manifest/正式运行;未令不动。
