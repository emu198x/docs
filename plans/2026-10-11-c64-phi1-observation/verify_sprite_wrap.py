"""Qualify pointer and MC continuity across the absolute-clock line boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

from capture import MODELS
from sprite_pointer import guest
from verify_sprite_pointer import stem, verify_sequence

# Native calibration: target sprite, neighbouring requested NOP delays, actual
# completed-store coordinates before and after DMA postpones the CPU write.
BOUNDARIES = {
    63: (2, (20, 21), ((90, 59), (91, 3))),
    65: (3, (23, 24), ((90, 61), (91, 3))),
    64: (2, (20, 21), ((90, 59), (91, 2))),
}


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, b, BOUNDARIES[c][0], d, 0, reverse)
        for m, _, c in MODELS
        for b in range(4)
        for d in BOUNDARIES[c][1]
        for reverse in (False, True)
    }
    actual = [
        (r["model"], r["bank"], r["sprite"], r["delay"], r["phase"], r["reverse"])
        for r in cases
    ]
    assert len(actual) == 80 and set(actual) == expected, "wrap case coverage"


def verify_case(case: dict, rows: list[list[str]], log: str) -> dict:
    result = verify_sequence(case, rows, log)
    sprite, delays, coordinates = BOUNDARIES[case["cycles"]]
    assert case["sprite"] == sprite and case["phase"] == 0
    assert case["delay"] in delays
    side = delays.index(case["delay"])
    assert (result["write_line"], result["write_cycle"]) == coordinates[side], (
        "CPU wrap boundary"
    )
    assert result["first_new_offset"] == (30 if side == 0 else 33), (
        "pointer transition row"
    )
    assert result["wrap_rows"] == 21, "positive wrap coverage"
    return {**result, "boundary": "before" if side == 0 else "after"}


def verify_archive(path: Path) -> dict:
    totals = Counter()
    sides = Counter()
    pairs = {}
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture.json"))
        verify_coverage(manifest["rows"])
        for case in manifest["rows"]:
            name = stem(case)
            program = archive.read(name + ".prg")
            assert program == guest(
                case["bank"],
                case["sprite"],
                case["delay"],
                case["phase"],
                case["reverse"],
            )
            assert hashlib.sha256(program).hexdigest() == case["program_sha256"]
            assert archive.read(name + ".bin") == bytes([0xA5])
            assert archive.read(name + "-ram.bin") == bytes(case["ram"])
            raw = archive.read(name + ".csv")
            assert hashlib.sha256(raw).hexdigest() == case["trace_sha256"]
            result = verify_case(
                case,
                list(csv.reader(io.StringIO(raw.decode()))),
                archive.read(name + ".log").decode(),
            )
            assert all(result[k] == v for k, v in case["trace"].items()), (
                "trace summary"
            )
            totals.update(
                {k: result[k] for k in ["records", "sprite_bytes", "wrap_rows"]}
            )
            sides[result["boundary"]] += 1
            pairs.setdefault((case["model"], case["bank"], case["reverse"]), {})[
                result["boundary"]
            ] = result["write_clock"]
    assert sides == {"before": 40, "after": 40} and len(pairs) == 40
    assert all(p["after"] - p["before"] == 7 for p in pairs.values()), "CPU stall span"
    return {"cases": 80, "boundaries": dict(sides), "stalled_pairs": 40, **dict(totals)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(verify_archive(parser.parse_args().archive), indent=2))
