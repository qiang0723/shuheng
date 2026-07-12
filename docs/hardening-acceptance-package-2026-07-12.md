# 可信度硬化窗口 · 验收包总表(2026-07-12)

> **外部第二视角复审为咨询输入,终签权=人。**(人令 2026-07-12,总表头部标注)
> 复审标准(施工单收口原文):非法路径是否真走不通、同一快照是否真复跑出同一结果。
> 施工单原文=`docs/hardening-window-order-2026-07-12.md`;库实物为权威,本表为索引。

## 1. 六项验收档索引

| 项 | commit 链(裁决留痕→施工→验收) | 验收档 | 架构窗口 |
|---|---|---|---|
| ① 台账状态机焊死 | `160e364`(开窗留痕)→`7a1520e`→`9d35e81`→`fd7e993` | `taosha/docs/hardening-item1-statemachine-acceptance-2026-07-12.md`(44/44) | ✅✅ 过窗 07-12 |
| ② StudySnapshot 快照锁定 | `5ad4e99`→`19bddd9`(tie 人拍A/013)→`f03d1b9` | `taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md`(fail-closed 16/16) | ✅✅ 过窗 07-12 |
| ③ 事件日 ST 修复+受控 diff | `b14872a`→`43bbdee`→`73ba918`→`f73aa1c`→`6dc5429`→`268aca8` | `taosha/docs/hardening-item3-st-eventday-acceptance-2026-07-12.md`(九连跑+三对归因) | ✅✅ 过窗 07-12(③⑤联合) |
| ④ 共享存活样本主干 | `99242b1`(开令)→`fae0dcd`→`24634b2`→`6d96eb6` | `taosha/docs/hardening-item4-shared-survivors-acceptance-2026-07-12.md`(ALL_MATCH+单一调用点) | ✅✅ 过窗 07-12(双证记功) |
| ⑤ experiment_addendum 附属表 | `ac713c3`(007+自检)→`f03d1b9`(前半)→`268aca8`(附注b/c+关闭) | `taosha/docs/hardening-item5-addendum-acceptance-2026-07-12.md`(8/8) | ✅✅ 过窗 07-12(③⑤联合) |
| ⑥ 环境钉死+集成回归 | `cf6f198`(即刻半)→`d1fa90c`(后半开令)→`93fde66`→`1e8fdd8`→`40dabc4` | `taosha/docs/hardening-item6-runtime-integration-acceptance-2026-07-12.md`(7/7) | ▶ 本总表交付项,待窗 |

## 2. 三份 post-ST 新基线(norm_sha256=剔 diagnostic 块;③产 ④重构后逐字节复证)

| 案 | norm_sha256 |
|---|---|
| #4(exp5,event_day 修复臂) | `eb6f01d43dcbec7f5ccaa99a3b96c4b09a80b024524bb67067c2e160601e190c` |
| #2b 事件版(exp3) | `b7d0879eeadcbcd182931d64a58da6dcb6c721d46974b67e443603def4c9450a` |
| #2b 策略版(exp3) | `7dbd9006b354c94b3e411526bd6ef579125f5733f41e2acf621a1a13c0ad4a4b` |

确定性硬项:③ B 臂 vs r2 双跑全等×3;④ 重构后 c 臂三跑 ALL_MATCH(`/root/s3hard4/verify_vs_baseline.json`)。合成域基线 `3116ba9b74f7c53b…` 全程零回归。

## 3. 旧闭卷 sha 对照表(**永存声明**:旧闭卷 sha 永久保留、不被取代;post-ST 新基线另立,不改判决)

