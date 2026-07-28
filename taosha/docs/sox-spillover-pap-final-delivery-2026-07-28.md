# exp24 sox_spillover 终版 PAP 候选 · 交付档（2026-07-28）

> 性质：数据前置验收 + 终版 PAP 文本收口；**不是冻结令**。本单元零数据库写、零研究
> manifest、零 A 股事件后收益读取、零正式运行、零 persist。

## 1. 开工状态与数据前置只读验收

- exp24=`registered`，`frozen_at/result_json/done_at`均空；台账 25 行=
  registered 13 / frozen 2 / done 9 / closed 1；无 exp24 研究 manifest。
- qbase 批 13=`nasdaq_giw:sox_daily`：3,395 行，2010-12-30..2024-06-27，
  close 空值 0；批 14=`tushare:sw_member`：208 行（184 现役），202 个证券，
  `in_date` 1998-09-24..2026-07-10。
- 源级快照 247 digest=
  `4a0dbd9e93e931422584036a50d0c522108f4c1cf8b481193133c4bc9fe1f450`；
  taosha 权威行、qbase 镜像、publication attestation 三处一致。qbase 向量明确含
  `sox_daily=13`、`sw_member=14`。snapshot 247 仅为数据前置源锚，不是 exp24 研究
  manifest。
- 封存触发脚本本轮只读复跑（只读 `sox_daily_snap/sw_member_snap/trade_cal_snap`，
  未触 A 股价格或收益）：SHA256=
  `b9c752d1d48346aa13255804a0711f2098a0456faa2f535856c16ab9eb711079`，与数据闭合
  交付一致。漏斗为 SOX 触发 314（up 161/down 153）→映射日 301→D4 碰撞 9 日、
  整组剔除 22 个触发→存活触发事件日 292（up 150/down 142）；±3% 恰等边界 0，
  存活事件日零成员日 0。

据此认定人裁 A4 的 SOX 源与 B1/C2 的半导体成员池两项冻结前数据前置已经闭合。

## 2. 终版候选实物

- 文件：`taosha/docs/sox-spillover-pap-final-2026-07-28.json`
- 顶层键：19；在草案 18 键基础上新增独立 `signed_ar`，其四个结构键与 exp20 同构：
  `application_level/estimand/formula/single_verdict`。
- 文件 SHA256 = 引擎 `canonical_pap_sha256` =
  `702637cb21ae2a6fb50b48a54574aac9a0e57c596bca6f8a1b90bc0db58e675a`
- `validate_pap` PASS；`parse_test_windows=(5,20,60)`；文件字节严格为排序键、紧凑分隔符、
  UTF-8 canonical JSON 加末尾单换行。
- 全文未决占位扫描：`待人/草案/NOT-FROZEN/尚未进入 qbase/未入库/未产出/冻结前必闭`
  均为 0。NOT-FROZEN 身份由本交付档和状态标记承载，不污染冻结正文语义。

## 3. 人裁落键

- A4：Nasdaq 官方站点内部端点为主锚，明确不得称官方授权 API；Yahoo `^SOX`仅交叉，
  不回改主锚。
- B1/C2：池限定申万半导体 L2 `801081.SI`，不扩电子链；采用 Tushare 重采批 14，
  接受“现行体系回溯+历史进出日期”的半 PIT 语义并写入偏差声明。
- D4：同一 A 股映射日对应多个 SOX 触发时整组剔除，仅计数；禁止累计、取末日或拆分。
- E1：知情接受低功效；正式 result 强制报告触发事件日数、ρ̄、N_eff，不因此调阈值。
- 确认清单 #1–6：τ0=映射日当日、三窗 5/20/60、market 等权、清洗冻结常量、
  2011-01-01≤event_date<2024-07-01、cost 四值与 `st_policy='reject'` 全部落键。
- `signed_ar` 明确符号作用于事件窗、估计期异常残差与全部方向相关统计输入，禁止只改
  最终 CAAR；合并事件集只产一个 ADJ-BMP 顶层判决，direction 仅 NFV 诊断。

## 4. 草案到终版的程序化对账

顶层键变化：新增 `signed_ar`；为消除占位并写入数据实物，改写
`benchmark/bias_statement/cleaning/diagnostic_dimensions/engine_params/event_def/pool/
reporting_commitments/snapshot_batch_req/verdict_power_note/window`。

逐字不变的 7 键：`analysis_type/cost/holdout/pap_digest_binding/pap_schema_version/
sample_gate/verdict_authority`。草案文件本体零修改，另立 superseded 标记。

## 5. 停止线

终版候选尚未冻结。下一步只能由人：

1. 复核本文件与 digest；
2. 亲自给出方向与把握度预判；
3. 另下绑定 digest 的冻结令，并决定冻结后最小适配施工授权。

未令不得冻结、建 exp24 研究 manifest、读取 A 股事件后收益、正式运行或 persist。
