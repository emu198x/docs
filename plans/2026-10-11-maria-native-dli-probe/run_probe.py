"""Measure the native DLI path while restoring the supplied source verbatim."""

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
    r"region=(Ntsc|Pal) height=(1|2|3|16) flags=([0-3]) guest=([0-2]) "
    r"enabled=(false|true) descriptors=(\d+) requests=(\d+) edges=(\d+) "
    r"vector_low=(\d+) vector_high=(\d+) handlers=(\d+) "
    r"first_request=(None|Some\(\(\d+, \d+\)\)) "
    r"first_edge=(None|Some\(\(\d+, \d+\)\))"
)
FIELDS = (
    "region",
    "height",
    "flags",
    "guest",
    "enabled",
    "descriptors",
    "requests",
    "edges",
    "vector_low",
    "vector_high",
    "handlers",
    "first_request",
    "first_edge",
)


def summarize(log: str, exit_code: int) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    keys: set[tuple[object, ...]] = set()
    for line in log.splitlines():
        if not line.startswith("region="):
            continue
        match = ROW.fullmatch(line)
        if match is None:
            raise ValueError("malformed observation")
        row = dict(zip(FIELDS, match.groups(), strict=True))
        parsed: dict[str, object] = {
            key: int(value) if key in FIELDS[1:4] + FIELDS[5:11] else value
            for key, value in row.items()
        }
        parsed["enabled"] = row["enabled"] == "true"
        key = tuple(parsed[name] for name in FIELDS[:5])
        if key in keys:
            raise ValueError("duplicate case")
        keys.add(key)
        descriptors = int(row["descriptors"])
        flags = int(row["flags"])
        expected = (0, descriptors, (descriptors + 1) // 2, int(descriptors > 1))[flags]
        if int(row["requests"]) != expected:
            raise ValueError("flag inventory differs from actual descriptors")
        if parsed["enabled"]:
            if descriptors <= 200 // int(row["height"]):
                raise ValueError("missing active DMA")
        elif descriptors:
            raise ValueError("DMA ran while disabled")
        if not expected and any(int(row[name]) for name in FIELDS[7:11]):
            raise ValueError("inactive control produced interrupts")
        delivered = all(int(row[name]) == expected for name in FIELDS[7:10])
        parsed["matches"] = delivered and int(row["handlers"]) == expected
        parsed["handler_only_mismatch"] = delivered and int(row["handlers"]) != expected
        rows.append(parsed)
    expected_keys = set(
        itertools.product(
            ("Ntsc", "Pal"), (1, 2, 3, 16), range(4), range(3), (False, True)
        )
    )
    if keys != expected_keys:
        raise ValueError("incomplete case inventory")
    mismatches = sum(not row["matches"] for row in rows)
    handler_only = sum(bool(row["handler_only_mismatch"]) for row in rows)
    footer = f"cases=192 mismatches={mismatches} handler_only_mismatches={handler_only}"
    if log.splitlines().count(footer) != 1:
        raise ValueError("missing or inconsistent completion summary")
    if exit_code != (101 if mismatches else 0):
        raise ValueError("cargo status differs from observed result")
    result = "FAILED. 0 passed; 1 failed" if mismatches else "ok. 1 passed; 0 failed"
    if f"test result: {result}" not in log:
        raise ValueError("missing executed test result")
    return {
        "cases": len(rows),
        "mismatches": mismatches,
        "handler_only_mismatches": handler_only,
        "cargo_exit": exit_code,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="emu198x source checkout")
    parser.add_argument(
        "output", type=Path, help="new or existing local output directory"
    )
    args = parser.parse_args()
    source = args.source.resolve()
    target = source / "crates/machine-atari-7800/src/lib.rs"
    before = target.read_bytes()
    if b"mod native_dli_probe" in before:
        raise ValueError("probe is already installed")
    probe = Path(__file__).with_name("probe.rs").read_bytes()
    injected = before + b"\n" + probe
    args.output.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source, text=True
        ).strip(),
        "machine_source_sha256": hashlib.sha256(before).hexdigest(),
        "probe_sha256": hashlib.sha256(probe).hexdigest(),
    }
    target.write_bytes(injected)
    try:
        for label, suppress in (("baseline", False), ("suppressed-handler", True)):
            environment = os.environ.copy()
            environment.pop("MARIA_PROBE_SUPPRESS_HANDLER", None)
            if suppress:
                environment["MARIA_PROBE_SUPPRESS_HANDLER"] = "1"
            path = args.output / f"{label}.log"
            with path.open("wb") as output:
                completed = subprocess.run(
                    [
                        "cargo",
                        "test",
                        "-p",
                        "machine-atari-7800",
                        "--lib",
                        "native_dli_probe::every_native_request_reaches_an_executed_handler",
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
            observed = summarize(path.read_text(), completed.returncode)
            if suppress and not observed["handler_only_mismatches"]:
                raise ValueError("suppressed handler did not defeat the outcome check")
            summary[label] = observed
            print(
                label, {key: value for key, value in observed.items() if key != "rows"}
            )
    finally:
        if target.read_bytes() != injected:
            # Preserve concurrent edits rather than overwriting them.
            backup = args.output / "machine-source-before.rs"
            backup.write_bytes(before)
            raise RuntimeError(
                f"source changed concurrently; original preserved in {backup}"
            )
        target.write_bytes(before)
        if target.read_bytes() != before:
            raise RuntimeError("source restoration failed")
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    # A captured failure is useful evidence, never a passing acceptance test.
    baseline = summary["baseline"]
    assert isinstance(baseline, dict)
    if baseline["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
