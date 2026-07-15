"""三窗判点①自检(人裁 2026-07-15,留痕 docs/holder-sell-rulings-2026-07-15.md)。

验收要求(人令原文):"测试须直接证明5/20/60三窗均真实计算,尤其使用三窗结果可区分的
fixture,不能只检查字段存在。既有合成结果及其他实验不得漂移。"

fixture 构造(确定性种子,窗取 2/4/6 日缩小规模、判点同构):40 证券×1 事件,事件日错峰;
对每证券在其自身 τ=0 注入 +3%、τ=2 注入 −2%、τ=4 注入 +1.5% 异常收益 →
  主窗[0,+1] CAAR ≈ +3%、次级窗[0,+3] CAAR ≈ +1%、稳健窗[0,+5] CAAR ≈ +2.5%
(等权市场吸收 ≈(3−2+1.5)%/40/日 稀释),三窗数值两两可区分且逐窗手算可核——
只查字段存在无法通过本件。

断言族:
  T1 结构:三窗 pap → car.secondary_windows.windows 恰 1 块 taus=[0,+3];
  T2 真实计算:三窗 CAAR 各落手算期望带内、两两差 > 判别阈、与 per_tau AAR 前缀和逐位一致、
     三窗 ADJ-BMP 皆非 None 且两两不同;
  T3 判决隔离:剔除 secondary_windows 后 _verdict 复算 == result 原 verdict/verdict_note
     (5日主窗唯一进判决,次级窗不参与);
  T4 分层贯通:type_strata 各层同样产出 secondary_windows(同窗);
  T5 零回归半:同 fixture 两窗 pap("后2/6日")→ result 全文无 secondary_windows 键
     (既有 #4/#2b/合成两窗形态 result 逐字节不变的结构性证明;
      全量零回归硬证=make_ashare_fixture 合成 e2e sha 3116ba9b 前后比对,随件另跑)。

用法:PYTHONPATH=… python -m taosha.harness.verify_three_windows
"""
from __future__ import annotations

import copy
import csv
import datetime as dt
import json
import math
import random
import tempfile

from taosha.engine import runner
from taosha.experiment import gates
from taosha.experiment import pap as pap_mod
from taosha.reader.synthetic import SyntheticReader

N_SEC = 40
N_DAYS = 340
EVENT_BASE_IDX = 270                     # 首事件日索引(估计窗 [T-250,T-91] 完整覆盖)
INJ = {0: 0.03, 2: -0.02, 4: 0.015}      # τ→注入异常收益(τ=0:=T+1)
INDUSTRIES = ("银行", "地产", "医药", "科技")
SEED = 20260715


