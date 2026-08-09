# exp14 `ex_div_gap` · §7 单次正式运行交付

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 运行代码：`2b9a613144782e05ced9b7102cb43789b45d6c19`
- 运行令：`ex-div-gap-s7-order-2026-08-09.md`
- 停止点：正式运行取证；未 persist，未修改 `experiment.result_json/done_at`。

## 一、运行前硬闸与补正

Fable 行为验收通过后，John 逐字授权生成 exp14 自有 manifest 与执行 §7 单次正式运行。运行前代码
审计发现 `146eea5` 中 `assert_reference()` 只在 recon 分支调用，正式分支缺 driver 内层三值硬闸；
正式单跑当时尚未消耗。

最小补正 commit=`2b9a613`：只在正式 selection 形成后、`ViewReader` 构造前调用既有
`assert_reference(selection)`，并新增一条顺序攻击断言。统计规则、PAP、SQL、报告语义均未改。
阿里云钉版环境实测 exp14 rules=`14/14`、adapter=`39/39`，其余31个离线入口全绿；数据库套件
`46/46+23/23+14/14+19/19+11/11+24/24+7/7`；规模闸门 PASS=
`223 files / 33,247 lines / 922 functions / debt 20+50`。

本机系统 Python3.9 不支持仓内 `dataclass(slots=True)`，adapter 在导入期停止；本机又无钉版镜像，
两次均未连接数据库或运行研究。真正验收全部在阿里云钉版 Python 环境完成，失败痕迹不删除。

运行前只读断言：exp14=`frozen/trial1/llm/prescreen`、冻结时间不变、双槽空、PAP canonical=
`a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`；台账26=
`6/3/15/2`；source375 三处 digest=
`2df8e289a7c1dbacebf571db100d36d4786e4af2b994018a795882a7d4c7a6b7`，qbase 13键精确；
taosha 派生批=`market_return88/pool_b1 18/pool_b1_return18`，父池及依赖锚可证。source375 recon
再次精确命中 `4,035 / 1,083 / ef9529b1…7f2f`。

## 二、manifest 432

只执行一次 `--create --from-source-snapshot 375`，生成并发布 exp14 自有 StudySnapshot：

- `snapshot_id=432`；digest=
  `94ee4a5e88a6a6927506d902260f75fcf88a979be97569e8056fd9705bebd0be`；
- qbase 键集恰等13项：`adj_factor7/daily6/dividend17/express15/fina_audit16/forecast1/
  holder_sell_predisclose12/namechange7/sox_daily13/stk_holdertrade2/stock_basic6/sw_member14/
  trade_cal10`；
- taosha 键集恰等3项：`market_return88/pool_b1 18/pool_b1_return18`；
- taosha 权威行、qbase mirror、publication attestation 三处 content/digest 一致。

digest 与 exp19 manifest398 相同，是两者消费同一16键向量的 content-addressed 结果，不是串档；
snapshot ID 与 note 均为 exp14 专属。

在任何收益读取前，对 manifest432 独立运行选择器并调用 `assert_reference`：事件=`4,035`、恰等边界
=`1,083`、selection SHA=
`ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`，六条恒等式全真。
正式 driver 内同一硬闸随后再次通过。

## 三、§7 唯一一次正式运行

运行容器名=`s14-formal-once`；钉版镜像=`shuheng-quant:579a354`，image ID=
`sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；当前代码树只读挂载。

- UTC 时间：`2026-08-09T08:01:53.566775741Z` 至 `08:03:29.684680871Z`；
  UTC+8：约 `16:01:53` 至 `16:03:29`；
- snapshot=`432`，完整 PAP digest 断言在场；
- Docker exit code=`0`；只执行一次，未自动重跑。

主结果：

- 事件总数=`4,035`；N_valid=`3,163`；剔除=`872`，剔除率=`21.6109%`，逐年剔除合计恰为872；
- 主窗 `[0,+4]` 完整样本 N=`3,095`；CAAR=
  `-0.018488168100005337`（约 `-1.8488%`）；
- 唯一判决统计 ADJ-BMP=`-0.9132553766202723`，双侧 α=`0.05`，顶层 verdict=`NOT_SIG`；
- ρ̄=`0.06601787166688029`；Kish N_eff=`15.079964080903466`、KP N_eff=
  `14.084416947469217`，以 N_valid=3,163 复算逐位相同；
- 逐τ N(0..4)=`3163/3145/3132/3127/3117`；逐τ缺失=`0/18/31/36/46`，主窗并集缺失
  `3163-3095=68` 落在 `[max46,sum131]` 内；
- 辅助方法：朴素t=`-12.758513063610579`、Corrado=`-9.235338509530482`、日历法=
  `-5.8473913923587775`，均为 NOT_FOR_VERDICT，不改变顶层判决；
- τ0 执行限制划分：`40+125+68+0+2930=3,163`；一字板比例=`1.2646%`，只作价格观察；
- 行业 unknown=`191/3,163=6.0386%`，触发>5%告警，仅为 NFV 诊断。

密封原文为「正，把握度60%」，实测主窗 CAAR 为负；若 persist，固定读法应为“方向未命中、统计
不显著”。本交付点不写校准册、不改预判，正式入册留待 persist 终令。

## 四、报告层已知文字错位

单跑原件永久保留、不覆盖；以下两处只影响报告文字，不影响 result、选择、CAR 或 verdict：

1. exp14 专属段仍写“snapshot375冻结前参考……不是正式运行硬断言”。冻结 PAP 原始身份确为参考，
   但本次 §7 令与 `2b9a613` 已将三值升格为收益前双层硬闸；该句对本次运行已过时。
2. 通用删失诊断标题写“ST=已剔除层→有效0”，与冻结 `st_policy=keep`、板块段“ST保留”及实测
   `ST有效24`矛盾。各数值行与 result 正确，错误仅为通用标题静态措辞。

两项均未在结果开封后改代码或重渲染；交独立复核分级。若需修复，必须由 John 另令限定为报告
文字窄修，不得重跑研究、覆盖三件原件或修改 result。

## 五、取证与运行后状态

阿里云目录=`/root/s14run/`：

- `preflight_selection.json` SHA=`2d981a3ca5d10803494347b9dd3da637e59c46da5cfe6081789f74666bffbb15`；
- `result.json` SHA=`5ef3a3137b769092bc09b9f0b7cefd0ebc8480f98b4b74193babd9f05ac51a33`；
- `report.txt` SHA=`8e36af391d33f448e256d614692a88fc6a7d2e66ab1f541d998f777002620a0c`；
- `formal.log` SHA=`cc5a51cf3f3fe20e3e8b4b07653c684740808111bc777c4ac99e362cf384d730`；
- `SHA256SUMS` SHA=`5b219552274fb56e946bfef76e069f718024854f351744c2936ace717a71117a`；
  四件 `sha256sum -c` 全部 OK，13类敏感词扫描0命中。

运行后只读核验：exp14仍 `frozen`，冻结时间与 PAP MD5不变，`result_json/done_at`为空，addendum=0；
台账仍26=`6/3/15/2`；StudySnapshot现21行/max432，仅新增本令授权的 manifest432；三处 digest/向量
未变；远端 HEAD=`2b9a613`且工作树干净。

结论：manifest 与 §7 单次正式运行完成，停在取证点。本令未 persist、未追加敏感性分析；下一步只能
由独立复核核验本交付，再由 John 另行决定报告文字窄修或 persist。