| 案 | 载体 | sha256 |
|---|---|---|
| #4(exp5,done 2026-07-08) | 台账 result_json(`sha256(result_json::text)`) | `c010ce9d4d235424eb34548c5647b8381db0758fd68e52a355ad079787241c8f` |
| #4 | 闭卷产物 result.json | `b48d29411ccab7f7d7a07c14bd9932b65cea3891636a59c77b5b87510a9f7698` |
| #2b(exp3,done 2026-07-12) | 台账 result_json | `e3d2aef92bd47c6b28c460d1847a3b63226bd72c2bdd936d4efbcdf761216332` |
| #2b | 事件版产物 drawdown_result.json | `0565b11520672acb5af615d0fb7e0bfa56bf0aab8f9bcbf95dd366c02a748026` |
| #2b | 策略版产物 gross_strategy_result.json | `fbf4d829222b2e44259c285169f614edc151f3d757d906bb8a1b4fb6f267111e` |

(产物备份 `/root/s3close_exp3/`;②③④ 诊断产物备份 `/root/s3hard2_backup/`、`/root/s3hard3_backup/`、`/root/s3hard4_backup/`。)

## 4. 闭卷可复现性硬证(人点名单列,2026-07-12)

**#2b 闭卷逐字节复现**:③ 受控 diff 实测,exp3 闭卷记录 vs ①②焊死环境重跑旧臂(manifest 路由+013 钉死后视图+legacy st_mode)——事件版与策略版 **closed vs 旧臂 n_diffs=0**(`/root/s3hard3/diff_2e.json`、`diff_2s.json`)。此为外审复审标准之二("同一快照真复跑同一结果")的**提前实证**:2026-07-12 闭卷、同日在焊死环境下逐字节复跑命中。

## 5. experiment_addendum 表实况(append-only,焊死)

实况 **4 行**(identity 序号空间至 6;**空洞 2/3/7=自检探针事务回滚,同 item1 §7 现象,登记不修**;⚠ 空洞语义随 Q4 纸面稿注明=人令 2026-07-12):

| addendum_id | exp_id | category | affects_verdict | result_sha256 锚 |
|---|---|---|---|---|
| 1 | 3 | strategy_version_qualification(附注a,人批原文) | false | `e3d2aef9…` |
| 4 | 3 | cleaning_defect_st_row0(附注b,含③diff实测) | false | `e3d2aef9…` |
| 5 | 5 | cleaning_defect_st_row0(附注b,含③diff实测) | false | `c010ce9d…` |
| 6 | 5 | event_view_tie_break_defect(附注c,tie人拍A) | false | `c010ce9d…` |

原 result_json 一字不动(补录前后 sha 断言全等);verify_addendum 8/8。

## 6. 两处超字面加固清单(施工中上报、人追认 2026-07-12)

1. **INSERT 出生焊死**(①,item1 §5):台账新行出生即受状态机字段约束(registered 态禁带 result/frozen_at/done_at 出生),超施工单字面"字段变更绑定迁移"的反向补强;
2. **引擎读径全收**(②,item2 §1):taosha_engine 对 `*_current` 视图+taosha 底表 SELECT 全部收回,唯一读径=manifest 路由 `*_snap`,超字面"不给引擎扩权"(收权而非仅不扩)。

## 7. 环境与集成回归实况(⑥)

Python 钉版 3.14(两台 3.14.4)+ 依赖锁 + verify_runtime strict 21/21;**端到端集成回归 verify_integration 7/7**(manifest 幂等生成→路由读取 fail-closed→survivors 主干清洗→检验→报告,同 manifest 双跑逐字节同,零台账写入断言);manifest 实况 2 行(#1 `2a8a271f…` 研究用/#2 `f660d76b…` 集成自检幂等生成,向量差=market_return 2)。自检家族总清单见 item6 验收档 §3(44/44+16/16+8/8+21/21+7/7+随件自检+合成 `3116ba9b`)。

## 8. 交付声明

六项施工与验收实物齐(①–⑤ 已过架构窗口,⑥ 随本总表交付)。**本总表交付=硬化窗口施工全毕**;流程余项=外部第二视角复审(咨询输入)+ 人终审(终签权=人)→ 窗口关闭,恢复假设检验(轮巡指针→分析师预期,检验排产人拍)。