def _biz_days(start: dt.date, n: int) -> list[dt.date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def make_fixture(prices_path: str, events_path: str) -> None:
    rng = random.Random(SEED)
    dates = _biz_days(dt.date(2020, 1, 2), N_DAYS)
    rm = [rng.gauss(0.0, 0.008) for _ in range(N_DAYS)]
    ev_idx = {i: EVENT_BASE_IDX + i for i in range(N_SEC)}   # 事件日错峰(逐日一只)
    with open(prices_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts_code", "trade_date", "close", "is_suspended",
                    "limit_status", "board", "is_st", "industry", "open"])
        for i in range(N_SEC):
            code = f"6{i:05d}.SH"
            px = 100.0 * (1 + i / 100)
            tau0 = ev_idx[i] + 1                              # τ=0 := T+1
            for t in range(N_DAYS):
                r = rm[t] + rng.gauss(0.0, 0.004)
                if t - tau0 in INJ:
                    r += INJ[t - tau0]
                px *= math.exp(r)
                w.writerow([code, dates[t].isoformat(), f"{px:.10f}", 0,
                            "none", "main", 0, INDUSTRIES[i % 4], f"{px:.10f}"])
    with open(events_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts_code", "event_id", "first_ann_date", "event_type_layer", "snapshot_batch"])
        for i in range(N_SEC):
            w.writerow([f"6{i:05d}.SH", f"3W-{i:03d}", dates[ev_idx[i]].isoformat(),
                        "预喜", "SYNTH-3W"])


def _pap(window: str) -> dict:
    p = pap_mod.build_pap(
        event_def={"kind": "SYNTH_3WIN", "anchor": "first_ann_date", "layer": "预喜"},
        window=window,
        pool={"kind": "全市场等权(合成)"},
        cleaning={"est_window": [-250, -91], "coverage_min": "112/160(70%)",
                  "suspension": "事件落停牌期剔除", "st": "剔除", "one_word": "顺延"},
        snapshot_batch_req="SYNTH-3W",
        extra={"pap_schema_version": pap_mod.PAP_SCHEMA_VERSION, "analysis_type": "event"},
    )
    p["_family_trial"] = 1
    return p


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        pp, ep = f"{td}/prices.csv", f"{td}/events.csv"
        make_fixture(pp, ep)

        # ── 三窗跑(后2/4/6日 → main=[0,+1] / secondary=[0,+3] / robust=[0,+5])──
        res = runner.run_study(SyntheticReader(pp, ep), _pap("T+1起,后2/4/6日"),
                               benchmark_mode="market")
        car = res["car"]

        # T1 结构
        sec_blk = car.get("secondary_windows")
        assert sec_blk and len(sec_blk["windows"]) == 1, f"T1: 次级窗块缺失/数目错 {sec_blk!r}"
        sw = sec_blk["windows"][0]
        assert sw["taus"] == "[0,+3]", f"T1: 次级窗 taus 错 {sw['taus']}"
        assert "不参与判决" in sec_blk["note"], "T1: 次级窗角色注记缺失"

        # T2 真实计算:CAAR 落手算期望带(注入 3/-2/1.5% − 等权市场稀释)且两两可区分
        mw, rw = car["main_window"], car["robust_window"]
        cm, cs, cr = mw["caar"], sw["caar"], rw["caar"]
        assert abs(cm - 0.0288) < 0.006, f"T2: 主窗 CAAR 偏离手算期望 {cm}"
        assert abs(cs - 0.0075) < 0.006, f"T2: 次级窗 CAAR 偏离手算期望 {cs}"
        assert abs(cr - 0.0213) < 0.006, f"T2: 稳健窗 CAAR 偏离手算期望 {cr}"
        assert cm - cs > 0.012 and cr - cs > 0.008 and cm - cr > 0.004, \
            f"T2: 三窗不可区分 main={cm} sec={cs} rob={cr}(fixture 判别力不足=测试无效)"
        # 与 per_tau AAR 前缀和逐位一致(同一 aar 真源,非另造字段)
        aar = [r["aar"] for r in res["per_tau"]["by_tau"]]
        for caar, L in ((cm, 2), (cs, 4), (cr, 6)):
            assert abs(caar - sum(aar[:L])) < 1e-12, f"T2: CAAR≠ΣAAR[:{L}](非同源计算)"
        # 三窗 ADJ-BMP 皆真实产出且两两不同
        zs = [mw["adj_bmp_car"], sw["adj_bmp_car"], rw["adj_bmp_car"]]
        assert all(z is not None for z in zs), f"T2: ADJ-BMP 缺 {zs}"
        assert len({round(z, 6) for z in zs}) == 3, f"T2: 三窗 ADJ-BMP 不可区分 {zs}"

        # T3 判决隔离:剔除次级窗后 _verdict 复算不变(5 日主窗唯一进判决)
        car2 = copy.deepcopy(car)
        car2.pop("secondary_windows")
        v2 = runner._verdict(gates.sample_verdict(res["n_valid"]), car2,
                             res["robustness"], res["audit"]["family_alpha"])
        assert v2 == (res["verdict"], res["verdict_note"]), \
            f"T3: 判决受次级窗影响 {v2} != {(res['verdict'], res['verdict_note'])}"

        # T4 分层贯通:各层 stats 同样产出次级窗
        for lay, blk in res["type_strata"]["layers"].items():
            lsw = blk["car"].get("secondary_windows")
            assert lsw and lsw["windows"][0]["taus"] == "[0,+3]", f"T4: 层 {lay} 次级窗缺失"

        # T5 零回归半:两窗 pap 同 fixture → result 全文无 secondary_windows 键
        res2 = runner.run_study(SyntheticReader(pp, ep), _pap("T+1起,后2/6日"),
                                benchmark_mode="market")
        assert "secondary_windows" not in json.dumps(res2, ensure_ascii=False, default=str), \
            "T5: 两窗 pap 泄出 secondary_windows 键(既有形态被扰动)"

        print("verify_three_windows: T1 结构 / T2 真实计算+可区分 / T3 判决隔离 / "
              "T4 分层贯通 / T5 两窗零键 —— 5/5 PASS")
        print(f"  三窗 CAAR: main[0,+1]={cm:.5f} secondary[0,+3]={cs:.5f} robust[0,+5]={cr:.5f}")
        print(f"  三窗 ADJ-BMP: {zs[0]:.3f} / {zs[1]:.3f} / {zs[2]:.3f}")


if __name__ == "__main__":
    main()
