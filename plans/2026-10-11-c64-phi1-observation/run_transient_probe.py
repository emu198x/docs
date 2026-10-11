"""Run the bank-transient CPU probe with byte-exact host-source restoration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def analyse(log: str, returncode: int) -> dict:
    expected = {"pal": False, "c64c": True, "ntsc": False, "c64cntsc": True}
    rows = []
    seen = set()
    for model, size, changed, custom in re.findall(
        r"BANK_TRANSIENT\|(\w+)\|(\d+)\|(\d+)\|([01])", log
    ):
        assert model in expected and model not in seen
        seen.add(model)
        size, changed = int(size), int(changed)
        assert size > 60_000 and 0 <= changed <= size
        assert bool(int(custom)) == expected[model]
        rows.append(
            {
                "model": model,
                "pixels": size,
                "changed": changed,
                "expected_change": expected[model],
                "failed": (changed != 0) != expected[model],
            }
        )
    assert seen == set(expected), "missing/duplicate model rows"
    failed = sum(r["failed"] for r in rows)
    assert returncode == (101 if failed else 0)
    return {"rows": rows, "failed": failed, "cargo_exit": returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, native, output = (
        args.repo.resolve(),
        args.native.resolve(),
        args.output.resolve(),
    )
    output.mkdir(exist_ok=False)
    reference = json.loads((native / "comparison.json").read_text())
    for row in reference["captures"]:
        path = native / (row["stem"] + ".prg")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["program_sha256"]
    relative = "crates/machine-commodore-c64/src/machine.rs"
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", relative], cwd=repo, check=True
    )
    source = repo / relative
    original = source.read_bytes()
    assert original.endswith(b"}\n")
    changed = (
        original[:-2]
        + Path(__file__).with_name("transient_probe.rs").read_bytes()
        + b"}\n"
    )
    command = [
        "cargo",
        "test",
        "-p",
        "machine-commodore-c64",
        "custom_glue_bank_swap_fetches_transient_bank_character",
        "--lib",
        "--",
        "--nocapture",
    ]
    source.write_bytes(changed)
    try:
        result = subprocess.run(
            command,
            cwd=repo,
            env=dict(os.environ, C64_BANK_TRANSIENT_INPUT=str(native)),
            capture_output=True,
            timeout=300,
            check=False,
        )
    finally:
        if source.read_bytes() != changed:
            raise RuntimeError("Concurrent source edit: refusing to overwrite")
        source.write_bytes(original)
    assert source.read_bytes() == original
    log = (result.stdout + result.stderr).decode(errors="replace")
    (output / "run.log").write_text(log)
    summary = analyse(log, result.returncode)
    summary.update(
        source_sha256=hashlib.sha256(original).hexdigest(),
        source_restored=True,
        command=command,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return int(summary["failed"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
