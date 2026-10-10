"""Compare native CIA reads with unchanged VICE functions, including SHIFT LOCK."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "2026-10-10-c64-keyboard-ghosting"
KEYS = {"LSHIFT": (1, 7), "SHIFTLOCK": (1, 7), "W": (1, 1), "X": (2, 7)}
# name, keys, PRA/PRB/DDRA/DDRB, joystick 1/2 pressed-bit masks.
CASES = [
    ("released", [], [0xFD, 0xFF, 2, 0], 0, 0),
    ("shift-forward", ["LSHIFT"], [0xFD, 0xFF, 2, 0], 0, 0),
    ("lock-forward", ["SHIFTLOCK"], [0xFD, 0xFF, 2, 0], 0, 0),
    ("shift-contention", ["LSHIFT"], [0xFD, 0xFF, 2, 0x80], 0, 0),
    ("lock-contention", ["SHIFTLOCK"], [0xFD, 0xFF, 2, 0x80], 0, 0),
    ("shift-reverse", ["LSHIFT"], [0xFF, 0x7F, 0, 0x80], 0, 0),
    ("lock-reverse", ["SHIFTLOCK"], [0xFF, 0x7F, 0, 0x80], 0, 0),
    ("lock-no-source", ["SHIFTLOCK"], [0xFF, 0xFF, 0, 0], 0, 0),
    ("lock-connected-highs", ["SHIFTLOCK", "W"], [0xFD, 0xFF, 2, 0x82], 0, 0),
    ("lock-other-row-low", ["SHIFTLOCK", "X"], [0xFB, 0xFF, 4, 0x80], 0, 0),
    ("lock-joystick-low", ["SHIFTLOCK", "W"], [0xFF, 0xFF, 0, 2], 0, 2),
    ("lock-cia-low", ["SHIFTLOCK", "W"], [0xFD, 0xFF, 2, 2], 0, 0),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--vice-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emulator", required=True)
    parser.add_argument("--record-baseline", action="store_true")
    parser.add_argument("--assembler", default="asm198x")
    parser.add_argument("--acme", default="acme")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    for name in ("assembler", "acme", "emulator"):
        found = shutil.which(getattr(args, name))
        assert found is not None, name
        setattr(args, name, found)
    oracle = args.output / "oracle"
    subprocess.run(
        [
            sys.executable,
            str(PREVIOUS / "reference.py"),
            "--vice-source",
            str(args.vice_source),
            "--output",
            str(oracle),
        ],
        check=True,
    )
    c_file = oracle / "vice-matrix.c"
    wrapper = c_file.read_text()
    # Change only wrapper inputs, never the extracted VICE functions.
    for old, new in (
        (
            "static int keyboard_get_shiftlock(void) { return 0; }",
            "static int shiftlock;\nstatic int keyboard_get_shiftlock(void) { return shiftlock; }",
        ),
        ("uint8_t input[14];", "uint8_t input[15];"),
        (
            "joy[0] = input[12]; joy[1] = input[13];",
            "joy[0] = input[12]; joy[1] = input[13]; shiftlock = input[14];",
        ),
    ):
        assert wrapper.count(old) == 1
        wrapper = wrapper.replace(old, new)
    source = (args.vice_source / "src/c64/c64cia1.c").read_text()
    begin = source.index("static void matrix_activate_column(")
    end = source.index("static void read_ciaicr(", begin)
    assert source[begin:end] in wrapper
    c_file.write_text(wrapper)
    binary = oracle / "vice-matrix"
    subprocess.run(
        [
            "cc",
            "-std=c99",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(c_file),
            "-o",
            str(binary),
        ],
        check=True,
    )
    helper = (
        args.samples.resolve()
        / "commodore-64/patterns/assembly/input/joystick-reading/verification/verify.py"
    )
    spec = importlib.util.spec_from_file_location("joystick_probe", helper)
    assert spec is not None and spec.loader is not None
    sample = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample)
    prg, sym = sample.RUN.build(args, args.output, (PREVIOUS / "probe.asm").read_text())
    rows = []
    for model in ("pal", "ntsc"):
        for name, keys, config, joy1, joy2 in CASES:
            matrix = [0] * 8
            for key in keys:
                row, col = KEYS[key]
                matrix[row] |= 1 << col
            expected = subprocess.run(
                [str(binary)],
                input=bytes(
                    [*matrix, *config, joy1 ^ 255, joy2 ^ 255, int("SHIFTLOCK" in keys)]
                ),
                capture_output=True,
                check=True,
            ).stdout
            assert len(expected) == 2
            dest = args.output / f"{model}-{name}"
            dest.mkdir()
            script = [
                {"action": "run_until_pc", "addr": sym["ready"]},
                {
                    "action": "input",
                    "events": [
                        *[{"Key": {"name": key, "pressed": True}} for key in keys],
                        *sample.buttons(joy1, joy2),
                    ],
                },
                {"action": "run_frames", "frames": 1},
                *[
                    {"action": "poke_byte", "addr": sym["config"] + i, "value": v}
                    for i, v in enumerate([*config, 255])
                ],
                {"action": "poke_byte", "addr": sym["request"], "value": 1},
                {"action": "run_until_pc", "addr": sym["done"]},
                {"action": "memory_read", "addr": sym["observed"], "len": 2},
            ]
            observations = sample.RUN.emu(args, dest, prg, model, script)
            reads = [r["bytes"] for r in observations if r["kind"] == "memory_read"]
            assert len(reads) == 1 and len(reads[0]) == 2
            rows.append(
                {
                    "model": model,
                    "name": name,
                    "keys": keys,
                    "config": config,
                    "joystick_pressed": [joy1, joy2],
                    "emulator": reads[0],
                    "reference": list(expected),
                }
            )
            print(model, name, reads[0], list(expected), flush=True)
    mismatches = sum(row["emulator"] != row["reference"] for row in rows)
    record = {
        "rows": rows,
        "mismatches": mismatches,
        "scope": "Native Emu198x vs compiled unchanged VICE port functions; no VICE UI or physical hardware claim.",
        "sha256": {
            str(p): sha(p)
            for p in (
                Path(__file__),
                c_file,
                args.vice_source / "src/c64/c64cia1.c",
                helper,
                PREVIOUS / "probe.asm",
                Path(args.emulator),
                Path(args.assembler),
                Path(args.acme),
                prg,
            )
        },
    }
    (args.output / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    assert len(rows) == 24
    assert bool(mismatches) == args.record_baseline, f"{mismatches} mismatches"
    print(f"{len(rows)} cases; {mismatches} mismatches")


if __name__ == "__main__":
    main()
