# 淘沙切片1 · 台账验收文档(2026-07-07)

> 验收标准(spec §7 切片1):五条登记入库、pap_json 冻结、UPDATE 被触发器拒绝的实测证据。
> 库为唯一真身;以下均库实物。人三裁(2026-07-07)已落地,终验 diff 归零。

## 一、基础设施

- **DB** `taosha`(属主 postgres);role **`taosha_app`** 仅 `SELECT/INSERT/UPDATE`、**非表属主 → 禁不掉触发器**(真焊死,仿 qbase 防拆)。DSN 只住 `.env`(`TAOSHA_APP_DSN`),不入 git。
- **表** `experiment` = spec §4 契约 + v1.5 元数据列 `data_class`/`crowding_prior`。`sql/001_experiment_ledger.sql`。
- **模块** `experiment/{pap,ledger,gates}.py` + `seed_founding.py` + `verify_pap_vs_spec.py`。
- **备份**:台账入每日备份链(`qbase/sync/backup.sh` 步骤[1b],pg_dump taosha),pg_dump 实测 OK(24K)。

## 二、焊死验收(spec §2 铁律,全用触发器实现,非 CHECK 替代)

| 铁律/规则 | 实测 |
|---|---|
| ④ pap_json 冻结后不可改 | 冻结行 UPDATE pap → `RAISE 铁律④`(自测 + 提交态真实行 + 重建后复检 三次证) |
| status 单向推进 | frozen→registered / frozen→done 跳变 → `RAISE 非法迁移` |
| 不可变列锁 | 改 title/source_type 等 → `RAISE 不可变列被改` |
| frozen_at/result_json/done_at 一次性 | result 二次写 → `RAISE 一次性写入` |
| append-only | DELETE → `permission denied`(无授权)+ 触发器双锁;TRUNCATE 触发器拒 |
| family_trial 触发器自增 | drawdown_rebuy 两行自动 1→2 |
| ① llm→prescreen 强制 | llm+full 插入 → `RAISE 铁律①` |
| 合法路径放行 | INSERT / registered→frozen / running→done(带 result+done_at) 成功 |

自测(rollback 无污染)10 项全过;提交态真实冻结行拒绝已实测;台账重建后触发器 4 个仍在、复检仍拒。

## 三、状态机注记(裁2,2026-07-07)

```
registered ──▶ frozen ──▶ running ──▶ done
     │            │
     └────────────┴──▶ closed
```
- 主链:`registered → frozen → running → done`(单向,触发器白名单)。
- **`closed` = 终态**:**仅自 `registered`/`frozen` 进入,无出边**;进入**必带 `result_json` 关闭原因**;**专用于"未跑先关"**(如被同族新变体取代)。非跑出的判决态(判决态走 done + verdict)。

## 四、登记终态(五条齐,库实物)

| exp_id | family | trial | status | source | 效力 | data_class | crowding_prior |
|---|---|---|---|---|---|---|---|
| 1 | radar_heat | 1 | frozen | platform | full | NULL | NULL |
| 2 | drawdown_rebuy | 1 | **closed** | human | full | NULL | NULL |
| 3 | drawdown_rebuy | 2 | frozen | human | full | 量价 | 高 |
| 4 | holder_sell | 1 | frozen | literature | full | NULL | NULL |
| 5 | forecast_drift | 1 | frozen | literature | full | NULL | NULL |
| 6 | rv_resonance | 1 | frozen | platform | full | NULL | NULL |

- **family_trial 自增实证**:drawdown_rebuy trial1(#2, closed)+ trial2(#2b, frozen)= "改参=新行、计数+1"。
- **#2 关闭**:result_json = `{"closure":"被 drawdown_rebuy trial 2(#2b)取代,未跑"}`。

## 五、三裁落地(2026-07-07)

- **裁1**:#3 `holder_sell` source_type=**literature**(主值);platform 成分记 contamination_note(§6 literature+platform;效力 full,主值选择不影响效力=均非 LLM 来源)。已补登。
- **裁2**:`closed` 编码批准 + 状态机注记(见 §三)。
- **裁3**:创始四条(#1/#3/#4/#5)`data_class`/`crowding_prior` 留 NULL(存量转录不回填);#2b 填 `data_class=量价`/`crowding_prior=高`(LLM 拟值、人批标注);此后新登记**强制填写**(`ledger.register` 焊,存量转录用 `allow_meta_null`)。

## 六、pap_json ↔ spec §6 逐字核对(diff 归零)

独立第二转录(`verify_pap_vs_spec.py` 内 §6 原文)vs 库 pap_json,event_def + window 共 12 字段:

```
exp family          字段        核对
1   radar_heat      event_def  ✅MATCH    1   radar_heat      window  ✅MATCH
2   drawdown_rebuy  event_def  ✅MATCH    2   drawdown_rebuy  window  ✅MATCH
3   drawdown_rebuy  event_def  ✅MATCH    3   drawdown_rebuy  window  ✅MATCH
4   holder_sell     event_def  ✅MATCH    4   holder_sell     window  ✅MATCH
5   forecast_drift  event_def  ✅MATCH    5   forecast_drift  window  ✅MATCH
6   rv_resonance    event_def  ✅MATCH    6   rv_resonance    window  ✅MATCH
==== 逐字核对: diff 归零(全 MATCH) ====
```
注:通用件(成本/基准/holdout/样本量闸)取 §6 冻结常量(`pap.py`:佣金万2.5/印花税千1/滑点单边千1/一字板不可成交;池内=雷达股池等权、全市场=全市场等权;holdout_start=2024-07-01;闸=30);cleaning 逐字转录 §5;pool 为数据源结构化(非 §6 字符串)。#2b event_def/window 逐字继承 §6 #2 原文,仅池改 b1。

## 七、结论

切片1 台账:焊死实测过、五条齐(4 族冻结 + #2b 变体 + #2 关闭)、三裁落地、pap↔§6 diff 归零、入备份链。**待人终签。** 终签后 → 切片2(开工令 + 十一条核对单)。
