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


def render(result: dict) -> str:
    a = result["audit"]
    L = []
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

    # ① 偏差方向声明(item 9)
    L.append(BIAS_DECLARATION)
    L.append("")

    # ③ 逐日 AR + 主/稳健窗(item 8)
    pt = result.get("per_tau") or {}
    if pt:
        L.append(f"【逐日 AR 标准输出(item 8;{pt['tau_axis']})】")
        L.append(f"  ρ̄={_fmt(pt['rho_bar'])}(行业内,{pt['rho_n_pairs']} 对;口径④)")
        L.append("  τ    N    AAR        BMP       ADJ-BMP")
        for r in pt["by_tau"]:
            L.append(f"  {r['tau']:>2}  {r['n']:>3}  {_fmt(r['aar'],5):>9}  "
                     f"{_fmt(r['bmp'],3):>8}  {_fmt(r['adj_bmp'],3):>8}")
        car = result["car"]
        for wk in ("main_window", "robust_window"):
            w = car[wk]
            L.append(f"  {wk} {w['taus']}: CAAR={_fmt(w['caar'],5)} N={w['n']} "
                     f"BMP_CAR={_fmt(w.get('bmp_car'),3)} ADJ-BMP_CAR={_fmt(w.get('adj_bmp_car'),3)}")
        L.append("")

    # ④ 板块分层(item 8)
    st = result.get("board_strata") or {}
    L.append("【板块分层(item 8)】")
    for k, v in st.items():
        if k.startswith("_"):
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
                 + ("  ⚠升级上报(>5%)" if ic.get("escalate") else ""))
    L.append("")

    # ④'' 删失诊断窗(步3b,R5;报告项·不进 verdict)
    cd = result.get("censor_diagnostic") or {}
    if cd:
        L.append(f"【删失诊断窗(R5;报告项·不进 verdict;{cd['window']})】")
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
        L.append("【稳健性两道(spec §6;三法之秩/日历)】")
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
        L.append("【三层分解(预喜/预亏/扭亏;pap 冻结 layers/event_def;各层独立同一流水线)】")
        L.append(f"  注: {ts.get('note','')}")
        L.append("  层(key)         N_valid  主窗[0,+M] CAAR      ADJ-BMP_CAR  朴素t      verdict")
        for key, blk in layers.items():
            mw = (blk.get("car") or {}).get("main_window") or {}
            adj = mw.get("adj_bmp_car")
            lab = f"{blk.get('layer_label','')}({key})"
            L.append(f"  {lab:<14} {blk.get('n_valid',0):>7}  "
                     f"{_fmt(mw.get('caar'),5):>16}  {_fmt(adj,3):>10}  "
                     f"{_fmt(mw.get('naive_t'),3):>8}   {blk.get('verdict','')}")
        # 各层 verdict_note 全文(不省;分歧不许挑有利的)
        for key, blk in layers.items():
            L.append(f"    · {blk.get('layer_label','')}({key}): {blk.get('verdict_note','')}")
        nvs = ts.get("n_valid_sum")
        if nvs is not None:
            L.append(f"  三层存活合计={nvs}(应=合并 N_valid={result.get('n_valid')};层外已在视图排除)")
        L.append("  ⚠ 合并口径 verdict 混合正负漂移可抵消,判读须以本三层分解为准(见上 note)。")
        L.append("")

    # ④'''' 可交易口径(选项2;pap cost 冻结;报告/锚对照,不改统计判决)
    tr = result.get("tradeable") or {}
    if tr.get("available"):
        c = tr.get("cost") or {}
        L.append("【可交易口径净收益(选项2;pap cost 冻结;报告项·不改统计判决)】")
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

    # ⑤ verdict(统计事实)
    L.append(f"【verdict(统计终态,非交易判断)】{result['verdict']}")
    L.append(f"  {result['verdict_note']}")
    L.append("")
    L.append(NO_ADVICE_FOOTER)
    return "\n".join(L)
