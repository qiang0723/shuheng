# exp10 `volume_drought_break` · manifest + §7 单次正式运行交付（2026-07-29）

## 结论

**§7 单次正式运行成功，现停在取证点。** 顶层判决=`NOT_SIG`：主窗`[0,+4]`市场调整后CAAR=`-0.006845906033937132`（约`-0.685%`，N=`11,312`），唯一权威统计量ADJ-BMP=`-0.30977878394328606`，双侧不显著。exp10仍为`frozen`，`result_json/done_at`为空；本轮未persist。

人的冻结预判原文为“正，把握度60%”，只押主窗方向、仅绑定PAP digest `18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`。密封开封对照与校准册入册留待persist终令，本交付点不改写预判、不提前闭卷。

## 1. 运行前硬闸

只读脚本`/root/s10run/preflight_exp10.py`实测全过：

- exp10=`frozen`，`frozen_at=2026-07-29 10:35:58.418183+08`不变，结果双槽空；DB PAP canonical与令定digest逐字相等；
- 台账25行=`registered 11 / frozen 3 / done 10 / closed 1`；零既有exp10正式manifest；
- source snapshot 74镜像与publication attestation digest均为`075efda777bd3bcdadac9f00cdfbcbd83ea945171d61b316fa2fccbf8ac1015c`；
- qbase八键精确为`daily=6 / forecast=1 / trade_cal=10 / adj_factor=7 / namechange=7 / stock_basic=6 / stk_holdertrade=2 / holder_sell_predisclose=12`；
- taosha三键精确为`market_return=88 / pool_b1=18 / pool_b1_return=18`；三批source anchor均指向snapshot 74，`pool_b1_return=18`父池为`pool_b1=18`；
- snapshot 74价格读视图覆盖至`2024-06-28`，`market_return=88`亦覆盖至`2024-06-28`；
- 缺市场基准的运行时实证：`sim_fit`对应异常收益为`None`，不是0。

## 2. exp10研究manifest

- 由source snapshot 74一次生成并发布：manifest=`271`，创建时间`2026-07-29 12:14:19.233988+08`；
- 完整向量键集恰等于上述十一键，无多键、无少键；
- 权威行、qbase镜像、publication attestation三处digest全为`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
- `verify_manifest_lineage=24/24 PASS`，`verify_snapshot_mirror=11/11 PASS`；
- manifest生成后study_snapshot为14行、max=`271`，experiment台账零写入。

## 3. §7唯一一次正式运行

- 精确生产代码commit=`579a354e2ae7e57783ec4e6979035edfc1e9b9e1`；生产镜像=`shuheng-quant:579a354`，image ID=`sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`，`amd64`、非root用户`shuheng`，strict runtime依赖`21/21 PASS`；
- Docker Hub元数据请求超时发生在构建阶段、正式运行前；按README既定边界改用DaoCloud透明缓存，基础镜像仍为相同钉死SHA256，依赖仍按lock，未改代码或运行口径；
- 运行窗口=`2026-07-29 12:17:37+08`至`12:25:19+08`，只启动一次，RC=`0`，log无Traceback，未自动重跑；
- PAP digest断言=`18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`，冻结`engine_params`七键逐字消费；
- 正式事件集=`13,889`；selection SHA=`3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`；三条恒等式`armed_terminal_identity_ok / breakout_terminal_identity_ok / event_period_identity_ok`全为true；
- N_valid=`11,432`，剔除`2,457`，剔除率=`17.69%`，告警如实保留；主窗完整N=`11,312`；
- 相关折算：ρ̄=`0.09654697718430001`，Kish N_eff=`10.349180778326598`，KP N_eff=`9.349998657845303`；
- 主窗`[0,+4]`：CAAR=`-0.006845906033937132`，ADJ-BMP=`-0.30977878394328606`，`NOT_SIG`；
- 次级窗`[0,+19]`：CAAR=`-0.012554080652801407`、ADJ-BMP=`-0.22129485153397868`；稳健窗`[0,+59]`：CAAR=`-0.016164729537024844`、ADJ-BMP=`-0.024282088790506796`，均`NOT_FOR_VERDICT`；
- 朴素t=`-12.899955408132525`、Corrado秩t=`-9.332`、日历t=`-6.950`名义显著，但全部为`NOT_FOR_VERDICT`，不得改写顶层判决；
- 行业unknown残余组=`621/11,432=5.4%`，升级上报；可交易口径主窗净均值约`-0.062%`，仅报告、不改判；
- result递归`verdict`键恰1个；bias_statement锚定冻结PAP digest；audit.study_snapshot完整记录manifest 271及十一键向量。

## 4. 运行后状态与取证

只读后核验全部通过：

- exp10仍为`frozen`，`frozen_at`不变，`result_json/done_at`为空；
- experiment台账仍25行=`11/3/10/1`，ledger零写入；
- manifest 271三处digest与完整十一键向量不变；
- 阿里云代码HEAD=`579a354e2ae7e57783ec4e6979035edfc1e9b9e1`且工作树净；
- 13类秘密扫描`TOTAL_HITS=0`，原始产物零修改；证据目录=`/root/s10run/`，`SHA256SUMS -c`全过。

三件原始产物SHA256：

- `result_exp10.json`：`211b9f44ff4bd1b64cf0892c37c846d2d4f0b33b972064d9d117cd9b77349c51`
- `report_exp10.txt`：`45dd146a6ef76fe1a7f072431ee4c592e3f1350ae1e32d5be9357f43699246ce`
- `run10.log`：`f7aed5f0b1641528ae0fd7d40d7a49a7442334593c42030eb25b3f177c9bb149`

## 5. 停止线

**本轮不授权、也未执行persist。** 结果原件、manifest与运行后冻结状态先交人验收并供Fable作GitHub侧独立复核；persist须由John另行明确授权。
