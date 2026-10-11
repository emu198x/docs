"""Verify late matrix ownership and consumption using CPU clocks and RAM dumps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from itertools import pairwise
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS
from graphics_fetch import graphics_byte, matrix_byte
from matrix_ownership import BOUNDARIES, guest, stem
from verify_fetch_trace import verify_rows


def verify_case(
    case: dict, rows: list[list[str]], matrix: bytes, graphics: bytes, log: str
) -> dict:
    cycles = {m: c for m, _, c in MODELS}[case["model"]]
    assert case["cycles"] == cycles and case["bank"] in range(4)
    bank = case["bank"]
    assert matrix == bytes(matrix_byte(bank, i) for i in range(1024)), (
        "matrix source RAM"
    )
    assert graphics == bytes(graphics_byte(bank, i) for i in range(8192)), (
        "graphics source RAM"
    )
    assert type(case["force"]) is bool
    writes = [
        [int(y), int(c), int(a, 16), int(t)]
        for y, c, a, t in re.findall("Trace store d011" + EVENT, log)
    ]
    assert writes == case["writes"] and len(writes) == 3, "CPU store coverage"
    assert [w[2] for w in writes] == [0, 0x1B, 0x1C if case["force"] else 0x1B], (
        "CPU register values"
    )
    assert all(a[3] < b[3] for a, b in pairwise(writes)), "CPU store order"
    height = {63: 312, 64: 262, 65: 263}[cycles]
    for y, c, _, t in writes:
        assert (y, c) == ((t // cycles) % height, t % cycles), "CPU coordinates"
    y, c, _, write_clock = writes[-1]
    assert y in (60, 61) and (y != 60 or c >= 14), "active-display probe scope"
    assert log.count("Stop on store d7ff") == 1 and "Unexpected token" not in log, (
        "completion event"
    )
    summary = verify_rows(rows, cycles)
    assert summary["first_clock"] < write_clock < summary["last_clock"]
    expected = {
        (line, cycle): ("P2", base + cycle - 14, 0)
        for line, base in [(51, 0), (59, 40), (68 if case["force"] else 67, 80)]
        for cycle in range(14, 54)
    }
    if case["force"] and y == 60:
        for cycle in range(c, 54):
            remaining = max(0, 3 - (cycle - c))
            expected[(60, cycle)] = (
                "MI" if remaining else "P2",
                40 + cycle - 14,
                remaining,
            )
    seen = []
    changed = {
        index: (255 if kind == "MI" else matrix[index])
        for (line, _), (kind, index, _) in expected.items()
        if line == 60
    }
    invalid = 0
    invalid_different_ram = 0
    valid_late = 0
    gslots = []
    last_latch = None
    for r in rows[2:-1]:
        kind = r[0]
        clock, line, cycle, logical, physical, data, dma, prefetch, flags, _, _ = map(
            int, r[1:]
        )
        assert kind in ("P1", "L1", "P2", "MI") and dma == 0, "unexpected DMA kind"
        assert cycle == clock % cycles and line == (clock // cycles) % height - (
            cycle == 0
        ), "absolute fetch coordinates"
        assert 40 <= line <= 70, "capture interval"
        if kind == "L1":
            last_latch = clock
            continue
        if kind in ("MI", "P2"):
            assert last_latch == clock, "matrix follows current Phi1"
            key = (line, cycle)
            assert key in expected, "unexpected matrix slot"
            want, index, remaining = expected[key]
            assert kind == want and prefetch == remaining, "matrix ownership countdown"
            assert flags & 0x8000 and logical == 0x400 + index, (
                "matrix address sequence"
            )
            assert key not in seen, "duplicate matrix slot"
            seen.append(key)
            if kind == "MI":
                assert physical == -1 and data == 255, "disconnected matrix access"
                invalid += 1
                invalid_different_ram += matrix[index] != 255
            else:
                assert physical == bank * 0x4000 + logical and data == matrix[index], (
                    "matrix RAM access"
                )
                valid_late += line == 60
            continue
        assert physical == bank * 0x4000 + logical, "Phi1 physical bank"
        if 0x2000 <= logical <= 0x3FFF:
            assert data == graphics[logical - 0x2000], "Phi1 graphics source byte"
        elif 0x400 <= logical <= 0x7FF:
            assert data == matrix[logical - 0x400], "Phi1 pointer source byte"
        assert ((flags & 0xE00) == 0x400) == (15 <= cycle <= 54), (
            "graphics slot identity"
        )
        if line not in (60, 61) or not 15 <= cycle <= 54:
            continue
        index = 40 + cycle - 15
        source = matrix[index]
        if index in changed and (line == 61 or cycle - 1 >= c):
            source = changed[index]
        address = 0x2000 + source * 8 + (line - 59)
        assert logical == address, "matrix consumption / retained row"
        gslots.append((line, cycle))
    assert seen == sorted(expected), "complete matrix sequence"
    assert gslots == [(line, cycle) for line in (60, 61) for cycle in range(15, 55)], (
        "graphics consumption coverage"
    )
    return {
        **summary,
        "invalid_matrix": invalid,
        "invalid_distinct_ram": invalid_different_ram,
        "valid_late_matrix": valid_late,
        "consumed_graphics": len(gslots),
        "write_line": y,
        "write_cycle": c,
        "write_clock": write_clock,
    }


def verify_directory(path: Path) -> dict:
    cases = json.loads((path / "capture.json").read_text())["rows"]
    assert cases
    totals = Counter()
    bins = Counter()
    for case in cases:
        n = stem(case)
        result = verify_case(
            case,
            list(csv.reader((path / (n + ".csv")).open())),
            (path / (n + "-matrix.bin")).read_bytes(),
            (path / (n + "-graphics.bin")).read_bytes(),
            (path / (n + ".log")).read_text(),
        )
        totals.update(
            {
                k: result[k]
                for k in (
                    "records",
                    "invalid_matrix",
                    "invalid_distinct_ram",
                    "valid_late_matrix",
                    "consumed_graphics",
                )
            }
        )
        bins[result["invalid_matrix"]] += 1
    return {"cases": len(cases), "invalid_counts": dict(sorted(bins.items())), **totals}


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, 0, d, p, True) for m, _, _ in MODELS for d in range(24) for p in (0, 3)
    }
    expected |= {
        (m, b, d, p, True)
        for m, _, c in MODELS
        for b in range(1, 4)
        for d, p in BOUNDARIES[c]
    }
    expected |= {
        (m, b, d, p, False)
        for m, _, c in MODELS
        for b in range(4)
        for d, p in BOUNDARIES[c]
    }
    actual = [
        tuple(r[k] for k in ("model", "bank", "delay", "phase", "force")) for r in cases
    ]
    assert len(actual) == 415 and set(actual) == expected, "matrix case coverage"


def verify_archive(path: Path) -> dict:
    totals = Counter()
    bins = Counter()
    controls = 0
    boundary_counts = Counter()
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture.json"))
        cases = manifest["rows"]
        verify_coverage(cases)
        for case in cases:
            n = stem(case)
            blobs = {}
            for key, suffix in [
                ("program", ".prg"),
                ("trace", ".csv"),
                ("matrix", "-matrix.bin"),
                ("graphics", "-graphics.bin"),
            ]:
                blobs[key] = archive.read(n + suffix)
                assert (
                    hashlib.sha256(blobs[key]).hexdigest() == case[key + "_sha256"]
                ), "artifact hash"
            assert blobs["program"] == guest(
                case["bank"], case["delay"], case["phase"], case["force"]
            ), "guest identity"
            assert archive.read(n + ".bin") == bytes([0xA5]), "completion sentinel"
            result = verify_case(
                case,
                list(csv.reader(io.StringIO(blobs["trace"].decode()))),
                blobs["matrix"],
                blobs["graphics"],
                archive.read(n + ".log").decode(),
            )
            assert all(result[k] == v for k, v in case["trace"].items()), (
                "trace summary"
            )
            totals.update(
                {
                    k: result[k]
                    for k in (
                        "records",
                        "invalid_matrix",
                        "invalid_distinct_ram",
                        "valid_late_matrix",
                        "consumed_graphics",
                    )
                }
            )
            bins[result["invalid_matrix"]] += 1
            if not case["force"]:
                assert result["invalid_matrix"] == result["valid_late_matrix"] == 0
                controls += 1
            if result["write_line"] == 60 and result["write_cycle"] in (51, 52, 53, 54):
                boundary_counts[
                    (case["model"], case["bank"], case["force"], result["write_cycle"])
                ] += 1
                assert result["invalid_matrix"] == (
                    54 - result["write_cycle"] if case["force"] else 0
                )
    assert controls == 100
    assert set(boundary_counts) == {
        (m, b, f, c)
        for m, _, _ in MODELS
        for b in range(4)
        for f in (False, True)
        for c in (51, 52, 53, 54)
    }, "cutoff boundary coverage"
    assert all(n == 1 for n in boundary_counts.values()), "duplicate boundary"
    return {
        "cases": len(cases),
        "controls": controls,
        "boundary_cases": len(boundary_counts),
        "invalid_counts": dict(sorted(bins.items())),
        **totals,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    path = parser.parse_args().path
    print(
        json.dumps(
            verify_directory(path) if path.is_dir() else verify_archive(path), indent=2
        )
    )
