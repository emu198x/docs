"""Verify every controller state, host input and guest execution marker."""
import csv
import hashlib
import json
from pathlib import Path

from build_guest import cartridge

ROOT = Path(__file__).parent
MASKS = [(1, 0), (2, 0), (4, 0), (8, 0), (16, 0), (32, 0),
         (64, 0), (128, 0), (0, 1), (0, 2), (0, 4), (0, 8)]


def verify() -> None:
    provenance = json.loads((ROOT / "provenance.json").read_text())
    assert hashlib.sha256(cartridge()).hexdigest() == provenance["guest_sha256"]
    failures = {}
    for engine in ["baseline", "mame", "fixed"]:
        with (ROOT / f"{engine}.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 4096
        failed = 0
        for state, row in enumerate(rows):
            assert int(row["state"]) == state
            expected = [255, 255]
            for bit, (even, odd) in enumerate(MASKS):
                if state & (1 << bit):
                    expected[0] &= ~even
                    expected[1] &= ~odd
            actual = [int(row["even"]), int(row["odd"])]
            failed += actual != expected
            assert row["before"] != row["after"], (engine, state, "no guest progress")
            if engine == "mame":
                assert int(row["p1"]) & 63 == (~state) & 63
                assert int(row["p2"]) & 63 == (~(state >> 6)) & 63
        failures[engine] = failed
    assert failures == {"baseline": 4032, "mame": 0, "fixed": 0}, failures
    assert "CAPTURE_COMPLETE states=4096" in (ROOT / "mame.log").read_text()
    print("4096 complete states per engine, all guest markers and MAME inputs verified:", failures)


if __name__ == "__main__":
    verify()
