"""Verify native sprite address/data/phase evidence, including complete coverage."""

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
from sprite_fetch import MASKS, guest, pattern
from verify_fetch_trace import verify_rows

# Zero-based raster_cycle fields from VICE 3.10 vicii-chip-model.c:
# cycle_tab_pal, cycle_tab_ntsc, cycle_tab_ntsc_old. These are not CPU
# monitor coordinates; sprite Phi2 runs before next_vicii_cycle().
POINTER_CYCLES = {
    63: (57, 59, 61, 0, 2, 4, 6, 8),
    65: (58, 60, 62, 64, 1, 3, 5, 7),
    64: (58, 60, 62, 0, 2, 4, 6, 8),
}


def verify_case(case: dict, rows: list[list[str]]) -> dict:
    cycles = {model: n for model, _, n in MODELS}[case["model"]]
    assert case["cycles"] == cycles
    bank, mask = case["bank"], case["mask"]
    assert bank in range(4) and mask in MASKS
    ram = case["ram"]
    assert ram == [
        pattern(bank, sprite, offset) for sprite in range(8) for offset in range(64)
    ], "source RAM"
    summary = verify_rows(rows, cycles)
    pointers = Counter()
    idle = Counter()
    offsets = [[] for _ in range(8)]
    clocks = [[] for _ in range(8)]
    phases = Counter()
    latch = None
    lines = set()
    for fields in rows[2:-1]:
        kind = fields[0]
        clock, line, cycle, logical, physical, data, dma, _, flags, _, _ = map(
            int, fields[1:]
        )
        assert not dma & ~mask, "disabled sprite DMA"
        assert kind in {"P1", "P2", "L1"}, "invalid ownership in ordinary capture"
        if kind == "L1":
            if latch is not None:
                assert line == latch[1] + (cycle == 1), "native line transition"
            latch = (clock, line, cycle)
            lines.add(line)
            continue
        assert physical == bank * 0x4000 + logical, "wrong physical bank"
        fetch, sprite = flags & 0xE00, (flags >> 12) & 7
        if kind == "P1" and fetch == 0x600:
            assert cycle == POINTER_CYCLES[cycles][sprite], "pointer phase"
            assert logical == 0x7F8 + sprite and data == 0x80 + sprite, "pointer source"
            pointers[sprite] += 1
            continue
        if kind == "P1" and fetch == 0x800:
            assert cycle == (POINTER_CYCLES[cycles][sprite] + 1) % cycles, (
                "middle phase"
            )
            if not dma & (1 << sprite):
                assert logical == 0x3FFF, "disabled middle source"
                idle[sprite] += 1
                continue
            byte = 1
        elif kind == "P2":
            assert fetch in {0x600, 0x800}, "unexpected Phi2 source"
            assert dma & (1 << sprite), "Phi2 without DMA"
            byte = 0 if fetch == 0x600 else 2
            expected_cycle = (POINTER_CYCLES[cycles][sprite] + (byte == 2)) % cycles
            assert cycle == expected_cycle, "Phi2 phase"
            assert latch is not None and clock == latch[0] + 1 and cycle == latch[2], (
                "Phi2 clock"
            )
            # Native raster_line advances after Phi1 cycle 0 has been logged.
            assert line == latch[1] + (cycle == 0), "Phi2 line"
        else:
            continue  # Refresh/graphics-idle bytes have separate observations.
        offset = logical - (0x2000 + 64 * sprite)
        assert 0 <= offset < 63 and offset % 3 == byte, "sprite byte position"
        assert data == ram[64 * sprite + offset], "sprite source byte"
        offsets[sprite].append(offset)
        clocks[sprite].append(clock)
        phases[kind] += 1
    assert lines == set(range(72, 113)), "incomplete line interval"
    for sprite in range(8):
        assert pointers[sprite] >= 39 and idle[sprite] >= 18, "pointer/idle coverage"
        assert offsets[sprite] == (list(range(63)) if mask & (1 << sprite) else []), (
            "DMA byte coverage"
        )
        for index, clock in enumerate(clocks[sprite]):
            row, byte = divmod(index, 3)
            # First Phi2 and next Phi1 share a native CPU clock; final Phi2
            # follows one clock later. Each three-byte row recurs next line.
            assert clock == clocks[sprite][0] + row * cycles + (byte == 2), (
                "DMA clock spacing"
            )
    return {
        **summary,
        "sprite_bytes": sum(map(len, offsets)),
        "sprite_phases": dict(phases),
    }


def verify_coverage(cases: list[dict]) -> None:
    expected = {(m, b, mask) for m, _, _ in MODELS for b in range(4) for mask in MASKS}
    actual = [(c["model"], c["bank"], c["mask"]) for c in cases]
    assert len(actual) == len(expected) and set(actual) == expected, "case coverage"


def verify_archive(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        capture = json.loads(archive.read("capture.json"))
        verify_coverage(capture["rows"])
        totals = Counter()
        for case in capture["rows"]:
            stem = f"{case['model']}-bank{case['bank']}-mask{case['mask']:02x}"
            program = archive.read(stem + ".prg")
            assert program == guest(case["bank"], case["mask"]), "guest changed"
            assert hashlib.sha256(program).hexdigest() == case["program_sha256"]
            assert archive.read(stem + ".bin") == bytes([0xA5]), "completion sentinel"
            assert archive.read(stem + "-ram.bin") == bytes(case["ram"]), (
                "native RAM dump"
            )
            payload = archive.read(stem + ".csv")
            assert hashlib.sha256(payload).hexdigest() == case["trace_sha256"]
            result = verify_case(case, list(csv.reader(io.StringIO(payload.decode()))))
            assert all(result[k] == v for k, v in case["trace"].items()), (
                "trace summary"
            )
            totals.update({k: result[k] for k in ["records", "sprite_bytes"]})
            totals.update(result["sprite_phases"])
        assert totals["sprite_bytes"] == 20_160
        return {
            "cases": len(capture["rows"]),
            **dict(totals),
            "binary_sha256": capture["binary_sha256"],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(verify_archive(parser.parse_args().archive), indent=2))
