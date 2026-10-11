"""Check late sprite-DMA substitution against CPU writes and recorded source RAM."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS
from sprite_fetch import pattern
from sprite_ownership import guest
from verify_fetch_trace import verify_rows
from verify_sprite_fetch import POINTER_CYCLES

# Calibrated guest delays. The expected outcome below is independently selected
# from the CPU's completed store clock, not the observed number of DMA reads.
BOUNDARIES = {
    63: ((14, 0, -2), (13, 3, -1), (15, 0, 0), (14, 3, 1), (16, 0, 2)),
    65: ((18, 0, -2), (17, 3, -1), (19, 0, 0), (18, 3, 1), (20, 0, 2)),
    64: ((16, 3, -2), (18, 0, -1), (17, 3, 0), (19, 0, 1), (18, 3, 2)),
}


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, b, d, phase)
        for m, _, c in MODELS
        for b in range(4)
        for d, phase, _ in BOUNDARIES[c]
    }
    actual = [(r["model"], r["bank"], r["delay"], r["phase"]) for r in cases]
    assert len(actual) == len(expected) and set(actual) == expected, "case coverage"


def verify_case(case: dict, rows: list[list[str]], log: str) -> dict:
    cycles = {m: c for m, _, c in MODELS}[case["model"]]
    assert case["cycles"] == cycles
    bank = case["bank"]
    assert bank in range(4)
    ram = case["ram"]
    assert ram == [pattern(bank, 0, i) for i in range(64)], "source RAM"
    summary = verify_rows(rows, cycles)
    assert "Unexpected token" not in log
    assert log.count("Stop on store d7ff") == 1, "completion event"
    writes = [
        [int(y), int(c), int(a, 16), int(t)]
        for y, c, a, t in re.findall("Trace store d015" + EVENT, log)
    ]
    assert writes == case["writes"] and len(writes) == 2, "CPU store coverage"
    assert [w[2] for w in writes] == [0, 1] and writes[0][3] < writes[1][3]
    height = {63: 312, 65: 263, 64: 262}[cycles]
    for y, c, _, t in writes:
        assert y == (t // cycles) % height and c == t % cycles, "CPU coordinates"
    y, enable_cycle, _, enable_clock = writes[1]
    assert y == 80
    # VICE checks DMA at zero-based 54/55 (PAL) or 55/56 (NTSC).
    # The completed CPU store clock is one after the write's VIC slot.
    # A store reported at the second check has missed the first check.
    second_check = 55 if cycles == 63 else 56
    state = (
        "early"
        if enable_cycle < second_check
        else "invalid"
        if enable_cycle == second_check
        else "late"
    )
    offsets = {(d, phase): offset for d, phase, offset in BOUNDARIES[cycles]}
    assert enable_cycle == second_check + offsets[case["delay"], case["phase"]], (
        "delay calibration"
    )
    first_data_clock = enable_clock - enable_cycle + POINTER_CYCLES[cycles][0] + 1
    data_rows = []
    pointers = 0
    lines = set()
    latch = None
    for row in rows[2:-1]:
        kind = row[0]
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
        ) = map(int, row[1:])
        assert dma in {0, 1}, "unexpected sprite DMA"
        assert kind in {"P1", "P2", "L1", "S0I"}, "unexpected access"
        if kind == "L1":
            if latch is not None:
                assert line == latch[1] + (cycle == 1), "line progression"
            latch = (clock, line, cycle)
            lines.add(line)
            continue
        if kind != "S0I":
            assert physical == bank * 0x4000 + logical, "physical bank"
        fetch, sprite = flags & 0xE00, (flags >> 12) & 7
        if kind == "P1" and fetch == 0x600:
            assert logical == 0x7F8 + sprite and data == 0x80 + sprite, "pointer source"
            assert cycle == POINTER_CYCLES[cycles][sprite], "pointer phase"
            pointers += 1
            continue
        if kind == "P1" and fetch == 0x800:
            if not dma & (1 << sprite):
                assert logical == 0x3FFF, "idle source"
                continue
            byte = 1
        elif kind in {"P2", "S0I"}:
            assert fetch in {0x600, 0x800} and dma == 1 and sprite == 0
            byte = 0 if fetch == 0x600 else 2
            assert latch is not None and clock == latch[0] + 1 and cycle == latch[2], (
                "Phi2 clock"
            )
        else:
            continue
        assert sprite == 0 and dma == 1
        offset = logical - 0x2000
        assert 0 <= offset < 63 and offset % 3 == byte, "byte position"
        assert cycle == POINTER_CYCLES[cycles][0] + (byte != 0), "fetch phase"
        assert clock == first_data_clock + (offset // 3) * cycles + (byte == 2), (
            "fetch clock"
        )
        assert line == 80 + offset // 3, "fetch line"
        if state == "invalid" and offset == 0:
            assert kind == "S0I" and physical == -1 and prefetch == 1, (
                "missing invalid access"
            )
            assert data == phi2 == 255 and data != ram[0], "substituted bus byte"
            assert phi1 == 0x80, "retained pointer byte"
        else:
            assert kind == ("P1" if byte == 1 else "P2"), "unexpected substitution"
            assert data == ram[offset], "RAM byte"
        data_rows.append(offset)
    assert lines == set(range(72, 113)) and pointers >= 39 * 8, "capture interval"
    assert data_rows == ([] if state == "late" else list(range(63))), "DMA coverage"
    assert [r for r in rows[2:-1] if r[0] == "S0I"] == case["invalid"], (
        "invalid record summary"
    )
    return {
        **summary,
        "state": state,
        "sprite_bytes": len(data_rows),
        "invalid_bytes": int(state == "invalid"),
    }


def verify_archive(path: Path) -> dict:
    totals = Counter()
    states = Counter()
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture.json"))
        verify_coverage(manifest["rows"])
        for case in manifest["rows"]:
            stem = f"{case['model']}-bank{case['bank']}-delay{case['delay']:02d}-phase{case['phase']}"
            prg = archive.read(stem + ".prg")
            assert prg == guest(case["bank"], case["delay"], case["phase"])
            assert hashlib.sha256(prg).hexdigest() == case["program_sha256"]
            assert archive.read(stem + ".bin") == bytes([0xA5])
            assert archive.read(stem + "-ram.bin") == bytes(case["ram"])
            raw = archive.read(stem + ".csv")
            assert hashlib.sha256(raw).hexdigest() == case["trace_sha256"]
            result = verify_case(
                case,
                list(csv.reader(io.StringIO(raw.decode()))),
                archive.read(stem + ".log").decode(),
            )
            assert all(result[k] == v for k, v in case["trace"].items()), (
                "trace summary"
            )
            states[result["state"]] += 1
            totals.update(
                {k: result[k] for k in ["records", "sprite_bytes", "invalid_bytes"]}
            )
    assert states == {"early": 40, "invalid": 20, "late": 40}
    return {"cases": 100, "states": dict(states), **dict(totals)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(verify_archive(parser.parse_args().archive), indent=2))
