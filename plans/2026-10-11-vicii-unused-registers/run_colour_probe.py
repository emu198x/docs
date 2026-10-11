"""Run the retained CPU colour-RAM probe, restoring the source byte for byte."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--guest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    guest = args.guest.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    relative = "crates/machine-commodore-c64/src/machine.rs"
    source = repo / relative
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", relative], cwd=repo, check=True
    )
    original = source.read_bytes()
    assert original.endswith(b"}\n")
    fragment = Path(__file__).with_name("colour-bus-probe.rs").read_bytes()
    changed = original[:-2] + fragment + b"}\n"
    environment = dict(os.environ, VICII_COLOUR_BUS_PRG=str(guest))
    command = [
        "cargo",
        "test",
        "-p",
        "machine-commodore-c64",
        "colour_ram_bus_matches_native_idle_fetches",
        "--lib",
        "--",
        "--nocapture",
    ]
    source.write_bytes(changed)
    try:
        run = subprocess.run(
            command,
            cwd=repo,
            env=environment,
            capture_output=True,
            timeout=120,
            check=False,
        )
    finally:
        if source.read_bytes() != changed:
            raise RuntimeError("Source changed concurrently; refusing to overwrite it")
        source.write_bytes(original)
    assert source.read_bytes() == original
    log = (run.stdout + run.stderr).decode(errors="replace")
    (output / "run.log").write_text(log)
    matches = re.findall(
        r"(PalBreadbin|NtscBreadbin|PalC64c|NtscC64c): (\d+)/544 wrong, values (\{[^\n]+\})",
        log,
    )
    assert len(matches) == 4 and len({m[0] for m in matches}) == 4, log
    rows = []
    for model, wrong_text, values_text in matches:
        values = ast.literal_eval(values_text)
        wrong = int(wrong_text)
        assert sum(values.values()) == 544 and all(
            0 <= value <= 255 for value in values
        )
        assert wrong == sum(count for value, count in values.items() if value != 0x9A)
        rows.append({"model": model, "wrong": wrong, "values": values})
    wrong = sum(row["wrong"] for row in rows)
    assert run.returncode == (101 if wrong else 0), log
    summary = {
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "guest_sha256": hashlib.sha256(guest.read_bytes()).hexdigest(),
        "command": command,
        "rows": rows,
        "mismatches": wrong,
        "cargo_exit": run.returncode,
        "source_restored": True,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return int(wrong != 0)


if __name__ == "__main__":
    raise SystemExit(main())
