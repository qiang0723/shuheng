# exp11 high_pullback PAP 冻结 + 最小适配 · 行为验收档(2026-07-24 五)

> 人令留痕:`taosha/docs/high-pullback-freeze-order-2026-07-24.md`(F 条先行,commit `5826842`)。
> 施工 commit:`90efa04`(四件)+`dd2b689`(recon 取数收编 snapshot GUC 路径),与留痕/验收分单。
> 禁区遵守:**零正式收益读取、零正式 manifest 生成、零正式运行、零 persist**;
> recon 全程零收益列(SELECT 仅 ts_code/trade_date/close/board/is_st,事件几何面,止于条件齐备日)。
> 预判(人令原文,仅登记于令文留痕):主窗市场调整后 CAR 为正,把握度 60%;仅押方向、
> 不押幅度、不预判统计显著性;仅绑定终版 digest `eaa54b3d…b6fc`,不继承不平移旧表述。

## 1. 冻结执行(令二)——全 PASS

- **冻结前只读确认五项(令一)全符**:①exp11 registered,frozen_at/result_json/done_at 全空
  ②零 manifest/运行残留(study_snapshot 10 行零命中/addendum 0/result NULL)③终版文件 SHA==
  引擎 canonical 重算==令 digest `eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc`
  (两台各自重算同值)④DB 登记 PAP=未冻结占位载荷(11 键,canonical `1b36abd8…3c5c`≠终版)
  ⑤台账 25 行=14/2/8/1。
- **冻结事务**(脚本 aliyun `/root/s11freeze/freeze_exp11.py`+log,承 exp12/exp13 状态机先例):
  taosha_app 同连接单事务=FOR UPDATE 行锁内再断言(registered/三槽空/25 行 14-2-8-1)→
  UPDATE pap_json=终版 canonical 原文(仓内冻结件逐字节读入,零改写零补键)→
  `ledger.freeze(11)`→一次 COMMIT。
- **读回核验**:status=frozen,**frozen_at=2026-07-24 20:09:53.513217+08**;
  DB 载荷 canonical==令 digest;**parsed_equal=True**(DB jsonb 对象==文件解析对象);
  载荷 md5(pap_json::text)=`b754e6f7e4230a71402cb194b38e1616`;
  **台账 25 行=registered 13/frozen 3/done 8/closed 1**(恰迁一行,零新增)。

## 2. 最小适配四件(令三;missing_bar_only 引擎路径已收编零再扩)

| 件 | 实物 | 说明 |
|---|---|---|
| ① 规则 | `compute/high_pullback_rules.py` | 阶段状态机纯函数(冻结 event_def 七条逐字转录);**闭区间边界=Decimal 精确乘法比较**(触带 close≤C0×0.97/入带下沿 close≥C0×0.95 闭/破五 close<C0×0.95/MA20 不破 20×close≥Σ20,零除法零二进制舍入)=冻结闭区间文本忠实实现 |
| ② driver | `harness/run_high_pullback_study.py` | engine_params 键集恰 7 逐字消费 fail-closed(无 st 键=引擎 spec §5 默认,不代传不发明);单层 high_pullback;--recon-only=本单元唯一授权模式;正式模式须 --snapshot-id 且对 recon 锚 212 fail-closed 防冒充 |
| ③ report | `engine/report.py` exp11 分支 | 真锚标题(present-but-None 同 fail-closed)+漏斗段(恒等式三件+MA20 NFV)+**τ0 术语=「事件后首个有真实bar的价格观察日」+人令原文句「τ0一字板事件仅为价格观察,不得表述为可执行策略证据。」**;无键→段落不出=零回归 |
| ④ fixture | `harness/verify_high_pullback_{rules,adapter}.py` | 24+26=50 断言,两台全绿(§3) |

## 3. 攻击 fixture 八组映射(令三.2)——两台全绿

| 令列攻击面 | fixture | 结果 |
|---|---|---|
| 锚重置(连续新高只留末锚) | rules F7(首锚不触/末锚成事件/重置留痕)+F8(连升一阶段重置4) | PASS |
| 首触即决三分支 | rules F1(EVENT)/F5(MA_KILL 不复看)/F3·F4(DEEP_KILL 不复活·跳空跨带) | PASS |
| 闭区间边界恰−3%/恰−5% | rules F1(恰−3% 入带)/F2(**恰−5% 闭区间在带,float 实现在此误判 DEEP_KILL**)/F3(低一分破五)/F6(MA20 恰等=不破/低一分=破) | PASS |
| 期内无 bar=NO_TOUCH | rules F9(锚后首 bar 落窗外=期满,bar 计窗会误触) | PASS |
| 右界 TRUNCATED | rules F10(恰期满于右界=NO_TOUCH/跨出右界=TRUNCATED,last_cal_rank 唯一依据) | PASS |
| 事件键唯一 | rules F11(注入碰撞全剔留痕+研究期漏斗)/F12(结构性两阶段违背 0) | PASS |
| digest 与 engine_params 逐字消费 | adapter ①(缺键/多键 fail-closed+6 参数逐字)+④(文件 SHA==canonical==令 digest/_family_trial 不进 digest/改实质键必变) | PASS |
| 「价格观察日」术语渲染 | adapter ⑤(术语在场+人令原文句在场+**exp11 漏斗段零『可交易』**+缺锚 fail-closed+他 exp 标题零命中+exp8 回归探针) | PASS |

