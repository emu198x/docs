"""Check complete observer records and Phi1 latch preservation across Phi2."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

HEADER = [
    "kind",
    "clock",
    "line",
    "cycle",
    "logical",
    "physical",
    "data",
    "dma",
    "prefetch",
    "flags",
    "phi1",
    "phi2",
]


def verify_rows(rows: Iterable[list[str]], cycles: int) -> dict:
    iterator = iter(rows)
    assert next(iterator, None) == ["EMU198X_VIC_FETCH", "1"]
    assert next(iterator, None) == HEADER
    count = 0
    kinds: Counter[str] = Counter()
    pending = None
    latch = None
    first_clock = None
    last_clock = None
    end = False
    for fields in iterator:
        assert fields, "empty record"
        if fields[0] == "END":
            assert len(fields) == 2 and int(fields[1]) == count
            assert next(iterator, None) is None, "trailing records"
            end = True
            break
        assert len(fields) == len(HEADER)
        kind = fields[0]
        assert kind in {"P1", "P2", "L1", "S0I", "S2I", "MI"}
        (
            clock,
            line,
            cycle,
            logical,
            physical,
            data,
            dma,
            prefetch,
            flags,
            phi1,
            phi2,
        ) = map(int, fields[1:])
        assert clock >= 0 and 0 <= line < 312 and 0 <= cycle < cycles
        assert all(0 <= v <= 255 for v in (data, dma, phi1, phi2))
        assert prefetch >= 0 and flags >= 0
        assert last_clock is None or clock >= last_clock
        last_clock = clock
        if first_clock is None:
            first_clock = clock
        if kind in {"P1", "P2"}:
            assert 0 <= logical < 0x4000 and 0 <= physical < 0x10000
        elif kind == "L1":
            assert logical == physical == -1
        else:
            assert 0 <= logical < 0x4000 and physical == -1 and prefetch > 0
            assert data == (255 if kind == "MI" else phi2)
        if kind == "P1":
            assert pending is None, "fetch without matching latch"
            pending = (clock, line, cycle, data)
        if kind == "L1":
            assert pending == (clock, line, cycle, data), "wrong/missing Phi1 fetch"
            assert data == phi1
            if latch is not None:
                assert clock == latch[0] + 1, "missing/duplicate clock"
                assert cycle == (latch[2] + 1) % cycles, "shifted cycle"
            latch = (clock, line, cycle, data)
            pending = None
        elif latch is not None:
            assert phi1 == latch[3], "retained Phi1 changed before the next latch"
        kinds[kind] += 1
        count += 1
    assert end and pending is None and 0 < count < 1_000_000
    assert kinds["P1"] == kinds["L1"] and kinds["L1"] > cycles
    return {
        "records": count,
        "kinds": dict(kinds),
        "first_clock": first_clock,
        "last_clock": last_clock,
    }


def verify(path: Path, cycles: int) -> dict:
    with path.open(newline="") as handle:
        return verify_rows(csv.reader(handle), cycles)
