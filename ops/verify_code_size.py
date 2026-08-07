"""枢衡代码规模闸门。

职责：阻止新增超大文件/函数，并冻结存量规模债务只减不增。
口径：docs/code-charter-nine-2026-07-12.md 第3、9条。
验收：本模块 --self-test + 仓库实扫；Docker 构建强制执行仓库实扫。
"""
from __future__ import annotations

import argparse
import ast
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "ops" / "runtime" / "code_size_baseline.json"
SCAN_ROOTS = ("ops", "qbase", "taosha", "web")
SOURCE_SUFFIXES = {".py", ".sql", ".ts", ".tsx", ".js", ".jsx", ".css", ".sh"}
EXCLUDED_PARTS = {
    ".vinext",
    ".wrangler",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "node_modules",
    "vendor",
}


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _source_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for root_name in SCAN_ROOTS:
        base = root / root_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            relative = path.relative_to(root)
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            found.append(relative)
    return sorted(found)


def _walk_functions(
    path: str,
    node: ast.AST,
    prefix: tuple[str, ...],
    sizes: dict[str, int],
) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            _walk_functions(path, child, (*prefix, child.name), sizes)
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualname = ".".join((*prefix, child.name))
            sizes[f"{path}::{qualname}"] = child.end_lineno - child.lineno + 1
            _walk_functions(path, child, (*prefix, child.name), sizes)
            continue
        _walk_functions(path, child, prefix, sizes)


def _function_sizes(root: Path, files: list[Path]) -> tuple[dict[str, int], list[str]]:
    sizes: dict[str, int] = {}
    errors: list[str] = []
    for relative in files:
        if relative.suffix != ".py":
            continue
        try:
            tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"Python语法错误，无法检查规模: {relative}:{exc.lineno}: {exc.msg}")
            continue
        _walk_functions(relative.as_posix(), tree, (), sizes)
    return sizes, errors


def _load_policy(path: Path) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("code_size_baseline schema_version 必须为 1")
    limits = policy.get("limits", {})
    if limits.get("file_lines") != 300 or limits.get("function_lines") != 60:
        raise ValueError("规模上限必须固定为 file=300/function=60")
    for name in ("file_exceptions", "function_exceptions"):
        values = policy.get(name)
        if not isinstance(values, dict) or not all(
            isinstance(key, str) and isinstance(value, int) for key, value in values.items()
        ):
            raise ValueError(f"{name} 必须为 string→integer 对象")
    return policy


def _check_limits(
    actual: dict[str, int],
    exceptions: dict[str, int],
    default_limit: int,
    kind: str,
) -> list[str]:
    errors: list[str] = []
    for key, size in sorted(actual.items()):
        allowed = exceptions.get(key, default_limit)
        if size > allowed:
            errors.append(f"{kind}超限: {key} = {size}, 允许 {allowed}")
        elif key in exceptions and size < allowed:
            errors.append(f"{kind}债务已下降: {key} = {size}; 请把基线 {allowed} 同步下调")
    for key, allowed in sorted(exceptions.items()):
        if key not in actual:
            errors.append(f"{kind}基线已失效: {key}; 请删除例外 {allowed}")
        elif actual[key] <= default_limit:
            errors.append(f"{kind}已回到标准: {key}; 请删除例外 {allowed}")
    return errors


def evaluate(root: Path, policy: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    files = _source_files(root)
    file_sizes = {path.as_posix(): _line_count(root / path) for path in files}
    function_sizes, errors = _function_sizes(root, files)
    limits = policy["limits"]
    errors.extend(
        _check_limits(
            file_sizes,
            policy["file_exceptions"],
            limits["file_lines"],
            "文件",
        )
    )
    errors.extend(
        _check_limits(
            function_sizes,
            policy["function_exceptions"],
            limits["function_lines"],
            "函数",
        )
    )
    summary = {
        "files": len(file_sizes),
        "lines": sum(file_sizes.values()),
        "functions": len(function_sizes),
        "file_debts": len(policy["file_exceptions"]),
        "function_debts": len(policy["function_exceptions"]),
    }
    return errors, summary


def _empty_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "limits": {"file_lines": 300, "function_lines": 60},
        "file_exceptions": {},
        "function_exceptions": {},
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "qbase" / "sample.py"
        source.parent.mkdir(parents=True)
        source.write_text("def small():\n    return 1\n", encoding="utf-8")
        errors, _ = evaluate(root, _empty_policy())
        assert not errors, errors

        source.write_text("def too_long():\n" + "    pass\n" * 60, encoding="utf-8")
        errors, _ = evaluate(root, _empty_policy())
        assert any("函数超限" in error for error in errors), errors

        source.write_text("# line\n" * 301, encoding="utf-8")
        errors, _ = evaluate(root, _empty_policy())
        assert any("文件超限" in error for error in errors), errors

        policy = _empty_policy()
        policy["file_exceptions"] = {"qbase/sample.py": 301}
        errors, _ = evaluate(root, policy)
        assert not errors, errors

        source.write_text("# line\n" * 302, encoding="utf-8")
        errors, _ = evaluate(root, policy)
        assert any("文件超限" in error for error in errors), errors
    print("verify_code_size self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description="枢衡代码规模闸门")
    parser.add_argument("--self-test", action="store_true", help="运行隔离正反向自检")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    policy = _load_policy(POLICY_PATH)
    errors, summary = evaluate(ROOT, policy)
    for error in errors:
        print(f"[FAIL] {error}")
    status = "PASS" if not errors else "FAIL"
    print(
        f"verify_code_size: {status}; files={summary['files']}, lines={summary['lines']}, "
        f"functions={summary['functions']}, debt_files={summary['file_debts']}, "
        f"debt_functions={summary['function_debts']}"
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
