"""淘沙 · engine · 体检报告(切片2 item 9;spec §2⑤ / 铁律⑤)。

报告**只陈述统计事实**:无建议口吻,无"该信号有 alpha/建议买入"类判断(铁律⑤)。
固定段落:①偏差方向声明(item 9,剔除类处置的保守偏差)②N_eff + 剔除率同报(item 11)
③逐日 AR + 主/稳健窗 ④板块分层 ⑤verdict(统计事实陈述)⑥口径审计摘要(item 10)。

红线:本模块不产出任何行动建议;verdict 为统计终态标签(SIG/NOT_SIG/INSUFFICIENT/
AMBIGUOUS)的事实陈述,不翻译成"值得交易"。
"""
from __future__ import annotations

# item 9:固定偏差方向声明段(保守偏差方向;剔除类处置一律朝"低估效应"方向)
BIAS_DECLARATION = (
    "【偏差方向声明(固定段,item 9)】\n"
    "本引擎的剔除类处置(估计窗覆盖不足剔除、事件落停牌期剔除、ST 剔除、一字板顺延、无价行剔除)"
    "均为**保守处置**:方向上倾向于**缩小可测得的异常收益**、而非放大——\n"
    "  · 覆盖不足/停牌/无价行剔除:剔除的是数据残缺样本,不因'结果好看'保留,避免幸存偏差朝有利方向;\n"
    "  · 一字板顺延:把不可成交日的极端收益移出 τ=0,倾向**低估**首日反应幅度;\n"
    "  · ST 剔除:移除 ±5% 限幅与财务困境扰动样本,方向上削弱而非制造效应。\n"
    "故若仍测得显著异常,真实效应不小于报告值(保守下界语义);若不显著,不能排除被保守处置削弱。"
)

NO_ADVICE_FOOTER = (
    "【口吻声明】本报告只陈述统计事实(CAR/检验统计量/样本数/校正门槛/verdict),"
    "不含任何交易建议或'该信号有 alpha'类判断(铁律⑤:用其手不引其忆)。"
)


def _fmt(x, nd=4):
    return "NA" if x is None else f"{x:.{nd}f}"


def _nfv_tag(blk) -> str:
    """非权威段直接带 NOT_FOR_VERDICT 标记(人令调整六;C6 二次回修)。
    默认路径(块无 not_for_verdict 键)→ 空串,渲染逐字节零回归。"""
    return " [NOT_FOR_VERDICT]" if isinstance(blk, dict) and blk.get("not_for_verdict") else ""


