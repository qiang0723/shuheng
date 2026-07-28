"""exp24 driver/τ0/report 适配攻击 fixture（零 DB、零收益实物）。"""
from __future__ import annotations

import copy
import datetime as dt
import json
import math
import os
import tempfile
from unittest import mock

from taosha.engine.cleaning import clean_event
from taosha.engine.report_sox_spillover import header_lines, selection_lines
from taosha.harness.run_sox_spillover_study import (
    PAP_DIGEST, SOURCE_ANCHOR_SNAPSHOT_ID, _run_formal, engine_kwargs_from_pap,
    selection_audit,
)
from taosha.reader.contract import CalendarRow, EventRow, PriceRow
from taosha.reader.sox_spillover import SoxSpilloverReader
from taosha.reader.view import _ENV_QBASE, _resolve_dsn


class Checks:
    def __init__(self):
        self.n = 0

    def ok(self, value, note):
        assert value, note
        self.n += 1


def _pap():
    with open("taosha/docs/sox-spillover-pap-final-v2-2026-07-28.json", encoding="utf-8") as fh:
        return json.load(fh)


def _rows(dates, missing=()):
    return [PriceRow("A.SZ", d, 100.0 + i / 100, False, "none", "main", False, "电子")
            for i, d in enumerate(dates) if i not in set(missing)]


def _clean(missing=(), *, same_day=True):
    dates = [dt.date(2019, 1, 1) + dt.timedelta(days=i) for i in range(400)]
    event = EventRow("A.SZ", "e", dates[300], "up", "fixture")
    return clean_event(_rows(dates, missing), event, {d: i for i, d in enumerate(dates)},
                       postpone_policy="missing_bar_only", axis_dates=dates,
                       tau0_on_anchor=same_day)


def _fake_selection():
    counters = {
        "input_sox_rows": 3395, "triggers": 314, "trigger_up": 161, "trigger_down": 153,
        "exact_boundary": 0, "mapped_dates": 301, "collision_dates": 9,
        "collision_triggers_dropped": 22, "surviving_trigger_dates": 292,
        "surviving_up": 150, "surviving_down": 142, "expanded_candidates": 100,
        "duplicate_event_keys": 0, "duplicate_events_dropped": 0, "final_events": 100,
    }
    return {
        "counters": counters, "trigger_event_dates": 292, "funnel_identity_ok": True,
        "data_quality_disclosure": "388行currency空值;2015-02-02差异;NOT_FOR_VERDICT",
        "trigger_yearly": {2020: 1}, "collision_items": [], "member_rejects": [],
        "duplicate_items": [], "pool_members_by_event_date": {dt.date(2020, 1, 3): 2},
    }


class _EngineReader:
    def __init__(self):
        self.dates = [dt.date(2019, 1, 1) + dt.timedelta(days=i) for i in range(400)]
        self.rows = [PriceRow("A.SZ", d, 100 + i * 0.03 + math.sin(i / 7), False,
                              "none", "main", False, "电子", open=100 + i * 0.03)
                     for i, d in enumerate(self.dates)]

    def prices_by_security(self):
        return {"A.SZ": self.rows}

    def calendar(self):
        return [CalendarRow(d, None if i == 0 else self.dates[i - 1])
                for i, d in enumerate(self.dates)]

    def market_return(self, dates):
        return [None] + [(0.002 if i % 2 else -0.001) for i in range(1, len(dates))]


