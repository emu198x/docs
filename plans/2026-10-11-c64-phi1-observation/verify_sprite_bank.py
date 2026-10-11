"""Verify CPU-timed live banks, held sprite pointers and uninterrupted MC."""

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
from sprite_bank import guest, pointer, stem
from sprite_fetch import pattern
from verify_fetch_trace import verify_rows
from verify_sprite_fetch import POINTER_CYCLES


def verify_sequence(
    case: dict,
    rows: list[list[str]],
    banks: list[bytes],
    pointers: list[bytes],
    log: str,
) -> dict:
    cycles = {m: c for m, _, c in MODELS}[case["model"]]
    assert cycles == case["cycles"]
    old, new, glue, target = (case[k] for k in ("old", "new", "glue", "sprite"))
    assert old in range(4) and new in range(4) and glue in (0, 1) and target in range(8)
    assert banks == [
        bytes(pattern(b, s, i) for s in range(8) for i in range(64)) for b in range(4)
    ], "source RAM"
    assert pointers == [bytes(pointer(b, s) for s in range(8)) for b in range(4)], (
        "pointer RAM"
    )
    assert f"GlueLogic={glue}" in log, "glue resource"
    assert log.count("Stop on store d7ff") == 1 and "Unexpected token" not in log, (
        "completion event"
    )
    writes = [
        [int(y), int(c), int(a, 16), int(t)]
        for y, c, a, t in re.findall("Trace store dd00" + EVENT, log)
    ]
    assert writes == case["writes"] and len(writes) == 2, "CPU store coverage"
    assert [w[2] for w in writes] == [3 - old, 3 - new], "CPU bank values"
    height = {63: 312, 64: 262, 65: 263}[cycles]
    for y, c, _, t in writes:
        assert (y, c) == ((t // cycles) % height, t % cycles), "CPU coordinates"
    assert writes[0][3] < writes[1][3]
    write_line, write_cycle, _, write_clock = writes[-1]
    assert write_line in (90, 91), "write interval"
    transient = glue == 1 and {old, new} == {1, 2}

    def bank_at(clock: int) -> int:
        if clock < write_clock:
            return old
        return 3 if transient and clock == write_clock else new

    result = verify_rows(rows, cycles)
    assert result["first_clock"] < write_clock < result["last_clock"], (
        "observed bank boundary"
    )
    frame = write_clock - write_line * cycles - write_cycle
    pointer_cycle = POINTER_CYCLES[cycles][target]
    first_line = 80 + (pointer_cycle < (54 if cycles == 63 else 55))
    first_pointer = frame + first_line * cycles + pointer_cycle
    held = None
    pointer_clock = None
    data_count = 0
    mixed_rows = 0
    transient_pointers = 0
    observed_transient = 0
    target_pointers = 0
    row_banks = []
    lines = set()
    for r in rows[2:-1]:
        kind = r[0]
        clock, line, cycle, logical, physical, data, dma, _, flags, _, _ = map(
            int, r[1:]
        )
        assert kind in ("P1", "P2", "L1") and dma in (0, 1 << target), "unexpected DMA"
        if kind in ("P1", "L1"):
            assert cycle == clock % cycles, "absolute Phi1 cycle"
            assert line == (clock // cycles) % height - (cycle == 0), (
                "absolute Phi1 line"
            )
        else:
            assert cycle == (clock - 1) % cycles, "absolute Phi2 cycle"
            assert line == ((clock - 1) // cycles) % height, "absolute Phi2 line"
        lines.add(line)
        if kind == "L1":
            continue
        bank = bank_at(clock)
        assert physical == bank * 0x4000 + logical, "CPU-clock physical bank"
        if kind == "P1" and clock == write_clock and transient:
            observed_transient += 1
        fetch, sprite = flags & 0xE00, (flags >> 12) & 7
        if kind == "P1" and fetch == 0x600:
            assert (
                cycle == POINTER_CYCLES[cycles][sprite] and logical == 0x7F8 + sprite
            ), "pointer address/phase"
            assert data == pointers[bank][sprite], "CPU-clock pointer source"
            if clock == write_clock and transient:
                transient_pointers += 1
            if sprite == target:
                held, pointer_clock = data, clock
                target_pointers += 1
            continue
        if kind == "P1" and fetch == 0x800:
            if sprite != target or dma == 0:
                assert logical == 0x3FFF, "idle middle source"
                continue
            byte = 1
        elif kind == "P2":
            assert (
                sprite == target and dma == (1 << target) and fetch in (0x600, 0x800)
            ), "sprite ownership"
            byte = 0 if fetch == 0x600 else 2
        else:
            continue
        assert held is not None and pointer_clock is not None
        offset = data_count
        assert offset < 63 and offset % 3 == byte, "byte sequence"
        assert pointer_clock == first_pointer + (offset // 3) * cycles, (
            "row pointer clock"
        )
        assert clock == pointer_clock + 1 + (byte == 2), "data clock"
        assert cycle == (pointer_cycle + (byte != 0)) % cycles, "data phase"
        assert logical == (held << 6) + offset, "held pointer / MC"
        assert data == banks[bank][(held - 0x80) * 64 + offset], "source byte"
        row_banks.append(bank)
        if byte == 2:
            mixed_rows += len(set(row_banks[-3:])) > 1
        data_count += 1
    assert (
        lines == set(range(72, 113)) and target_pointers >= 39 and data_count == 63
    ), "capture coverage"
    assert observed_transient == int(transient), "transient coverage"
    return {
        **result,
        "sprite_bytes": data_count,
        "write_clock": write_clock,
        "write_line": write_line,
        "write_cycle": write_cycle,
        "transient_fetches": observed_transient,
        "transient_pointers": transient_pointers,
        "mixed_rows": mixed_rows,
    }


def verify_directory(path: Path) -> dict:
    manifest = json.loads((path / "capture.json").read_text())
    totals = Counter()
    results = []
    for case in manifest["rows"]:
        name = stem(case)
        result = verify_sequence(
            case,
            list(csv.reader((path / (name + ".csv")).open())),
            [(path / (name + f"-bank{b}.bin")).read_bytes() for b in range(4)],
            [(path / (name + f"-pointers{b}.bin")).read_bytes() for b in range(4)],
            (path / (name + ".log")).read_text(),
        )
        totals.update(
            {
                k: result[k]
                for k in (
                    "records",
                    "sprite_bytes",
                    "transient_fetches",
                    "transient_pointers",
                    "mixed_rows",
                )
            }
        )
        results.append({**case, **result})
    assert results
    return {"cases": len(results), **totals, "rows": results}


# Adjacent requested NOP delays, calibrated with the three-clock BIT alignment.
BOUNDARIES = {63: (17, 18), 65: (20, 21), 64: (19, 20)}


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, g, o, n, d, 3, 0)
        for m, _, c in MODELS
        for g in (0, 1)
        for o in range(4)
        for n in range(4)
        for d in BOUNDARIES[c]
    }
    actual = [
        tuple(r[k] for k in ("model", "glue", "old", "new", "delay", "phase", "sprite"))
        for r in cases
    ]
    assert len(actual) == 320 and set(actual) == expected, "bank case coverage"


def verify_case(
    case: dict,
    rows: list[list[str]],
    banks: list[bytes],
    pointers: list[bytes],
    log: str,
) -> dict:
    result = verify_sequence(case, rows, banks, pointers, log)
    delays = BOUNDARIES[case["cycles"]]
    assert case["phase"] == 3 and case["sprite"] == 0 and case["delay"] in delays, (
        "qualified boundary"
    )
    side = delays.index(case["delay"])
    before = 56 if case["cycles"] == 64 else 55
    assert (result["write_line"], result["write_cycle"]) == (90, before + 7 * side), (
        "CPU stall boundary"
    )
    assert result["mixed_rows"] == 0, "ordinary CPU write outside DMA row"
    return {**result, "boundary": "after" if side else "before"}


def verify_archive(path: Path, calibration: bool = False) -> dict:
    totals = Counter()
    pairs = {}
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture.json"))
        cases = manifest["rows"]
        if calibration:
            expected = {
                (m, g, 1, 2, d, p, 0)
                for m, _, c in MODELS
                for g in (0, 1)
                for d in (range(15, 24) if c == 63 else range(17, 22))
                for p in (0, 3)
            }
            actual = [
                tuple(
                    r[k]
                    for k in ("model", "glue", "old", "new", "delay", "phase", "sprite")
                )
                for r in cases
            ]
            assert len(actual) == 132 and set(actual) == expected, (
                "calibration coverage"
            )
        else:
            verify_coverage(cases)
        for case in cases:
            name = stem(case)
            program = archive.read(name + ".prg")
            assert program == guest(
                case["old"], case["new"], case["sprite"], case["delay"], case["phase"]
            ), "guest identity"
            assert hashlib.sha256(program).hexdigest() == case["program_sha256"], (
                "program hash"
            )
            raw = archive.read(name + ".csv")
            assert hashlib.sha256(raw).hexdigest() == case["trace_sha256"], "trace hash"
            assert archive.read(name + ".bin") == bytes([0xA5]), "completion sentinel"
            check = verify_sequence if calibration else verify_case
            result = check(
                case,
                list(csv.reader(io.StringIO(raw.decode()))),
                [archive.read(name + f"-bank{b}.bin") for b in range(4)],
                [archive.read(name + f"-pointers{b}.bin") for b in range(4)],
                archive.read(name + ".log").decode(),
            )
            assert all(result[k] == v for k, v in case["trace"].items()), (
                "trace summary"
            )
            totals.update(
                {
                    k: result[k]
                    for k in (
                        "records",
                        "sprite_bytes",
                        "transient_fetches",
                        "transient_pointers",
                        "mixed_rows",
                    )
                }
            )
            if not calibration:
                key = tuple(case[k] for k in ("model", "glue", "old", "new"))
                pairs.setdefault(key, {})[result["boundary"]] = result["write_clock"]
    if not calibration:
        assert len(pairs) == 160 and all(
            p["after"] - p["before"] == 7 for p in pairs.values()
        ), "CPU stall pair coverage"
        assert totals["transient_fetches"] == 20
    return {"cases": len(cases), **totals, "stalled_pairs": len(pairs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--calibration", action="store_true")
    args = parser.parse_args()
    result = (
        verify_directory(args.path)
        if args.path.is_dir()
        else verify_archive(args.path, args.calibration)
    )
    result.pop("rows", None)
    print(json.dumps(result, indent=2))
