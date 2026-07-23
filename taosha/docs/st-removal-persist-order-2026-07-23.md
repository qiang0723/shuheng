# exp12 `st_removal` persist 终令 + 正式闭卷(原文留痕,2026-07-23)

> 人令下达于会话内(2026-07-23 二深夜),本档为 F 条裁决留痕,**原文措辞即口径,不得善意改写**。
> 令性质:取证验收通过;授权 persist(既有状态机单事务)并正式闭卷;闭卷留痕四条;
> **完成后停工交终签,不再追加重跑或敏感性分析。**

---

## 人令原文

**枢衡工地:**

exp12取证验收通过,授权persist并正式闭卷。

前置只读断言,任一不符立即停止:

/root/s12run/result_exp12.json SHA256必须为
92ff3eacbc7237cfb7f10ea83491f13cbff4de263fff879be5c3dbb0b97f4a7f;

exp12仍为frozen,result_json与done_at为空;

PAP canonical digest=62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353;

manifest 212三处digest一致;

result关键值为:NOT_SIG、事件641、N_valid 473、主窗N 463、CAAR 0.017953489818958123、ADJ-BMP 0.24556225505262455;

台账25行,分布14/3/7/1。

确认后仅走既有状态机,以taosha_app同连接单事务执行:

start_running(12) → finish(12, 已验收result原件) → 一次COMMIT

禁止重跑、改写result、旁路SQL或新增台账行。

persist后核验:

exp12=done、verdict=NOT_SIG;
库内result与原件parsed_equal;
台账25行,分布14/2/8/1;
manifest、PAP及三件产物SHA不变;
两台git干净同步。

闭卷留痕:

预判"主窗CAR为正、约+5%、把握度70%"对照实测+1.795%:方向命中,但幅度低于预判;ADJ-BMP不显著,终态NOT_SIG;

不得把朴素t、日历法名义显著改读为有效结论;Corrado反向分歧如实保留;

τ0一字板71/473仅为价格观察,不构成可成交策略证据;

效力维持llm/prescreen。

完成后停工交终签,不再追加重跑或敏感性分析。
