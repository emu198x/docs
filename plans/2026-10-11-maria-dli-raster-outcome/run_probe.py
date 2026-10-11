"""Capture the CPU-to-framebuffer DLI gate without retaining source edits."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import subprocess
from pathlib import Path

ROW = re.compile(
    r"region=(Ntsc|Pal) height=(1|2|3|16) flags=([0-3]) requests=(\d+) "
    r"handlers=(\d+) writes=(\d+) pixels=(\d+) wrong_pixels=(\d+) "
    r"wrong_bus_pixels=(\d+) wrong_previous=(\d+) min_age=(\d+)"
)
FIELDS = (
    "region",
    "height",
    "flags",
    "requests",
    "handlers",
    "writes",
    "pixels",
    "wrong_pixels",
    "wrong_bus_pixels",
    "wrong_previous",
    "min_age",
)


def summarize(log: str, status: int) -> dict[str, object]:
    rows = []
    keys = set()
    for line in log.splitlines():
        if not line.startswith("region="):
            continue
        match = ROW.fullmatch(line)
        if match is None:
            raise ValueError("malformed observation")
        row = dict(zip(FIELDS, match.groups(), strict=True))
        values = {key: int(row[key]) for key in FIELDS[1:]}
        key = (row["region"], values["height"], values["flags"])
        if key in keys:
            raise ValueError("duplicate case")
        keys.add(key)
        if values["flags"] and values["min_age"] < 400:
            raise ValueError("insufficient pixel deadline margin")
        if values["pixels"] != 192:
            raise ValueError("incomplete pixels")
        if values["flags"] in (1, 2) and values["requests"] <= 100 // values["height"]:
            raise ValueError("missing active requests")
        if values["flags"] == 3 and values["requests"] != 1:
            raise ValueError("missing single request")
        if values["flags"] == 0 and any(
            values[name]
            for name in ("requests", "handlers", "wrong_pixels", "wrong_bus_pixels")
        ):
            raise ValueError("inactive control failed")
        matches = (
            values["handlers"] == values["requests"]
            and values["writes"] == values["requests"] + 1
            and values["wrong_pixels"] == values["wrong_bus_pixels"] == 0
        )
        rows.append({"region": row["region"], **values, "matches": matches})
    expected = set(itertools.product(("Ntsc", "Pal"), (1, 2, 3, 16), range(4)))
    if keys != expected:
        raise ValueError("incomplete case inventory")
    failures = sum(not row["matches"] for row in rows)
    if log.splitlines().count(f"cases=32 failures={failures}") != 1:
        raise ValueError("inconsistent completion summary")
    if status != (101 if failures else 0):
        raise ValueError("cargo status differs from observations")
    result = "FAILED. 0 passed; 1 failed" if failures else "ok. 1 passed; 0 failed"
    if f"test result: {result}" not in log:
        raise ValueError("missing executed test result")
    return {
        "cases": len(rows),
        "failures": failures,
        "cargo_exit": status,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    target = source / "crates/machine-atari-7800/src/lib.rs"
    before = target.read_bytes()
    probe = Path(__file__).with_name("probe.rs").read_bytes()
    if b"mod dli_raster_probe" in before:
        raise ValueError("probe already installed")
    injected = before + b"\n" + probe
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source, text=True
        ).strip(),
        "machine_sha256": hashlib.sha256(before).hexdigest(),
        "probe_sha256": hashlib.sha256(probe).hexdigest(),
    }
    target.write_bytes(injected)
    try:
        for label, redirect in (("baseline", False), ("redirected-write", True)):
            environment = os.environ.copy()
            environment.pop("MARIA_PROBE_REDIRECT_COLOUR", None)
            if redirect:
                environment["MARIA_PROBE_REDIRECT_COLOUR"] = "1"
            path = args.output / f"{label}.log"
            with path.open("wb") as output:
                result = subprocess.run(
                    [
                        "cargo",
                        "test",
                        "-p",
                        "machine-atari-7800",
                        "--lib",
                        "dli_raster_probe::requested_interrupts_reach_pixels",
                        "--",
                        "--exact",
                        "--nocapture",
                    ],
                    cwd=source,
                    env=environment,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            observed = summarize(path.read_text(), result.returncode)
            if redirect and not any(
                row["handlers"] == row["requests"] and row["wrong_pixels"] > 0
                for row in observed["rows"]
            ):
                raise ValueError("negative did not defeat framebuffer acceptance")
            summary[label] = observed
            print(
                label,
                {key: value for key, value in observed.items() if key != "rows"},
                flush=True,
            )
    finally:
        if target.read_bytes() != injected:
            backup = args.output / "machine-source-before.rs"
            backup.write_bytes(before)
            raise RuntimeError(f"concurrent edit; original preserved at {backup}")
        target.write_bytes(before)
        if target.read_bytes() != before:
            raise RuntimeError("source restoration failed")
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if summary["baseline"]["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
