"""枢衡 Python 依赖架构棘轮。

拒绝内部循环、qbase→taosha 反向依赖、底层→harness 倒置，以及新增的实验专属
rules/driver 横向依赖。存量横向债务按精确边基线只减不增。
"""
from __future__ import annotations

import argparse
import ast
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "ops" / "runtime" / "architecture_baseline.json"
SCAN_ROOTS = ("ops", "qbase", "taosha")
EXCLUDED_PARTS = {"__pycache__", "docs", "vendor"}


def _module_name(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _modules(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for name in SCAN_ROOTS:
        base = root / name
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            relative = path.relative_to(root)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            found[_module_name(relative)] = relative
    return found


def _absolute_from(source: str, node: ast.ImportFrom, is_package: bool) -> str:
    if not node.level:
        return node.module or ""
    package = source if is_package else source.rpartition(".")[0]
    parts = package.split(".") if package else []
    keep = max(len(parts) - node.level + 1, 0)
    prefix = parts[:keep]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix)


def _resolve(target: str, modules: set[str]) -> str | None:
    candidate = target
    while candidate:
        if candidate in modules:
            return candidate
        candidate = candidate.rpartition(".")[0]
    return None


def _imports(source: str, tree: ast.AST, modules: set[str], is_package: bool) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = _absolute_from(source, node, is_package)
            names = [f"{base}.{alias.name}" if base else alias.name for alias in node.names]
        for name in names:
            resolved = _resolve(name, modules)
            if resolved and resolved != source:
                targets.add(resolved)
    return targets


def _graph(root: Path) -> tuple[dict[str, set[str]], list[str]]:
    modules = _modules(root)
    graph = {name: set() for name in modules}
    errors: list[str] = []
    for name, relative in modules.items():
        try:
            tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"Python语法错误: {relative}:{exc.lineno}: {exc.msg}")
            continue
        graph[name] = _imports(name, tree, set(modules), relative.name == "__init__.py")
    return graph, errors


def _cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    state: dict[str, int] = {}
    stack: list[str] = []
    found: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for target in sorted(graph[node]):
            if state.get(target) == 1:
                ring = stack[stack.index(target):]
                rotations = [tuple(ring[index:] + ring[:index]) for index in range(len(ring))]
                found.add(min(rotations))
            elif not state.get(target):
                visit(target)
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if not state.get(node):
            visit(node)
    return sorted(found)


def _is_experiment_edge(source: str, target: str) -> bool:
    source_leaf = source.rpartition(".")[2]
    target_leaf = target.rpartition(".")[2]
    rules = (source.startswith("taosha.compute.") and target.startswith("taosha.compute.")
             and source_leaf.endswith("_rules") and target_leaf.endswith("_rules"))
    drivers = (source.startswith("taosha.harness.run_")
               and target.startswith("taosha.harness.run_")
               and source_leaf.endswith("_study") and target_leaf.endswith("_study"))
    return rules or drivers


def _forbidden_edge(source: str, target: str) -> bool:
    if source.startswith("qbase.") and target.startswith("taosha."):
        return True
    lower = ("taosha.compute.", "taosha.engine.", "taosha.reader.")
    return source.startswith(lower) and target.startswith("taosha.harness.")


def _load_policy(path: Path) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("architecture baseline schema_version 必须为 1")
    edges = policy.get("cross_experiment_imports")
    if not isinstance(edges, list) or not all(isinstance(edge, str) for edge in edges):
        raise ValueError("cross_experiment_imports 必须为字符串数组")
    if edges != sorted(set(edges)):
        raise ValueError("cross_experiment_imports 必须去重并排序")
    return policy


def evaluate(root: Path, policy: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    graph, errors = _graph(root)
    edges = {(source, target) for source, targets in graph.items() for target in targets}
    for cycle in _cycles(graph):
        errors.append(f"内部循环依赖: {' -> '.join((*cycle, cycle[0]))}")
    for source, target in sorted(edges):
        if _forbidden_edge(source, target):
            errors.append(f"层级倒置: {source} -> {target}")
    actual = {f"{source} -> {target}" for source, target in edges
              if _is_experiment_edge(source, target)}
    baseline = set(policy["cross_experiment_imports"])
    for edge in sorted(actual - baseline):
        errors.append(f"新增跨实验依赖: {edge}")
    for edge in sorted(baseline - actual):
        errors.append(f"跨实验债务已下降: {edge}; 请同步删除基线")
    return errors, {"modules": len(graph), "edges": len(edges),
                    "cross_experiment_debts": len(baseline)}


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "qbase").mkdir()
        (root / "taosha" / "compute").mkdir(parents=True)
        (root / "taosha" / "harness").mkdir()
        (root / "qbase" / "base.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "taosha" / "compute" / "a_rules.py").write_text(
            "from taosha.compute import b_rules\n", encoding="utf-8")
        (root / "taosha" / "compute" / "b_rules.py").write_text("VALUE = 2\n", encoding="utf-8")
        policy = {"cross_experiment_imports": [], "schema_version": 1}
        errors, _ = evaluate(root, policy)
        assert any("新增跨实验依赖" in error for error in errors), errors
        policy["cross_experiment_imports"] = [
            "taosha.compute.a_rules -> taosha.compute.b_rules"]
        errors, _ = evaluate(root, policy)
        assert not errors, errors
        (root / "taosha" / "compute" / "a_rules.py").write_text("VALUE = 3\n", encoding="utf-8")
        errors, _ = evaluate(root, policy)
        assert any("债务已下降" in error for error in errors), errors
        (root / "taosha" / "compute" / "a_rules.py").write_text(
            "from taosha.compute import b_rules\n", encoding="utf-8")
        (root / "taosha" / "compute" / "b_rules.py").write_text(
            "from taosha.compute import a_rules\n", encoding="utf-8")
        errors, _ = evaluate(root, policy)
        assert any("内部循环依赖" in error for error in errors), errors
        (root / "qbase" / "base.py").write_text(
            "from taosha.compute import a_rules\n", encoding="utf-8")
        errors, _ = evaluate(root, policy)
        assert any("层级倒置" in error for error in errors), errors
    print("verify_architecture self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description="枢衡 Python 依赖架构棘轮")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors, summary = evaluate(ROOT, _load_policy(POLICY_PATH))
    for error in errors:
        print(f"[FAIL] {error}")
    status = "PASS" if not errors else "FAIL"
    print(f"verify_architecture: {status}; modules={summary['modules']}, "
          f"edges={summary['edges']}, "
          f"cross_experiment_debts={summary['cross_experiment_debts']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
