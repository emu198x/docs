"""Relate bank-3 pixels to completed-instruction native store traces."""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import re
import subprocess
from pathlib import Path

from bank_transient import guest, pixels
from capture import MODELS, digest

EVENT = r"\)\s+(\d+)/\$[0-9a-f]+,\s+(\d+)/\$[0-9a-f]+\n\.C:[^\n]+ A:([0-9A-F]{2})[^\n]*?\s+(\d+)\n"


def analyse(model: str, log: str, evidence: Path) -> dict:
    cycles = next(c for name, _, c in MODELS if name == model)
    lines = 312 if cycles == 63 else 262 if cycles == 64 else 263
    crop = 16 if cycles == 63 else 28
    frame = cycles * lines
    assert "GlueLogic=1" in log and "Unexpected token" not in log
    events = re.findall("Trace store dd00" + EVENT, log)
    assert len(events) == 8193
    rows = [[int(y), int(x), int(a, 16), int(t)] for y, x, a, t in events]
    assert rows[0][2] == 3
    assert [a for _, _, a, _ in rows[1:]] == [2, 1] * 4096
    for y, x, _, clock in rows:
        assert y == (clock // cycles) % lines and x == clock % cycles
    assert all(a[3] < b[3] for a, b in itertools.pairwise(rows))
    done = re.findall("Stop on store d7ff" + EVENT, log)
    assert len(done) == 1
    y, x, a, t = done[0]
    stop_line, stop_cycle, stop_clock = int(y), int(x), int(t)
    assert int(a, 16) == 0xA5 and stop_clock > rows[-1][3]
    assert (
        stop_line == (stop_clock // cycles) % lines
        and stop_cycle == stop_clock % cycles
    )
    # Source: c64.c machine_get_line_cycle reports maincpu_clk, not an
    # electrical sample instant. vicii_cycle_end_of_line flushes completed
    # lines; the screenshot's unfinished line still belongs to the prior frame.
    base = stop_clock - stop_line * cycles - stop_cycle
    writes = {clock for _, _, _, clock in rows[2:]}  # first 0->1 is no transient
    size, zero = pixels(evidence / f"{model}-1-2-marker00-glue1.png")
    other_size, ones = pixels(evidence / f"{model}-1-2-markerff-glue1.png")
    assert size == other_size == (384, 272 if cycles == 63 else 247)
    mask = {
        i // 3 for i in range(0, len(zero), 3) if zero[i : i + 3] != ones[i : i + 3]
    }
    cells = []
    covered = set()
    for line in range(51, 251):
        line_base = base if line < stop_line else base - frame
        for column in range(40):
            positions = {
                (line - crop) * 384 + 32 + 8 * column + bit for bit in range(8)
            }
            overlap = positions & mask
            assert not overlap or overlap == positions, "partial glyph mask"
            covered |= overlap
            # First g-access is table cycle 16. The observed store trace for
            # its affected glyph is monitor cycle 15: qualify that explicit
            # relation without equating table, monitor and emulator counters.
            store_clock = line_base + line * cycles + 15 + column
            cells.append((store_clock, bool(overlap)))
    assert covered == mask and len(cells) == 8000 and len(mask) > 0
    shifts = {
        str(offset): sum(
            actual != ((clock + offset) in writes) for clock, actual in cells
        )
        for offset in range(-2, 3)
    }
    assert shifts["0"] == 0, shifts
    assert all(shifts[str(i)] > 0 for i in (-2, -1, 1, 2)), shifts
    wide = sum(
        actual != any((clock + offset) in writes for offset in (-1, 0))
        for clock, actual in cells
    )
    assert wide > 0
    return {
        "model": model,
        "stores": len(rows),
        "glyph_cells": len(cells),
        "bank3_pixels": len(mask),
        "stop": [stop_line, stop_cycle, stop_clock],
        "shifted_clock_mismatches": shifts,
        "two_clock_window_mismatches": wide,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument(
        "--evidence", type=Path, default=Path(__file__).with_name("transient-native")
    )
    parser.add_argument("--x64sc", type=Path, default=Path("/opt/homebrew/bin/x64sc"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    (output / "empty.cfg").write_text("")
    reference = json.loads(
        gzip.decompress((args.evidence / "comparison.json.gz").read_bytes())
    )
    rows, logs = [], {}
    for model, _, _ in MODELS:
        program = output / f"{model}.prg"
        program.write_bytes(guest((1, 2), 0xFF))
        monitor, image = output / f"{model}.mon", output / f"{model}.png"
        monitor.write_text(
            f'delete\nload "{program}" 0\nresourceget "GlueLogic"\ntrace store $dd00\nbreak store $d7ff\ng $0800\nr\nscreenshot "{image}" 2\nquit\n'
        )
        cmd = [
            str(args.x64sc),
            "-config",
            str(output / "empty.cfg"),
            "-default",
            "-console",
            "-silent",
            "-sounddev",
            "dummy",
            "-warp",
            "-model",
            model,
            "-gluelogictype",
            "1",
            "-VICIIfilter",
            "0",
        ]
        for rom in ("kernal", "basic", "chargen"):
            cmd += [f"-{rom}", str(args.roms.resolve() / f"{rom}.rom")]
        cmd += [
            "-initbreak",
            "ready",
            "-limitcycles",
            "30000000",
            "-nativemonitor",
            "-moncommands",
            str(monitor),
        ]
        run = subprocess.run(cmd, capture_output=True, check=True, timeout=60)
        log = (run.stdout + run.stderr).decode(errors="replace")
        logs[model] = log
        with gzip.open(output / f"{model}.log.gz", "wt") as stream:
            stream.write(log)
        original = next(
            r
            for r in reference["captures"]
            if r["stem"] == f"{model}-1-2-markerff-glue1"
        )
        assert digest(program) == original["program_sha256"]
        assert digest(image) == original["image_sha256"], (
            "tracing changed captured image"
        )
        row = analyse(model, log, args.evidence)
        row.update(
            program_sha256=digest(program), image_sha256=digest(image), command=cmd
        )
        rows.append(row)
        print(json.dumps(row), flush=True)
    identities = {
        p.name: digest(p)
        for p in [
            args.x64sc,
            *(args.roms / f"{r}.rom" for r in ("kernal", "basic", "chargen")),
        ]
    }
    (output / "summary.json").write_text(
        json.dumps({"identities": identities, "rows": rows}, indent=2) + "\n"
    )
    with gzip.open(output / "logs.json.gz", "wt") as stream:
        json.dump(logs, stream)


if __name__ == "__main__":
    main()
