# exp10 `volume_drought_break` 冻结与最小适配 · 行为验收（2026-07-29）

## 结论

**通过，停在行为验收点。** exp10 已按人令冻结；成交额事件规则、只读视图、driver、报告与攻击 fixture 已完成。未创建 exp10 正式研究 manifest，未读取事件后收益，未正式运行，未 persist。

人冻结预判原文为：**「正，把握度60%」**。本实验唯一解释为主窗 `[0,+4]` 市场调整后 CAR 方向为正；仅押方向，不押幅度或显著性；只绑定 PAP digest `18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`。

## 1. 冻结凭证

- 终版 PAP：`volume-drought-break-pap-final-2026-07-29.json`；文件 SHA256、引擎 canonical 重算与人令 digest 三者全等；18 键，`validate_pap=PASS`，窗口 `(5,20,60)`；
- 冻结前：exp10=`registered`、三槽空、无 manifest/addendum，数据库为占位 PAP；台账 `25=12/2/10/1`；
- 执行：`taosha_app` 同连接单事务，`FOR UPDATE` 复核后写终版 canonical 原文并调用 `ledger.freeze(10)`，一次 COMMIT；
- 读回：exp10=`frozen`，`frozen_at=2026-07-29 10:35:58.418183+08`；DB canonical 与人令 digest 相等，`parsed_equal=True`，载荷 MD5=`dfd9963436c1b1e7c2a5a8411e175802`；
- 冻结后：结果槽与 `done_at` 仍空，台账 `25=registered 11/frozen 3/done 10/closed 1`，恰迁一行、零新增。

冻结脚本与日志存阿里云内部证据目录 `/root/s10freeze/`。

## 2. 最小适配与可维护性

施工链：`5944c02`（F 条令文）→ `14660dd`（规则、视图、driver、fixture）→ `77f2639`（报告模块化）。

- `qbase/sql/022_volume_drought_reader.sql`：current/snapshot 只读视图对，holdout 与北交所排除焊死，最小列面仅含事件识别所需字段；已由 `qbase_app` 单事务 apply，并以 `taosha_engine` 验证可读；
- `taosha/compute/volume_drought_rules.py`：纯函数状态机，Decimal 严格边界；prior60 可跨停牌，gap/异常 bar 仅打断低量段与 armed；首次放量即终局；
- `taosha/harness/run_volume_drought_study.py`：冻结 `engine_params` 7 键逐字消费；recon 只允许 snapshot 248；正式模式拒绝 248 冒充 exp10 manifest；
- `taosha/engine/report_volume_drought.py`：exp10 专属 58 行报告模块；通用 `report.py` 只留路由，较施工初版净减少 33 行；
- 新增生产代码最大函数 85 行，其余主要函数不超过 58 行；未修改统计内核、清洗、收益或判决逻辑。

## 3. 攻击 fixture

本地钉定 Docker 与阿里云钉版 venv 独立复跑：

- `verify_volume_drought_rules`：`14/14 PASS`；
- `verify_volume_drought_adapter`：`19/19 PASS`；
- 覆盖：不足60根、prior60排当日与跨停牌、gap/异常打断、连续5日武装、30%/100%严格边界、armed 中间带、首个放量收阳/非收阳终局、重新蓄积、一阶段至多一事件、唯一性 fail-closed、研究期边界、digest/engine_params 全键消费、报告真锚/NFV/价格观察日术语；
- 报告模块化后另跑 exp11 adapter `29/29 PASS`，证明共享价格观察术语路径不外溢。

## 4. snapshot 248 只读 recon

snapshot 248 仅作为已发布只读对账锚；正式模式已显式拒绝其冒充 exp10 manifest。双跑 JSON 逐字节一致，SHA256 均为：

`4837f4c8c8cb21262f299e9dfd2092a3673fb95cc0c05cc4f05e95ce3aeaf964`

冻结漏斗精确复现：

- 视图 15,100,462 行 → 日历外 3 → 日历内 15,100,459 → 异常 232 → 有效扫描 15,100,227；
- armed 38,417 = 全期事件 27,467 + 非收阳拒绝 7,204 + gap 打断 3,328 + 异常打断 1 + 右删失 417；
- 首次放量终局 34,671 = 事件 27,467 + 非收阳拒绝 7,204；
- 研究期事件 **13,889**，事件键重复 0；selection SHA=`3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`；
- 与冻结参考逐项精确一致，未读取事件日后收益，未追数、未改规则。

## 5. 全家福与零回归

- 阿里云数据库/离线全家福 28 个入口全部通过：状态机 `46/46`、PAP 硬门 `23/23`、addendum `14/14`、snapshot 探针 `19/19`、镜像 `11/11`、血缘 `24/24`、集成 `7/7`，以及 exp8/10/11/12/13/20/24 与 holder 全部 rules/engine/adapter；
- `verify_pap_vs_spec` 为历史非全家福入口，存在既知 `synthetic_smoke` KeyError，本单元按既有边界未运行、未修补；
- 默认合成 e2e 在本地 Docker 与阿里云各双跑，四份 result SHA256 全为 `3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`，与历史基线逐字节一致；
- 阿里云证据清单 `/root/s10adapt/SHA256SUMS` 覆盖 42 件，`sha256sum -c` 全部通过。

## 6. 停止线

- 当前 exp10=`frozen`，结果槽空；台账 `25=11/3/10/1`；`study_snapshot` 仍 13 行、max=248，说明本单元没有创建正式研究 manifest；
- 本地与阿里云 HEAD 同步、工作树净；
- **正式 manifest、正式收益读取、§7 单次运行与 persist 均未授权、未执行。**

下一步仅在外部复核通过并获人新令后：生成 exp10 自有研究 manifest → §7 单次正式运行；persist 仍须结果验收后另令。