def render(result: dict) -> str:
    a = result["audit"]
    L = []
    # 横幅:#2b(含 drawdown_diagnostic 键)出专属标题;#4/合成无此键 → 保留原标题(约束③不动 #4)。
    if result.get("drawdown_diagnostic") is not None:
        L.append("═══ 淘沙 · 事件研究体检报告(#2b 回撤反抽·b1池 事件版)═══")
    else:
        L.append("═══ 淘沙 · 事件研究体检报告(切片2 合成验收)═══")
    L.append(f"快照批次: {result.get('snapshot_batch')}  |  基准口径: {a['benchmark_mode']}(口径②)")
    L.append(f"冻结口径审计: frozen_config={a['frozen_config_digest'][:16]}… "
             f"frozen_ashare={a['frozen_ashare_digest'][:16]}…")
    L.append("")

    # ② N_eff + 剔除率同报(item 11)
    rej = result["rejections"]
    L.append(f"【样本与剔除(存活数与剔除率同报,item 11)】")
    L.append(f"  事件总数={rej['total']}  有效存活 N_valid={result['n_valid']}  "
             f"剔除={rej['rejected']}  剔除率={_fmt(rej['reject_ratio'], 4)}"
             + ("  ⚠告警(>5%)" if rej["alert"] else ""))
    ner = result.get("n_eff_rho")
    if ner:
        L.append(f"  相关性折算有效 N(ρ̄={_fmt(ner['rho_bar'],4)},口径④): "
                 f"Kish={_fmt(ner['kish'],1)}  KP={_fmt(ner['kp'],1)}  "
                 f"(N_valid={ner['n_valid']} 为存活事件数;ADJ-BMP 已内嵌此坍缩)")
    L.append(f"  样本量闸={result['sample_gate']['gate']} → {result['sample_gate']['state']}")
    cov = result["coverage"]
    L.append(f"  估计窗覆盖: 分母={cov['denominator']} 门槛={cov['min_valid']}(70%) "
             f"有效日[min/mean/max]={cov['valid_days_min']}/"
             f"{_fmt(cov['valid_days_mean'],1)}/{cov['valid_days_max']}")
    L.append("  剔除率按年份分解(item 7):")
    for y, d in rej["by_year"].items():
        L.append(f"    {y}: 总{d['total']} 剔{d['rejected']} 率{_fmt(d['reject_ratio'],3)} "
                 f"原因{d['by_reason']}")
    L.append("")

    # ① 偏差方向声明(item 9;P1-4 二次回修:result 携带冻结 PAP bias_statement 时直接消费
    #    渲染〔权威来源唯一=pap,runner 已锚定〕;默认无键 → 原固定段逐字节不变)
    bs = result.get("bias_statement")
    if bs:
        L.append("【偏差方向声明(冻结 PAP bias_statement,report 直接消费;P1-4 二次回修)】")
        L.append(f"  {bs['text']}")
        L.append(f"  来源锚: {bs['source_anchor']}")
    else:
        L.append(BIAS_DECLARATION)
    L.append("")

    # ③ 逐日 AR + 主/稳健窗(item 8)
    pt = result.get("per_tau") or {}
    if pt:
        L.append(f"【逐日 AR 标准输出(item 8;{pt['tau_axis']})】" + _nfv_tag(pt))
        L.append(f"  ρ̄={_fmt(pt['rho_bar'])}(行业内,{pt['rho_n_pairs']} 对;口径④)")
        L.append("  τ    N    AAR        BMP       ADJ-BMP")
        for r in pt["by_tau"]:
            L.append(f"  {r['tau']:>2}  {r['n']:>3}  {_fmt(r['aar'],5):>9}  "
                     f"{_fmt(r['bmp'],3):>8}  {_fmt(r['adj_bmp'],3):>8}")
        car = result["car"]
        for wk in ("main_window", "robust_window"):
            w = car[wk]
            # 主窗字段角色(人令调整六,nfv 时有键):唯一判决权字段=adj_bmp_car,其余非权威
            fr = w.get("field_roles") or {}
            role_tag = (" [字段角色: adj_bmp_car=VERDICT_AUTHORITY,其余统计=NOT_FOR_VERDICT]"
                        if fr else "")
            L.append(f"  {wk} {w['taus']}: CAAR={_fmt(w['caar'],5)} N={w['n']} "
                     f"BMP_CAR={_fmt(w.get('bmp_car'),3)} ADJ-BMP_CAR={_fmt(w.get('adj_bmp_car'),3)}"
                     + _nfv_tag(w) + role_tag)
        # 预注册次级报告窗(人裁 2026-07-15,三窗 pap 时才有;不参与判决)——两窗 result 无此键零回归
        for w in (car.get("secondary_windows") or {}).get("windows", ()):
            L.append(f"  secondary_window {w['taus']}(预注册次级报告窗·不判决): CAAR={_fmt(w['caar'],5)} "
                     f"N={w['n']} BMP_CAR={_fmt(w.get('bmp_car'),3)} ADJ-BMP_CAR={_fmt(w.get('adj_bmp_car'),3)}")
        L.append("")

    # ④ 板块分层(item 8)
    st = result.get("board_strata") or {}
    L.append("【板块分层(item 8)】" + _nfv_tag(st))
    for k, v in st.items():
        if k.startswith("_") or not isinstance(v, dict):   # 非板块行(如 C6 not_for_verdict 标记)跳过
            continue
        L.append(f"  {k}: 总{v['total']} 有效{v['valid']} 剔{v['rejected']}")
    cx = st.get("_chinext_regime")
    if cx:
        L.append(f"  创业板 regime 边界 {cx['boundary']}: 前(±10%){cx['pre_10pct']} "
                 f"后(±20%){cx['post_20pct']}")
    if st.get("_st_note"):
        L.append(f"  注: {st['_st_note']}")
    ic = result.get("industry_coverage") or {}
    if ic:
        L.append(f"  行业覆盖(口径④): 'unknown' 残余组 {ic['unknown_n']}/{ic['n_valid']} "
                 f"({_fmt(ic['unknown_pct'], 3)})"
                 + ("  ⚠升级上报(>5%)" if ic.get("escalate") else "") + _nfv_tag(ic))
    L.append("")

    # ④'' 删失诊断窗(步3b,R5;报告项·不进 verdict)
    cd = result.get("censor_diagnostic") or {}
    if cd:
        L.append(f"【删失诊断窗(R5;报告项·不进 verdict;{cd['window']})】" + _nfv_tag(cd))
        allp = cd.get("all", {})
        L.append("  ① 各 τ 逐日 AR(全体;反应时间形状/延迟价格发现):")
        L.append("     τ   N     AAR        BMP     ADJ-BMP")
        for r in allp.get("by_tau_ar", []):
            L.append(f"    {r['tau']:>2} {str(r['n']):>4}  {_fmt(r['aar'],5):>9} "
                     f"{_fmt(r['bmp'],3):>7} {_fmt(r['adj_bmp'],3):>7}")
        L.append("  ② 各 τ 删失计数占比(全体;一字板/涨停/跌停/停牌):")
        L.append("     τ   N   一字板  涨停  跌停  停牌   删失占比")
        for r in allp.get("by_tau_censor", []):
            L.append(f"    {r['tau']:>2} {r['n']:>3}   {r['one_word']:>4} {r['limit_up']:>5} "
                     f"{r['limit_down']:>5} {r['suspend']:>5}   {_fmt(r['censored_pct'],3)}")
        L.append("  ③ 板块四层分拆(main/chinext/star/ST;ST=已剔除层→有效0;τ=0 概况,全量见 result_json):")
        for b, panel in cd.get("by_board", {}).items():
            cens = panel.get("by_tau_censor", [])
            c0 = cens[0] if cens else {}
            L.append(f"    {b}: 有效{c0.get('n',0)}  "
                     f"τ=0[一字{c0.get('one_word',0)}/涨停{c0.get('limit_up',0)}/"
                     f"停牌{c0.get('suspend',0)}/删失占比{_fmt(c0.get('censored_pct'),3)}]")
        L.append("")

    # ④' 稳健性两道(spec §6 三法之二/三)
    rb = result.get("robustness") or {}
    if rb:
        cr = (rb.get("corrado_rank") or {})
        ct = (rb.get("calendar_time") or {})
        L.append("【稳健性两道(spec §6;三法之秩/日历)】" + _nfv_tag(rb))
        L.append(f"  Corrado 秩检验: 主窗 t_rank={_fmt((cr.get('main') or {}).get('t_rank'),3)} "
                 f"稳健窗 t_rank={_fmt((cr.get('robust') or {}).get('t_rank'),3)}(非参,对非正态/事件方差稳健)")
        cm, crob = (ct.get('main') or {}), (ct.get('robust') or {})
        L.append(f"  日历时间组合法: 主窗 t_cal={_fmt(cm.get('t_cal'),3)}(日历日 {cm.get('n_cal_days')}) "
                 f"稳健窗 t_cal={_fmt(crob.get('t_cal'),3)}(日历日 {crob.get('n_cal_days')})(聚集并单观测)")
        L.append("")

    # ④''' 三层分解(预喜/预亏/扭亏;pap layers/event_def 冻结定义)
    ts = result.get("type_strata") or {}
    layers = ts.get("layers") or {}
    if layers:
        L.append("【三层分解(预喜/预亏/扭亏;pap 冻结 layers/event_def;各层独立同一流水线)】"
                 + _nfv_tag(ts))
        L.append(f"  注: {ts.get('note','')}")
        L.append("  层(key)         N_valid  主窗[0,+M] CAAR      ADJ-BMP_CAR  朴素t      verdict")
        for key, blk in layers.items():
            mw = (blk.get("car") or {}).get("main_window") or {}
            adj = mw.get("adj_bmp_car")
            lab = f"{blk.get('layer_label','')}({key})"
            # C6 二次回修:nfv 层块零判决字段(改名旁路已废)→ 渲染 NOT_FOR_VERDICT 标记;
            # 默认路径 verdict 键在位、渲染零回归
            sig = blk.get("verdict",
                          "NOT_FOR_VERDICT" if blk.get("not_for_verdict") else "")
            L.append(f"  {lab:<14} {blk.get('n_valid',0):>7}  "
                     f"{_fmt(mw.get('caar'),5):>16}  {_fmt(adj,3):>10}  "
                     f"{_fmt(mw.get('naive_t'),3):>8}   {sig}")
        # 各层 verdict_note 全文(不省;分歧不许挑有利的;nfv 层块无判决注 → 标记行)
        for key, blk in layers.items():
            note = blk.get("verdict_note")
            if note is None:
                note = ("NOT_FOR_VERDICT(层内零判决字段,C6 二次回修)"
                        if blk.get("not_for_verdict") else "")
            L.append(f"    · {blk.get('layer_label','')}({key}): {note}")
        nvs = ts.get("n_valid_sum")
        if nvs is not None:
            L.append(f"  三层存活合计={nvs}(应=合并 N_valid={result.get('n_valid')};层外已在视图排除)")
        L.append("  ⚠ 合并口径 verdict 混合正负漂移可抵消,判读须以本三层分解为准(见上 note)。")
        L.append("")
    elif ts.get("applicable") is False:
        L.append(f"【三层分解】不适用 —— {ts.get('note', '')}")
        L.append("")

    # ④''''' #2b 事件生成诊断 D1/D2/D3(F2 附录F-rev1;报告项·不进 verdict)
    dd = result.get("drawdown_diagnostic")
    if dd:
        L.append("【#2b 事件生成诊断 D1/D2/D3(F2;报告项·不进 verdict)】")
        L.append(f"  注: {dd.get('note', '')}")

        def _dd_line(tag, s):
            if not s or s.get("n", 0) == 0:
                L.append(f"  {tag:<10} N=0(无事件)")
                return
            d2 = s.get("d2") or {}
            L.append(
                f"  {tag:<10} N={s['n']:<6} "
                f"D1(从未破ma10)={_fmt(s.get('d1_never_broke_ma10_frac'),3)}({s.get('d1_count')}) | "
                f"D2(触发→进场交易日)[min/中位/mean/max]="
                f"{d2.get('min')}/{_fmt(d2.get('median'),1)}/{_fmt(d2.get('mean'),1)}/{d2.get('max')} | "
                f"D3(进场前破ma20)={_fmt(s.get('d3_broke_ma20_before_entry_frac'),3)}({s.get('d3_count')})")

        _dd_line("池内生成", dd.get("generated"))
        _dd_line("清洗存活", dd.get("valid"))
        L.append("")

    # ④'''' 可交易口径(选项2;pap cost 冻结;报告/锚对照,不改统计判决)
    tr = result.get("tradeable") or {}
    if tr.get("available"):
        c = tr.get("cost") or {}
        L.append("【可交易口径净收益(选项2;pap cost 冻结;报告项·不改统计判决)】" + _nfv_tag(tr))
        L.append(f"  成本(冻结率): 佣金={_fmt(c.get('commission'),5)} 印花(卖)={_fmt(c.get('stamp_tax_sell'),5)} "
                 f"滑点(单边)={_fmt(c.get('slippage_oneway'),5)} → 买费={_fmt(c.get('buy_fee'),5)} "
                 f"卖费={_fmt(c.get('sell_fee'),5)}")
        L.append(f"  口径: 进场=τ=0 后复权 open,出场=窗尾后复权 close,净额={c.get('net_formula')}")

        def _tr_line(tag, blk):
            for wk in ("main", "robust"):
                w = blk.get(wk) or {}
                net, gro = (w.get("net") or {}), (w.get("gross") or {})
                cen = w.get("exit_censor") or {}
                L.append(
                    f"  {tag:<10} {wk:<6}{w.get('window',''):<9} N={w.get('n_events',0):<6} "
                    f"净:均值={_fmt(net.get('mean'),5)} 中位={_fmt(net.get('median'),5)} "
                    f"胜率={_fmt(net.get('pos_frac'),3)} | 毛均={_fmt(gro.get('mean'),5)} "
                    f"| 排除(窗尾缺close)={w.get('excluded_no_close',0)} "
                    f"出场删失[一字{cen.get('one_word',0)}/跌停{cen.get('limit_down',0)}/"
                    f"停牌{cen.get('suspend_or_missing',0)}]")

        _tr_line("合并", tr.get("combined") or {})
        for key, blk in (tr.get("layers") or {}).items():
            _tr_line(f"{blk.get('layer_label','')}({key})", blk)
        L.append(f"  注: {tr.get('note','')}")
        L.append("")

    # ④'''''' 正交诊断维度(C6 二次回修;两条独立轴,无键 → 段落不出=既有渲染零回归)
    dd2 = result.get("diagnostic_dimensions")
    if dd2:
        L.append("【正交诊断维度(C6 二次回修;两条独立轴,每层 NOT_FOR_VERDICT·不判决不改判)】")
        for dim, dblk in (dd2.get("dims") or {}).items():
            L.append(f"  轴 {dim} [NOT_FOR_VERDICT]: {dblk.get('note','')}")
            for lay, blk in (dblk.get("layers") or {}).items():
                head = (f"    {lay} [NOT_FOR_VERDICT]: 事件N={blk['n_events']} "
                        f"存活={blk['n_valid']} 剔除={blk['n_rejected']}")
                if blk.get("status"):
                    L.append(head + f" → {blk['status']}")
                    L.append(f"      剔除逐因: {blk.get('rejections_by_reason_total') or {}}"
                             f"(逐年分解见 result_json)")
                else:
                    st_ = blk.get("stats") or {}
                    mw_ = st_.get("main_window") or {}
                    rw_ = st_.get("robust_window") or {}
                    L.append(head)
                    L.append(f"      主窗{mw_.get('taus','')}: CAAR={_fmt(mw_.get('caar'),5)} "
                             f"ADJ-BMP_CAR={_fmt(mw_.get('adj_bmp_car'),3)} "
                             f"朴素t={_fmt(mw_.get('naive_t'),3)}(预注册报告统计,非判决)")
                    L.append(f"      稳健窗{rw_.get('taus','')}: CAAR={_fmt(rw_.get('caar'),5)} "
                             f"ADJ-BMP_CAR={_fmt(rw_.get('adj_bmp_car'),3)}")
        cc = dd2.get("cross_counts")
        if cc:
            L.append(f"  二维计数核对(仅计数,不计统计/判决): {cc.get('cells')}")
        L.append("")

    # ⑤ verdict(统计事实)。nfv 结构化水印(回修单元 C6):有键才渲染 → 既有 result 渲染零回归
    nfvp = result.get("not_for_verdict_policy")
    if nfvp:
        L.append(f"【NOT_FOR_VERDICT 结构化(回修单元 C6)】{nfvp.get('label','')}")
        L.append(f"  已标记块: {', '.join(nfvp.get('marked_blocks', []))}")
        L.append("")
    L.append(f"【verdict(统计终态,非交易判断)】{result['verdict']}")
    L.append(f"  {result['verdict_note']}")
    L.append("")

    # ⑥ 数据质量敏感性(exp4 专属键,人令 2026-07-16 五.5;无此键 → 段落不出=既有 result 渲染零回归)
    sb = result.get("sensitivity_holder_resolved_only")
    if sb:
        st = sb["study"]
        L.append("【数据质量敏感性(report-only · NOT_FOR_VERDICT)】")
        L.append(f"  {sb['basis']}")
        L.append(f"  事件面: 主跑={sb['n_events_main']} 排除(holder未解析)={sb['n_events_excluded']} "
                 f"保留={sb['n_events_kept']}(排除占比={_fmt(sb['excluded_share'], 4)})")
        mw = (st.get("car") or {}).get("main_window") or {}
        L.append(f"  复算: N_valid={st['n_valid']} 主窗CAAR={_fmt(mw.get('caar'))} "
                 f"主窗ADJ-BMP={_fmt(mw.get('adj_bmp_car'), 3)}")
        L.append(f"  {sb['label']}")
        L.append("")
    L.append(NO_ADVICE_FOOTER)
    return "\n".join(L)


