# holder_sell 规则 v2 施工+验收档(人裁 2026-07-16,§7 正式运行)

> 裁决留痕=`docs/holder-sell-rules-v2-ruling-2026-07-16.md`(F 条,commit `5a4b19b`)。
> 本档=交付六件:规则 v2 / 裁决表 / 攻击测试 / 漏斗差异 / manifest / 正式运行结果。
> 证据实物=/root/s2b_gates/(SHA §8)+/root/s7run/。

## §1 规则 v2 实物(taosha/compute/holder_sell_rules.py,commit `e23b61e`+修缮)

| 裁定 | 落地 | 关键防护 |
|---|---|---|
| A1 到期→结果类 | `减持[^，。；]{0,12}计划[^，。；]{0,8}(期满|届满|到期)`+兜底面增"到期" | 负语境掩码扩:①`(限售|锁定|解禁|禁售|持有)…到期`②**资管/资产管理/纾困/信托/理财…计划到期**(语料实测 9 行,含"纾困计划到期按规定披露减持计划"真首披,不加此掩码兜底面会误杀) |
| A2 达到N%→进展 | `progress_reached` 子标签:`减持…(达到|累计超过|累计达到|(?<!不)超过)…N%` 且无新计划披露指示 | ①`(拟|预计)…减持`前掩(拟减持达到N%=新计划不误判)②`(?<!不)超过`(**"减持不超过N%"=计划上限**,语料 300184 实证)③含"暨后续/及未来减持计划"指示者按 A2 原文不归进展→fwp 形态表外 fail-closed |
| A3 修正→修订类 | `减持[^，。；]{0,12}修正|修正[^，。；]{0,4}减持` 锚定 | 按裁定原文"不得因无关事项修正误杀首次"——"修正"**不入**广义兜底面(兜底 suspect 亦是误杀;冻结语料"修正"行全集=1 条且被锚定命中,零残余) |
| A4 跨代码 PIT 归属 | `_dedup_and_attribute`:公告京日∈[list_date, delist_date) 唯一命中保留;无/多命中 `pit_attribution_unresolved` fail-closed 留痕;listing 缺省=fail-closed | 禁输入序(v1 行为已废);listing 经 explore_reader_listing(_snap) 视图 |
| A5 中键降级 | 30 日窗只产 `diagnostics.midkey_candidates_30d` 诊断清单,**零剔除**;自动去重仅=①id 重复②强键③冻结裁决表在册对 | 裁决表 SHA256 焊进模块常量,`load_adjudication` 前置断言改动即拒 |
| A6 fwp 单列 | `first_with_progress` 类:达到N%(带防护)+并披指示(预披露 或 新/后续/未来…减持);逐行裁决表门,过门者 1% 门比例=**裁决表新计划比例**(覆写 parsed);表外/未过=fail-closed | 不成新假设、不独立 verdict(块内零判决键,§5 敏感性同理) |

## §2 冻结裁决表(taosha/compute/holder_sell_adjudication_exp4_v1.json,SHA256 `78847ed14a017482c4a71b723f0593965e60e3dff9f5222ab81f8ce3f218751e`)

构建=`build_adjudication.py`(证据源 gate_pdf_verdicts3.json+gate_a6_fwp.json+窄闸报告 §1.2 终版):
- **pair_drops 54**=item2b 同计划坐实 13(剔后续)+item2b 疑似15+证据不足18=33(剔后续标
  `ambiguous_possible_duplicate`)+item1_mid 同计划 7+疑似 1(300266);链式对(603616/300664/301259)
  全部收敛"最早者存"。**item1_mid 权威=报告 §1.2 终版人工判读**,与抽取器自动判定两处出入均注记
  (301182 auto=SAME 被人工判读覆写=真实新计划;300505 auto=DIFFERENT 人工判读=同计划修正)。
  注:报告 §1.2 表"300366/300707 等"行经与 verdicts3 逐对核对系 **300266 之误写**(300366/300707
  属 item2b 13 坐实清单),裁决表按 12 对实物 aid 构建。
- **pair_keeps_different 126**=item2b 不同计划 122+**300143/301182 两条真实新计划恢复**+002426/300736
  两泄漏对(b 侧由 A1/A2 类拒,非同计划对,无 pair 处置)。
- **first_with_progress 12 行逐条核验(人令 A6)**:总数 12/过门 **9**/fail-closed **1**/非并披 **2**。
  - 过门 9(新计划比例,PDF 计划句锚定):000034=1.0、000607=5.99、002194=**0.50**(<1% 门,后续被
    比例门正常拒)、002298=1.0(**人令陷阱案坐实**:parsed 1.0 系进展/90日窗数字;PDF 计划句=
    14,510,635 股,由披露持股 71,542,543 股=总股本 9.67% 推得≈总股本 1.96%,90 日窗总股本口径明示
    1%,取保守 1.0 登记)、002361=2.76、002530=1.08(进展句 2.25% 另列,两源可区分)、002618=2.0、
    300256=1.0、300518=1.0(后两条=被动减持,计划总量未另标,取明示总股本口径下限)。
  - fail-closed 1:002209(PDF 正文无计划/进展锚定句可抽取,两比例来源无法可靠区分)。
  - 非并披 2:002047(含提前终止并披=A6 定义外,combo 类拒照旧)、300184(不超过1%=计划上限,
    PDF 证实无进展成分,正常首次不经 fwp 门)。
  - 对账:v1 下 12 行中 9 行在事件集(非报告所记 8;300184 计入与否口径差,如实登记);v2 下 9 行
    仍在(8 过门+300184),事件集此面**零净变化**——A6 处置的效应=堵住将来漂移+002209 类不可核验者。
