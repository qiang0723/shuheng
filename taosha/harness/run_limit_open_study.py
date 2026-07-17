"""驱动:对真实数据跑 exp8 limit_open(连续一字涨停开板)事件版 → 报告(冻结令 2026-07-17 深夜五)。

令原文档 = taosha/docs/limit-open-freeze-order-2026-07-17.md(原文即口径):
  · engine_params **逐字消费冻结 PAP v3**,driver 不保留任何运行时自由选择(键集不符=fail-closed);
  · 向引擎传 pap_sha256_assert(仅逐字断言;digest 唯一权威=引擎对实收 pap 重算,回修三);
  · 参数或 digest 不一致一律 fail-closed;
  · 不改变既有默认路径与其他实验输出(纯新增文件,主干零触碰)。

数据流(设计档 limit-open-generator-design-2026-07-17.md §1):
  台账已冻结 pap(铁律③)→ ViewReader(sample=listing 全A键集)prices 全宇宙流(视图零改动,
  holdout/.BJ/∩calendar 焊死)→ groupby 逐票 → limit_open_rules.select_limit_open_events(冻结纯函数)
  → merge_selections → EventRow(layer=recent_listing|seasoned)→ ViewReader(sample=事件票)
  → runner.run_study(events=显式事件源)→ report.render。
**只算+出报告+可选 dump,不改 ledger**(persist 另令,台账结果槽不写)。

用法:
  set -a; . /opt/quant/.env; set +a
  python -m taosha.harness.run_limit_open_study --exp-id 8 --snapshot-id N \
      --pap-sha256-assert <digest> [--json OUT] [--report OUT]
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json

from taosha.compute.limit_open_rules import merge_selections, select_limit_open_events
from taosha.reader.contract import EventRow

# PAP v3 engine_params 键集(冻结件逐字消费;缺键/多键=fail-closed,不许运行时补选)。
# note=PAP 内说明文字,非引擎参数,消费时校验在场但不传引擎。
ENGINE_PARAM_KEYS = frozenset({
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
    "postpone_policy", "st_mode", "st_policy", "strata_enabled", "verdict_policy"})

LAYER_RECENT = "recent_listing"
LAYER_SEASONED = "seasoned"
# 逐条入 audit 的剔除类(PAP reporting_commitments:重复映射与 listing fail-closed 逐条)
ITEMIZED_REJECT_REASONS = (
    "duplicate_event_date_mapping", "listing_missing_fail_closed",
    "pre_listing_bar_fail_closed", "listing_window_anomaly_fail_closed")


def engine_kwargs_from_pap(pap: dict) -> dict:
    """冻结 PAP v3 engine_params → run_study 关键字参数(逐字消费,fail-closed)。

    键集与冻结件不符(缺/多)→ 拒;值原样透传零改写(diagnostic_dims list→tuple 系
    run_study 签名的容器形态要求,元素逐字不动)。"""
    ep = pap.get("engine_params")
    if not isinstance(ep, dict):
        raise SystemExit("fail-closed: 冻结 PAP 缺 engine_params 或非对象(令三:逐字消费)")
    got = set(ep)
    if got != set(ENGINE_PARAM_KEYS):
        raise SystemExit(
            f"fail-closed: engine_params 键集与冻结件不符(缺={sorted(set(ENGINE_PARAM_KEYS) - got)} "
            f"多={sorted(got - set(ENGINE_PARAM_KEYS))});driver 不保留运行时自由选择")
    return {"benchmark_mode": ep["benchmark_mode"],
            "strata_enabled": ep["strata_enabled"],
            "st_mode": ep["st_mode"],
            "st_policy": ep["st_policy"],
            "verdict_policy": ep["verdict_policy"],
            "nfv_structured": ep["nfv_structured"],
            "postpone_policy": ep["postpone_policy"],
            "diagnostic_dims": tuple(ep["diagnostic_dims"])}


def events_from_prices(price_rows, listing: dict, batch: str) -> tuple[list[EventRow], dict]:
    """全宇宙 prices 行流 → EventRow 显式事件源(纯函数,零 I/O)。

    price_rows: PriceRow 迭代器,(ts_code, trade_date) 升序(SQL ORDER BY 钉死;fixture=构造行)。
    listing: {ts_code: {list_date, delist_date, ...}}(P1-2/C5 锚定,缺=该票 fail-closed)。
    返回 (events, selection)——selection 全量留痕(counters/rejects/reject_reasons)入 audit。
    层键=recent_listing|seasoned 二值(规则 recent_listing 布尔标记直译;白名单对账在 runner)。"""
    per_security = []
    for ts_code, grp in itertools.groupby(price_rows, key=lambda r: r.ts_code):
        rows = [{"trade_date": r.trade_date, "limit_status": r.limit_status,
                 "open_limit_status": r.open_limit_status} for r in grp]
        per_security.append(select_limit_open_events(ts_code, rows,
                                                     listing=listing.get(ts_code)))
    sel = merge_selections(per_security)
    events = [EventRow(ts_code=e["ts_code"],
                       event_id=f"{e['ts_code']}:{e['event_date'].replace('-', '')}",
                       first_ann_date=dt.date.fromisoformat(e["event_date"]),
                       event_type_layer=(LAYER_RECENT if e["recent_listing"]
                                         else LAYER_SEASONED),
                       snapshot_batch=batch)
              for e in sel["events"]]
    return events, sel


def selection_audit(sel: dict) -> dict:
    """selection → audit 块(纯函数;PAP reporting_commitments 转录):
    计数/剔除逐年逐因分解/重复映射与 listing fail-closed 逐条/链长分布/逐年分布/层分布。"""
    def year_of(item: dict) -> str:
        return (item.get("event_date") or item["chain_end_date"])[:4]

    chain_len_dist: dict = {}
    yearly: dict = {}
    layer_counts = {LAYER_RECENT: 0, LAYER_SEASONED: 0}
    for e in sel["events"]:
        chain_len_dist[str(e["chain_len"])] = chain_len_dist.get(str(e["chain_len"]), 0) + 1
        yearly[year_of(e)] = yearly.get(year_of(e), 0) + 1
        layer_counts[LAYER_RECENT if e["recent_listing"] else LAYER_SEASONED] += 1
    rejects_yearly_by_reason: dict = {}
    for r in sel["rejects"]:
        by_year = rejects_yearly_by_reason.setdefault(r["reason"], {})
        by_year[year_of(r)] = by_year.get(year_of(r), 0) + 1
    itemized = {reason: [r for r in sel["rejects"] if r["reason"] == reason]
                for reason in ITEMIZED_REJECT_REASONS}
    return {"counters": sel["counters"],
            "reject_reasons": sel["reject_reasons"],
            "rejects_yearly_by_reason": rejects_yearly_by_reason,
            "itemized_rejects": itemized,
            "chain_len_dist": chain_len_dist,
            "events_yearly": yearly,
            "layer_counts": layer_counts}


def main():
    # DB 依赖延迟导入:fixture(verify_limit_open_adapter)零 DB 消费上方纯函数
    from taosha.engine import report, runner
    from taosha.experiment import ledger
    from taosha.experiment.pap import canonical_pap_sha256
    from taosha.reader.view import ViewReader

    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", type=int, required=True)
    ap.add_argument("--snapshot-id", type=int, required=True,
                    help="StudySnapshot manifest ID(硬化② fail-closed,无 manifest 拒运行)")
    ap.add_argument("--pap-sha256-assert", required=True,
                    help="冻结批复绑定 digest(仅逐字断言;权威=引擎重算,不一致 fail-closed)")
    ap.add_argument("--json", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    row = ledger.get(a.exp_id)
    if row is None:
        raise SystemExit(f"exp_id={a.exp_id} 不存在")
    if row["status"] != "frozen":
        raise SystemExit(f"铁律③:引擎拒执行 status={row['status']}≠frozen(exp_id={a.exp_id})")

    pap = dict(row["pap_json"])
    pap["_family_trial"] = row["family_trial"]
    # driver 侧先行断言(fail-fast;权威断言仍在 runner 内重算处,双保险不替代)
    driver_recalc = canonical_pap_sha256(pap)
    if driver_recalc != a.pap_sha256_assert:
        raise SystemExit(f"fail-closed: 台账冻结 pap 重算 canonical digest={driver_recalc} "
                         f"≠ --pap-sha256-assert={a.pap_sha256_assert}(令二绑定 digest)")
    kwargs = engine_kwargs_from_pap(pap)
    print(f"exp_id={a.exp_id} {row['family']}/{row['title']} status={row['status']} "
          f"family_trial={row['family_trial']} verdict_power={row['verdict_power']}", flush=True)
    print(f"pap canonical digest={driver_recalc}(断言通过)", flush=True)
    print(f"engine_params(逐字消费冻结件)= "
          f"{ {k: v for k, v in kwargs.items()} }", flush=True)

    # 全宇宙事件生成(设计 §1):sample=listing 全A键集 → prices 流 → 逐票纯函数
    vr = ViewReader(snapshot_id=a.snapshot_id)
    listing = vr.listing()
    universe = ViewReader(snapshot_id=a.snapshot_id, sample=set(listing))
    batch = f"study_snapshot:{a.snapshot_id}"
    events, sel = events_from_prices(universe.prices(), listing, batch)
    print(f"limit_open 全宇宙扫描: 票={len(listing)} 输入行={sel['counters']['input_rows']} "
          f"链≥N={sel['counters']['chains_ge_n']} → 事件={len(events)}"
          f"(剔除留痕入 audit)", flush=True)

    reader = ViewReader(snapshot_id=a.snapshot_id, sample={e.ts_code for e in events})
    result = runner.run_study(reader, pap, events=events,
                              pap_sha256_assert=a.pap_sha256_assert, **kwargs)
    result["audit"]["study_snapshot"] = reader.snapshot_info
    result["audit"]["limit_open_selection"] = selection_audit(sel)

    rendered = report.render(result)
    print("\n" + rendered)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
        print(f"\nresult_json → {a.json}", flush=True)
    if a.report:
        with open(a.report, "w") as fh:
            fh.write(rendered)
        print(f"report → {a.report}", flush=True)


if __name__ == "__main__":
    main()
