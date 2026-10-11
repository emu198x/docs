"""Run the CPU fetch probe and restore its host source exactly."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def analyse(log: str, reference: dict, returncode: int) -> dict:
    expected = {
        (r["model"], r["endpoint"]): r
        for r in reference["rows"]
        if r["model"] != "oldntsc"
    }
    assert len(expected) == 8
    rows = []
    seen = set()
    for model, endpoint, status, reported, values in re.findall(
        r"ROW\|(\w+)\|(io1|colour)\|(\d+)\|(\d+)\|(\[[^\n]+\])", log
    ):
        key = model, endpoint
        assert key in expected and key not in seen
        seen.add(key)
        oracle = expected[key]
        actual = ast.literal_eval(values)
        assert len(actual) == oracle["cycles"] and all(
            type(v) is int and 0 <= v <= 255 for v in actual
        )
        differences = [
            (i, a, e)
            for i, (a, e) in enumerate(zip(actual, oracle["actual"], strict=True))
            if a != e
        ]
        assert len(differences) == int(reported)
        rows.append(
            {
                "model": model,
                "endpoint": endpoint,
                "completion": int(status),
                "samples": len(actual),
                "mismatches": len(differences),
                "actual": actual,
                "differences": differences,
            }
        )
    assert seen == set(expected), "missing or repeated model/endpoint rows"
    wrong = sum(r["mismatches"] for r in rows)
    assert returncode == (101 if wrong else 0), "unexpected Cargo exit"
    return {
        "rows": rows,
        "mismatches": wrong,
        "samples": sum(r["samples"] for r in rows),
        "cargo_exit": returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    native = args.native.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    reference = json.loads((native / "comparison.json").read_text())
    for row in reference["rows"]:
        for suffix, key in [(".prg", "program_sha256"), (".bin", "dump_sha256")]:
            data = (native / f"{row['model']}-{row['endpoint']}{suffix}").read_bytes()
            assert hashlib.sha256(data).hexdigest() == row[key]
    relative = "crates/machine-commodore-c64/src/machine.rs"
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", relative], cwd=repo, check=True
    )
    source = repo / relative
    original = source.read_bytes()
    assert original.endswith(b"}\n")
    fragment = Path(__file__).with_name("probe.rs").read_bytes()
    changed = original[:-2] + fragment + b"}\n"
    command = [
        "cargo",
        "test",
        "-p",
        "machine-commodore-c64",
        "phi1_guest_reads_match_native_endpoints",
        "--lib",
        "--",
        "--nocapture",
    ]
    source.write_bytes(changed)
    try:
        result = subprocess.run(
            command,
            cwd=repo,
            env=dict(os.environ, C64_PHI1_INPUT=str(native)),
            capture_output=True,
            timeout=180,
            check=False,
        )
    finally:
        if source.read_bytes() != changed:
            raise RuntimeError("Concurrent source edit: refusing to overwrite")
        source.write_bytes(original)
    assert source.read_bytes() == original
    log = (result.stdout + result.stderr).decode(errors="replace")
    (output / "run.log").write_text(log)
    summary = analyse(log, reference, result.returncode)
    summary.update(
        source_sha256=hashlib.sha256(original).hexdigest(),
        source_restored=True,
        command=command,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("Mismatches:", summary["mismatches"], "/", summary["samples"])
    return int(summary["mismatches"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
