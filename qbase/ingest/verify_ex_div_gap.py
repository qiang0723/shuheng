#!/usr/bin/env python3
"""exp14 最小只读视图与recon接线的离线攻击验证。"""
from __future__ import annotations

from pathlib import Path

def main() -> int:
    checks = 0

    def check(name, got, expected):
        nonlocal checks
        checks += 1
        if got != expected:
            raise AssertionError(f"{name}: got={got!r} expected={expected!r}")

    ddl = Path("qbase/sql/028_ex_div_gap_reader.sql").read_text(encoding="utf-8")
    expected_views = {
        "explore_reader_ex_div_gap", "explore_reader_ex_div_gap_snap",
        "explore_reader_ex_div_factor", "explore_reader_ex_div_factor_snap",
    }
    for view in sorted(expected_views):
        check(f"视图在场:{view}", f"VIEW public.{view}" in ddl, True)
        check(f"只授视图:{view}", f"GRANT SELECT ON public.{view} TO taosha_engine" in ddl,
              True)
    check("dividend current/snap路由", "source='tushare:dividend'" in ddl
          and "study_snap_batch('dividend')" in ddl, True)
    check("factor current/snap路由", "source='tushare:adj_factor'" in ddl
          and "study_snap_batch('adj_factor')" in ddl, True)
    check("holdout四焊", ddl.count("<DATE '2024-07-01'") , 4)
    check("SH/SZ四白名单", ddl.count("~ '\\.(SH|SZ)$'") , 4)
    check("L1零事件阈值", ">=0.5" in ddl or ">= 0.5" in ddl, False)
    check("不改事实表", "CREATE TABLE" in ddl or "UPDATE public." in ddl, False)
    check("零价格收益字段", "raw_close" in ddl or "adj_close" in ddl, False)

    print(f"verify_ex_div_gap: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
