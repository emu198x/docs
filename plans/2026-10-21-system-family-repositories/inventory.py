"""Record declared workspace edges without resolving or building dependencies."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import tomllib
from pathlib import Path


def inventory(root: Path) -> str:
    workspace = tomllib.loads((root / "Cargo.toml").read_text())["workspace"]
    members = workspace["members"]
    if not members or len(members) != len(set(members)):
        raise ValueError("workspace members must be nonempty and unique")
    packages = {}
    pending = list(members)
    seen = set()
    while pending:
        member = pending.pop(0)
        manifest = root / member / "Cargo.toml"
        if manifest.resolve() in seen:
            continue
        seen.add(manifest.resolve())
        data = tomllib.loads(manifest.read_text())
        name = data["package"]["name"]
        if name in packages:
            raise ValueError(f"duplicate package: {name}")
        packages[name] = (manifest, data)
        tables = [data] + list(data.get("target", {}).values())
        for table in tables:
            for kind in ("dependencies", "dev-dependencies", "build-dependencies"):
                for dep in table.get(kind, {}).values():
                    if isinstance(dep, dict) and "path" in dep:
                        directory = (manifest.parent / dep["path"]).resolve()
                        pending.append(str(directory.relative_to(root)))
    paths = {
        manifest.parent.resolve(): name for name, (manifest, _) in packages.items()
    }
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "package",
            "manifest",
            "version",
            "publish_enabled",
            "dependency_kind",
            "target",
            "dependency",
            "local_manifest",
            "optional",
            "requirement",
        ]
    )
    for name, (manifest, data) in sorted(packages.items()):
        package = data["package"]
        version = package["version"]
        if isinstance(version, dict):
            version = workspace["package"]["version"]
        base = [
            name,
            str(manifest.relative_to(root)),
            version,
            str(package.get("publish") is not False).lower(),
        ]
        writer.writerow(base + ["package", "-", "-", "-", "-", "-"])
        sections = [
            (kind, "", data.get(kind, {}))
            for kind in ("dependencies", "dev-dependencies", "build-dependencies")
        ]
        sections += [
            (kind, target, settings.get(kind, {}))
            for target, settings in data.get("target", {}).items()
            for kind in ("dependencies", "dev-dependencies", "build-dependencies")
        ]
        for kind, target, dependencies in sorted(sections):
            for alias, dep in sorted(dependencies.items()):
                if not isinstance(dep, dict) or "path" not in dep:
                    continue
                directory = (manifest.parent / dep["path"]).resolve()
                target_manifest = directory / "Cargo.toml"
                if not target_manifest.is_file():
                    raise ValueError(f"missing local manifest: {target_manifest}")
                target_name = tomllib.loads(target_manifest.read_text())["package"][
                    "name"
                ]
                if target_name != dep.get("package", alias):
                    raise ValueError(f"dependency name mismatch: {name} / {alias}")
                if directory not in paths:
                    raise ValueError(
                        f"local edge leaves the recorded workspace: {name} / {alias}"
                    )
                writer.writerow(
                    base
                    + [
                        kind,
                        target or "-",
                        target_name,
                        str(target_manifest.relative_to(root)),
                        str(dep.get("optional", False)).lower(),
                        dep.get("version", "-"),
                    ]
                )
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.source.resolve()
    destination = Path(__file__).with_name("dependencies.tsv")
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    expected = Path(__file__).with_name("source-commit.txt")
    result = inventory(root)
    if args.check:
        if (
            destination.read_text() != result
            or expected.read_text().strip() != revision
        ):
            raise SystemExit(
                "inventory or source revision differs; review before refreshing"
            )
        print("Inventory and source revision match")
    else:
        destination.write_text(result)
        expected.write_text(revision + "\n")
        print(
            f"Recorded {len(result.splitlines()) - 1} package/edge rows at {revision}"
        )


if __name__ == "__main__":
    main()
