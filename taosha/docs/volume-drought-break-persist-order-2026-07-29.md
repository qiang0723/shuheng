# exp10 `volume_drought_break` persist终令 · 人令留痕（2026-07-29）

> John在exp10 §7结果、取证与Fable复核交验后明示：**“批准执行”**。该原文承接上一问“批准exp10 persist并闭卷”，授权范围仅为将已验收result原件经既有状态机单事务persist，并完成闭卷核验与留痕；不授权研究重跑、结果改写或追加敏感性分析。

## 一、外审B项闭合

1. `n_eff_rho`按顶层存活样本`N_valid=11,432`报告，为引擎一贯NFV诊断口径（exp24同型）；主窗ADJ-BMP在`_car_test`内另以完整主窗`N=11,312`计算，二者无混用，诊断N_eff不进入判决；
2. result既有`per_tau.by_tau`披露τ0–τ4样本量=`11,432/11,409/11,386/11,375/11,366`；主窗要求五个τ均非缺失，交集为`11,312`，差120来自至少一个τ缺失事件的并集，禁零填充；
3. KP N_eff公式为`N(1−ρ̄)/(1+(N−1)ρ̄)`，实现与result注记一致；基础镜像RepoDigest只读实测为`m.daocloud.io/docker.io/library/python@sha256:fc74d22ffd0d5ac395a4b7bdda75a4539758862c49ebf3005647084631e63789`，与Dockerfile钉死digest相同。

以上均为既有result、代码与镜像原文的只读指认，不修改PAP、事件、result或判决，不另开施工单元。

## 二、唯一输入与前置断言

- result原件：`/root/s10run/result_exp10.json`，SHA256=`211b9f44ff4bd1b64cf0892c37c846d2d4f0b33b972064d9d117cd9b77349c51`；
- report SHA256=`45dd146a6ef76fe1a7f072431ee4c592e3f1350ae1e32d5be9357f43699246ce`；run log SHA256=`f7aed5f0b1641528ae0fd7d40d7a49a7442334593c42030eb25b3f177c9bb149`；
- exp10仍为`frozen`，`frozen_at=2026-07-29 10:35:58.418183+08`，`result_json/done_at`为空；
- DB PAP canonical=`18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1`；
- manifest 271权威行、qbase镜像、publication attestation三处digest均为`21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`；
- result关键值：递归唯一verdict=`NOT_SIG`、事件`13,889`、`N_valid=11,432`、主窗`N=11,312`、CAAR=`-0.006845906033937132`、ADJ-BMP=`-0.30977878394328606`、selection SHA=`3dc4e83be46a3354cdd056995d4ec1a33a35b5ec5f0a97788d31f4847d08e0b9`、三条漏斗恒等式全真；
- 台账25行，分布应为`registered 11 / frozen 3 / done 10 / closed 1`。

任一不符立即停止，不修补、不重跑。

## 三、执行与后核验

仅以`taosha_app`同连接单事务执行`start_running(10)→finish(10,已验收result原件)→一次COMMIT`；零重跑、零改写、零旁路SQL、零新增行。

persist后只读核验：exp10=`done/NOT_SIG`；库内result与原件`parsed_equal`且canonical双侧一致；台账仍25行、分布应为`11/2/11/1`；PAP canonical、manifest 271三处digest与三件产物SHA均不变。

## 四、闭卷固定读法

校准册第七条逐字记录人的冻结预判原文“正，把握度60%”（仅押主窗方向，绑定上述PAP digest）→实测主窗CAAR=`-0.6846%`，**方向未命中**；ADJ-BMP=`-0.310`不显著，终态`NOT_SIG`。入册后七条方向读数=`3命中/4未命中`。

不得认定存在可靠的正向或负向“缩量干涸后放量收阳”效应；朴素t、Corrado秩、日历法虽同向名义显著，均为`NOT_FOR_VERDICT`，不得改写顶层判决。剔除率17.69%、行业unknown 5.4%、相关折算N_eff与可交易口径均如实保留；效力维持`llm/prescreen`。

完成后更新交付档与STATE，提交并同步，停工交终签；不再追加复核、重跑或敏感性分析。
