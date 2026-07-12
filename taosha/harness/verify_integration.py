"""淘沙 · harness · 端到端集成回归常设自检(硬化⑥后半,人开令 2026-07-12)。

一条龙:manifest 生成(幂等)→ 路由读取(ViewReader fail-closed,焊死环境=manifest 路由
+holdout 视图焊死)→ 清洗(engine/survivors 单一主干,经 runner)→ 检验 → 报告渲染;
要点=全链在焊死环境下走通且**可重复**(同链双跑逐字节)。小样本(首 K 只事件票)。
自检域(同 verify_study_snapshot/verify_runtime 先例):零台账写入(跑前后 experiment 行数
断言全等)、result 只在内存断言即弃、不产判决不落任何槽;pap 用桩(口径转录 #4 冻结通用件,
与台账状态解耦——自检不消费台账行,铁律③辖产判决之运行)。
运行:aliyun `python -m taosha.harness.verify_integration`(需 .env:TAOSHA_APP_DSN=manifest
生成/行数断言 + TAOSHA_ENGINE_* = ViewReader 引擎读径)。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys

import psycopg
from psycopg.types.json import Json

from taosha.engine import report, runner
from taosha.experiment import snapshot
from taosha.reader.view import ViewReader

SAMPLE_K = 6                       # 小样本:事件票排序后首 K 只
HOLDOUT_START = dt.date(2024, 7, 1)   # 焊死值=qbase 008/012 视图 WHERE(此处为读面实测断言)

PAP_STUB = {   # 口径桩:转录 #4 冻结通用件之检验窗(pap 由调用方传入=合成验收先例,零台账消费)
    "window": "T+1起,后20/60日",
    "_family_trial": 1,
}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     default=str).encode()).hexdigest()


def _manifest_idempotent() -> tuple[int, str, bool]:
    """S1 manifest 生成(幂等):批次向量同现值已有 manifest → 复用;否则真实生成新行。"""
    content = snapshot.collect_content()
    with psycopg.connect(os.environ["TAOSHA_APP_DSN"]) as conn, conn.cursor() as cur:
        cur.execute("SELECT snapshot_id, digest FROM study_snapshot WHERE content = %s::jsonb "
                    "ORDER BY snapshot_id LIMIT 1", (Json(content),))
        row = cur.fetchone()
    if row:
        return int(row[0]), row[1], True
    sid, digest, _ = snapshot.create(note="硬化⑥端到端集成回归自检(幂等生成)")
    return sid, digest, False


def _exp_rowcount() -> int:
    with psycopg.connect(os.environ["TAOSHA_APP_DSN"]) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM experiment")
        return int(cur.fetchone()[0])


def _chain(sid: int) -> tuple[dict, str, int]:
    """路由读取(小样本)→ survivors 主干清洗 → 检验 → 报告。返回 (result, 报告文本, 样本事件数)。"""
    probe = ViewReader(snapshot_id=sid)
    evs_all = list(probe.events())
    codes = sorted({e.ts_code for e in evs_all})[:SAMPLE_K]
    subset = [e for e in evs_all if e.ts_code in set(codes)]
    vr = ViewReader(snapshot_id=sid, sample=set(codes))
    all_dates = [c.trade_date for c in vr.calendar()]
    assert all_dates and max(all_dates) < HOLDOUT_START, "holdout 泄漏(读面实测)"
    result = runner.run_study(vr, PAP_STUB, benchmark_mode="market", events=subset,
                              strata_enabled=True, st_mode="event_day")
    result["audit"]["study_snapshot"] = vr.snapshot_info()   # driver 同款记账(§2 硬化)
    rendered = report.render(result)
    return result, rendered, len(subset)


def main() -> int:
    ok = True

    def p(tag, msg):
        print(f"[PASS] {tag} {msg}")

    n0 = _exp_rowcount()
    sid, digest, reused = _manifest_idempotent()
    assert len(digest) == 64, digest
    p("S1", f"manifest 生成(幂等)—— snapshot_id={sid} digest={digest[:8]}… "
            f"{'复用现值向量同行' if reused else '新行已生成(append-only)'}")
    for bad, tag in ((None, "缺 snapshot_id"), (10 ** 9, "manifest 不存在")):
        try:
            ViewReader(snapshot_id=bad)
            ok = False
            print(f"[FAIL] S2 fail-closed 未拒({tag})")
        except (RuntimeError, TypeError) as e:
            p("S2", f"fail-closed 拒({tag})—— {str(e)[:48]}")
    r1, t1, n_ev = _chain(sid)
    assert r1["n_events_total"] == n_ev and r1["verdict"], "链产出结构不完整"
    assert r1["audit"]["study_snapshot"]["snapshot_id"] == sid
    p("S3", f"路由读取小样本 —— 事件票 {SAMPLE_K} 只/事件 {n_ev}/日历轴 max<holdout")
    p("S4", f"清洗(survivors 主干)→检验 —— n_valid={r1['n_valid']} verdict={r1['verdict']}"
            f"(自检域仅走通性,不作研究结论)")
    assert t1 and len(t1) > 100, "报告渲染空/过短"
    p("S5", f"报告渲染 —— {len(t1)} 字")
    r2, t2, _ = _chain(sid)
    assert _sha(r1) == _sha(r2) and t1 == t2, "双跑不可重复!"
    p("S6", f"可重复 —— 同 manifest 双跑 result sha {_sha(r1)[:8]}… 逐字节同/报告文本同")
    assert _exp_rowcount() == n0, "台账行数变动!"
    p("S7", f"零台账写入 —— experiment 行数前后 {n0} 全等")
    print(f"\n== 集成回归自检: {'7/7 PASS' if ok else 'FAIL'} ==")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
