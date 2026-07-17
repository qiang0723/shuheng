# exp8 冻结前回修单元 · 交付验收档(2026-07-17 深夜二;人令=`limit-open-premend-order-2026-07-17.md`)

> ⛔ **本验收结论已被撤回(人 2026-07-17,外部复核,执行令=`limit-open-premend2-order-2026-07-17.md`)**:
> 交付暂不通过;C1、C3、C6 及 P1-4 未按裁定形成真实执行行为;原测试虽为绿灯,但部分 fixture
> 固化的是旧错误行为,**不构成验收通过**。本档正文仅作历史留痕,不再具验收效力。
> §1 之 PAP digest `a6a2da9a…` 已作废(文件本体永久保留,见 `limit-open-pap-final-2026-07-17.WITHDRAWN.md`)。

> 性质:回修交付,**非冻结令**。全程未写 driver、未读收益、未生成 manifest、台账零写入、未运行正式研究。

## §1 最终 PAP JSON 及 digest

- 实物 = `taosha/docs/limit-open-pap-final-2026-07-17.json`(canonical 序列化:
  `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',',':'))` + 末尾单换行)。
- **文件 sha256 = `a6a2da9aeaf72ab8479b49b06b0206b86d4bbe0305f064e6da5b2d66f07393a9`**
- canonical 串本体 sha256 = `2c876978da7f1c0367d3b7599f07628b668c4c26c7dd460a38be49323b3baf47`
- 结构预验:`validate_pap` PASS(schema v2/analysis_type=event);`parse_test_windows`=(5,20,60)
  =主[0,+4]/次级[0,+19]/稳健[0,+59]。
- 相对草案的裁决落点:C1=引擎实物 τ0(含顺延+超5剔,入 cleaning 句)/C2=乙案 `st_policy='keep'`
  (spec §5 之 exp8 单点例外,入 cleaning+engine_params)/C3=甲案预注册(入 bias_statement)/
  C4=涉事链全剔上报(入 event_def)/C5=行序号≤30+listing fail-closed(入 event_def)/
  C6=结构化 NOT_FOR_VERDICT(入 verdict_authority+engine_params.nfv_structured)。
  **P1-4 偏差声明=新增 `bias_statement` 键:"方向未知、估计对象限于存活样本",显式作废承 exp4
  之"保守方向"措辞(仅对 exp8;exp4 已闭卷不动)。**
- 新增 `engine_params` 键 = 回修三参数冻结值(st_policy/verdict_policy/nfv_structured
  + strata_enabled/st_mode/benchmark_mode),driver 施工时逐字消费,不留运行时选择。

## §2 触碰面(全部在人令授权内)

| 文件 | 动作 |
|---|---|
| `taosha/compute/limit_open_rules.py` | listing 锚定 fail-closed 三类异常(P1-2/C5):`_listing_anomaly` + 候选事件剔除留痕 + counters |
| `taosha/harness/verify_limit_open_rules.py` | fixture 33→**40**(listing 七例:缺 listing/缺 list_date/上市日前 bar/delist≤list/bar 越退市日/健康窗照收/无链票计数) |
| `taosha/engine/cleaning.py` | `st_policy` 参数('reject' 默认原行为逐字 / 'keep' 保留入样本;非法值拒) |
| `taosha/engine/survivors.py` | `st_policy` 穿线(默认 'reject',零判断) |
| `taosha/engine/runner.py` | 三参数显式化:`st_policy`/`verdict_policy`('three_method' 默认=spec §6 原行为逐字保留;'adj_bmp_main_only'=P1-1)/`nfv_structured`(C6:非权威块注入 not_for_verdict、分层块 verdict 键改名 sig_state_report_only、审计记参数;默认 False 零新键);`_board_strata` ST 注记随策略 |
| `taosha/engine/report.py` | 分层键名回退渲染 + NFV 水印段(有键才渲染)+ board_strata 非 dict 值守卫 |
| `taosha/harness/verify_limit_open_engine.py` | 新增,32/32(见 §3) |
| `taosha/docs/limit-open-pap-final-2026-07-17.json` | 新增,终版 PAP 实物 |
| qbase 一切对象 / 台账 / manifest / driver | **零触碰** |