另:rules F13(伪新高不成锚)/F14(cal_rank 非递增 fail-closed)/F15(确定性双跑)/F16(聚合);
adapter ②(EventRow 形态/日历外 bar fail-closed)/③(三恒等式+参考对账块)。

## 4. 漏斗 recon 复现 + 42,719 参考归因(令三.3)——闭合

- **取数路径(结构发现,如实报)**:taosha_engine 角色结构上仅有 `_snap`(GUC 钉批)视图授权,
  现值视图零授权→recon 必经 snapshot 钉批。recon 锚=**StudySnapshot 212**(既有已发布
  exp12 研究 manifest,**批次向量 daily6/adj7/cal10/basic6/name7==42,719 参考基精确同**;
  仅只读取数承 exp13 对 121 先例,零 manifest 生成;正式模式对 212 fail-closed 防冒充;
  取数路径属边界内工程自决,如实留痕待验收)。
- **双跑**:`--recon-only --recon-snapshot-id 212` 两跑 RC=0,recon_json **SHA256 一致
  `9ddf806caba2d36cd91df6cf5a914bfef5629c6e81900c1940385df21c0a710e`**(aliyun /root/s11adapt/)。
- **漏斗(冻结规则 Decimal 精确算术)**:输入 15,099,011 行/日历轴 8,187(<2024-07-01 钉批轴)→
  新高日 361,296(=阶段 124,614+重置 236,682 恒等 OK)→EVENT 66,745/MA_KILL 2,385/
  DEEP_KILL 53,498/NO_TOUCH 1,941/TRUNCATED 45(和==阶段数 OK)→pre2011 剔 23,961→
  **最终事件集 42,784**;事件键唯一性违背 0;MA20 通过率 0.9655 NFV;三恒等式全 OK。
- **Δ=+65 血缘归因(不追数不改规则)**:归因件 `/root/s11adapt/s11_diff_attrib.py`+
  `diff_attrib.json`=同一 snapshot 212 数据逐票双口径对撞(A=冻结 Decimal 规则;B=草案
  float 算术逐字模拟)。**B 侧窗内=42,719 精确复现参考(模拟保真自证)**;A/B 全年份对称差
  167 条,逐条归因:**恰−5% 边界 108 + 恰−3% 边界 32 + MA20 恰等 3(首因 143 条,全部落在
  数学恰位边界)+ 同票首分歧后的级联果 24;UNCLASSIFIED=0**。结论:全部差异=float 二进制
  舍入在数学恰位边界对闭区间端点的误判(如恰−5% 被 float 判为 DEEP_KILL 剔除),冻结 PAP
  文本=闭区间(−5%≤ret≤−3%),Decimal 精确算术为忠实实现;42,784 为冻结规则确定性产出,
  42,719 维持"草案 float 对账参考"身份不升格。**差异归因 100% 闭合,无对账异常上报面。**

## 5. 全家福 + e2e 零回归(令三.4)——两台全绿

- **aliyun(钉版 venv)**:状态机 46/46/pap 硬门 23/23/addendum 14/14/快照镜像 11/11/
  manifest 血缘 24/24/集成 7/7/study_snapshot 探针 19/19/冻结口径运行时探针 PASS/
  敏感性 6/6/三窗输出正常/holder 81+10/limit_open 116+40+24/limit_down 48+34/
  st_removal 42+43/earnings_revision 33+73+24/**exp11 新二件 24/24+26/26**。
- **AWS**:非 DB 套件同清单全绿(含 exp11 新二件)。
- **e2e 合成基线**:AWS 双跑+aliyun 双跑全=`3116ba9b74f7c53b…4c22`==历史基线,逐字节零回归
  (report.py exp11 分支为无键不出段设计,默认路径零新行)。

## 6. 已知面上报(不改动,待人裁)

1. **引擎通用 per-τ 段 `tau_axis` 文案**=「τ=0:=T+1(首个**可交易日**,S2-DEC3)」——
   S2-DEC3 全实验共用冻结文案(runner.py),exp11 正式运行报告将含此行。人终版收口令的
   『可交易』禁面=exp11 PAP JSON(零残留已断言)与 exp11 专属段(fixture 断言零命中);
   通用段不在本单元四件授权面,且改动将破 exp8/12/13/20 封存报告字节稳定。**如需 exp11
   报告内该行同步改术语,须另令。**
2. recon 锚=snapshot 212 为取数路径自决(§4),正式运行仍须 exp11 自有 manifest(另令)。

## 7. 取证与待人

- 取证包=AWS `~/shuheng/s11_freeze_adapt_delivery_2026-07-24/`(冻结脚本+log/recon 双跑 json+log/
  归因件+diff_attrib.json/令文/本档,SHA256SUMS);aliyun 原件 `/root/s11freeze/`+`/root/s11adapt/`。
- **▶停行为验收点待人:①验收冻结凭证+适配行为面+Δ=+65 归因(§4)②已知面两条(§6)确认;
  外部复核通过后另令=exp11 自有研究 manifest 生成→单次正式运行→persist;未令不动。**
