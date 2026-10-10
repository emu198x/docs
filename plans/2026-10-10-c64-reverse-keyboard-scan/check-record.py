"""Require reference parity in the maintained joystick sample's probe record."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    raw = args.record.read_bytes()
    data = json.loads(gzip.decompress(raw) if args.record.suffix == ".gz" else raw)
    probes = data["keyboard_probe"]
    expected = {
        (model, key)
        for model in ("pal", "ntsc")
        for key in ("none", "1", "SPACE", "RETURN", "A")
    }
    assert len(probes) == 10
    assert {(row["model"], row["key"]) for row in probes} == expected
    for row in probes:
        assert row["emulator"] == row["reference"], row
        assert row["matches_reference"] and row["known_difference"] is None, row
    assert len(data["cases"]) == 412
    assert len(data["live"]) == 32
    pictures = sum("picture" in row for row in data["cases"] + data["live"])
    assert pictures == 48
    negatives = data["negative_control"]
    assert len(negatives) == 12
    assert sum(row["rejected"] for row in negatives) == 4
    print(
        json.dumps(
            {
                "record_sha256": hashlib.sha256(raw).hexdigest(),
                "keyboard_comparisons": len(probes),
                "keyboard_mismatches": 0,
                "state_display_checks": len(data["cases"]),
                "native_captures": pictures,
                "rejected_held_fire_mutations": 4,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
