"""exp11 high_pullback 事件规则攻击 fixture 自检(冻结令 2026-07-24 五;零 DB、零真实数据、零收益)。

覆盖冻结令三.2 攻击面(规则侧六组)+ 交叉验证:
  F1/F2/F3/F4 首触即决三分支+闭区间边界(恰−3%入带、恰−5%在带〔float 实现会误判 DEEP_KILL,
    Decimal 精确算术为冻结闭区间忠实实现〕、略破五 DEEP_KILL 不复活、跳空跨带);
  F5/F6 MA_KILL 首触即决不复看+MA20 恰等=不破/差一分=破;
  F7/F8 锚重置(连续新高只留末锚;一段连续上行一阶段);
  F9 期内无bar=NO_TOUCH(观察窗按交易所交易日,非 bar 计窗);
  F10 右界 TRUNCATED vs 恰期满 NO_TOUCH 分类(last_cal_rank 唯一依据);
  F11/F12 事件键唯一 fail-closed(注入碰撞全剔留痕;结构性两阶段两事件违背 0)+研究期漏斗;
  F13 伪新高(前史<250)不成锚;F14 cal_rank 非递增 fail-closed;F15 确定性双跑;F16 跨票聚合。
冻结口径 = PAP digest eaa54b3d…b6fc event_def(阶段状态机;闭区间 Decimal 精确算术)。
用法: python taosha/harness/verify_high_pullback_rules.py
"""
import datetime as dt
import json
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.high_pullback_rules import (  # noqa: E402
    REASON_DUPLICATE, REASON_POST, REASON_PRE2011, finalize_events,
    merge_selections, select_high_pullback_events)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


START = dt.date(2015, 1, 5)   # 事件日落 2015=研究期内;日期仅需升序(观察窗以 cal_rank 计)


def mk_rows(closes, ranks=None):
    return [{"trade_date": START + dt.timedelta(days=k), "close": Decimal(str(c)),
             "cal_rank": (ranks[k] if ranks is not None else k + 1),
             "board": "main", "is_st": False}
            for k, c in enumerate(closes)]


def run(closes, ranks=None, last=None, ts="000001.SZ"):
    rows = mk_rows(closes, ranks)
    if last is None:
        last = rows[-1]["cal_rank"] + 100
    return select_high_pullback_events(ts, rows, last)


def outcomes(sel):
    c = sel["counters"]
    return {k: c["outcome_" + k] for k in
            ("EVENT", "MA_KILL", "DEEP_KILL", "NO_TOUCH", "TRUNCATED") if c["outcome_" + k]}


H100 = [100] * 250   # 平史:零伪新高、零锚;首个高于 100 的 bar(第 251 根)即成锚

# ── F1 EVENT+恰−3% 边界(闭区间上沿入带)─────────────────────────────────────────
s = run(H100 + [200, 194])   # 194/200-1 = 恰−3%;MA20=(19×100+194)/20 远低于 194
check("F1 恰−3% 首触入带→EVENT", outcomes(s), {"EVENT": 1})
check("F1 事件几何(锚/事件日/偏移/回落%)",
      (s["events"][0]["anchor_date"], s["events"][0]["event_date"],
       s["events"][0]["offset_days"], s["events"][0]["pullback_pct"]),
      ((START + dt.timedelta(days=250)).isoformat(),
       (START + dt.timedelta(days=251)).isoformat(), 1, -3.0))
check("F1 计数(新高日1=阶段1+重置0;offset_1=1;伪新高0)",
      (s["counters"]["newhigh_days"], s["counters"]["stages"],
       s["counters"]["resets_within_stage"], s["counters"]["offset_1"],
       s["counters"]["pseudo_newhigh_hist_insufficient"]), (1, 1, 0, 1, 0))

# ── F2 恰−5% 闭区间在带(⚠float 实现在此误判 DEEP_KILL;Decimal=冻结闭区间忠实)────────
s = run(H100 + [200, 190])   # 190 = 200×0.95 精确;闭区间下沿=在带
check("F2 恰−5% 闭区间在带→EVENT(float 会误判 DEEP_KILL)", outcomes(s), {"EVENT": 1})
check("F2 回落%=−5.0", s["events"][0]["pullback_pct"], -5.0)

