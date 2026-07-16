"""holder_sell 事件规则攻击性 fixture 自检(§2B 验收点③三证,正反例全覆盖,零DB零I/O)。
三证:①真首次收(含对抗性负语境) ②六类全拒 ③同计划多公告仅一首次。
用法: python taosha/harness/verify_holder_sell_rules.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.holder_sell_rules import (  # noqa: E402
    CLS_COMBO, CLS_FIRST, CLS_HALFWAY, CLS_PROGRESS, CLS_RESULT, CLS_REVISION,
    CLS_SUSPECT, CLS_TERMINATION, classify_event_title, select_first_events)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


# ── 证一:真首次收(正例,含对抗性负语境) ──────────────────────────────────
check("首次·标准预披露", classify_event_title("关于持股5%以上股东减持股份计划的预披露公告"), CLS_FIRST)
check("首次·计划公告无预披露字样", classify_event_title("股东减持股份计划公告"), CLS_FIRST)
check("首次·提示性公告", classify_event_title("关于持股5%以上股东股份减持计划的提示性公告"), CLS_FIRST)
check("首次·对抗:限售期满后减持(负语境掩码)",
      classify_event_title("部分董事及高级管理人员股权激励所获股票限售期满后减持股份计划的公告"), CLS_FIRST)
check("首次·对抗:锁定期届满后拟减持",
      classify_event_title("关于控股股东所持股份锁定期届满后减持计划的预披露公告"), CLS_FIRST)
check("首次·暨字但无污染词", classify_event_title("关于股东减持股份达到1%暨减持计划的预披露公告"), CLS_FIRST)
check("首次·对抗:股权激励持有期满后减持计划",
      classify_event_title("董事高级管理人员股权激励所获股票持有期满后集中竞价减持股份计划公告"), CLS_FIRST)
check("拒·对抗:计划结果(非紧邻)仍兜底剔除",
      classify_event_title("上海电力股份有限公司股东减持股份计划结果公告"), CLS_SUSPECT)

# ── 证二:六类全拒(反例) ─────────────────────────────────────────────────
check("拒·时间过半", classify_event_title("关于股东减持计划时间过半的公告"), CLS_HALFWAY)
check("拒·数量过半", classify_event_title("关于持股5%以上股东减持股份达到1%暨减持计划减持数量过半的公告"), CLS_HALFWAY)
check("拒·进展(换源防线)", classify_event_title("关于控股股东减持计划实施进展的公告"), CLS_PROGRESS)
check("拒·实施情况", classify_event_title("关于股东减持计划实施情况的公告"), CLS_PROGRESS)
check("拒·计划期满", classify_event_title("关于公司持股5%以上股东股份减持计划期满的公告"), CLS_RESULT)
check("拒·期满未减持", classify_event_title("关于董事、高级管理人员减持计划期满未减持公司股份的公告"), CLS_RESULT)
check("拒·减持结果", classify_event_title("旭升集团控股股东提前结束减持计划暨减持股份结果公告"), CLS_TERMINATION)
check("拒·减持完毕", classify_event_title("关于公司高级管理人员减持股份计划完毕的公告"), CLS_RESULT)
check("拒·提前终止", classify_event_title("关于公司控股股东减持计划提前终止的公告"), CLS_TERMINATION)
check("拒·更正", classify_event_title("关于《持股5%以上股东减持预披露公告》的更正公告"), CLS_REVISION)
check("拒·修订", classify_event_title("关于股东减持计划的修订公告"), CLS_REVISION)
check("拒·补充", classify_event_title("关于股东减持股份计划的补充公告"), CLS_REVISION)
check("拒·延期", classify_event_title("关于股东减持计划延期实施的公告"), CLS_REVISION)
check("拒·混合:终止暨后续预披露",
      classify_event_title("关于公司控股股东减持计划提前终止暨后续减持计划的预披露公告"), CLS_COMBO)
check("拒·混合:期满及未来预披露",
      classify_event_title("关于公司控股股东减持计划期满及未来减持计划预披露的公告"), CLS_COMBO)
check("拒·兜底:非计划语境终止+预披露→suspect不静默",
      classify_event_title("关于终止募投项目暨控股股东股份减持计划预披露的公告"), CLS_SUSPECT)
check("拒·兜底:泛完成词→suspect",
      classify_event_title("关于完成工商变更登记暨股东减持计划的公告"), CLS_SUSPECT)

# ── 证三:同计划多公告仅一首次(select_first_events 流水线) ────────────────
ROW = dict(ts_code="000001.SZ", stock_code="000001", holder_name="张三",
           reduce_ratio_max_pct=2.0, reduce_period_start="2023-02-01",
           reduce_period_end="2023-07-31", title="关于股东减持股份计划的预披露公告")


def row(**kw):
    r = dict(ROW)
    r.update(kw)
    return r


# 强键同计划隔日再披 → 仅首条
res = select_first_events([
    row(announcement_id="A1", valid_time="2023-01-10T09:00:00+00:00"),
    row(announcement_id="A2", valid_time="2023-01-11T09:00:00+00:00"),
])
check("同计划强键:两公告→1事件", res["counters"]["events"], 1)
check("同计划强键:被剔理由", [x["reason"] for x in res["rejects"]], ["same_plan_strong_key"])
check("同计划强键:保最早", res["events"][0]["announcement_ids"], ["A1"])

# 中键(票,股东,比例)30日内 → 剔;31日外 → 两事件(新计划)
res = select_first_events([
    row(announcement_id="B1", valid_time="2023-01-10T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
    row(announcement_id="B2", valid_time="2023-02-05T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
    row(announcement_id="B3", valid_time="2023-06-01T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
])
check("同计划中键30日内剔/31日外为新计划", res["counters"]["events"], 2)
check("中键被剔者", [x["reason"] for x in res["rejects"]], ["same_plan_midkey_window"])

# 同日两股东两计划 → 均保留,合并为同一市场事件日
res = select_first_events([
    row(announcement_id="C1", holder_name="张三", valid_time="2023-03-01T09:00:00+00:00"),
    row(announcement_id="C2", holder_name="李四", reduce_ratio_max_pct=3.0,
        valid_time="2023-03-01T10:00:00+00:00"),
])
check("同日双股东:1事件日", res["counters"]["events"], 1)
check("同日双股东:n_ann=2", res["events"][0]["n_ann"], 2)

# 比例门:未解析 fail-closed / 0.5%拒 / 恰1.0%过
res = select_first_events([
    row(announcement_id="D1", reduce_ratio_max_pct=None, holder_name=None,
        valid_time="2023-04-01T09:00:00+00:00"),
    row(announcement_id="D2", reduce_ratio_max_pct=0.5, holder_name=None,
        valid_time="2023-04-02T09:00:00+00:00"),
    row(announcement_id="D3", reduce_ratio_max_pct=1.0, holder_name=None,
        valid_time="2023-04-03T09:00:00+00:00"),
])
check("比例门:仅≥1%成事件", res["counters"]["events"], 1)
check("比例门:剔除理由集",
      sorted(x["reason"] for x in res["rejects"]),
      ["ratio_below_gate", "ratio_unparsed_fail_closed"])

# 跨票同id(代码变更同实体) → 保首条+conflict 留痕
res = select_first_events([
    row(announcement_id="E1", valid_time="2023-05-01T09:00:00+00:00"),
    row(announcement_id="E1", stock_code="601975", ts_code="601975.SH",
        valid_time="2023-05-01T09:00:00+00:00"),
])
check("跨票同id:1事件", res["counters"]["events"], 1)
check("跨票同id:conflict留痕", res["conflicts"],
      [{"announcement_id": "E1", "kept": "000001", "dropped": "601975"}])

# 污染类混入流水线 → 全拒不进事件
res = select_first_events([
    row(announcement_id="F1", title="关于股东减持计划时间过半的公告",
        valid_time="2023-06-01T09:00:00+00:00"),
    row(announcement_id="F2", title="关于股东减持计划提前终止的公告",
        valid_time="2023-06-02T09:00:00+00:00"),
])
check("污染类入流水线:0事件", res["counters"]["events"], 0)

# 确定性:同输入双跑逐字节同
import json  # noqa: E402
r1 = json.dumps(select_first_events([row(announcement_id="G1", valid_time="2023-07-01T09:00:00+00:00"),
                                     row(announcement_id="G2", holder_name="李四",
                                         valid_time="2023-07-02T09:00:00+00:00")]),
                sort_keys=True, ensure_ascii=False)
r2 = json.dumps(select_first_events([row(announcement_id="G1", valid_time="2023-07-01T09:00:00+00:00"),
                                     row(announcement_id="G2", holder_name="李四",
                                         valid_time="2023-07-02T09:00:00+00:00")]),
                sort_keys=True, ensure_ascii=False)
check("确定性:双跑逐字节同", r1 == r2, True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
