"""exp8 limit_open driver 专项验收(冻结令 2026-07-17 深夜五 三;零DB零I/O,合成行+仓内冻结件)。

验四面:
  ① engine_kwargs_from_pap = 逐字消费冻结 PAP v3(真实冻结文件),缺键/多键 fail-closed;
  ② events_from_prices 映射正确性(EventRow 字段/event_id 格式/层键二值/listing fail-closed/
    留痕透传/跨票分组/确定性双跑);
  ③ selection_audit 块(计数/逐年逐因/重复映射与 listing 逐条/链长分布/层分布);
  ④ driver 依赖的 digest 不变量(冻结文件 canonical==令绑定 digest;_family_trial 运行时键不进 digest)。
用法: python taosha/harness/verify_limit_open_adapter.py
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.experiment.pap import canonical_pap_sha256                    # noqa: E402
from taosha.harness.run_limit_open_study import (                         # noqa: E402
    ENGINE_PARAM_KEYS, engine_kwargs_from_pap, events_from_prices, selection_audit)
from taosha.reader.contract import PriceRow                               # noqa: E402

FAIL = 0
N = 0

ORDER_DIGEST = "afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb"
PAP_V3 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "docs", "limit-open-pap-final-v3-2026-07-17.json")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


# ── ① engine_params 逐字消费(真实冻结件)────────────────────────────────────
with open(PAP_V3, "rb") as fh:
    pap = json.loads(fh.read())
kw = engine_kwargs_from_pap(pap)
check("①kwargs 全集", kw, {
    "benchmark_mode": "market", "strata_enabled": False, "st_mode": "event_day",
    "st_policy": "keep", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
    "postpone_policy": "unified", "diagnostic_dims": ("listing_age", "st")})
check("①note 不进引擎参数", "note" in kw, False)

bad = dict(pap)
bad["engine_params"] = {k: v for k, v in pap["engine_params"].items() if k != "st_policy"}
try:
    engine_kwargs_from_pap(bad)
    check("①缺键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①缺键 fail-closed", "st_policy" in str(e), True)

bad2 = dict(pap)
bad2["engine_params"] = dict(pap["engine_params"], runtime_free_choice=1)
try:
    engine_kwargs_from_pap(bad2)
    check("①多键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①多键 fail-closed", "runtime_free_choice" in str(e), True)

# ── ② events_from_prices(合成 PriceRow)────────────────────────────────────
def P(ts, d, lim, olim):
    return PriceRow(ts_code=ts, trade_date=dt.date.fromisoformat(d), close=10.0,
                    is_suspended=False, limit_status=lim, board="main",
                    is_st=False, industry="X", open=10.0, open_limit_status=olim)


ROWS = [
    # A票: 2日一字涨停链 → 开板(none) → 事件 2023-01-06;行序 1-3 → recent_listing
    P("000001.SZ", "2023-01-04", "one_word", "open_at_up_limit"),
    P("000001.SZ", "2023-01-05", "one_word", "open_at_up_limit"),
    P("000001.SZ", "2023-01-06", "none", "none"),
    # B票: 同构链但 listing 缺失 → fail-closed 零事件
    P("600000.SH", "2023-03-01", "one_word", "open_at_up_limit"),
    P("600000.SH", "2023-03-02", "one_word", "open_at_up_limit"),
    P("600000.SH", "2023-03-03", "none", "none"),
]
LISTING = {"000001.SZ": {"list_date": dt.date(2023, 1, 4), "delist_date": None}}

events, sel = events_from_prices(iter(ROWS), LISTING, "study_snapshot:99")
check("②事件数(B票 listing fail-closed)", len(events), 1)
check("②event_id 格式", events[0].event_id, "000001.SZ:20230106")
check("②first_ann_date", events[0].first_ann_date, dt.date(2023, 1, 6))
check("②层键=recent_listing(行序3≤30)", events[0].event_type_layer, "recent_listing")
check("②snapshot_batch 透传", events[0].snapshot_batch, "study_snapshot:99")
check("②listing fail-closed 留痕", sel["reject_reasons"], {"listing_missing_fail_closed": 1})
check("②counters 跨票求和", sel["counters"]["input_rows"], 6)

# seasoned 层:链起点行序 31(>30)
LONG = [P("000002.SZ", (dt.date(2023, 1, 2) + dt.timedelta(days=i)).isoformat(),
          "none", "none") for i in range(30)]
LONG += [P("000002.SZ", "2023-02-10", "one_word", "open_at_up_limit"),
         P("000002.SZ", "2023-02-11", "one_word", "open_at_up_limit"),
         P("000002.SZ", "2023-02-12", "none", "none")]
ev2, _ = events_from_prices(iter(LONG), {"000002.SZ": {"list_date": dt.date(2023, 1, 2),
                                                       "delist_date": None}}, "b")
check("②层键=seasoned(行序31>30)", [e.event_type_layer for e in ev2], ["seasoned"])

r1 = [e.event_id for e in events_from_prices(iter(ROWS), LISTING, "b")[0]]
r2 = [e.event_id for e in events_from_prices(iter(ROWS), LISTING, "b")[0]]
check("②确定性双跑", r1 == r2, True)

# ── ③ selection_audit ───────────────────────────────────────────────────────
aud = selection_audit(sel)
check("③counters 透传", aud["counters"], sel["counters"])
check("③链长分布", aud["chain_len_dist"], {"2": 1})
check("③逐年分布", aud["events_yearly"], {"2023": 1})
check("③层计数", aud["layer_counts"], {"recent_listing": 1, "seasoned": 0})
check("③逐因逐年剔除分解", aud["rejects_yearly_by_reason"],
      {"listing_missing_fail_closed": {"2023": 1}})
check("③listing 逐条入档", len(aud["itemized_rejects"]["listing_missing_fail_closed"]), 1)
check("③重复映射逐条槽在场", "duplicate_event_date_mapping" in aud["itemized_rejects"], True)

# ── ④ digest 不变量(driver fail-fast 依赖)─────────────────────────────────
with open(PAP_V3, "rb") as fh:
    raw = fh.read()
import hashlib                                                            # noqa: E402
check("④文件 SHA256==令绑定 digest", hashlib.sha256(raw).hexdigest(), ORDER_DIGEST)
check("④canonical==令绑定 digest", canonical_pap_sha256(pap), ORDER_DIGEST)
pap_rt = dict(pap, _family_trial=1)
check("④_family_trial 运行时键不进 digest", canonical_pap_sha256(pap_rt), ORDER_DIGEST)
check("④改实质键 digest 必变",
      canonical_pap_sha256(dict(pap, sample_gate=31)) == ORDER_DIGEST, False)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
