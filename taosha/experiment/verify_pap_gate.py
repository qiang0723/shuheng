"""淘沙 · PAP 可执行离场硬门自检(外审五项修法 #1,常设)。

职责: 以 taosha_app 身份实测三层硬门之层②(冻结触发器 _pap_freeze_gate)+层③(策略驱动
启动校验,子进程实测)——反向(a)禁组合/缺必填/白名单外/缺schema/伪称legacy/legacy升级为
策略/越权写registry 全拒 + 正向(b)legacy事件版冻结、两类合法执行方式、纯事件schema 全通。
(层①=python validate_pap,自检在 `python -m taosha.experiment.pap`。)
口径依据: docs/postaudit-five-order-2026-07-13.md #1(人终签 2026-07-13)。
验收档: taosha/docs/postaudit-item1-pap-execution-gate-acceptance-2026-07-13.md。

机制: 单事务 + 逐用例 SAVEPOINT + 末尾整体 ROLLBACK,台账/registry 零残留。
运行: aliyun `python -m taosha.experiment.verify_pap_gate`(需 TAOSHA_APP_DSN;层③子进程
     另需 TAOSHA_ENGINE_* DSN 于环境中)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import psycopg

FAMILY = "_smtest_papgate"

SE_C2N = {"execution_profile": "close_to_next_open", "decision_time": "close_confirmed",
          "fill_time": "next_open", "fill_price": "next_adjusted_open",
          "slippage_rule": "frozen_cost"}
# 窄补(2026-07-13): preclose_to_tail 时间字段结构化(HH:MM;~~自由文本占位~~作废)
SE_PCT = {"execution_profile": "preclose_to_tail", "decision_cutoff": "14:50",
          "decision_price_source": "探针占位(人定)",
          "fill_window": {"start": "14:55", "end": "15:00"},
          "fill_price_rule": "探针占位(人定)", "slippage_rule": "frozen_cost"}

_results: list[tuple[str, bool, str]] = []


def _ok(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))


def _pap(**extra) -> str:
    base = {"probe": True, "note": "papgate 探针,事务内回滚不落库"}
    base.update(extra)
    return json.dumps(base, ensure_ascii=False)


def _insert(cur, title: str, pap_text: str) -> int:
    cur.execute(
        """INSERT INTO experiment (family, family_trial, title, source_type, verdict_power,
                                   contamination_note, pap_json, data_class, crowding_prior)
           VALUES (%s, 0, %s, 'human', 'full', 'papgate 探针行(回滚不落库)',
                   %s::jsonb, '量价', '低') RETURNING exp_id""",
        (FAMILY, title, pap_text))
    return cur.fetchone()[0]


def _freeze_reject(cur, name: str, pap_text: str) -> None:
    """插入探针行→尝试冻结,期望被层② gate 拒;SAVEPOINT 全程回滚。"""
    cur.execute("SAVEPOINT c")
    try:
        e = _insert(cur, f"[papgate] {name}", pap_text)
        cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (e,))
    except psycopg.Error as err:
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, True, str(err).splitlines()[0][:130])
        return
    cur.execute("ROLLBACK TO SAVEPOINT c")
    _ok(name, False, "本应被拒却放行")


def _freeze_allow(cur, name: str, pap_text: str) -> None:
    cur.execute("SAVEPOINT c")
    try:
        e = _insert(cur, f"[papgate] {name}", pap_text)
        cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (e,))
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, True)
    except psycopg.Error as err:
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, False, f"合法路径被误拒: {str(err).splitlines()[0][:130]}")


def _engine_fill_probe(frozen_pap: dict) -> None:
    """窄补反向测试①(引擎半)+ 窄补第三轮 #1-a/#1-b(2026-07-13): 用 DB 冻结后读回的 pap
    实跑合成单事件,**直接断言事件级 fill 字段**(signal_date/fill_date/fill_price/fill_source,
    禁由聚合净收益反推);E3=人令反例(当天 open 可成交但收盘跌停 → 不顺延,日终字段不进判定);
    E4=开盘恰在跌停位 → 按冻结代理规则顺延(fill_source='postponed_open')。
    附 E2: 结构合法 preclose_to_tail(可冻结)执行 fail-closed 拒(未实现不得旧口径兜底)。"""
    import datetime as dt
    import math

    from taosha.engine.drawdown_strategy import run_strategy
    from taosha.reader.contract import CalendarRow, PriceRow

    base = dt.date(2020, 1, 6)
    n_days = 400
    dates = [base + dt.timedelta(days=i) for i in range(n_days)]
    closes = ([100.0 + 0.5 * math.sin(i) for i in range(330)]
              + [102.0] * 15 + [90.0] + [95.0] * (n_days - 346))

    def _rows(ts, closes_, opens_=None, lim=None, olim=None):
        opens_ = opens_ or closes_
        return [PriceRow(ts_code=ts, trade_date=dates[i], close=closes_[i], is_suspended=False,
                         limit_status=(lim or {}).get(i, "none"), board="main", is_st=False,
                         industry="I", open=opens_[i],
                         open_limit_status=(olim or {}).get(i, "none")) for i in range(n_days)]

    class _Ev:
        ts_code = "A01"; event_id = "A01:E1"; snapshot_batch = "SYNTH"
        first_ann_date = dates[330]; event_type_layer = None
        d1_never_broke_ma10 = False; d2_episode_to_entry_days = 3; d3_broke_ma20_before_entry = False

    def _reader(rows):
        class _Rd:
            def prices_by_security(self):
                return {"A01": rows}
            def calendar(self):
                return [CalendarRow(trade_date=d, pretrade_date=None) for d in dates]
            def pool_return(self, ds):
                return [None] + [(0.001 if i % 2 == 0 else -0.001) for i in range(1, len(ds))]
        return _Rd()

    pap = dict(frozen_pap)
    pap["_family_trial"] = 1
    # E1: idx345 close=90 破 ma20 收盘确认;次日 idx346 open=95 成交。
    # 窄补第三轮 #1-a: 直接断言 fill 字段值(净收益比对保留为交叉项,不再是判据本体)。
    fill_next_open = 95.0 * (1 - 0.00225) / (102.0 * (1 + 0.00125)) - 1
    try:
        res = run_strategy(_reader(_rows("A01", closes)), pap, [_Ev()])
        sv = res["strategy_version"]
        f0 = sv["fills"]["records"][0]
        ok = (f0["signal_date"] == dates[345].isoformat()
              and f0["fill_date"] == dates[346].isoformat()
              and f0["fill_price"] == 95.0
              and f0["fill_source"] == "next_open"
              and sv["fills"]["by_source"] == {"next_open": 1}
              and abs(sv["net"]["mean"] - fill_next_open) < 1e-12          # 交叉项
              and sv["execution"]["profile"] == "close_to_next_open"
              and "非真实委托成交验证" in sv["execution"]["fill_feasibility_proxy_rule"])
        _ok("E1 冻结后 fill 字段直接断言: signal=触发日/fill=次日@open95/source=next_open", ok,
            f"signal={f0['signal_date']} fill={f0['fill_date']}@{f0['fill_price']} "
            f"[{f0['fill_source']}]")
    except Exception as err:  # noqa: BLE001 —— 探针如实报错
        _ok("E1 冻结后 fill 字段直接断言: signal=触发日/fill=次日@open95/source=next_open",
            False, str(err)[:130])

    # E3(窄补第三轮反例,人令统一验收要求): 名义成交日 idx346 open=97 可成交(开盘时点字段
    # 'none')但**收盘跌停**(日终 limit_status='limit_down')→ 照常当日 open 成交,不顺延。
    # 旧实现(日终 _sellable 判开盘)在此序列会错误顺延到 idx347——新代理规则已消灭该前视。
    c3 = list(closes); c3[346] = 85.0                       # 收盘跌停日的 close(数值仅示意)
    o3 = list(closes); o3[346] = 97.0; o3[347] = 91.0       # 开盘 97 可成交;若误顺延会拿到 91
    try:
        res = run_strategy(_reader(_rows("A01", c3, o3, lim={346: "limit_down"})), pap, [_Ev()])
        f0 = res["strategy_version"]["fills"]["records"][0]
        ok = (f0["fill_date"] == dates[346].isoformat() and f0["fill_price"] == 97.0
              and f0["fill_source"] == "next_open")
        _ok("E3 反例: 当日open=97可成交而收盘跌停 → 当日open成交**不顺延**(日终字段不进判定)",
            ok, f"fill={f0['fill_date']}@{f0['fill_price']} [{f0['fill_source']}]"
                f"(误顺延将={dates[347].isoformat()}@91.0)")
    except Exception as err:  # noqa: BLE001
        _ok("E3 反例: 当日open=97可成交而收盘跌停 → 当日open成交**不顺延**(日终字段不进判定)",
            False, str(err)[:130])

    # E4: 名义成交日开盘恰在跌停位(open_limit_status='open_at_down_limit')→ 按冻结代理规则
    # 顺延至首个代理可成交 bar 的 open,fill_source='postponed_open'(能力边界=代理非验证)。
    o4 = list(closes); o4[346] = 88.0; o4[347] = 91.0
    try:
        res = run_strategy(_reader(_rows("A01", closes, o4,
                                         olim={346: "open_at_down_limit"})), pap, [_Ev()])
        f0 = res["strategy_version"]["fills"]["records"][0]
        ok = (f0["fill_date"] == dates[347].isoformat() and f0["fill_price"] == 91.0
              and f0["fill_source"] == "postponed_open")
        _ok("E4 开盘恰在跌停位 → 按代理规则顺延(postponed_open;代理规则非成交验证)",
            ok, f"fill={f0['fill_date']}@{f0['fill_price']} [{f0['fill_source']}]")
    except Exception as err:  # noqa: BLE001
        _ok("E4 开盘恰在跌停位 → 按代理规则顺延(postponed_open;代理规则非成交验证)",
            False, str(err)[:130])

    try:
        run_strategy(_reader(_rows("A01", closes)), dict(pap, strategy_execution=SE_PCT), [_Ev()])
        _ok("E2 preclose_to_tail 可冻结但执行 fail-closed 拒(未实现不得兜底)", False, "放行=静默兜底")
    except SystemExit as err:
        _ok("E2 preclose_to_tail 可冻结但执行 fail-closed 拒(未实现不得兜底)",
            "未实现" in str(err), str(err)[:130])


def main() -> int:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        print("环境无 TAOSHA_APP_DSN(应 source /opt/quant/.env,勿回显)", file=sys.stderr)
        return 2
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        # ── 结构断言: registry 物化普查 ──
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname='pap_legacy_registry' AND NOT t.tgisinternal""")
        _ok("S1 legacy registry 表+焊死触发器在位", cur.fetchone()[0] >= 2)
        cur.execute("""SELECT count(*),
                              count(*) FILTER (WHERE status_at_migration='registered'),
                              count(*) FILTER (WHERE status_at_migration='frozen'),
                              count(*) FILTER (WHERE status_at_migration='done'),
                              count(*) FILTER (WHERE status_at_migration='closed')
                       FROM pap_legacy_registry""")
        tot, r, f_, d, c = cur.fetchone()
        _ok("S2 物化普查=全 25 存量(确认点②含 frozen/done/closed)",
            (tot, r, f_, d, c) == (25, 18, 3, 3, 1), f"total={tot} reg={r} froz={f_} done={d} closed={c}")
        cur.execute("SELECT count(*) FROM pap_legacy_registry WHERE exp_id IN (3,4,5)")
        _ok("S3 exp3(#2b)/exp4(#3)/exp5(#4) 在册", cur.fetchone()[0] == 3)

        # ── 正向(b) ──
        # F1 标本=动态选取 registered 态 legacy 实验(原硬编码 exp8;exp8 依冻结令
        # 2026-07-17 深夜五真冻结后标本失效——探针语义不变,只换活标本,SAVEPOINT 回滚零残留)
        cur.execute("""SELECT min(e.exp_id) FROM experiment e
                       JOIN pap_legacy_registry r ON r.exp_id = e.exp_id
                       WHERE e.status = 'registered'""")
        f1_specimen = cur.fetchone()[0]
        cur.execute("SAVEPOINT f1")
        try:
            cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() "
                        "WHERE exp_id=%s AND status='registered'", (f1_specimen,))
            ok = f1_specimen is not None and cur.rowcount == 1
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok(f"F1 既有 registered 纯事件 legacy 实验(exp{f1_specimen})事件版冻结放行", ok)
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok(f"F1 既有 registered 纯事件 legacy 实验(exp{f1_specimen})事件版冻结放行", False,
                str(err).splitlines()[0][:130])
        _freeze_allow(cur, "F2 合法 close_to_next_open PAP 冻结放行",
                      _pap(pap_schema_version=2, analysis_type="strategy", strategy_execution=SE_C2N))
        _freeze_allow(cur, "F3 合法 preclose_to_tail PAP(必填全给)冻结放行",
                      _pap(pap_schema_version=2, analysis_type="event_and_strategy",
                           strategy_execution=SE_PCT))
        _freeze_allow(cur, "F4 新纯事件 schema PAP 冻结放行(不要求 strategy_execution)",
                      _pap(pap_schema_version=2, analysis_type="event"))

        # ── 反向(a) ──
        _freeze_reject(cur, "R1 新登记删除 pap_schema_version 冻结拒",
                       _pap())
        _freeze_reject(cur, "R2 close_confirmed+same_close 禁组合冻结拒(信息时序)",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "close_to_next_open",
                                                "decision_time": "close_confirmed",
                                                "fill_time": "same_close",
                                                "fill_price": "same_close",
                                                "slippage_rule": "frozen_cost"}))
        _freeze_reject(cur, "R3 preclose_to_tail 缺 decision_cutoff/decision_price_source 冻结拒",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "preclose_to_tail",
                                                "fill_window": "尾盘", "fill_price_rule": "x",
                                                "slippage_rule": "frozen_cost"}))
        _freeze_reject(cur, "R4 execution_profile 白名单外冻结拒",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "same_close_exec"}))
        _freeze_reject(cur, "R5 伪称 legacy(pap 带 legacy 字段/自报 registered_at)冻结拒",
                       _pap(legacy=True, registered_at_claim="2026-07-01"))
        cur.execute("SAVEPOINT r6")
        try:
            cur.execute("UPDATE experiment SET pap_json = pap_json || %s::jsonb "
                        "WHERE exp_id=8 AND status='registered'",
                        (json.dumps({"pap_schema_version": 2, "analysis_type": "strategy",
                                     "strategy_execution": SE_C2N}),))
            cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=8")
            cur.execute("ROLLBACK TO SAVEPOINT r6")
            _ok("R6 legacy 升级 schema 后 analysis_type=strategy 冻结拒(legacy 只许事件版)",
                False, "本应被拒却放行")
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT r6")
            _ok("R6 legacy 升级 schema 后 analysis_type=strategy 冻结拒(legacy 只许事件版)",
                True, str(err).splitlines()[0][:130])
        cur.execute("SAVEPOINT r7")
        try:
            cur.execute("INSERT INTO pap_legacy_registry (exp_id, status_at_migration, note) "
                        "VALUES (26, 'registered', 'x')")
            cur.execute("ROLLBACK TO SAVEPOINT r7")
            _ok("R7 taosha_app 写 legacy registry 拒(权限验证)", False, "本应被拒却放行")
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT r7")
            _ok("R7 taosha_app 写 legacy registry 拒(权限验证)", True,
                str(err).splitlines()[0][:120])

        # ── 窄补(外审第二轮 2026-07-13): 结构化时间字段反向 ──
        _freeze_reject(cur, "R8 反向时间窗口冻结拒: decision_cutoff(15:00) ≥ fill_window.start(14:55)",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution=dict(SE_PCT, decision_cutoff="15:00")))
        _freeze_reject(cur, "R9 decision_cutoff 自由文本冻结拒(结构化 HH:MM,非字符串非空判断)",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution=dict(SE_PCT, decision_cutoff="尾盘前(自由文本)")))
        _freeze_reject(cur, "R10 fill_window 非结构化冻结拒(须 {start,end} HH:MM)",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution=dict(SE_PCT, fill_window="尾盘窗占位(字符串)")))

        # ── 窄补 E1(反向测试①): 合法 close_to_next_open 冻结后,实际成交=次日开盘 ──
        cur.execute("SAVEPOINT e1")
        e1_pap = None
        try:
            e = _insert(cur, "[papgate] E1 冻结→执行探针",
                        _pap(pap_schema_version=2, analysis_type="strategy",
                             strategy_execution=SE_C2N,
                             window="事件版20/60日;策略版按离场",
                             cost={"commission": 0.00025, "stamp_tax_sell": 0.001,
                                   "slippage_oneway": 0.001, "limit_up_board_untradeable": True}))
            cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (e,))
            cur.execute("SELECT pap_json FROM experiment WHERE exp_id=%s AND status='frozen'", (e,))
            e1_pap = cur.fetchone()[0]
        except psycopg.Error as err:
            _ok("E1 合法 close_to_next_open 冻结后实际成交=次日开盘(非同刻收盘)", False,
                f"冻结段失败: {str(err).splitlines()[0][:120]}")
        cur.execute("ROLLBACK TO SAVEPOINT e1")
        if e1_pap is not None:
            _engine_fill_probe(e1_pap)

        conn.rollback()
        cur.execute("SELECT count(*) FROM experiment WHERE family=%s", (FAMILY,))
        n1 = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM experiment")
        n2 = cur.fetchone()[0]
        _ok("Z1 回滚后零残留(探针 0 行/台账 25 行)", n1 == 0 and n2 == 25, f"probe={n1} total={n2}")
        conn.rollback()

    # ── 层③: 策略驱动启动校验(子进程实测,exp3=legacy 在册) ──
    p = subprocess.run(
        [sys.executable, "-m", "taosha.harness.run_drawdown_strategy",
         "--exp-id", "3", "--snapshot-id", "1", "--diagnostic", "--reason", "papgate 层③探针"],
        capture_output=True, text=True, timeout=120)
    out = (p.stdout or "") + (p.stderr or "")
    _ok("L1 层③ 策略驱动对 legacy(exp3)一律拒(含 --diagnostic)",
        p.returncode != 0 and "修法#1" in out and "pap_legacy_registry" in out,
        out.strip().splitlines()[-1][:130] if out.strip() else f"rc={p.returncode}")

    failed = [r for r in _results if not r[1]]
    print(f"\n== PAP 硬门自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    if failed:
        for name, _, detail in failed:
            print(f"  FAIL: {name} {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
