"""敏感性块自检(人令 2026-07-16 五.5+批复:同 manifest 同一次运行、report-only、not_for_verdict,
并测试删除整个敏感性块后主 verdict 逐字节复算不变)。合成 fixture(复用三窗件),零 DB 零真实数据。

断言族:
  S1 结构: 块在、not_for_verdict=True、块内递归无 verdict/verdict_note 键(不产判决);
  S2 删除不变性(核心): 全流程 result 删除整块后 == 独立重算的无敏感性 result 逐字节同
     (同时证确定性与零污染:敏感性复算不触碰主 result 任何既有键);
  S3 verdict 显式等: 带块/不带块 verdict+verdict_note 逐字等;
  S4 渲染零回归: render(无块 result) == render(删块 result) 逐字节同;有块 → NOT_FOR_VERDICT 段出现;
  S5 复算真实性: 排除 10/40 → study.n_events_total=30、excluded_share=0.25、CAAR 与主跑可区分产出;
  S6 确定性: 全流程双跑逐字节同。

用法:PYTHONPATH=… python -m taosha.harness.verify_sensitivity_block
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import tempfile

from taosha.engine import report, runner
from taosha.harness.run_holder_sell_study import sensitivity_block, split_sensitivity_events
from taosha.harness.verify_three_windows import (
    EVENT_BASE_IDX, N_DAYS, N_SEC, _biz_days, _pap, make_fixture)
from taosha.reader.synthetic import SyntheticReader


def _sel_fixture() -> tuple[list[dict], list[dict]]:
    """合成 sel_events(40 事件)+语料行(前 10 事件 holder 未解析)。"""
    dates = _biz_days(dt.date(2020, 1, 2), N_DAYS)
    sel_events, rows = [], []
    for i in range(N_SEC):
        code = f"6{i:05d}.SH"
        aid = f"SENS-{i:03d}"
        sel_events.append({"ts_code": code, "event_date": dates[EVENT_BASE_IDX + i].isoformat(),
                           "n_ann": 1, "announcement_ids": [aid]})
        rows.append({"announcement_id": aid,
                     "holder_name": None if i < 10 else "张三",
                     "snapshot_batch": "SYNTH-SENS"})
    return sel_events, rows


def _run_flow(pp: str, ep: str, with_sensitivity: bool) -> dict:
    """驱动同构流程:主跑(显式事件源+strata off=exp4 形态)±敏感性复算(fresh reader)。"""
    sel_events, rows = _sel_fixture()
    pap = _pap("T+1起,后2/4/6日")
    main_events, n0 = split_sensitivity_events(sel_events, [dict(r, holder_name="有") for r in rows],
                                               "SYNTH-SENS")
    assert n0 == 0, "主事件构造不应剔除"
    res = runner.run_study(SyntheticReader(pp, ep), pap, benchmark_mode="market",
                           events=main_events, strata_enabled=False)
    if with_sensitivity:
        sens_events, n_excl = split_sensitivity_events(sel_events, rows, "SYNTH-SENS")
        sens_res = runner.run_study(SyntheticReader(pp, ep), pap, benchmark_mode="market",
                                    events=sens_events, strata_enabled=False)
        res["sensitivity_holder_resolved_only"] = sensitivity_block(
            sens_res, len(sel_events), n_excl)
    return res


def _find_keys(obj, names, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in names:
                hits.append(f"{path}.{k}")
            hits += _find_keys(v, names, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _find_keys(v, names, f"{path}[{i}]")
    return hits


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        pp, ep = f"{td}/prices.csv", f"{td}/events.csv"
        make_fixture(pp, ep)

        base = _run_flow(pp, ep, with_sensitivity=False)   # 独立重算:无敏感性机器
        full = _run_flow(pp, ep, with_sensitivity=True)
        full2 = _run_flow(pp, ep, with_sensitivity=True)   # S6 双跑

        blk = full["sensitivity_holder_resolved_only"]
        assert blk["not_for_verdict"] is True, "S1: not_for_verdict 缺失"
        bad = _find_keys(blk, {"verdict", "verdict_note"})
        assert not bad, f"S1: 敏感性块内出现判决键 {bad}(不产判决被破坏)"
        print("[PASS] S1 结构: 块在+not_for_verdict+块内零判决键")

        stripped = copy.deepcopy(full)
        del stripped["sensitivity_holder_resolved_only"]
        j = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)  # noqa: E731
        assert j(stripped) == j(base), "S2: 删除敏感性块后主 result 与独立重算不逐字节同"
        print("[PASS] S2 删除不变性: 删块 result == 独立无块重算(逐字节)")

        assert (full["verdict"], full["verdict_note"]) == (base["verdict"], base["verdict_note"]), \
            "S3: verdict 漂移"
        print("[PASS] S3 verdict 显式等:", full["verdict"])

        r_base, r_stripped, r_full = report.render(base), report.render(stripped), report.render(full)
        assert r_base == r_stripped, "S4: 渲染零回归破坏(删块渲染≠无块渲染)"
        assert "NOT_FOR_VERDICT" in r_full and "数据质量敏感性" in r_full, "S4: 有块渲染缺敏感性段"
        assert "NOT_FOR_VERDICT" not in r_base, "S4: 无块渲染不应出现敏感性段"
        print("[PASS] S4 渲染: 无块==删块逐字节;有块出 NOT_FOR_VERDICT 段")

        st = blk["study"]
        assert blk["n_events_main"] == 40 and blk["n_events_excluded"] == 10 \
            and blk["n_events_kept"] == 30 and abs(blk["excluded_share"] - 0.25) < 1e-12, \
            f"S5: 事件面计数错 {blk['n_events_main']}/{blk['n_events_excluded']}"
        assert st["n_events_total"] == 30, f"S5: 复算输入应为 30,got {st['n_events_total']}"
        mw_full = full["car"]["main_window"]["caar"]
        mw_sens = st["car"]["main_window"]["caar"]
        assert mw_sens is not None and abs(mw_sens - mw_full) > 1e-9, \
            "S5: 敏感性 CAAR 与主跑不可区分(疑未真实复算)"
        print(f"[PASS] S5 复算真实性: 30/40 事件,主CAAR={mw_full:.6f} 敏感CAAR={mw_sens:.6f}")

        assert j(full) == j(full2), "S6: 全流程双跑不确定"
        print("[PASS] S6 确定性: 双跑逐字节同")

        print("\n6/6 PASS")


if __name__ == "__main__":
    main()
