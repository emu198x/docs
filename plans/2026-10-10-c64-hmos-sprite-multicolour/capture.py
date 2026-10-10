"""Reproduce the eight native sprite-mode captures with VICE 3.10.

Requires the existing local Pillow installation, native x64sc, C64 ROMs and
VICE testbench. ROMs are read only and are not included in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--testbench", type=Path, required=True)
parser.add_argument("--roms", type=Path, required=True)
parser.add_argument("--x64sc", default="/opt/homebrew/bin/x64sc")
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(exist_ok=False)
source = args.source.resolve(strict=True)
bench = args.testbench.resolve(strict=True)
roms = args.roms.resolve(strict=True)
colours = [
    int(x.replace("_", ""), 16) & 0xFFFFFF
    for x in re.findall(
        r"0x(FF[0-9A-F_]+)", (source / "crates/mos-vic-ii/src/palette.rs").read_text()
    )
]
assert len(colours) == 16
palette = out / "indexed.vpl"
palette.write_text(
    "\n".join(f"{x >> 16:02X} {(x >> 8) & 255:02X} {x & 255:02X}" for x in colours)
    + "\n"
)
(out / "empty.cfg").write_text("")
rgb = [(x >> 16, (x >> 8) & 255, x & 255) for x in colours]


def indices(path: Path) -> bytes:
    image = Image.open(path).convert("RGB")
    assert image.size == (384, 272), (path, image.size)
    cache = {
        p: min(range(16), key=lambda i: sum((a - b) ** 2 for a, b in zip(p, rgb[i])))
        for p in set(image.get_flattened_data())
    }
    return bytes(cache[p] for p in image.get_flattened_data())


rows = []
for name in ["ss-hires-mc", "ss-hires-mc-exp", "ss-mc-hires", "ss-mc-hires-exp"]:
    for model, suffix in [("pal", ""), ("c64c", "-8565")]:
        label = name + ("-6569" if not suffix else suffix)
        prg = bench / f"spritesplit/{name}.prg"
        screenshot = out / f"{label}.png"
        monitor = out / f"{label}.mon"
        monitor.write_text(
            f'radix d\ndelete\nload "{prg}" 0\nbreak store $d7ff\ng $0815\nr\nm $d7ff $d7ff\ndelete\ntrace store $d01c\nbreak store $d7ff\ng\nr\nscreenshot "{screenshot}" 2\nquit\n'
        )
        cmd = [
            args.x64sc,
            "-config",
            str(out / "empty.cfg"),
            "-default",
            "-console",
            "-silent",
            "-sounddev",
            "dummy",
            "-warp",
            "-model",
            model,
            "-VICIIfilter",
            "0",
            "-VICIIextpal",
            "-VICIIpalette",
            str(palette),
        ]
        for setting in ["saturation", "contrast", "brightness", "gamma", "tint"]:
            cmd += [f"-VICII{setting}", "1000"]
        for kind in ["kernal", "basic", "chargen"]:
            cmd += [f"-{kind}", str(roms / f"{kind}.rom")]
        cmd += [
            "-initbreak",
            "ready",
            "-limitcycles",
            "12000000",
            "-nativemonitor",
            "-moncommands",
            str(monitor),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        log = (result.stdout + result.stderr).decode()
        (out / f"{label}.log").write_text(log)
        assert "Stop on store d7ff" in log and "Unexpected token" not in log
        actual = indices(screenshot)
        ref = bench / f"spritesplit/references/{name}.prg{suffix}.png"
        expected = indices(ref)
        mismatch = sum(a != b for a, b in zip(actual, expected, strict=True))
        rows.append(
            {
                "name": label,
                "mismatches": mismatch,
                "actual_sha256": hashlib.sha256(actual).hexdigest(),
                "reference_sha256": hashlib.sha256(expected).hexdigest(),
                "command": cmd,
                "program_sha256": hashlib.sha256(prg.read_bytes()).hexdigest(),
            }
        )
        print(label, mismatch, flush=True)
(out / "comparison.json").write_text(json.dumps(rows, indent=2) + "\n")
assert [r["mismatches"] for r in rows] == [0, 0, 0, 0, 0, 44, 0, 44]
