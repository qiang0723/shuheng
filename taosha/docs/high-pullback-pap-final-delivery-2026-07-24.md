# exp11 high_pullback PAP 终版文本收口 · 交付档(2026-07-24 四)

> 人令留痕:`taosha/docs/high-pullback-pap-final-order-2026-07-24.md`(F 条先行,commit `ec8db86`)。
> 单元性质=终版文本收口(非冻结);§3 第 1-6 项人已全部确认;方向与把握度预判待冻结令由人另绑。
> 禁区遵守:零生产代码、零库写、零冻结、零 manifest、零收益、零运行;历史原件(草案 JSON/旧交付档/令文)零修改。

## 1. 终版实物与 digest

- **终版=`taosha/docs/high-pullback-pap-final-2026-07-24.json`(新建,草案零覆盖),NOT-FROZEN 终版候选**;18 键事件版结构不变。
- **候选 digest=文件 SHA256==两台引擎 canonical 重算==`eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc`**;validate_pap PASS;parse_test_windows=(5,20,60)。
- 草案 `high-pullback-pap-draft-2026-07-24.json`(digest `00644af8…4450`)本体零改动,自本单元起为 **superseded(被终版取代,不得直接冻结)**;标记仅入本档与 STATE。

## 2. 草案→终版逐键 diff(程序化断言:改动恰 4 键,余 14 键逐字节相等)

字节级替换恰 4 处(`s11_make_final.py`,每处唯一命中):

| # | 键 | 旧 | 新 |
|---|---|---|---|
| R1 | `cleaning` | τ0映射(裁定七:CAR从事件后首个**可交易日**开始)=event_date之后首个有真实bar的**交易日**(之后=严格晚于event_date当日) | τ0映射(裁定七+人终版收口令2026-07-24)=**事件后首个有真实bar的价格观察日**(事件后=严格晚于event_date当日) |
| R2 | `window` | τ0=event_date之后首个有真实bar的**交易日**(裁定七:CAR从事件后首个**可交易日**开始; | τ0=**事件后首个有真实bar的价格观察日**(裁定七+人终版收口令2026-07-24; |
| R3 | `event_def` | τ0=event_date之后首个有真实bar的**交易日**(裁定七; | τ0=**事件后首个有真实bar的价格观察日**(裁定七; |
| R4 | `reporting_commitments` | …;效力水印强制。 | …;效力水印强制。**τ0一字板事件仅为价格观察,不得表述为可执行策略证据。**(人令原文一字不改,追加于键尾) |

- missing_bar_only 实质零变动:`engine_params.postpone_policy='missing_bar_only'`、仅缺 bar 顺延≤5 交易所交易日第 6 日剔、一字板有真实 bar 即为 τ0 入 CAR——三处语义文本未触碰,仅 τ0 称名统一。
- 键集不变(18)、`analysis_type`/`benchmark`/`bias_statement`/`cost`/`diagnostic_dimensions`/`engine_params`/`holdout`/`pap_digest_binding`/`pap_schema_version`/`pool`/`sample_gate`/`snapshot_batch_req`/`verdict_authority`/`verdict_power_note` 共 14 键逐字节相等(程序化断言)。

## 3. 验收断言(全过,两台)

1. **"可交易"零残留**:终版 canonical 串内 `可交易` 命中 0(脚本硬断言;`交易所交易日`=日历单位非"可交易",不在禁面)。
2. **正向恒等**:文件 SHA256==canonical_pap_sha256==`eaa54b3d…b6fc`(AWS+aliyun 同值);validate_pap PASS;窗口解析 (5,20,60)。
3. **逆向还原证明**:对终版按 R4→R1 逆序回替(每处唯一命中)→ 还原字节流 SHA256==草案文件 SHA256==`00644af8ef22902ca995945367b87af8e3faa79a65c2e211e3f90255beb64450`=变化仅限令内 4 处替换。
4. 历史原件零修改:草案 JSON/草案交付档/两道令文 git 内容未动(本单元新增文件=终版 JSON+本档+令文留痕)。
5. 台账零写:exp11 仍 registered 三槽空。

## 4. 取证

工具与断言输出=AWS `~/shuheng/s11_papfinal_delivery_2026-07-24/`(终版 JSON+本档+令文+`s11_make_final.py`+两台断言输出+SHA256SUMS);aliyun 镜像 `/root/s11pap/final/`。

**▶停交验点待人:①复核终版(digest `eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc`)②以终版 digest 另下冻结令+方向与把握度预判(人亲拟,绑定本 digest);未令不动。冻结后下一步(须另令)=最小适配施工(rules/driver/report 分支/fixture 常规四件)→exp11 自有 manifest→单次正式运行→persist。**