## §3 fixture 结果(必验逐项映射)

- `verify_limit_open_rules` = **40/40 PASS**(两台):必验"上市日前历史bar、缺失list_date及上市区间
  异常fail-closed"= listing 七例全绿;原五性质 33 例零漂移。
- `verify_limit_open_engine` = **32/32 PASS**(两台):
  - 必验"T+1停牌顺延1/5/6日边界"= 顺延1(留,τ0=T+2)/5(留,τ0=T+6=上限)/6(剔 postpone)
    ×{纯一字、一字+停牌缺行混合}全绿;**实物注记如实报告:T 或 T+1 纯停牌走 item7 先剔
    'suspension' 不进顺延**(冻结既有行为,fixture 固化)。
  - 必验"st_policy=reject/keep"= 默认不传/显式 reject=ST 剔除逐字零回归;keep=保留入样本
    (is_st 留标、全流水线 ST 层 valid>0、N_valid 严格增、注记切换);非法值拒。
  - 必验"辅助方法反向不得改变 adj_bmp_main_only 判决"= 秩反向/日历反向两用例:
    three_method=AMBIGUOUS(既有行为保留)vs adj_bmp_main_only=**SIG 不改判**+分歧逐字入
    note;聚集假阳性、三法同向、INSUFFICIENT 闸两策略同;非法 policy 拒。
  - 必验"所有非权威结果结构化 NOT_FOR_VERDICT"= 全 result 递归扫描:唯一 `verdict` 键=顶层,
    分层块=sig_state_report_only;标记块清单={per_tau, n_eff_rho, robustness, type_strata,
    tradeable, board_strata, censor_diagnostic, industry_coverage, car.robust_window
    (+secondary_windows 三窗时)};审计记三参数;渲染含水印段。
  - 默认路径:双跑逐字节相等、零新键、分层 verdict 键在位、ST 注记原文不变、渲染无水印段。

## §4 既有全家福回归(两台全绿,aliyun=钉版 venv python)

状态机 46/46 / pap 硬门 23/23 / addendum 14/14 / 快照镜像 11/11 / manifest 血缘 24/24 /
fail-closed 探针 19/19 / **集成回归 7/7** / 运行时钉版 ALL PASS / 三窗 5/5 / holder_sell 规则
81/81 / holder_sell 适配 10/10 / 敏感性块 6/6 / cleaning 自检 / pap 自检。

## §5 默认路径逐字节零回归证明

- 合成 e2e(make_ashare_fixture→run_ashare_study):**改前基线=改后=两台= `3116ba9b74f7c53b…`**,
  且 AWS 改前/改后产物 `cmp` 逐字节相等,双跑确定性同。
- 集成回归 S6 双跑 sha=`63e2c9fc…`;**受控 A/B 归因**:改前 commit `1c2f1b5` 临时 worktree
  同库同环境跑集成=同 `63e2c9fc` 7/7 → 与 07-16 记录基线 `f145ac51` 之差系 **manifest 87 发布
  (库态换代)** 所致(承 3bef1f81→f145ac51 同型受控漂移先例),与本回修代码零关系;
  改前改后代码面逐字节同。
- 结构性证明:`nfv_structured`/`st_policy`/`verdict_policy` 默认值路径零新键(递归扫描),
  spec §6 三法一致裁决文案逐字保留。

## §6 边界遵守实录

未写 driver;未读任何收益列;未生成 manifest;台账 25 行零写入;未运行正式研究;qbase 零新对象。
**本交付不构成冻结:等人对终版 PAP(§1 digest)下冻结批复(批复句内嵌方向+把握度预判,密封甲案)。**
