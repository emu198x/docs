"""Validate capture coverage, executed guest markers and the red/green results."""
import csv
import gzip
import hashlib
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(rows: list[dict[str, str]], debounce: bool, failures: int) -> None:
    selectors = [0] if debounce else range(4)
    controls = [1, 3] if debounce else [0, 2]
    expected = {(kind, str(port), str(selector), str(control))
                for kind in ["idle", "fire1", "x", "y", "fire2", "keypad"]
                for port in [0, 1, 2, 3, 4, 5, 255]
                for selector in selectors for control in controls}
    keys = [(r["case"], r["port"], r["selected"], r["skctl"]) for r in rows]
    assert len(keys) == len(expected) and set(keys) == expected
    assert all(int(r["guest_loops"]) > 100 for r in rows)
    assert all(r["passed"] in {"true", "false"} for r in rows)
    assert sum(r["passed"] == "false" for r in rows) == failures


def main() -> None:
    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    for label in ["original", "corrected"]:
        for name, debounce, old_failures in [("baseline", False, 176),
                                             ("debounce-baseline", True, 46)]:
            data = gzip.decompress((HERE / f"{label}-{name}.csv.gz").read_bytes()).decode()
            rows = list(csv.DictReader(io.StringIO(data)))
            failures = old_failures if label == "original" else 0
            check(rows, debounce, failures)
            for mutation in [rows[:-1], [*rows, rows[0]],
                             [dict(r, guest_loops="0") for r in rows]]:
                try:
                    check(mutation, debounce, failures)
                except AssertionError:
                    continue
                raise AssertionError("capture mutation unexpectedly passed")
    negative = gzip.decompress((HERE / "scanner-negative.log.gz").read_bytes()).decode()
    assert "reference row 1,0,3,1,0" in negative and "test result: FAILED" in negative
    phase = gzip.decompress((HERE / "cpu-phase-red.log.gz").read_bytes()).decode()
    assert "left: 160" in phase and "right: 162" in phase
    print("840 guest captures checked: 222 original failures, zero corrected; 12 coverage/execution mutations rejected")


if __name__ == "__main__":
    main()
