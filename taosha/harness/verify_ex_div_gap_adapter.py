"""exp14 冻结前 reader/recon 接线攻击 fixture；零数据库连接。"""
from __future__ import annotations

import sys
from pathlib import Path

from taosha.harness.run_ex_div_gap_recon import (
    DRAFT_DIGEST, EXPECTED_BATCHES, SOURCE_SNAPSHOT_ID, _assert_equal, _assert_snapshot,
)
from taosha.reader.ex_div_gap import VIEWS


FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def raises(name, function, contains):
    try:
        function()
    except SystemExit as exc:
        check(name, contains in str(exc), True)
    else:
        check(name, "未拒绝", contains)


check("F1 source snapshot钉375", SOURCE_SNAPSHOT_ID, 375)
check("F2 NOT-FROZEN草案digest全值钉定", len(DRAFT_DIGEST), 64)
check("F3 三条qbase消费批次", EXPECTED_BATCHES,
      {"dividend": 17, "adj_factor": 7, "trade_cal": 10})
check("F4 current/snapshot各两张专属视图",
      (set(VIEWS), {key: len(value) for key, value in VIEWS.items()}),
      ({"current", "snapshot"}, {"current": 2, "snapshot": 2}))
check("F5 current/snapshot视图名不复用", set(VIEWS["current"]) == set(VIEWS["snapshot"])
      and not (set(VIEWS["current"].values()) & set(VIEWS["snapshot"].values())), True)

good_info = {"snapshot_id": 375, "content": {"qbase": EXPECTED_BATCHES}, "digest": "x"}
_assert_snapshot(good_info)
check("F6 snapshot375正确向量通过", True, True)
raises("F7 snapshot ID篡改拒绝",
       lambda: _assert_snapshot({**good_info, "snapshot_id": 374}), "snapshot375")
raises("F8 qbase批次篡改拒绝",
       lambda: _assert_snapshot({**good_info, "content": {"qbase": {**EXPECTED_BATCHES,
                                                                        "adj_factor": 99}}}),
       "向量不符")

base = {"source_batches": {"dividend": "batch17"}, "selection": {"events": [1]},
        "selection_content_sha256": "a"}
_assert_equal(base, dict(base))
check("F9 current/snapshot相等通过", True, True)
raises("F10 选择差异fail-closed",
       lambda: _assert_equal(base, {**base, "selection": {"events": [2]},
                                    "selection_content_sha256": "b"}), "选择不一致")
raises("F11 批次差异fail-closed",
       lambda: _assert_equal(base, {**base, "source_batches": {"dividend": "batch18"}}),
       "批次不一致")

reader = Path("taosha/reader/ex_div_gap.py").read_text(encoding="utf-8")
check("F12 连接建立即只读", 'options="-c default_transaction_read_only=on"' in reader, True)
check("F13 因子按键限量请求", reader.count("unnest(%s::text[],%s::date[])") , 1)
check("F14 reader零价格收益字段", "adj_close" in reader or "raw_close" in reader
      or "ret_eqw" in reader or "log_return" in reader, False)
recon = Path("taosha/harness/run_ex_div_gap_recon.py").read_text(encoding="utf-8")
check("F15 recon不加载runner", "runner" in recon or "run_study" in recon, False)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
