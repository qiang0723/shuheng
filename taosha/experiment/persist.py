"""淘沙 · 检验结果 append-only 落库(切片2 item 11;spec §5 末端)。

引擎跑完 → result 落库对接台账 Experiment 对象:走 registered→frozen→running→done
**既有状态机路径**,复用切片1 已终签台账触发器(result 一次性写入 / append-only 焊死),
**不另建通路**。N_eff 与剔除率随 result 同落(门②成色报告数据前提)。

切片2 合成验收(S2-DEC2):专设一条 `[SMOKE]` 合成冒烟登记行(source_type=llm、
verdict_power=prescreen、contamination_note 明写非真实结论),不写六条创始行(护其一次性
result 槽留给切片3真实数据)。

红线:唯一写入=台账;无写回上游;result 一次性(改判=INSERT 新行,不覆写)。
"""
from __future__ import annotations

from . import ledger


def persist_study(result: dict, *, family: str, title: str, source_type: str,
                  verdict_power: str, contamination_note: str, pap: dict,
                  data_class: str, crowding_prior: str, conn=None) -> int:
    """把一次检验结果落库:register→freeze→running→done(单连接单事务,末尾一次提交)。

    result 内已含 verdict / n_eff / rejections(剔除率)/ per_tau / car / robustness / audit。
    返回 exp_id。触发器为权威 enforcement(此处仅编排既有路径)。
    """
    own = conn is None
    conn = conn or ledger.connect()
    try:
        exp_id = ledger.register(
            family=family, title=title, source_type=source_type,
            verdict_power=verdict_power, pap=pap, contamination_note=contamination_note,
            data_class=data_class, crowding_prior=crowding_prior, conn=conn)
        ledger.freeze(exp_id, conn=conn)
        ledger.start_running(exp_id, conn=conn)
        ledger.finish(exp_id, result, conn=conn)
        if own:
            conn.commit()
        return exp_id
    except Exception:
        if own:
            conn.rollback()
        raise
    finally:
        if own:
            conn.close()