def _verdict_key_count(obj) -> int:
    if isinstance(obj, dict):
        return sum(k == "verdict" for k in obj) + sum(_verdict_key_count(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(_verdict_key_count(v) for v in obj)
    return 0


def main():
    c = Checks()
    with tempfile.TemporaryDirectory() as tmp:
        env_file = os.path.join(tmp, ".env")
        with open(env_file, "w", encoding="utf-8") as fh:
            fh.write(f"{_ENV_QBASE}=file-dsn\n")
        with mock.patch.dict(os.environ, {_ENV_QBASE: "env-dsn"}, clear=True):
            c.ok(_resolve_dsn(_ENV_QBASE, "explicit-dsn", env_file) == "explicit-dsn",
                 "DSN显式参数优先")
            c.ok(_resolve_dsn(_ENV_QBASE, env_path="/unreadable/not-opened") == "env-dsn",
                 "容器环境优先于env文件且不触文件读取")
        with mock.patch.dict(os.environ, {}, clear=True):
            c.ok(_resolve_dsn(_ENV_QBASE, env_path=env_file) == "file-dsn", ".env兜底")
            empty_file = os.path.join(tmp, "empty.env")
            open(empty_file, "w", encoding="utf-8").close()
            try:
                SoxSpilloverReader(247, env_path=empty_file)
            except RuntimeError:
                c.ok(True, "三路均缺时fail-closed")
            else:
                c.ok(False, "缺DSN不得继续")
    pap = _pap()
    kwargs = engine_kwargs_from_pap(pap)
    c.ok(kwargs["tau0_on_anchor"] is True, "映射日当日τ0固定")
    c.ok(kwargs["direction_layers"] == ("up", "down"), "方向白名单固定")
    c.ok(kwargs["direction_signed_main"] is True, "signed主路径")
    c.ok(kwargs["postpone_policy"] == "missing_bar_only", "仅缺bar顺延")
    c.ok(set(pap["signed_ar"]) == {"application_level", "estimand", "formula", "single_verdict"},
         "signed_ar全键")

    bad = copy.deepcopy(pap)
    bad["engine_params"]["extra"] = 1
    try:
        engine_kwargs_from_pap(bad)
    except SystemExit:
        c.ok(True, "engine_params多键拒")
    else:
        c.ok(False, "engine_params篡改应拒")
    bad = copy.deepcopy(pap)
    del bad["signed_ar"]["formula"]
    try:
        engine_kwargs_from_pap(bad)
    except SystemExit:
        c.ok(True, "signed_ar缺键拒")
    else:
        c.ok(False, "signed_ar篡改应拒")

    ce = _clean()
    c.ok(ce.tau0_idx == 300, "τ0=event_date当日")
    c.ok(_clean(same_day=False).tau0_idx == 301, "默认旧路径仍锚后首日")
    c.ok(_clean(missing=range(300, 305)).tau0_idx == 305, "缺bar顺延5日保留")
    c.ok(_clean(missing=range(300, 306)).reject_reason == "postpone", "第6日仍缺bar剔除")
    one_word_dates = [dt.date(2019, 1, 1) + dt.timedelta(days=i) for i in range(400)]
    rows = _rows(one_word_dates)
    rows[300] = PriceRow("A.SZ", one_word_dates[300], 103.0, False, "one_word",
                         "main", False, "电子")
    ev = EventRow("A.SZ", "e", one_word_dates[300], "up", "fixture")
    ow = clean_event(rows, ev, {d: i for i, d in enumerate(one_word_dates)},
                     postpone_policy="missing_bar_only", axis_dates=one_word_dates,
                     tau0_on_anchor=True)
    c.ok(ow.tau0_idx == 300 and ow.postponed == 0, "一字板有bar当日入CAR")
    try:
        clean_event(rows, ev, {d: i for i, d in enumerate(one_word_dates)},
                    postpone_policy="legacy", tau0_on_anchor=True)
    except ValueError:
        c.ok(True, "同日τ0与非missing_bar策略组合拒绝")
    else:
        c.ok(False, "非法参数组合应拒")

    audit = {"benchmark_mode": "market", "study_snapshot": {"snapshot_id": 999, "digest": "d"}}
    title = "\n".join(header_lines(audit))
    c.ok("exp24 SOX半导体链同向溢出" in title, "exp24真锚标题")
    c.ok("StudySnapshot=999" in title, "报告快照锚")
    lines = "\n".join(selection_lines(_fake_selection()))
    c.ok("存活触发事件日=292" in lines, "低功效事件日数")
    c.ok("388行currency空值" in lines and "2015-02-02" in lines, "数据质量披露")
    c.ok("NOT_FOR_VERDICT" in lines, "诊断水印")
    c.ok(not any(k == "verdict" for k in _fake_selection()), "诊断块零verdict键")
    json_audit = selection_audit(_fake_selection(), pap)
    c.ok(json_audit["pool_members_by_event_date"] == {"2020-01-03": 2},
         "date审计键确定性转换为ISO字符串")
    encoded_audit = json.dumps(json_audit, ensure_ascii=False)
    c.ok(json.loads(encoded_audit)["pool_members_by_event_date"] == {"2020-01-03": 2},
         "完整selection_audit可JSON序列化并读回ISO日期键")

    class Args:
        snapshot_id = SOURCE_ANCHOR_SNAPSHOT_ID
    try:
        _run_formal(Args(), pap, kwargs, {}, {})
    except SystemExit as exc:
        c.ok("仅为源级锚" in str(exc), "snapshot247冒充正式manifest拒绝")
    else:
        c.ok(False, "snapshot247应拒")
    c.ok(len(PAP_DIGEST) == 64, "冻结digest全长")

    from taosha.engine import runner
    engine_pap = copy.deepcopy(pap)
    engine_pap["_family_trial"] = 1
    rd = _EngineReader()
    engine_event = EventRow("A.SZ", "e", rd.dates[300], "up", "fixture")
    result = runner.run_study(rd, engine_pap, events=[engine_event],
                              pap_sha256_assert=PAP_DIGEST, **kwargs)
    c.ok(result["n_valid"] == 1, "缺axes的exp24冻结PAP经显式白名单可确定执行")
    c.ok(result["audit"]["premend_params"]["tau0_on_anchor"] is True, "同日τ0入审计")
    c.ok(result["per_tau"]["tau_axis"].startswith("τ=0:=event_date当日"), "τ轴正文正确")
    c.ok(_verdict_key_count(result) == 1, "全文唯一顶层verdict")

    sql = open("qbase/sql/021_sox_spillover_reader.sql", encoding="utf-8").read()
    c.ok("study_snap_batch('sox_daily')" in sql and "study_snap_batch('sw_member')" in sql,
         "两数据腿均由manifest路由")
    c.ok("GRANT SELECT ON public.explore_reader_sox_daily_snap TO taosha_engine" in sql,
         "引擎只读授权显式")
    c.ok("s.trade_date < DATE '2024-07-01'" in sql, "SOX holdout视图焊死")

    print(f"verify_sox_spillover_adapter: {c.n}/{c.n} PASS")


if __name__ == "__main__":
    main()