- **不可变边界(人令)**:本表于本次 exp4 冻结;正式运行后获新证据只能另建版本+新 manifest 重跑留痕。

## §3 攻击测试(fixture)

- `verify_holder_sell_rules.py` **81/81 PASS**(两台):v1 全部用例保留+真实反例(人令"不能只测合成
  标题"):A1 泄漏 3 实题+资管到期 2 实题、A2 300736 实题+累计超过、A3 300505 实题+无关修正负例、
  A4 招商南油真实 aid 三态(唯一命中/多命中/无 listing 全 fail-closed)、A5 中键改判(30 日内不剔+
  诊断对留痕)+裁决表两理由、A6 四态(过门覆写/未过/表外/**parsed=5.0 计划=0.5 陷阱→比例门拒**)、
  冻结裁决表实物 8 断言(SHA 拒改/54/13/33/恢复行不在剔集/12 行/9 过门)。
  三处 v1 期望值改判均注记人裁出处,非删除。
- `verify_holder_sell_adapter.py` 10/10 PASS。

## §4 漏斗差异(人令五.4;/root/s2b_gates/funnel_v2_diff.json,输入=explore_reader 视图 batch12=§7 消费面)

| | v1(作废) | v2 |
|---|---|---|
| input/unique | 23,371/23,366 | 同 |
| 类判别 | 首次 20,099 | 首次 19,922+fwp 12;result 245→**388**(+143)/combo 102→**120**(+18)/progress_reached **10**(新)/revision 278→279/suspect 44→**37** |
| 关联去重 | 强键 2+中键 12 | 强键 2+裁决表 45 生效(13 坐实中 1 条已先被 progress_reached 类拒,表条目幂等) |
| 比例门后 | 12,334 | 12,204 |
| **事件** | **12,165** | **12,042**(−123 事件日) |

公告级:**出 132 / 进 2**,全量归因:
- 进 2=**300143(1207901152)+301182(1220023184)人令恢复坐实**(v1 剔因均=same_plan_midkey_window);
- 出 132=result 70(全部"减持计划到期"结果公告,逐题眼检零误杀)+combo 12(全部"计划到期暨新计划
  预披露"并披——v1 对同语义"期满暨预披露"早已 combo 剔,词表缺"到期"致漏网,归并既有冻结政策)+
  same_plan_adjudicated 12+ambiguous_possible_duplicate 33(裁决表)+progress_reached 3(纯进展)+
  fwp_not_adjudicated 2(并披形态不在人框定 12 行核验集,fail-closed 留痕);
- 泄漏清零断言:v2 事件集"减持计划到期"型残留 **0**、"达到N%无预披露"型残留 **0**;
- **招商南油 5 事件全部 601975.SH**(v1 全归退市码 600087.SH=输入序错误归属实锤;事件日不变);
- 中键 30 日诊断清单(不改集合):**1 对**(A1-A3+裁决表落地后自然收敛,301182 型占窗已消除);
- holder 未解析统一口径(人令):首次候选 7,133/其中 4,828 进原事件集/涉 4,782 事件=39.31%(v1 面)。

## §5 敏感性块(人令五.5+批复边界)

driver 纯后置函数(`split_sensitivity_events`/`sensitivity_block`),同 manifest 同一次运行,
`sensitivity_holder_resolved_only` 块 `not_for_verdict=true`、块内递归零 verdict 键;render 段键守卫。
`verify_sensitivity_block.py` **6/6 PASS**(两台):S1 结构/S2 **删除整块后主 result 与独立无块重算
逐字节同**/S3 verdict 显式等/S4 渲染零回归(无块==删块)/S5 复算真实性(30/40,CAAR 可区分)/S6 双跑确定。

## §6 回归全家福(2026-07-16 深夜,aliyun 生产)

规则 81/81+适配器 10/10+敏感性 6/6+三窗 5/5+状态机 46/46+pap_gate 23/23+addendum 14/14+镜像 11/11+
lineage 24/24+探针 19/19+**集成 7/7(S6 双跑 sha `f145ac51` 同基线)**+冻结覆写 PASS+runtime ALL PASS;
AWS 合成 e2e `3116ba9b` 双跑逐字节同基线(report.py 增敏感性段键守卫零回归硬证)。

## §7 manifest+正式运行

- 首次 `--create --from-source-snapshot 74` 被血缘触发器拒(market_return 批 39 锚 trade_cal=8≠快照 74
  向量 trade_cal=10;批 9/10=第三轮审计并发测试批,业务内容与批 8 逐行全等)——第二轮验收档遗留注记
  预告情形,fail-closed 正确方向。
- 合法再种序(第三轮人批范式,人令"使用 source snapshot 74 创建研究 manifest"即排产):三派生批绑
  `--source-snapshot-id 74` 再种,新旧批双向 EXCEPT 逐行全等验证:market_eqw_return 批 88 vs 39=**0/0**
  (双算闸 6.523e-16);pool_b1 批 18 vs 5=**0/0**(2,948,735 行/8,068 评估日/均池 365.5 同数);
  pool_b1_return 批 18 vs 5=**0/0**(8,066 行,双算闸 1.683e-16)。注:pret 首跑误带 --verify(独立
  验收模式,引擎读 pool_b1_current 已收权=第二轮遗留携带项)未落库零残留,按 E2E 范式重跑。
- 研究 manifest **87**(digest `21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd`)=
  qbase 半=快照 74 向量(holder_sell_predisclose:12/trade_cal:10 等 8 键)+taosha 半=
  {market_return:88, pool_b1:18, pool_b1_return:18}。
- **§7 单次正式运行**(exp4 frozen,非诊断,冻结版本,人令"只运行冻结后的正式版本"):§9。
- §5 挂起两项验收随之闭合:①六类拒=§3+§4 泄漏清零;②legacy 事件版合法路径跑通=本次正式运行。

## §8 证据 SHA(sha256 前 16 位)

| 实物 | sha |
|---|---|
| holder_sell_adjudication_exp4_v1.json(仓内=库外同物) | `78847ed14a017482` |
| gate_pdf_verdicts3.json(168+12+2 对逐对证据,窄闸产物) | `e1225fb496762e07` |
| gate_a6_fwp.json(A6 12 行 PDF 证据句) | `1f1f58aff109fed3` |
| gate_a6_fwp.py(A6 核验件) | `311e0ecf14ea82a9` |
| build_adjudication.py(裁决表构建件) | `0d3f4b8eba9d6bcf` |
| funnel_v2_diff.py / funnel_v2_diff.json | `0063c0b77116560e` / `652ad9cc90714c3f` |

## §9 正式运行结果(§7 单跑,2026-07-16 深夜,RC=0)

- 运行形态:exp4 status=frozen 非诊断正式路径(铁律③),manifest **87**,market 全市场等权单跑
  (人裁② 07-15),三窗固定判决角色(人裁① 07-15:5日主检验唯一进 verdict/20日预注册次级/60日稳健);
  运行代码 HEAD=`010bb14`(与仓 HEAD 差仅验收档 docs,代码面同一);单次运行,无第二跑。
- 选择面(audit 留痕):23,371 行 → **12,042 事件**(==§4 漏斗差异 v2 全等,pit conflicts 5/中键诊断对 1/
  adjudication_sha256 入 audit)。
- 样本:N_valid=**9,003**(剔除 3,039=25.24%,item 11 同报告警;ρ̄=0.1069 → N_eff Kish 9.3/KP 8.3)。
- 主窗 [0,+4]:CAAR=**−0.00494**,ADJ-BMP=−0.113(双侧 α=0.05 临界±1.960)→ 不显著;
  朴素 t=−6.675 显著而 ADJ-BMP 不显著=聚集假阳性,以 ADJ-BMP 为准;Corrado 秩 t=−3.121[dir−1]、
  日历时间 t=−4.035[dir−1](三法方向一致为负,均不改判决权)。
- 次级窗 [0,+19](不判决):CAAR=−0.00873,ADJ-BMP=−0.028;稳健窗 [0,+59]:CAAR=−0.01634,ADJ-BMP=+0.074。
- **verdict = NOT_SIG**(统计终态,非交易判断)。
- 敏感性块(NOT_FOR_VERDICT,人令五.5):排除 holder 未解析事件 **4,702=39.05%**(v2 面实测;v1 面口径
  4,782/39.31% 如实并记),保留 7,340,复算 N_valid=5,528,主窗 CAAR=−0.0063、ADJ-BMP=−0.153 ——
  与主跑同向同不显著,**方向未因身份缺失样本改变**;按令不做择优改判,结论解读权在人。
- 产物(/root/s7run/,持久盘):exp4_result.json sha256 `b5edac5d143e6979…` / exp4_report.txt sha256
  `3d01ffec299649b8…` / run7.log / 裁决表副本;台账 25 行零写入(persist 待人验收另令)。
- §5 挂起项②"legacy 事件版合法路径跑通"随本跑闭合:源级快照 74 → 再种三批(EXCEPT 0/0)→ 研究
  manifest 87 → frozen 正式运行 → 报告,全链 fail-closed 门逐一放行,零旁路。

## §10 工时(§8 同期记,2026-07-16 深夜段)

研究≈1.5h(裁决评审+A6 十二行 PDF 逐条核验+裁决表构建判读+漏斗差异归因眼检)/
维护·审查≈1.5h(规则 v2+fixture+敏感性块施工与自检+全家福回归+再种序+manifest+§7 运行看护)。
