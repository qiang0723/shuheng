"""淘沙 · 统计纪律闸门(切片1,纯函数)。

spec §2②:样本量闸=30(<30→INSUFFICIENT,合法终态非报错);multiple-testing 门槛
按族内次数抬高 α=0.05/n;holdout(2024-07-01)动用须人批、每假设一次。
本模块只给判定;是否放行由引擎/ledger 调用,结果落 result_json 可审计。
"""
from __future__ import annotations

SAMPLE_GATE = 30
FAMILY_ALPHA_BASE = 0.05


def sample_verdict(n_events: int) -> str:
    """样本量闸:事件数 < 30 → 'INSUFFICIENT'(合法终态),否则 'OK'。"""
    if n_events < 0:
        raise ValueError("n_events 不可为负")
    return "INSUFFICIENT" if n_events < SAMPLE_GATE else "OK"


def family_alpha(family_trial: int) -> float:
    """族内多重检验门槛:α = 0.05 / n,n = 族内第几次(family_trial)。"""
    if family_trial < 1:
        raise ValueError("family_trial 从 1 起")
    return FAMILY_ALPHA_BASE / family_trial


def require_holdout_approval(approved: bool) -> None:
    """holdout 门:未获人批动用 → 拒绝(每假设仅一次,批在 ledger 外流程)。"""
    if not approved:
        raise PermissionError("holdout 动用须人批(每假设一次),未批不得触及 holdout 区")
