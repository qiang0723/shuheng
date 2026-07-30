# exp16 `yearend_strength` manifest + §7 单次正式运行交付

日期：2026-07-30（UTC+8）  
授权令：`taosha/docs/yearend-strength-s7-order-2026-07-30.md`  
PAP digest：`3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345`

## 1. 二元结论

§7 唯一一次正式研究执行 `RC=0`，统计结果为 `NOT_SIG`；exp16 运行后仍为
`frozen`，`result_json/done_at` 为空，ledger 零写入，persist 未执行。

但正式 `result/report` 遗漏冻结 PAP 强制要求的 `llm/prescreen` 效力水印。
该缺口不改变事件、样本、统计量、判决或血缘，但影响正式产物解读边界；因此本次
交付停在取证点，**不进入 persist**。原始三件保持不变，不自动重跑、不自行修补。

## 2. manifest 与运行锚

- source snapshot：`74`，digest
  `075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`；
- exp16 自有研究 manifest：`317`，创建于
  `2026-07-30 12:05:08.853003+08`；
- manifest 权威行、qbase 镜像、publication attestation 三处 digest 均为
  `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
- qbase 八键与 taosha 三键完整向量通过，血缘 `24/24`、镜像 `11/11`；
- 正式运行镜像：`shuheng-quant:579a354`，image ID
  `sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`；
- 实际正式执行窗口：`2026-07-30 12:09:14+08` 至
  `2026-07-30 12:13:03+08`，只执行一次。

执行前选择硬闸精确命中：事件 `7,751`，selection SHA
`057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`，
三条漏斗恒等式均为真。

## 3. 正式统计结果

- 顶层唯一 verdict：`NOT_SIG`；
- 事件 `7,751`，`N_valid=6,942`；剔除 `809`，剔除率 `10.44%`；
- 主窗 `[0,+4]`：`N=6,881`，CAAR
  `-0.0031967252693485917`（`-0.3197%`），ADJ-BMP
  `-0.11178944002480809`；
- 次级窗 `[0,+19]`：`N=6,681`，CAAR
  `-0.020236189162599585`，ADJ-BMP `-0.34184903129385713`，NFV；
- 稳健窗 `[0,+59]`：`N=6,224`，CAAR
  `-0.036015496691283344`，ADJ-BMP `-0.30548020113248625`，NFV；
- `rho_bar=0.12220364037830078`，Kish `N_eff=8.174603811028497`，
  KP `N_eff=7.175637466670484`；事件集中于 14 个事件日；
- 朴素 t `-3.588868091488583`、Corrado `-2.793420569127647`、
  日历 t `-1.7454580693074708`，均为 `NOT_FOR_VERDICT`；
- τ0 执行限制审计：分母 `6,942`，一字板 `29`、涨停 `310`、跌停
  `232`、普通 `6,371`；仅价格观察，不构成可执行策略证据；
- 行业 unknown `334/6,942=4.811%`，未触 5% 升级阈值。

`N_valid-N_main=61`；逐 τ 样本量为
`6,942/6,920/6,919/6,913/6,910`，缺失并集 `61` 落在
`[max=32, sum=106]` 内。

人的密封预判为“正，把握度50%”；实测主窗方向为负。正式开封对照与校准册登记
属于 persist 阶段，本交付未写入、未改述。

## 4. 原始取证

- `result_exp16.json`：
  `31b8115b47b9c69ee72bbd62a4849ec93dc180f6307cafcacd7ae2fba8156edb`；
- `report_exp16.txt`：
  `79ca36833f8c6a8e31c291b70506f28a1a7a8ad32eb51bbc1dc328d652440709`；
- `run_exp16.log`：
  `e7bdfdd318317fc4ff0cb988825b3f5f8c8c904f62688d75db6b1e69e34b5b54`。

13 类秘密扫描 `TOTAL_HITS=0`；递归 `SHA256SUMS -c` 全部通过。证据目录：
阿里云 `/root/s16run/`。

运行后只读核验：exp16 保持 `frozen`、`frozen_at` 不变、结果双槽空；台账
26 行仍为 `registered 9 / frozen 3 / done 12 / closed 2`；manifest 317
三处 digest 不变。

## 5. 唯一停止项：效力水印遗漏

冻结 PAP 的 `verdict_power_note` 明确要求“报告强制水印”，
`reporting_commitments` 明确要求正式 result 报告 `llm/prescreen` 水印。实物核验：

- `result.audit.experiment_identity` 不存在；
- result 顶层 `source_type/verdict_power` 不存在；
- report 中 `prescreen`、`power=`、`效力`、`水印` 均为零命中。

根因位于 exp16 专属适配边界：driver 未像 exp568 一样把台账实验身份写入
`audit.experiment_identity`，专属 report header 也未 fail-closed 消费该字段；现有 fixture
未覆盖效力水印断言。

后续若获人令，只允许一个窄修闭合：补实验身份写入、报告 fail-closed 水印与攻击 fixture；
原始三件永久保留。是否以“不重跑研究、仅从已验收原件和冻结台账身份确定性生成
v2 result/report”的方式收口，须由人另行裁定；本令未授权，当前未执行。

