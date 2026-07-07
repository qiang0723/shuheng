"""口径冻结 · 运行时不可覆写实测(切片2 item 10 验收贴)。

item 10:全部口径参数(门槛/窗口/剔除规则)从冻结配置读取、运行时不可覆写;
参数变更走配置审计留痕。本脚本**实测**:对 frozen_config / frozen_ashare 的每个冻结键
尝试运行时覆写,断言一律抛 TypeError(MappingProxyType 只读);打印两模块 audit_digest。

用法:python -m taosha.harness.verify_frozen_immutable
"""
from __future__ import annotations

from types import MappingProxyType

from taosha.compute import frozen_ashare as fa
from taosha.compute import frozen_config as fc


def _try_override(proxy, key, val) -> bool:
    """尝试覆写一个键,返回 True 当且仅当被 TypeError 挡住(=不可覆写)。"""
    try:
        proxy[key] = val
        return False
    except TypeError:
        return True


def _walk_assert(name: str, frozen) -> list[str]:
    """遍历冻结映射的每个键(含嵌套 MappingProxyType),逐个实测不可覆写。"""
    lines = []
    for k, v in frozen.items():
        ok = _try_override(frozen, k, "__HACK__")
        lines.append(f"  {name}[{k!r}] 覆写被拒={ok}")
        assert ok, f"{name}[{k!r}] 可被运行时覆写(item 10 违反!)"
        if isinstance(v, MappingProxyType):
            for k2 in v:
                ok2 = _try_override(v, k2, "__HACK__")
                assert ok2, f"{name}[{k!r}][{k2!r}] 可被覆写(item 10 违反!)"
    return lines


def main():
    print("═══ item 10 · 口径冻结运行时不可覆写实测 ═══")
    fc_lines = _walk_assert("frozen_config.FROZEN", fc.FROZEN)
    fa_lines = _walk_assert("frozen_ashare.FROZEN", fa.FROZEN)
    for l in fc_lines + fa_lines:
        print(l)
    # 覆盖门槛/窗口专项(挡"120/84"复燃已在 frozen_config import 期断言;此处再证只读)
    assert _try_override(fc.FROZEN["coverage"], "min_valid", 84), "覆盖门槛可被改!"
    assert _try_override(fc.FROZEN["estimation_window"], "length", 120), "估计窗长可被改!"
    assert _try_override(fa.FROZEN["event_windows"], "main", (0, 9)), "事件窗可被改!"
    print("  专项: 覆盖门槛/估计窗长/事件窗 均不可覆写")
    print(f"\naudit_digest:")
    print(f"  frozen_config = {fc.audit_digest()}")
    print(f"  frozen_ashare = {fa.audit_digest()}")
    print("\nitem 10 实测 PASS:全部冻结口径运行时不可覆写;变更须改源+审计摘要随之变(留痕)。")


if __name__ == "__main__":
    main()
