"""淘沙 · 硬化③ 受控语义 diff 分析件(post-ST 新基线归因)。

职责: 对同一研究的〈闭卷记录 / legacy 旧臂 / event_day 修复臂〉产物做受控语义 diff——
事件计数/剔除计数(原因×年份)/板块分层归属逐项 + 统计事实增量;三方归因:
闭卷 vs 旧臂 = 013 tie 钉死效应(#4;#2b 不消费事件视图,预期≈0 以实测为准);
旧臂 vs 修复臂 = ST 事件日修复效应。影响以 diff 实测陈述(人令:禁止以修复前计数预判)。
口径依据: docs/hardening-window-order-2026-07-12.md ③;验收档 hardening-item3-*。

用法: python -m taosha.harness.diff_post_st --old A.json --new B.json [--closed-exp N]
      [--strategy] --label "#4" --out DIFF.json
"""
from __future__ import annotations

import argparse
import json
import sys


def _focus_event(r: dict) -> dict:
    """事件研究 result → 受控 diff 焦点面(剔除 audit/diagnostic/报告性文案)。"""
    rej = r.get("rejections", {})
    by_year = {str(y): {"total": d.get("total"), "rejected": d.get("rejected"),
                        "by_reason": dict(sorted((d.get("by_reason") or {}).items()))}
               for y, d in (rej.get("by_year") or {}).items()}
    by_reason_total: dict = {}
    for d in (rej.get("by_year") or {}).values():
        for k, v in (d.get("by_reason") or {}).items():
            by_reason_total[k] = by_reason_total.get(k, 0) + v
    strata = {k: v for k, v in (r.get("board_strata") or {}).items() if not k.startswith("_st_note")}
    ts = r.get("type_strata")
    type_strata = None
    if isinstance(ts, dict) and ts.get("layers"):
        type_strata = {lay: {"n_valid": d.get("n_valid"),
                             "sig_state": (d.get("adj_bmp") or {}).get("sig_state") or d.get("sig_state")}
                       for lay, d in ts["layers"].items()}
    car = r.get("car") or {}
    car_f = {w: {"caar": d.get("caar"), "adj_bmp_car": d.get("adj_bmp_car"),
                 "sig_state": d.get("sig_state")}
             for w, d in car.items() if isinstance(d, dict)}
    return {
        "n_events_total": r.get("n_events_total"),
        "n_valid": r.get("n_valid"),
        "reject_total": rej.get("rejected"), "reject_ratio": rej.get("reject_ratio"),
        "reject_by_reason_total": dict(sorted(by_reason_total.items())),
        "reject_by_year": by_year,
        "board_strata": strata,
        "type_strata": type_strata,
        "verdict": r.get("verdict"),
        "car": car_f,
        "n_eff_rho": r.get("n_eff_rho"),
    }


def _focus_strategy(r: dict) -> dict:
    """策略版 result → 焦点面(strategy_version 块)。"""
    sv = r.get("strategy_version") or {}
    def _m(key):
        d = sv.get(key) or {}
        return {k: d.get(k) for k in ("mean", "adj_z", "sig_state", "t_sa") if k in d}
    return {
        "n_consumed": sv.get("n_consumed"),
        "n_survivors_sourced": sv.get("n_survivors_sourced"),
        "sourcing_diff": sv.get("sourcing_diff") or sv.get("source_set_diff"),
        "net": _m("net"), "bhar": _m("bhar"), "bhar_gross": _m("bhar_gross"),
        "adj_bmp_bhar_gross": _m("adj_bmp_bhar_gross"), "adj_bmp_bhar": _m("adj_bmp_bhar"),
        "skew_adjusted_t_gross": _m("skew_adjusted_t_gross"),
        "exits": sv.get("exits") or sv.get("exit_breakdown"),
        "censored": sv.get("censored") or (sv.get("g5_censor") or {}).get("n"),
        "dsr": (sv.get("dsr") or {}).get("dsr"),
        "sample_gate": (sv.get("sample_gate") or {}).get("state"),
    }


def _deep_diff(a, b, path=""):
    """叶级差异 [(path, old, new)];dict 并集键,list 长度+逐位(短路前 5 差)。"""
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            diffs += _deep_diff(a.get(k), b.get(k), f"{path}.{k}" if path else str(k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append((f"{path}.__len__", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diffs += _deep_diff(x, y, f"{path}[{i}]")
    elif a != b:
        diffs.append((path, a, b))
    return diffs


def _pair(label: str, fa: dict, fb: dict) -> dict:
    ds = _deep_diff(fa, fb)
    return {"pair": label, "n_diffs": len(ds),
            "diffs": [{"path": p, "old": o, "new": n} for p, o, n in ds]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="legacy_row0 旧臂 JSON")
    ap.add_argument("--new", required=True, help="event_day 修复臂 JSON")
    ap.add_argument("--closed-exp", type=int, default=None, help="闭卷 exp_id(读台账 result_json)")
    ap.add_argument("--strategy", action="store_true", help="策略版焦点面(strategy_version 块)")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    focus = _focus_strategy if a.strategy else _focus_event
    with open(a.old) as f:
        f_old = focus(json.load(f))
    with open(a.new) as f:
        f_new = focus(json.load(f))

    out = {"label": a.label, "protocol": {
        "closed_vs_old": "013 tie 钉死效应(#2b 不消费事件视图,预期≈0 以实测为准)",
        "old_vs_new": "ST 事件日修复效应(hardening ③ 修法)"},
        "focus_old": f_old, "focus_new": f_new,
        "old_vs_new": _pair("legacy_row0 → event_day(ST 效应)", f_old, f_new)}

    if a.closed_exp is not None:
        from taosha.experiment import ledger
        row = ledger.get(a.closed_exp)
        if row is None or row.get("result_json") is None:
            print(f"exp {a.closed_exp} 无 result_json", file=sys.stderr)
            return 2
        closed = row["result_json"]
        if a.strategy and "strategy_version" not in closed:
            print(f"exp {a.closed_exp} result 无 strategy_version 块", file=sys.stderr)
            return 2
        f_closed = focus(closed)
        out["focus_closed"] = f_closed
        out["closed_vs_old"] = _pair("closed → legacy_row0(tie 钉死效应)", f_closed, f_old)

    with open(a.out, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True, default=str)

    print(f"== {a.label} 受控语义 diff ==")
    if "closed_vs_old" in out:
        print(f"闭卷 vs 旧臂(tie 效应): {out['closed_vs_old']['n_diffs']} 处叶差")
    print(f"旧臂 vs 修复臂(ST 效应): {out['old_vs_new']['n_diffs']} 处叶差")
    for d in out["old_vs_new"]["diffs"][:40]:
        print(f"  {d['path']}: {d['old']} → {d['new']}")
    if out["old_vs_new"]["n_diffs"] > 40:
        print(f"  …(其余 {out['old_vs_new']['n_diffs'] - 40} 处见 {a.out})")
    print(f"diff → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
