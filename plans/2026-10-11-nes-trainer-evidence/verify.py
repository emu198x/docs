"""Verify the complete trainer probe matrix, bytes and original ROM hashes."""

import hashlib
import itertools
import json
from pathlib import Path

from build_roms import build


def verify() -> None:
    rows = json.loads(Path(__file__).with_name("complete-results.json").read_text())
    cases = set(
        itertools.product(
            [0, 1, 3, 4, 5, 34, 68], [False, True], [False, True], [False, True]
        )
    )
    keys = [(r["mapper"], r["nes2"], r["battery"], r["trainer"]) for r in rows]
    assert len(rows) == len(set(keys)) == len(cases) == 56
    assert set(keys) == cases
    totals = {"emu": 0, "mesen": 0, "fixed": 0}
    for row in rows:
        key = (row["mapper"], row["nes2"], row["battery"], row["trainer"])
        assert hashlib.sha256(build(*key)).hexdigest() == row["rom_sha256"]
        expected = (
            bytes((i * 37 + 11) & 255 for i in range(512))
            if row["trainer"]
            else bytes(512)
        )
        for engine in totals:
            observed = bytes.fromhex(row[engine + "_hex"])
            assert len(observed) == 512
            bad = sum(a != b for a, b in zip(observed, expected, strict=True))
            if engine != "fixed":
                assert bad == row[engine + "_mismatches"]
            expected_bad = row["trainer"] and (
                engine == "emu"
                or (engine == "mesen" and row["mapper"] == 5 and row["battery"])
            )
            assert bad == (510 if expected_bad else 0), (key, engine, bad)
            totals[engine] += bool(bad)
    assert totals == {"emu": 28, "mesen": 2, "fixed": 0}
    print(
        "56 distinct cases; all 512 bytes checked per engine; ROM hashes reproduced:",
        totals,
    )


if __name__ == "__main__":
    verify()
