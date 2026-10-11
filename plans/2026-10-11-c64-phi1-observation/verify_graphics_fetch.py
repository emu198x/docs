"""Verify native stable-mode graphics and matrix reads against captured RAM."""

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
from graphics_fetch import graphics_byte, guest, matrix_byte
from verify_fetch_trace import verify_rows


def stem(case: dict) -> str:
    return f"{case['model']}-bank{case['bank']}-mode{case['mode']}"


def verify_coverage(cases: list[dict]) -> None:
    expected = {
        (m, b, mode) for m, _, _ in MODELS for b in range(4) for mode in range(8)
    }
    actual = [(c["model"], c["bank"], c["mode"]) for c in cases]
    assert len(actual) == 160 and set(actual) == expected, "graphics case coverage"


def verify_case(
    case: dict, rows: list[list[str]], matrix: bytes, graphics: bytes, log: str
) -> dict:
    models = {m: c for m, _, c in MODELS}
    cycles = models[case["model"]]
    assert cycles == case["cycles"], "model clock geometry"
    bank, mode = case["bank"], case["mode"]
    assert bank in range(4) and mode in range(8)
    assert matrix == bytes(matrix_byte(bank, i) for i in range(1024)), "matrix RAM dump"
    assert graphics == bytes(graphics_byte(bank, i) for i in range(8192)), (
        "graphics RAM dump"
    )
    assert log.count("Stop on store d7ff") == 1 and "Unexpected token" not in log, (
        "completion event"
    )
    result = verify_rows(rows, cycles)
    assert set(result["kinds"]) == {"P1", "L1", "P2"}, "unexpected fetch kind"
    height = 312 if cycles == 63 else 263 if cycles == 65 else 262
    graphics_slots = []
    matrix_slots = []
    counts = Counter()
    for fields in rows[2:-1]:
        kind = fields[0]
        clock, line, cycle, logical, physical, data, dma, prefetch, flags, _, _ = map(
            int, fields[1:]
        )
        assert cycle == clock % cycles, "absolute fetch cycle"
        assert line == (clock // cycles) % height - (cycle == 0), "absolute fetch line"
        assert 40 <= line <= 76 and dma == 0, "capture scope"
        if kind == "L1":
            continue
        if kind == "P2":
            assert line in (51, 59, 67, 75) and 14 <= cycle <= 53, "matrix timing"
            assert flags & 0x8000 and prefetch == 0, "matrix ownership"
            column = cycle - 14
            index = ((line - 51) // 8) * 40 + column
            assert logical == 0x400 + index, "matrix address sequence"
            assert physical == bank * 0x4000 + logical, "matrix physical bank"
            assert data == matrix[index], "matrix source byte"
            matrix_slots.append((line, column))
            continue
        is_graphics = (flags & 0x0E00) == 0x400
        assert is_graphics == (15 <= cycle <= 54), "graphics slot identity"
        if not is_graphics or not 41 <= line <= 75:
            continue
        column = cycle - 15
        graphics_slots.append((line, column))
        if line < 51:
            address = 0x3FFF
            counts["idle_graphics"] += 1
        else:
            row, rc = divmod(line - 51, 8)
            index = row * 40 + column
            source = index if mode & 2 else matrix[index]
            address = 0x2000 | (source << 3) | rc
            counts["active_graphics"] += 1
            if line not in (51, 59, 67, 75):
                counts["retained_matrix_graphics"] += 1
        if mode & 4:
            address &= 0x39FF
        assert logical == address, "graphics address / row counter"
        assert physical == bank * 0x4000 + address, "graphics physical bank"
        assert data == graphics[address - 0x2000], "graphics source byte"
    assert graphics_slots == [
        (line, col) for line in range(41, 76) for col in range(40)
    ], "graphics column coverage"
    assert matrix_slots == [
        (line, col) for line in (51, 59, 67, 75) for col in range(40)
    ], "matrix column coverage"
    assert counts == {
        "idle_graphics": 400,
        "active_graphics": 1000,
        "retained_matrix_graphics": 840,
    }
    return {**result, **counts, "matrix_bytes": len(matrix_slots)}


def verify_archive(path: Path) -> dict:
    totals = Counter()
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture.json"))
        verify_coverage(manifest["rows"])
        for case in manifest["rows"]:
            name = stem(case)
            blobs = {}
            for key, suffix in [
                ("program", ".prg"),
                ("trace", ".csv"),
                ("matrix", "-matrix.bin"),
                ("graphics", "-graphics.bin"),
            ]:
                blobs[key] = archive.read(name + suffix)
                assert (
                    hashlib.sha256(blobs[key]).hexdigest() == case[key + "_sha256"]
                ), "artifact hash"
            assert blobs["program"] == guest(case["bank"], case["mode"]), (
                "guest identity"
            )
            assert archive.read(name + ".bin") == bytes([0xA5]), "completion sentinel"
            result = verify_case(
                case,
                list(csv.reader(io.StringIO(blobs["trace"].decode()))),
                blobs["matrix"],
                blobs["graphics"],
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
                        "idle_graphics",
                        "active_graphics",
                        "retained_matrix_graphics",
                        "matrix_bytes",
                    )
                }
            )
    return {"cases": 160, **totals}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(verify_archive(parser.parse_args().archive), indent=2))
