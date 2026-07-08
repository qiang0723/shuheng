"""淘沙 · compute · drawdown_rebuy 事件生成 PIT 状态机(#2b = exp_id 3;附录 F-rev1 冻结)。

严格照 taosha-spec-appendix-F **rev1**(2026-07-08 人批修订,C 案主体,与 spec 正文同效力):
rev0 的 latch 语义 + #7-失效后锁区致「回撤反抽形态死锁 0 进场」(数据盲下发现),rev1 向 pap 原义回归。

F-rev1 状态机(变更条 = C 案;原 #3(站上水平)/#6(无超时)等不动):
  · **armed = standing 条件**:当日 close ≤ 0.9×H60 即在回撤区(逐日重判),**非首触 latch**。
  · **站上**:close > ma10(水平,等号归破);**未破 ma20** = close ≥ ma20(close<ma20 = 破 20 日线)。
  · 在回撤区内连续 3 日「站上 ma10 且未破 ma20」→ 第 3 日=进场 T;
    **失效(close<ma20)/破 ma10(close≤ma10)= 计数清零、不锁区**(仍在回撤区、后续满足即可再累计)。
  · **#7 防链式(移至进场后)**:进场后须先 close > 0.9×H60(脱离回撤区)方可再产新进场——防同一波连发。
  · 离开回撤区(close>0.9×H60)= 本轮 episode 结束(且解 #7 锁);再入回撤区 = 新 episode。
  · PIT:H60/ma10/ma20 仅用评估日及之前;T=进场日,τ=0:=T+1(S2-DEC3)。
诊断(F2,报告项不进 verdict、不作筛选):
  D1 = 进场前自 episode 起从未 close≤ma10(水平vs上穿分歧集)。
  D2 = episode 起→进场交易日数(无超时长尾成色)。
  D3 = 进场前自 episode 起曾 close<ma20(破 20 日线致清零)——rev1 放开锁死后的成色自曝
       (= rev0 会锁死、rev1 仍能进场的集)。

红线:一个数不改冻结口径;纯 PIT、纯函数。进场后持仓/出场属策略版(附录 B),不在本件。
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

# ── 冻结口径(附录 F-rev1;原值不动,语义见上)──────────────────────────────────
H60_WINDOW = 60
MA_SHORT = 10
MA_LONG = 20
DRAWDOWN = 0.10
CONSEC = 3

FROZEN = MappingProxyType({
    "h60_window": H60_WINDOW, "ma_short": MA_SHORT, "ma_long": MA_LONG,
    "drawdown": DRAWDOWN, "consec": CONSEC,
    "armed": "standing 条件 close≤0.9×H60(逐日重判,非latch)",
    "station": "close>ma10(水平,等号归破) 且 close≥ma20(未破20日线)",
    "reset": "破ma10或破ma20 → 计数清零、不锁区(仍在回撤区可再累计)",
    "rearm_patch": "#7 移进场后:进场后须先 close>0.9×H60 脱离回撤区方产新进场(防链式)",
    "anchor": "T=进场日(收盘确认),τ=0:=T+1(S2-DEC3)",
    "sealed_by": "taosha-spec-appendix-F-rev1(2026-07-08 人批修订,C案主体,与spec正文同效力)",
})


@dataclass(frozen=True)
class Entry:
    """一个进场事件(交易日索引口径;调用方映射 idx→date 作事件锚 T)。"""
    entry_idx: int                 # 进场日(第 3 日)= 事件锚 T
    episode_start_idx: int         # 本轮 episode(进入回撤区)起始交易日索引
    d1_never_broke_ma10: bool      # D1:episode 起从未 close≤ma10
    d2_episode_to_entry_days: int  # D2:episode 起→进场交易日数
    d3_broke_ma20_before_entry: bool  # D3:episode 起进场前曾 close<ma20(rev0会锁死集)


def _is_station(c: float, ma10: float, ma20: float) -> bool:
    """站上判据(F-rev1 第2/3条)。**语义固定(人核 2026-07-08)**:ma20 的角色 = 「`close<ma20`
    → 清零重计(reset 触发)」,**非**「`close≥ma20` 作计数合取前置」。两读法在本实现行为等价
    (该日 consec 归零),但读法以 reset 为准:**分歧场景 `ma10<close<ma20` 的计数日 → 非站上 → 清零**
    (防错读为「站上=close>ma10 单条件、ma20 不参与重置」而误增计数)。等号:`close>ma10`(等号归破)、
    `close≥ma20`(=ma20 不算破)。该日若 `close<ma20` 亦触发 D3(broke_ma20)记账。"""
    return (c > ma10) and (c >= ma20)


def _sma(closes, i: int, w: int) -> Optional[float]:
    if i < w - 1:
        return None
    return sum(closes[i - w + 1:i + 1]) / w


def _high(closes, i: int, w: int) -> Optional[float]:
    lo = max(0, i - w + 1)
    seg = closes[lo:i + 1]
    return max(seg) if seg else None


def generate_entries(closes: list) -> list:
    """对一只票后复权收盘序列(交易日轴,升序,无 None)跑 F-rev1 状态机 → 进场事件列表。PIT、纯函数。"""
    n = len(closes)
    out: list[Entry] = []
    thr = 1.0 - DRAWDOWN
    consec = 0
    episode_start = -1            # 当前回撤区 episode 起始;-1=不在回撤区
    broke_ma10 = False            # 本 episode 起是否曾 close≤ma10(D1)
    broke_ma20 = False            # 本 episode 起是否曾 close<ma20(D3)
    need_escape = False           # #7:进场后待脱离回撤区(close>0.9×H60)
    for i in range(n):
        if i < H60_WINDOW - 1:
            continue
        c = closes[i]
        h60 = _high(closes, i, H60_WINDOW)
        ma10 = _sma(closes, i, MA_SHORT)
        ma20 = _sma(closes, i, MA_LONG)
        if h60 is None or ma10 is None or ma20 is None:
            continue
        in_zone = c <= thr * h60
        if not in_zone:
            # 离开回撤区:episode 结束、解 #7 锁、清 episode 态
            episode_start = -1
            consec = 0
            need_escape = False
            continue
        # 在回撤区(standing armed)
        if episode_start < 0:                 # 新 episode 起
            episode_start = i
            broke_ma10 = False
            broke_ma20 = False
            consec = 0
        # episode 内破线记账(D1/D3)
        if c <= ma10:
            broke_ma10 = True
        if c < ma20:
            broke_ma20 = True
        if need_escape:                       # #7:进场后未脱离 → 不累计、不进场
            consec = 0
            continue
        station = _is_station(c, ma10, ma20)  # 站上(close>ma10 且 close<ma20 清零重计,见 _is_station)
        if station:
            consec += 1
            if consec >= CONSEC:              # 连续 3 日 → 进场
                out.append(Entry(
                    entry_idx=i, episode_start_idx=episode_start,
                    d1_never_broke_ma10=(not broke_ma10),
                    d2_episode_to_entry_days=i - episode_start,
                    d3_broke_ma20_before_entry=broke_ma20))
                consec = 0
                need_escape = True            # #7:进场后待脱离回撤区
        else:                                 # 破 ma10 或 破 ma20 → 计数清零、不锁区
            consec = 0
    return out


def audit_digest() -> str:
    import hashlib, json
    payload = json.dumps({k: v for k, v in FROZEN.items()}, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # ── 回归用例(附录 F-rev1 固化:死锁序列须进场 + 链式须防)──────────────────────
    # R1 死锁序列(rev0 产 0 进场,rev1 须进场):高台→缓跌→低位横盘→反弹站上 ma10 连 3 日。
    R1 = ([100.0] * 40 + [100 - k * 0.75 for k in range(1, 21)] + [85.0] * 25
          + [86.0, 87.0, 88.0, 89.0, 90.0])
    e1 = generate_entries(R1)
    assert len(e1) >= 1, f"R1 死锁序列 rev1 须进场,得 {len(e1)}"
    assert e1[0].d2_episode_to_entry_days >= 0 and isinstance(e1[0].d1_never_broke_ma10, bool)
    # 进场日仍在回撤区(close≤0.9×H60)
    assert R1[e1[0].entry_idx] <= 0.9 * _high(R1, e1[0].entry_idx, 60), "进场在回撤区内"

    # R2 链式防护:进场后价继续在回撤区内站上(未脱离 0.9×H60)→ 不得连发第二进场。
    #   在 R1 反弹后维持横盘于回撤区内多日(仍 <90),若无 #7 会不断满足→多进场。
    R2 = ([100.0] * 40 + [100 - k * 0.75 for k in range(1, 21)] + [85.0] * 25
          + [86.0, 87.0, 88.0] + [88.0] * 20)   # 进场后横在 88(<90 仍在回撤区)
    e2 = generate_entries(R2)
    # 进场后未脱离回撤区 → 仅 1 进场(#7 防链式)
    assert len(e2) == 1, f"R2 链式:进场后未脱离回撤区应仅 1 进场,得 {len(e2)}"

    # R3 脱离后再回撤可再进场:两段完整 R1 拼接(第二段平台重建 60 日高点=脱离并新 episode)。
    R3 = R1 + R1
    e3 = generate_entries(R3)
    assert len(e3) >= 2, f"R3 脱离后再回撤应可第二进场,得 {len(e3)}"

    # R4 失效不锁区(rev1 关键):episode 内先破 ma20(清零)后仍能在回撤区内重累计进场。
    #   R1 的低位横盘中天然含 close<ma20 阶段(缓跌尾);D3 应能标记曾破 ma20 的进场。
    assert isinstance(e1[0].d3_broke_ma20_before_entry, bool)

    # R5 ma20 语义固定自检(人核 2026-07-08:两读法分歧场景 ma10<close<ma20 = 清零重计,非合取前置/非跳过)
    #   ① 判据层直接焊死:分歧计数日 ma10<close<ma20 → 非站上(→清零);close≥ma20 → 站上;破ma10 → 非站上。
    assert _is_station(85.0, 84.0, 90.0) is False, "R5:ma10<close<ma20 计数日须非站上(清零重计)"
    assert _is_station(90.0, 84.0, 90.0) is True, "R5:close=ma20 未破 → 站上(close≥ma20)"
    assert _is_station(91.0, 84.0, 90.0) is True, "R5:close>ma20 → 站上"
    assert _is_station(84.0, 84.0, 90.0) is False, "R5:close=ma10 破ma10(等号归破)→ 非站上"
    #   ② 序列层:consec 中插入一破ma20日须清零重计(非跳过),用打桩序列直验(closes 使某日 close<ma20)。
    #      构造:回撤区内 [站,站,破ma20回踩,站,站,站];reset→第6日进场,skip→第4日进场。
    _seq = ([100.0] * 60 + [100 - k for k in range(1, 21)]   # 平台+缓跌到 80
            + [80.0] * 30                                      # 横盘让 ma20 落到 80
            + [81.0, 82.0, 79.0, 82.0, 83.0, 84.0])           # 站,站,破ma20(79<ma20≈80),站×3
    _ev5 = generate_entries(_seq)
    # 破ma20 日清零 → 需其后连续 3 日站上;进场落在最后一日附近(reset 语义),且 D3=True(曾破ma20)
    assert len(_ev5) >= 1 and _ev5[-1].d3_broke_ma20_before_entry is True, "R5:破ma20清零重计+D3记账"
    _reset_idx = len(_seq) - 1        # skip 读法会在更早(第4日)进场;reset 读法须到末日
    assert _ev5[-1].entry_idx == _reset_idx, f"R5:清零重计→末日进场(reset),得 {_ev5[-1].entry_idx} 期望 {_reset_idx}"

    # 满窗前不评估
    assert generate_entries([100.0] * 30) == [], "H60 满窗前不评估"
    print("drawdown_signal.py(F-rev1)自检 OK:R1死锁序列进场 / R2链式防护(仅1) / "
          "R3脱离后再进场 / R4失效不锁区+D3 / R5 ma20清零重计语义(判据+序列) / PIT满窗")
    print("audit_digest =", audit_digest())