def render_strategy(result: dict) -> str:
    """#2b 策略版报告(附录B B1/B2 + 附录G;步③模块④增段)。

    独立于 render()(事件版/合成共享渲染,不碰 → 约束③零回归);消费 drawdown_strategy.run_strategy
    的 result。只陈述统计事实(铁律⑤);判决权归事件版(四件套④)。"""
    sv = result["strategy_version"]
    a = result["audit"]
    L = []
    L.append("═══ 淘沙 · 事件研究体检报告(#2b 回撤反抽·b1池 策略版)═══")
    L.append(f"  定义: {sv['definition']}")
    L.append(f"  判决权: {sv['verdict_authority']} —— {sv['authority_note']}")
    L.append("")

    # ① 样本 + 同源一致性(步④硬项)
    sc = sv["source_consistency"]
    L.append(f"【样本 · 同源一致性】输入事件={sv['n_events_input']} → 同源存活(=事件版 N_valid 同构造)"
             f"={sv['n_survivors_sourced']} → 策略版消费={sv['n_consumed']} "
             f"(样本闸 {sv['sample_gate']['gate']}:{sv['sample_gate']['state']})")
    L.append(f"  差集归因: 建仓价缺={sc['excluded_no_entry_open']['n']} "
             f"基准缺日={sc['excluded_bench_gap']['n']} 标准化不可得={sc['excluded_sbhar_none']['n']}"
             + ("(差集为空:消费集==同源存活全集)" if not (sc['excluded_no_entry_open']['n']
                or sc['excluded_bench_gap']['n'] or sc['excluded_sbhar_none']['n']) else ""))
    L.append(f"  {sc['note']}")
    L.append("")

    # ② 事件级收益分布(净/毛/基准BH/毛超额/净超额)
    c = sv["cost"]
    L.append(f"【事件级收益分布(附录G 离场;成本乘式:买费={_fmt(c['buy_fee'],5)} 卖费={_fmt(c['sell_fee'],5)})】")
    for tag, key in (("净收益", "net"), ("毛收益", "gross"), ("池同跨度BH", "benchmark_bh"),
                     ("毛超额(毛−基准)", "bhar_gross"), ("净超额(净−基准)", "bhar")):
        d = sv[key]
        L.append(f"  {tag:<14} N={d['n']:<7} 均值={_fmt(d['mean'],5)} 中位={_fmt(d['median'],5)} "
                 f"胜率={_fmt(d['pos_frac'],3)} sd={_fmt(d['std'],5)}")
    L.append("")

    # ③ ADJ-BMP 四件套检验:主检验=毛超额(人批补正 2026-07-11)、净额并报;③右偏稳健项毛/净并列
    def _test_line(tag, ab, st):
        L.append(f"  {tag}: SBHAR 均值={_fmt(ab['mean'])} sd={_fmt(ab['sd'])} z={_fmt(ab['z'],3)} "
                 f"× KP={_fmt(ab['kp_factor'],6)} → adj_z={_fmt(ab['adj_z'],3)} | "
                 f"右偏项(Hall/LBT): skew={_fmt(st['skew'],3)} t_plain={_fmt(st['t_plain'],3)} "
                 f"→ t_sa={_fmt(st['t_sa'],3)}")

    abg = sv["adj_bmp_bhar_gross"]
    L.append(f"【ADJ-BMP(四件套②:SBHAR=超额/(σ_est·√H) 截面;主检验=毛超额、净额并报)】"
             f"ρ̄={_fmt(abg['rho_bar'])}(行业内 {abg['rho_n_pairs']} 对) N={abg['n']} "
             f"(双侧 α={abg['alpha']:.4f} 临界±{abg['z_crit']:.3f},family_trial={abg['family_trial']})")
    _test_line("毛超额(主检验)", abg, sv["skew_adjusted_t_gross"])
    _test_line("净超额(并报) ", sv["adj_bmp_bhar"], sv["skew_adjusted_t"])
    L.append(f"  统计事实标注(挂毛超额): {abg['sig_state']} —— {abg['sig_note']}")
    L.append(f"  偏离留痕: {sv['test_object_note']}")
    L.append("")

    # ③b 开卡对照菜单(人指 2026-07-11;四数注明量纲)
    am = sv["anchor_menu"]
    L.append("【开卡对照菜单(量纲:①②③=事件级简单收益均值〔小数,×100=%〕;④=净收益>0 事件占比)】")
    L.append(f"  ① 毛超额均值   = {_fmt(am['gross_bhar_mean'],6)}")
    L.append(f"  ② 原始净额均值 = {_fmt(am['net_raw_mean'],6)}")
    L.append(f"  ③ 净超额均值   = {_fmt(am['net_bhar_mean'],6)}")
    L.append(f"  ④ 胜率(净)     = {_fmt(am['win_rate_net'],4)}")
    L.append("")

    # ④ DSR 常设报告项(施工令①;不进 verdict)
    d = sv.get("dsr") or {}
    L.append(f"【DSR(常设报告项,不进 verdict;V口径=proxy 人裁 2026-07-10)】")
    L.append(f"  n={d.get('n')} N_trials={d.get('N')} v_mode={d.get('v_mode')} "
             f"SR̂={_fmt(d.get('sr_hat'),5)} skew={_fmt(d.get('skew'),3)} kurt={_fmt(d.get('kurtosis'),3)}")
    L.append(f"  V(proxy)={_fmt(d.get('v'),8)} SR*={_fmt(d.get('sr_star'),6)} "
             f"PSR(vs 0)={_fmt(d.get('psr_vs_zero'),6)} DSR={_fmt(d.get('dsr'),6)}")
    L.append(f"  {sv['dsr_note']}")
    L.append("")

    # ④b 成交明细(窄补第三轮 #1-a:**直接消费** fills 事件级字段渲染,禁由净收益倒推展示)
    fl = sv.get("fills") or {}
    L.append("【成交明细(事件级 fill 证据字段直接渲染;#1-a)】")
    L.append(f"  n={fl.get('n')} 按来源: {fl.get('by_source')}")
    recs = fl.get("records") or []
    for r in recs[:5]:                                   # 样例前 5 行(全量在 result_json.fills.records)
        L.append(f"    · {r['event_id']}: 进场 {r['entry_date']}@{_fmt(r['entry_price'],4)} → "
                 f"决策(收盘确认) {r['signal_date']} → 成交 {r['fill_date']}@{_fmt(r['fill_price'],4)} "
                 f"[{r['fill_source']}]" + ("(删失标记,非成交)" if r["right_censored"] else ""))
    if len(recs) > 5:
        L.append(f"    …(共 {len(recs)} 行,全量见 result_json.fills.records)")
    L.append(f"  {fl.get('note')}")
    L.append("")

    # ⑤ 附录G 诊断(报告项)
    dg = sv["diagnostics"]
    L.append("【附录G 诊断(报告项)】")
    L.append(f"  离场主因: {dg['exit_reasons']} | G2 同日双触发={dg['dual_trigger']['n']}"
             f"(双 flag 均记账,主因归强平)")
    po = dg["postpone"]
    dd = po.get("days_dist") or {}
    L.append(f"  G4 顺延: n={po['n_postponed']} 天数[min={dd.get('min')} 中位={dd.get('median')} "
             f"均值={_fmt(dd.get('mean'),2)} max={dd.get('max')}](日历交易日轴) "
             f"极端(>20 交易日)={len(po['extreme_cases'])} 例(单列不静默):")
    for x in po["extreme_cases"]:
        L.append(f"    · {x['event_id']}: 顺延 {x['postpone_days']} 交易日"
                 f"(present-bar 差 {x['postpone_bars']};删失={x['right_censored']})")
    rc = dg["right_censored"]
    un = rc.get("unrealized_net") or {}
    L.append(f"  G5 右删失(open_position): n={rc['n']} 占比={_fmt(rc['pct'],5)} "
             f"末端 mark-to-market 未实现净收益: 均值={_fmt(un.get('mean'),5)} N={un.get('n')}(不剔除)")
    hb, hd = dg.get("holding_bars_dist") or {}, dg.get("holding_days_dist") or {}
    L.append(f"  持有期: bars[中位={hb.get('median')} 均值={_fmt(hb.get('mean'),1)} max={hb.get('max')}] "
             f"日历交易日[中位={hd.get('median')} 均值={_fmt(hd.get('mean'),1)} max={hd.get('max')}]")
    L.append("")

    # ⑥ 已知口径特征登记(附录G;显式不藏)
    L.append("【已知口径特征登记(附录G,显式不藏)】")
    for feat in sv["known_caliber_features"]:
        L.append(f"  · {feat}")
    L.append("")

    # ⑦ 偏差方向声明(同事件版清洗流水线,同段适用)+ 审计
    L.append(BIAS_DECLARATION)
    L.append("")
    L.append("【口径审计摘要】")
    L.append(f"  frozen_config={a['frozen_config_digest'][:8]}… frozen_ashare={a['frozen_ashare_digest'][:8]}… "
             f"benchmark={a['benchmark_mode']} family_trial={a['family_trial']} α={a['family_alpha']}")
    ps = a.get("pool_snapshot") or {}
    L.append(f"  池血缘: pool_b1_batch={ps.get('pool_b1_batch')} pool_return_batch={ps.get('pool_return_batch')}")
    L.append("")
    L.append(NO_ADVICE_FOOTER)
    return "\n".join(L)