# ── F3 略破五→DEEP_KILL 阶段终止,反弹回带不复活 ────────────────────────────────
s = run(H100 + [200, Decimal("189.99"), 191])   # 189.99<190 破五;191 回带但阶段已死
check("F3 略破五→DEEP_KILL;回带 191 不复活零事件", outcomes(s), {"DEEP_KILL": 1})
check("F3 事件零", s["events"], [])

# ── F4 跳空跨带(−2%→−6%)→DEEP_KILL(首触即 <−5%)────────────────────────────────
s = run(H100 + [200, 197, 188])   # 197 未触(>194);188<190 首触即深
check("F4 跳空跨带→DEEP_KILL(offset_2)", (outcomes(s), s["counters"]["offset_2"]),
      ({"DEEP_KILL": 1}, 1))

# ── F5 MA_KILL 首触即决:破线阶段终结,窗内后续带内 bar 不复看 ─────────────────────
H220 = [220] * 250
s = run(H220 + [221, 212, 213])   # 212 入带但 20×212=4240 < 19×220+212=4392 → 破线;213 不复看
check("F5 破线→MA_KILL;窗内 213 回带不复看零事件", (outcomes(s), s["events"]), ({"MA_KILL": 1}, []))

# ── F6 MA20 恰等=不破(≥)/低一分=破 ───────────────────────────────────────────────
H209 = [209] * 250
s = run(H209 + [221, 216, 210])   # MA20=(17×209+221+216+210)/20=210 恰等→不破
check("F6a MA20 恰等→不破→EVENT", outcomes(s), {"EVENT": 1})
s = run(H209 + [221, 216, Decimal("209.99")])  # 20×209.99=4199.80 < 4199.99 → 破
check("F6b 低一分→破→MA_KILL", outcomes(s), {"MA_KILL": 1})

# ── F7 锚重置:连续新高只留末锚(首锚基准下不触带,末锚基准下成事件)────────────────
s = run(H100 + [200, 205, 196])   # 196 vs 末锚205=−4.39% 入带;vs 首锚200=−2% 不触
check("F7 末锚基准→EVENT(新高日2=阶段1+重置1)",
      (outcomes(s), s["counters"]["newhigh_days"], s["counters"]["stages"],
       s["counters"]["resets_within_stage"]), ({"EVENT": 1}, 2, 1, 1))
check("F7 事件锚=末锚(重置留痕 resets_in_stage=1,offset=1)",
      (s["events"][0]["anchor_date"], s["events"][0]["resets_in_stage"],
       s["events"][0]["offset_days"]),
      ((START + dt.timedelta(days=251)).isoformat(), 1, 1))

# ── F8 一段连续上行只形成一个阶段(尽头未决按全局日历归 NO_TOUCH)──────────────────
s = run(H100 + [200, 201, 202, 203, 204])
check("F8 连续上行一阶段(重置4);期满 NO_TOUCH",
      (s["counters"]["stages"], s["counters"]["resets_within_stage"], outcomes(s)),
      (1, 4, {"NO_TOUCH": 1}))

# ── F9 期内无 bar=NO_TOUCH(观察窗=交易所交易日;bar 计窗会误触)─────────────────────
ranks = list(range(1, 252)) + [262]            # 锚 rank 251;下一 bar rank 262(窗外)
s = run(H100 + [200, 190], ranks=ranks)        # 190 若按 bar 计窗=第1根入带→误 EVENT
check("F9 停牌跨期→NO_TOUCH(窗外 bar 不判带)", (outcomes(s), s["events"]), ({"NO_TOUCH": 1}, []))

