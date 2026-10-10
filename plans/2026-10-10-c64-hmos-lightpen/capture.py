"""Capture the full light-pen measurement on four native VICE 3.10 models."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--testbench", type=Path, required=True)
parser.add_argument("--roms", type=Path, required=True)
parser.add_argument("--x64sc", default="/opt/homebrew/bin/x64sc")
args = parser.parse_args()
root = args.output.resolve()
root.mkdir(exist_ok=False)
(root / "empty.cfg").write_text("")
bench = args.testbench.resolve(strict=True)
roms = args.roms.resolve(strict=True)
rows = []
for model, chip in [
    ("pal", "6569"),
    ("c64c", "8565"),
    ("ntsc", "6567"),
    ("c64cntsc", "8562r4"),
]:
    monitor = root / f"{chip}.mon"
    output = root / f"{chip}.bin"
    monitor.write_text(
        f'radix d\ndelete\nload "{bench}/split-tests/lightpen/lightpen.prg" 0\nbreak store $d7ff\ng $0815\nr\nbsave "{output}" 0 $4000 $44ff\nquit\n'
    )
    cmd = [
        args.x64sc,
        "-config",
        str(root / "empty.cfg"),
        "-default",
        "-console",
        "-silent",
        "-sounddev",
        "dummy",
        "-warp",
        "-model",
        model,
    ]
    for name in ["kernal", "basic", "chargen"]:
        cmd += [f"-{name}", str(roms / f"{name}.rom")]
    cmd += [
        "-initbreak",
        "ready",
        "-limitcycles",
        "65000000",
        "-nativemonitor",
        "-moncommands",
        str(monitor),
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=90, check=True)
    log = (r.stdout + r.stderr).decode(errors="replace")
    (root / f"{chip}.log").write_text(log)
    assert "Stop on store d7ff" in log and "Unexpected token" not in log
    actual = output.read_bytes()
    expected = (bench / f"split-tests/lightpen/dumps/dump{chip}.prg").read_bytes()[2:]
    assert len(actual) == len(expected) == 1280, (chip, len(actual))
    diffs = [
        (i, a, e)
        for i, (a, e) in enumerate(zip(actual, expected, strict=True))
        if a != e
    ]
    rows.append({"chip": chip, "differences": diffs, "command": cmd})
    print(chip, len(diffs), diffs[:8], flush=True)
(root / "comparison.json").write_text(json.dumps(rows, indent=2))
assert len(rows) == 4
for row in rows:
    assert [(i, (a - e) & 255) for i, a, e in row["differences"]] == [
        (766, 4),
        (767, 4),
    ]
