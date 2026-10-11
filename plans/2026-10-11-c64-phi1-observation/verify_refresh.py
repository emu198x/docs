"""Verify refresh capture coverage and reject incorrect counter schedules."""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

from capture import MODELS


def verify(data: dict) -> dict:
    rows = data["rows"]
    wanted = {
        (m, b, c)
        for m, _, _ in MODELS
        for b, c in itertools.product(range(4), ["ordinary", "rollover", "frame-wrap"])
    }
    seen = set()
    mutants = {
        "predecrement": 0,
        "increment": 0,
        "reset_each_line": 0,
        "omit_frame_reset": 0,
    }
    checked = 0
    for row in rows:
        key = (row["model"], row["bank"], row["case"])
        assert key in wanted and key not in seen
        seen.add(key)
        model_cycles = next(c for m, _, c in MODELS if m == row["model"])
        assert row["cycles"] == model_cycles
        assert row["lines"] == (
            312 if model_cycles == 63 else 262 if model_cycles == 64 else 263
        )
        page = row["refresh_page"]
        assert len(page) == 256 and all(type(v) is int and 0 <= v <= 255 for v in page)
        assert row["trace_samples"] == row["cycles"]
        samples = row["refresh"]
        assert len(samples) == 5 and [s["monitor_cycle"] for s in samples] == list(
            range(11, 16)
        )
        assert [s["sample"] for s in samples] == list(range(10, 15))
        if row["case"] == "frame-wrap":
            assert [s["monitor_line"] for s in samples] == [
                row["lines"] - 2,
                row["lines"] - 1,
                0,
                1,
                2,
            ]
        for s in samples:
            line, phase = s["monitor_line"], s["monitor_cycle"] - 11
            low = (255 - 5 * line - phase) & 255
            assert s["address"] == row["bank"] * 0x4000 + 0x3F00 + low
            assert s["actual"] == s["expected"] == page[low]
            candidates = {
                "predecrement": (low - 1) & 255,
                "increment": (255 + 5 * line + phase) & 255,
                "reset_each_line": (255 - phase) & 255,
            }
            if row["case"] == "frame-wrap" and line < 3:
                candidates["omit_frame_reset"] = (low - 5 * row["lines"]) & 255
            for name, address in candidates.items():
                mutants[name] += int(page[address] != s["actual"])
            checked += 1
    assert seen == wanted and checked == 300
    assert all(count > 0 for count in mutants.values()), "negative schedule survived"
    return {
        "rows": len(rows),
        "refresh_samples": checked,
        "counter_mutation_mismatches": mutants,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    raw = args.capture.read_bytes()
    if args.capture.suffix == ".gz":
        raw = gzip.decompress(raw)
    print(json.dumps(verify(json.loads(raw)), indent=2))


if __name__ == "__main__":
    main()
