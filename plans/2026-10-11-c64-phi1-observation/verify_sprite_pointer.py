"""Verify pointer selection from CPU clocks, held row sources and continuous MC."""

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
from sprite_pointer import guest
from verify_fetch_trace import verify_rows
from verify_sprite_fetch import POINTER_CYCLES

BOUNDARIES = {63: (18, 19), 65: (20, 21), 64: (18, 19)}


def stem(case: dict) -> str:
    return (
        f"{case['model']}-bank{case['bank']}-sprite{case['sprite']}"
        f"-delay{case['delay']:02d}-phase{case['phase']}-reverse{int(case['reverse'])}"
    )


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, b, 0, d, 0, reverse)
        for m, _, c in MODELS
        for b in range(4)
        for d in BOUNDARIES[c]
        for reverse in (False, True)
    }
    actual = [
        (r["model"], r["bank"], r["sprite"], r["delay"], r["phase"], r["reverse"])
        for r in cases
    ]
    assert len(actual) == 80 and set(actual) == expected, "case coverage"


def verify_case(case: dict, rows: list[list[str]], log: str) -> dict:
    cycles = {m: c for m, _, c in MODELS}[case["model"]]
    assert case["cycles"] == cycles and case["sprite"] == 0 and case["phase"] == 0
    bank = case["bank"]
    assert bank in range(4) and type(case["reverse"]) is bool
    ram = case["ram"]
    assert ram == [pattern(bank, s, i) for s in range(8) for i in range(64)], (
        "source RAM"
    )
    old, new = (0x81, 0x80) if case["reverse"] else (0x80, 0x81)
    summary = verify_rows(rows, cycles)
    assert log.count("Stop on store d7ff") == 1 and "Unexpected token" not in log, (
        "completion event"
    )
    address = bank * 0x4000 + 0x7F8
    writes = [
        [int(y), int(c), int(a, 16), int(t)]
        for y, c, a, t in re.findall(f"Trace store {address:04x}" + EVENT, log)
    ]
    assert writes == case["writes"] and len(writes) == 3, "CPU store coverage"
    assert [r[2] for r in writes] == [0x80, old, new]
    height = {63: 312, 65: 263, 64: 262}[cycles]
    for y, c, _, clock in writes:
        assert (y, c) == ((clock // cycles) % height, clock % cycles), "CPU coordinates"
    assert writes[0][3] < writes[1][3] < writes[2][3]
    write_line, write_cycle, _, write_clock = writes[-1]
    before = case["delay"] == BOUNDARIES[cycles][0]
    assert case["delay"] in BOUNDARIES[cycles]
    assert (write_line, write_cycle) == (90, 55 if before else 62), "CPU boundary"
    frame = write_clock - write_line * cycles - write_cycle
    first_pointer = frame + 80 * cycles + POINTER_CYCLES[cycles][0]
    expected_new_offset = 3 * ((write_clock - first_pointer + cycles - 1) // cycles)
    assert expected_new_offset == (30 if before else 33), "row boundary"
    pointer = None
    pointer_clock = None
    latch = None
    pointer_values = []
    data_pointers = []
    lines = set()
    for row in rows[2:-1]:
        kind = row[0]
        clock, line, cycle, logical, physical, data, dma, _, flags, _, _ = map(
            int, row[1:]
        )
        assert kind in {"P1", "P2", "L1"} and dma in {0, 1}, "unexpected DMA"
        if kind == "L1":
            if latch is not None:
                assert line == latch[1] + (cycle == 1), "line progression"
            latch = (clock, line, cycle)
            lines.add(line)
            continue
        assert physical == bank * 0x4000 + logical, "physical bank"
        fetch, sprite = flags & 0xE00, (flags >> 12) & 7
        if kind == "P1" and fetch == 0x600:
            assert (
                cycle == POINTER_CYCLES[cycles][sprite] and logical == 0x7F8 + sprite
            ), "pointer phase/address"
            expected = (
                (new if clock >= write_clock else old) if sprite == 0 else 0x80 + sprite
            )
            assert data == expected, "CPU-clock pointer selection"
            if sprite == 0:
                pointer, pointer_clock = data, clock
                pointer_values.append(data)
            continue
        if kind == "P1" and fetch == 0x800:
            if sprite != 0 or dma == 0:
                assert logical == 0x3FFF, "idle source"
                continue
            byte = 1
        elif kind == "P2":
            assert sprite == 0 and dma == 1 and fetch in {0x600, 0x800}
            byte = 0 if fetch == 0x600 else 2
            assert latch is not None and clock == latch[0] + 1 and cycle == latch[2], (
                "Phi2 clock"
            )
        else:
            continue
        assert pointer is not None and pointer_clock is not None
        offset = len(data_pointers)
        assert offset < 63 and offset % 3 == byte, "byte sequence"
        assert logical == (pointer << 6) + offset, "latched pointer/MC source"
        assert data == ram[(pointer - 0x80) * 64 + offset], "source byte"
        assert cycle == POINTER_CYCLES[cycles][0] + (byte != 0), "fetch phase"
        assert pointer_clock == first_pointer + (offset // 3) * cycles, (
            "row pointer clock"
        )
        assert clock == pointer_clock + 1 + (byte == 2), "data clock"
        data_pointers.append(pointer)
    assert lines == set(range(72, 113)) and len(pointer_values) >= 39, (
        "capture interval"
    )
    assert (
        set(pointer_values) == {old, new}
        and pointer_values[0] == old
        and pointer_values[-1] == new
    )
    assert data_pointers == [old] * expected_new_offset + [new] * (
        63 - expected_new_offset
    ), "transition coverage"
    return {
        **summary,
        "sprite_bytes": 63,
        "first_new_offset": expected_new_offset,
        "write_clock": write_clock,
        "boundary": "before" if before else "after",
    }


def verify_archive(path: Path) -> dict:
    totals = Counter()
    boundaries = Counter()
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
            totals.update({k: result[k] for k in ["records", "sprite_bytes"]})
            boundaries[result["boundary"]] += 1
            key = (case["model"], case["bank"], case["reverse"])
            pairs.setdefault(key, {})[result["boundary"]] = result["write_clock"]
    assert boundaries == {"before": 40, "after": 40}
    # One added NOP requests two clocks; DMA makes the actual gap seven.
    assert len(pairs) == 40 and all(
        p["after"] - p["before"] == 7 for p in pairs.values()
    ), "CPU stall coverage"
    return {
        "cases": 80,
        "boundaries": dict(boundaries),
        "stalled_pairs": len(pairs),
        **dict(totals),
    }


def verify_controls(path: Path) -> dict:
    pairs = {}
    records = 0
    with zipfile.ZipFile(path) as archive:
        cases = json.loads(archive.read("capture.json"))["rows"]
        expected = {(m, d) for m, _, c in MODELS for d in BOUNDARIES[c]}
        actual = [(r["model"], r["delay"]) for r in cases]
        assert len(actual) == 10 and set(actual) == expected, "control coverage"
        for case in cases:
            assert case["dma_enabled"] is False
            assert (
                case["bank"] == case["sprite"] == case["phase"] == 0
                and not case["reverse"]
            )
            name = stem(case)
            program = archive.read(name + ".prg")
            assert program == guest(0, 0, case["delay"], 0, False, True)
            active_program = guest(0, 0, case["delay"], 0, False)
            assert len(program) == len(active_program)
            assert [
                (a, b) for a, b in zip(active_program, program, strict=True) if a != b
            ] == [(1, 0)], "DMA-only control"
            assert hashlib.sha256(program).hexdigest() == case["program_sha256"]
            assert archive.read(name + ".bin") == bytes([0xA5])
            assert archive.read(name + "-ram.bin") == bytes(
                pattern(0, s, i) for s in range(8) for i in range(64)
            )
            raw = archive.read(name + ".csv")
            assert hashlib.sha256(raw).hexdigest() == case["trace_sha256"]
            rows = list(csv.reader(io.StringIO(raw.decode())))
            summary = verify_rows(rows, case["cycles"])
            assert summary == case["trace"]
            assert set(summary["kinds"]) == {"P1", "L1"}, "DMA disabled"
            log = archive.read(name + ".log").decode()
            assert (
                log.count("Stop on store d7ff") == 1 and "Unexpected token" not in log
            )
            writes = [
                [int(y), int(c), int(a, 16), int(t)]
                for y, c, a, t in re.findall("Trace store 07f8" + EVENT, log)
            ]
            assert (
                writes == case["writes"]
                and len(writes) == 3
                and [r[2] for r in writes] == [128, 128, 129]
            )
            pointers = [r for r in rows[2:-1] if r[0] == "P1" and int(r[4]) == 0x7F8]
            assert len(pointers) >= 39 and {int(r[6]) for r in pointers} == {128, 129}
            assert all(
                int(r[6]) == (129 if int(r[1]) >= writes[-1][3] else 128)
                for r in pointers
            ), "control pointer source"
            assert all(int(r[7]) == 0 for r in rows[2:-1]), "DMA flag"
            pairs.setdefault(case["model"], {})[case["delay"]] = writes[-1][3]
            records += summary["records"]
    assert len(pairs) == 5
    for pair in pairs.values():
        low, high = sorted(pair)
        assert high - low == 1 and pair[high] - pair[low] == 2, "unstalled CPU control"
    return {"cases": 10, "unstalled_pairs": 5, "records": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(verify_archive(parser.parse_args().archive), indent=2))
