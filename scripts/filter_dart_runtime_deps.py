#!/usr/bin/env python3
"""Derive a runtime-only Dart dependency graph from `dart pub deps --json`.

Modern Dart JSON dependency output already contains dependency kinds and cannot be
combined with `--dev`/`--no-dev`. This script walks only the root package's
runtime/direct dependencies and their transitive dependencies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"dart runtime dependency filter failed: {message}")


def names(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"{field} must be a list of package names")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read input JSON: {exc}")

    if not isinstance(payload, dict):
        fail("input must be a JSON object")
    root_name = payload.get("root")
    packages = payload.get("packages")
    if not isinstance(root_name, str) or not root_name:
        fail("input has no root package name")
    if not isinstance(packages, list) or not packages:
        fail("input has no packages")

    package_by_name: dict[str, dict[str, Any]] = {}
    for package in packages:
        if not isinstance(package, dict):
            fail("packages must contain objects")
        name = package.get("name")
        if not isinstance(name, str) or not name:
            fail("package entry has no name")
        if name in package_by_name:
            fail(f"duplicate package entry: {name}")
        package_by_name[name] = package

    root = package_by_name.get(root_name)
    if root is None:
        fail(f"root package {root_name!r} is missing from packages")

    if "directDependencies" in root:
        runtime_roots = names(root["directDependencies"], "root.directDependencies")
    else:
        immediate = set(names(root.get("dependencies", []), "root.dependencies"))
        dev = set(names(root.get("devDependencies", []), "root.devDependencies"))
        runtime_roots = sorted(immediate - dev)

    keep = {root_name}
    pending = list(runtime_roots)
    while pending:
        name = pending.pop()
        if name in keep:
            continue
        package = package_by_name.get(name)
        if package is None:
            fail(f"referenced package {name!r} is missing from packages")
        keep.add(name)
        dependency_field = (
            package.get("directDependencies")
            if "directDependencies" in package
            else package.get("dependencies", [])
        )
        pending.extend(names(dependency_field, f"{name}.dependencies"))

    filtered_packages: list[dict[str, Any]] = []
    for package in packages:
        name = package["name"]
        if name not in keep:
            continue
        copy = dict(package)
        if name == root_name:
            copy["dependencies"] = list(runtime_roots)
            if "directDependencies" in copy:
                copy["directDependencies"] = list(runtime_roots)
            if "devDependencies" in copy:
                copy["devDependencies"] = []
        filtered_packages.append(copy)

    output = dict(payload)
    output["packages"] = filtered_packages
    args.output_json.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        f"Dart runtime dependency graph: {len(filtered_packages)} of "
        f"{len(packages)} packages retained"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
