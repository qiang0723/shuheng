"""exp8 limit_open 事件规则构造 fixture 自检(冻结前裁决 2026-07-17;零 DB、零真实数据、零收益)。
五性质(人授权验证范围):①连续性(自身行序,禁跨非一字真实bar拼接) ②停牌(缺bar不计不重置、
不可为事件日) ③反向一字板顺延(链后一字跌停继续顺延) ④最大饱和链(不重复截取子链)
⑤唯一事件((ts_code,event_date) 重复映射 fail-closed 全剔上报)。
另证:范围过滤 2007-01-01≤event_date<2024-07-01(再挡一道)/N=2 门/双条件链成员判据/
recent_listing 草案标记不改事件集/确定性双跑/跨票聚合。
用法: python taosha/harness/verify_limit_open_rules.py
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.limit_open_rules import (  # noqa: E402
    merge_selections, select_limit_open_events)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


_BASE = dt.date(2015, 3, 2)   # 研究期内基准日;fixture 日期仅需升序(行序=自身交易行序)


def _rows(spec, base=_BASE):
    """spec = [(日偏移, 形态)];形态: up=一字涨停 / down=一字跌停 / ow_none=一字但开盘位异常 /
    none=普通 / limit_up=触板未一字 / limit_down=触跌停板未一字。日偏移跳号即停牌缺 bar。"""
    kind = {
        "up":         ("one_word", "open_at_up_limit"),
        "down":       ("one_word", "open_at_down_limit"),
        "ow_none":    ("one_word", "none"),
        "none":       ("none", "none"),
        "limit_up":   ("limit_up", "none"),
        "limit_down": ("limit_down", "none"),
    }
    out = []
    for off, k in spec:
        ls, ols = kind[k]
        out.append({"trade_date": base + dt.timedelta(days=off),
                    "limit_status": ls, "open_limit_status": ols})
    return out


def sel(spec, ts="000001.SZ", base=_BASE):
    return select_limit_open_events(ts, _rows(spec, base))


def ev_dates(s):
    return [e["event_date"] for e in s["events"]]


def d(off, base=_BASE):
    return (base + dt.timedelta(days=off)).isoformat()


# ── 证一:连续性(自身行序连续;禁跨非一字真实 bar 拼接;N=2 门;双条件判据)──────
s = sel([(0, "up"), (1, "up"), (2, "none")])
check("①两连一字→1链len2", (s["counters"]["chains_ge_n"], s["events"][0]["chain_len"]), (1, 2))
check("①事件日=链后首个非一字行", ev_dates(s), [d(2)])

s = sel([(0, "up"), (1, "none"), (2, "up"), (3, "none")])
check("①单板夹普通日→无链无事件(N=2门)", (s["counters"]["chains_ge_n"], len(s["events"])), (0, 0))

s = sel([(0, "up"), (1, "up"), (2, "none"), (3, "up"), (4, "up"), (5, "none")])
check("①两独立链→两事件(不同事件日)", ev_dates(s), [d(2), d(5)])

s = sel([(0, "up"), (1, "limit_up"), (2, "up"), (3, "up"), (4, "none")])
check("①触板未一字真实bar断链(禁跨拼接)", (s["counters"]["chains_ge_n"], ev_dates(s)), (1, [d(4)]))
check("①断链后前段单板不成链", s["events"][0]["chain_start_date"], d(2))

s = sel([(0, "ow_none"), (1, "up"), (2, "up"), (3, "none")])
check("①双条件判据:one_word但开盘位非up不入链",
      (s["events"][0]["chain_start_date"], s["events"][0]["chain_len"]), (d(1), 2))

# ── 证二:停牌(缺 bar 不计交易日、不重置链、不可为事件日)────────────────────────
s = sel([(0, "up"), (7, "up"), (8, "none")])
check("②停牌缺bar不重置链(行序相邻=连续)",
      (s["counters"]["chains_ge_n"], s["events"][0]["chain_len"]), (1, 2))

s = sel([(0, "up"), (1, "up"), (9, "none")])
check("②链后停牌:事件日=复牌真实bar(停牌日不可为事件日)", ev_dates(s), [d(9)])

s = sel([(0, "up"), (5, "up"), (11, "none")])
check("②链中+链后双缺口混合", (s["events"][0]["chain_len"], ev_dates(s)), (2, [d(11)]))

# ── 证三:反向一字板顺延(链后一字跌停/任何一字继续顺延)──────────────────────────
s = sel([(0, "up"), (1, "up"), (2, "down"), (3, "none")])
check("③链尾一字跌停顺延1行", (ev_dates(s), s["events"][0]["deferred_one_word_rows"]), ([d(3)], 1))

s = sel([(0, "up"), (1, "up"), (2, "down"), (3, "down"), (4, "none")])
check("③连续两日一字跌停顺延2行", (ev_dates(s), s["events"][0]["deferred_one_word_rows"]), ([d(4)], 2))

s = sel([(0, "up"), (1, "up"), (2, "ow_none"), (3, "none")])
check("③一字但开盘位异常行同属一字状态→顺延",
      (ev_dates(s), s["events"][0]["deferred_one_word_rows"]), ([d(3)], 1))

s = sel([(0, "up"), (1, "up"), (2, "down")])
check("③顺延至数据边界无事件日→right_censored剔除",
      ([r["reason"] for r in s["rejects"]], len(s["events"])),
      (["right_censored_no_event_day"], 0))

# ── 证四:最大饱和链(不重复截取 2/3 板子链)───────────────────────────────────────
s = sel([(0, "up"), (1, "up"), (2, "up"), (3, "up"), (4, "up"), (5, "none")])
check("④五连板=恰1链len5恰1事件(无子链)",
      (s["counters"]["chains_ge_n"], s["events"][0]["chain_len"], len(s["events"])), (1, 5, 1))

s2 = sel([(0, "up"), (1, "up"), (2, "up"), (3, "up"), (4, "up"), (5, "none")])
check("④确定性:同输入双跑逐项相等", s == s2, True)

# ── 证五:唯一事件((ts_code,event_date) 重复映射 fail-closed 全剔上报)────────────
s = sel([(0, "up"), (1, "up"), (2, "down"), (3, "up"), (4, "up"), (5, "none")])
check("⑤上下上夹层:两链映射同事件日→全部fail-closed剔除", len(s["events"]), 0)
check("⑤重复映射逐条上报(reason+碰撞链数)",
      sorted((r["reason"], r["n_chains_colliding"]) for r in s["rejects"]),
      [("duplicate_event_date_mapping", 2), ("duplicate_event_date_mapping", 2)])
check("⑤涉事链几何如实留痕(两链起点)", sorted(r["chain_start_date"] for r in s["rejects"]), [d(0), d(3)])

# ── 范围过滤(裁决二.1;视图 holdout 已焊死,此处再挡一道)────────────────────────
_b06 = dt.date(2006, 12, 25)
s = sel([(0, "up"), (1, "up"), (2, "none")], base=_b06)
check("范围:事件日<2007-01-01剔除留痕",
      ([r["reason"] for r in s["rejects"]], len(s["events"])),
      (["event_date_out_of_study_range"], 0))
s = sel([(4, "up"), (5, "up"), (10, "none")], base=_b06)   # 链在2006末,事件日2007-01-04
check("范围:链跨年、事件日入2007→收(按event_date判)", ev_dates(s), ["2007-01-04"])
_b24 = dt.date(2024, 6, 27)
s = sel([(0, "up"), (1, "up"), (4, "none")], base=_b24)    # 事件日2024-07-01
check("范围:事件日≥2024-07-01剔除(再挡一道)", [r["reason"] for r in s["rejects"]],
      ["event_date_out_of_study_range"])
_b96 = dt.date(1995, 5, 8)
s = sel([(0, "up"), (1, "up"), (2, "none")], base=_b96)
check("诊断:制度前(<1996-12-16)链计数+范围剔除",
      (s["counters"]["chains_pre_regime"], [r["reason"] for r in s["rejects"]]),
      (1, ["event_date_out_of_study_range"]))

# ── 事件日形态:非一字即合法(触板未一字/触跌停板未一字均可为开板日)────────────────
s = sel([(0, "up"), (1, "up"), (2, "limit_up"), (3, "none")])
check("事件日=触板未一字行(经典开板日)合法", ev_dates(s), [d(2)])
s = sel([(0, "up"), (1, "up"), (2, "limit_down"), (3, "none")])
check("事件日=触跌停板未一字行合法(有成交区间)", ev_dates(s), [d(2)])

# ── recent_listing 草案标记(链起点行序号≤30;仅标记,不改事件集)──────────────────
pre = [(i, "none") for i in range(28)]                      # 28 个普通行 → 链起点=第29行
s = sel(pre + [(28, "up"), (29, "up"), (30, "none")])
check("recent_listing:链起点第29行→True且事件照收",
      (s["events"][0]["recent_listing"], s["events"][0]["chain_start_rank"], len(s["events"])),
      (True, 29, 1))
pre = [(i, "none") for i in range(30)]                      # 30 个普通行 → 链起点=第31行
s = sel(pre + [(30, "up"), (31, "up"), (32, "none")])
check("recent_listing:链起点第31行→False且事件照收",
      (s["events"][0]["recent_listing"], s["events"][0]["chain_start_rank"]), (False, 31))
pre = [(i, "none") for i in range(29)]                      # 边界:链起点=第30行
s = sel(pre + [(29, "up"), (30, "up"), (31, "none")])
check("recent_listing:边界第30行→True(≤30含)", s["events"][0]["recent_listing"], True)

# ── 跨票聚合(merge_selections:counters 求和 + reject_reasons 计数)────────────────
sa = sel([(0, "up"), (1, "up"), (2, "none")], ts="000001.SZ")
sb = sel([(0, "up"), (1, "up"), (2, "down")], ts="000002.SZ")
m = merge_selections([sa, sb])
check("聚合:事件/剔除/计数求和",
      (len(m["events"]), len(m["rejects"]), m["counters"]["chains_ge_n"]), (1, 1, 2))
check("聚合:reject_reasons 计数", m["reject_reasons"], {"right_censored_no_event_day": 1})
check("聚合:事件带 ts_code(跨票唯一键=ts_code+event_date)", m["events"][0]["ts_code"], "000001.SZ")

# ── 空输入/全普通行退化 ─────────────────────────────────────────────────────────
s = sel([])
check("空输入:零链零事件零剔除",
      (s["counters"]["input_rows"], len(s["events"]), len(s["rejects"])), (0, 0, 0))
s = sel([(0, "none"), (1, "limit_up"), (2, "down")])
check("无链票:单日一字跌停不成链", (s["counters"]["chains_ge_n"], len(s["events"])), (0, 0))

print(f"\n{'='*60}\nverify_limit_open_rules: {N - FAIL}/{N} PASS"
      + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
