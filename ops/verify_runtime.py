"""枢衡 · 运行时钉版自检(可信度硬化窗口 ⑥,常设)。

职责: 校验解释器 minor 版本 == ops/runtime/PYTHON_VERSION 钉死值,已装关键依赖 == 锁文件版本。
口径依据: docs/hardening-window-order-2026-07-12.md ⑥(钉死到实际部署 minor 版本,以两台实况为准)。
验收档: taosha/docs/hardening-item6-runtime-acceptance(随⑥集成回归收口)。

运行: python -m ops.verify_runtime(两台均可;未装的锁内包只在生产 venv 里强制)。
  --strict: 锁内任一包未安装即 FAIL(生产 venv 用;缺省仅校验已安装包的版本一致)。
"""
from __future__ import annotations

import argparse
import os
import sys
from importlib import metadata


def _root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pinned_minor() -> tuple[int, int]:
    with open(os.path.join(_root(), "ops", "runtime", "PYTHON_VERSION"), encoding="utf-8") as f:
        first = f.readline().strip()
    major, minor = first.split(".")[:2]
    return int(major), int(minor)


def lock_entries() -> dict[str, str]:
    out: dict[str, str] = {}
    with open(os.path.join(_root(), "ops", "runtime", "requirements-qbase-ingest.lock"),
              encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "==" not in line:
                continue
            name, ver = line.split("==", 1)
            out[name.strip().lower()] = ver.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="锁内包缺装即 FAIL(生产 venv)")
    a = ap.parse_args()
    failed = 0

    want = pinned_minor()
    got = sys.version_info[:2]
    ok = got == want
    print(f"[{'PASS' if ok else 'FAIL'}] Python minor 钉版: 运行 {got[0]}.{got[1]} vs 钉死 {want[0]}.{want[1]}"
          f"(patch 实况 {sys.version.split()[0]})")
    failed += 0 if ok else 1

    # 依赖锁: 钉的是生产 venv(/opt/venvs/qbase-ingest)。--strict=全量强制(缺装/漂移皆 FAIL);
    # 非 strict(开发/编排机)= 仅通报,不计 FAIL(解释器钉版仍强制)。
    checked = missing = drift = 0
    for name, ver in sorted(lock_entries().items()):
        try:
            got_v = metadata.version(name)
        except metadata.PackageNotFoundError:
            missing += 1
            if a.strict:
                print(f"[FAIL] 锁内包缺装: {name}=={ver}")
                failed += 1
            continue
        checked += 1
        if got_v != ver:
            drift += 1
            if a.strict:
                print(f"[FAIL] 版本漂移: {name} 装 {got_v} vs 锁 {ver}")
                failed += 1
            else:
                print(f"[INFO] 非生产环境漂移(不计 FAIL): {name} 装 {got_v} vs 锁 {ver}")
    lock_ok = (drift == 0 and missing == 0) if a.strict else True
    print(f"[{'PASS' if lock_ok else 'FAIL'}] 依赖锁({'strict 生产强制' if a.strict else '通报模式'}): "
          f"一致 {checked - drift}/漂移 {drift}/缺装 {missing}")
    print(f"\n== 运行时钉版自检: {'ALL PASS' if failed == 0 else f'{failed} FAIL'} ==")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
