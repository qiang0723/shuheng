# exp13 `limit_down_open` PAP 终版文本收口单元 · 人裁定令(原文留痕,2026-07-21)

> 人令下达于会话内(2026-07-21 晚),本档为 F 条裁决留痕,**原文措辞即口径,不得善意改写**。
> 令性质:**授权 PAP 终版文本收口单元;本令不是冻结令**——完成后停交验点,等待人以终版 digest
> 另下冻结令。令内含:①权威数字确认 ②三处终版文本修正 ③18 键终版逐项确认 ④人预判原文登记
> (仅登记,不密封,不绑草案 digest,不写入 PAP 正文)⑤终版交付要求 ⑥范围与停止线。

---

## 人令原文

**枢衡工地:**

外部只读复核结论:exp13 PAP草案、钉批对账、主事件漏斗、36项恒等断言及交付包验收通过。现授权执行**PAP终版文本收口单元**。

本令不是冻结令;完成后必须停交验点,等待人以终版digest另下冻结令。

### 一、权威数字确认

本次冻结前数据基线为StudySnapshot 121钉批视图与交易日历轴内连接语义:

- 输入行:15,099,011;
- 一字跌停成员行:18,106;
- 最大饱和链:3,323;
- 右删失:47;
- 2007年前剔除:456;
- listing异常:0;
- duplicate mapping:0;
- reversal_hijack:26;
- 最终主事件集:2,794;
- ST:1,480;
- 非ST:1,314;
- recent_listing:29;
- seasoned:2,765;
- hijack占候选事件:26/2,820=0.922%。

旧`57.5% / 2,489 / 30.9% / 差异30条`维持作废;旧3,661不具硬基线资格,不得恢复引用。

### 二、三处终版文本修正

#### 1. 对账术语勘误

原"current−钉批=3行"改读为:

> current raw视图与snapshot 121 raw视图的批次向量及行集一致;3行差异发生在raw价格视图与"snapshot 121钉批视图+交易日历轴内连接"的正式ViewReader读取语义之间。三行均为1992/1993年的日历外周日bar,`limit_status=none`、`open_limit_status=none`,不改变A/B链集合、事件集合、reversal_hijack集合或最终主事件集合。

原交付包和脚本保持封存不改;在交付档追加勘误说明,明确原脚本中的"current−钉批"只是"current raw−钉批并日历"的简写,避免误读为批次向量差异。

不得重跑、重生成或覆盖原证据。

#### 2. N参数精确化

PAP中所有可能被理解为运行时可选的"`N≥2`"改为明确冻结值:

> `N_MIN=2`,即长度不少于2的最大饱和一字跌停链进入候选。

不得保留N的运行时选择。

#### 3. Snapshot身份精确化

终版PAP须明确:

- StudySnapshot 121仅是本次冻结前只读对账锚;
- StudySnapshot 121属于既有研究manifest,不得冒充exp13正式manifest;
- exp13正式运行前须另行生成、发布自己的研究manifest;
- exp13实际qbase依赖键固定为:

  - daily;
  - adj_factor;
  - stock_basic;
  - namechange;
  - trade_cal;

- 正式manifest必须与本次冻结前数据向量相容;如批次发生变化,不得静默沿用本次数量,须停下报人。

### 三、18键终版确认

草案18个顶层键全部批准进入终版,具体边界如下。

#### 8个沿承键

1. `analysis_type='event'`:批准。
2. `benchmark`:批准保留;本次唯一实际运行基准为`market_hypothesis=全市场等权`,`pool_hypothesis`仅为schema保留,不运行、不产生第二判决。
3. `cost`:四值批准保留为schema及审计字段;exp13是事件研究,不得据此表述为"成本后策略证据"。
4. `holdout`:批准。
5. `pap_digest_binding`:批准。
6. `pap_schema_version=2`:批准。
7. `sample_gate=30`:批准。
8. `window='T+1起,后5/20/60日'`:批准。

#### 10个对偶改写键

以下按草案批准:

- `bias_statement`
- `cleaning`
- `diagnostic_dimensions`
- `engine_params`
- `event_def`
- `pool`
- `reporting_commitments`
- `snapshot_batch_req`
- `verdict_authority`
- `verdict_power_note`

并确认:

- 估计窗为事件日前250至91交易日;
- 估计窗总长160日;
- 有效覆盖门槛112日;
- `postpone_policy='unified'`;
- T+1起不可交易状态统一顺延,最多5个交易日,第6日剔除;
- `st_policy='keep'`;
- `st_mode='event_day'`;
- `verdict_policy='adj_bmp_main_only'`;
- `diagnostic_dims=['st','listing_age']`;
- ST为首要NFV诊断轴,listing_age为第二NFV诊断轴;
- B连续性口径仅作NFV对照;
- reversal_hijack只进入事件几何audit,禁止进入收益、CAR、显著性或独立结论;
- 顶层主窗ADJ-BMP为唯一判决权;
- 朴素t、Corrado、日历时间法、次级窗、稳健窗及所有诊断层均不得改判;
- 效力固定为`llm/prescreen`,不得写成full。

### 四、人预判原文登记

人已给出以下预判原文:

> 主窗`[0,+4]`市场调整后CAR为正,预计约`+5%`,即连续一字跌停真正开板后出现超跌反弹;把握度70%。

解释边界:

- `+5%`为主窗平均市场调整后CAR的幅度预判;
- 不是"上涨股票比例";
- 不预判统计显著性;
- 方向为正,机制解释为超跌反弹。

**本令只登记预判原文,不构成正式密封,不得把它绑定当前草案digest `a432877a…89e2`,也不得写入PAP正文。**

待终版PAP digest生成并经人复核后,由人另下冻结句,将以上原文逐字绑定终版digest;不得由工地改写、补充或平移。

### 五、终版交付要求

1. 新建PAP终版JSON,不覆盖草案文件。
2. 草案继续保留`NOT-FROZEN`标记,并注明已被终版候选取代但从未冻结。
3. 提交:

   - 终版文件完整路径;
   - 文件SHA256;
   - 引擎canonical重算digest;
   - 文件SHA与canonical digest逐字相等证明;
   - `validate_pap`结果;
   - `parse_test_windows=(5,20,60)`;
   - 草案→终版程序化逐键diff;
   - 证明变化仅限本令要求的文本精确化;
   - 18键完整清单及人裁映射。

4. 交付档追加:

   - 3行差异术语勘误;
   - snapshot 121只读对账锚身份;
   - 正式exp13 manifest尚未生成;
   - 人预判原文待终版digest绑定,不得写成已密封。

### 六、范围与停止线

本单元仅允许修改:

- PAP终版文本;
- 草案状态标记;
- 交付档;
- 人令留痕;
- `ops/STATE.md`。

继续禁止:

- 修改生产代码;
- 修改统计内核;
- 新增driver或report分支;
- 读取收益;
- 计算CAR或显著性;
- 冻结exp13;
- 新建source snapshot或研究manifest;
- 正式运行;
- persist;
- 写入台账。

不重复数据双跑,不追加第三跑,不重新生成既有证据。

完成终版PAP及digest后立即停交验点。下一步只能由人另下:

> 终版PAP digest冻结令+上述预判原文绑定令。