# ── F10 右界分类:恰期满(a_r+10≤last)=NO_TOUCH / 跨出右界=TRUNCATED ────────────────
s = run(H100 + [200], last=261)                # 锚 rank 251;251+10=261≤261 期满
check("F10a 恰期满于右界→NO_TOUCH", outcomes(s), {"NO_TOUCH": 1})
s = run(H100 + [200], last=260)                # 261>260 观察窗跨出数据右界
check("F10b 跨出右界→TRUNCATED", outcomes(s), {"TRUNCATED": 1})

# ── F11 finalize:事件键唯一 fail-closed(碰撞全剔留痕)+研究期漏斗 ─────────────────
def _ev(ts, date, anchor="2015-06-01"):
    return {"ts_code": ts, "event_date": date, "anchor_date": anchor,
            "offset_days": 1, "resets_in_stage": 0, "anchor_close": "200",
            "event_close": "194", "pullback_pct": -3.0,
            "board_event": "main", "is_st_event": False}


fin = finalize_events({"events": [
    _ev("000001.SZ", "2015-06-02"), _ev("000001.SZ", "2015-06-02", anchor="2015-05-20"),
    _ev("000002.SZ", "2015-06-02"),          # 异票同日:键含 ts_code,不碰撞
    _ev("000003.SZ", "2010-05-10"),          # pre2011
    _ev("000004.SZ", "2024-07-01"),          # post(上界不含)
    _ev("000005.SZ", "2024-06-28")],         # 在窗
    "counters": {}})
check("F11 碰撞键全剔(违背1键/剔2条)+期外计数+最终集",
      (fin["counters"]["event_key_uniqueness_violations"],
       fin["counters"]["uniqueness_dropped_events"],
       fin["counters"][REASON_PRE2011], fin["counters"][REASON_POST],
       fin["counters"]["final_events"],
       sorted(e["ts_code"] for e in fin["events"])),
      (1, 2, 1, 1, 2, ["000002.SZ", "000005.SZ"]))
check("F11 剔除逐条留痕(reason 三类)",
      sorted(fin["reject_reasons"]),
      sorted([REASON_DUPLICATE, REASON_PRE2011, REASON_POST]))

# ── F12 结构性唯一:两阶段两事件(不同日)违背 0 ───────────────────────────────────
s = run(H100 + [200, 194, 196, 210, 202])      # 阶段1 EVENT(194);阶段2 锚210→EVENT(202)
fin = finalize_events(merge_selections([s]))
check("F12 两阶段两事件·键唯一违背0",
      (s["counters"]["stages"], fin["counters"]["final_events"],
       fin["counters"]["event_key_uniqueness_violations"]), (2, 2, 0))

# ── F13 伪新高(前史<250)不成锚 ─────────────────────────────────────────────────
s = run([100 + k for k in range(100)])         # 100 根连升:99 伪新高,零锚零阶段
check("F13 伪新高仅计数不成锚",
      (s["counters"]["pseudo_newhigh_hist_insufficient"], s["counters"]["stages"],
       s["counters"]["newhigh_days"], s["events"]), (99, 0, 0, []))

# ── F14 cal_rank 非递增 fail-closed ─────────────────────────────────────────────
try:
    run([100, 101], ranks=[5, 5])
    check("F14 cal_rank 非递增→ValueError", "no-raise", "ValueError")
except ValueError:
    check("F14 cal_rank 非递增→ValueError", "ValueError", "ValueError")

# ── F15 确定性双跑 ──────────────────────────────────────────────────────────────
a = json.dumps(run(H100 + [200, 205, 196]), sort_keys=True, default=str)
b = json.dumps(run(H100 + [200, 205, 196]), sort_keys=True, default=str)
check("F15 确定性双跑逐字节同", a == b, True)

# ── F16 跨票聚合(counters 求和+events 拼接)──────────────────────────────────────
s1 = run(H100 + [200, 194], ts="000001.SZ")
s2 = run(H100 + [200, 190], ts="000002.SZ")
m = merge_selections([s1, s2])
check("F16 聚合(事件2/阶段2/EVENT2)",
      (len(m["events"]), m["counters"]["stages"], m["counters"]["outcome_EVENT"]), (2, 2, 2))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
