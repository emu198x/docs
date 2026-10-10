"""Compare native C64 multi-key pin reads; preserve disagreements before a fix."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
KEYS = {"DELETE": (0, 0), "RETURN": (0, 1), "3": (1, 0), "W": (1, 1)}
TRIANGLE = ["RETURN", "W", "3"]
# Configuration order: PRA, PRB, DDRA, DDRB. Joystick masks use pressed bits.
CASES = [
    ("released-forward", [], [0xFE, 0xFF, 1, 0], 0, 0),
    ("return-forward", ["RETURN"], [0xFE, 0xFF, 1, 0], 0, 0),
    ("triangle-forward", TRIANGLE, [0xFE, 0xFF, 1, 0], 0, 0),
    ("triangle-forward-pa-high", TRIANGLE, [0xFE, 0xFF, 0xFF, 0], 0, 0),
    ("triangle-reverse-input-high", TRIANGLE, [0xFF, 0xFE, 0, 1], 0, 0),
    ("triangle-reverse-output-high", TRIANGLE, [0xFF, 0xFE, 0, 3], 0, 0),
    ("same-pa", ["RETURN", "W"], [0xFE, 0xFF, 1, 0], 0, 0),
    ("same-pb", ["3", "W"], [0xFF, 0xFE, 0, 1], 0, 0),
    ("one-low-against-pb-high", ["DELETE"], [0xFE, 0xFF, 1, 1], 0, 0),
    ("two-lows-against-pb-high", ["DELETE", "3"], [0xFC, 0xFF, 3, 1], 0, 0),
    ("connected-but-one-low", ["DELETE", "3"], [0xFE, 0xFF, 1, 1], 0, 0),
    ("pb-low-against-pa-high", ["DELETE"], [0xFF, 0xFE, 1, 1], 0, 0),
    ("joystick-1-chain", TRIANGLE, [0xFF, 0xFF, 0, 0], 1, 0),
    ("joystick-2-chain", TRIANGLE, [0xFF, 0xFF, 0, 0], 0, 1),
    ("joystick-1-pb-output-high", ["DELETE"], [0xFF, 0xFF, 0, 1], 1, 0),
    ("joystick-2-pb-output-high", ["DELETE"], [0xFF, 0xFF, 0, 1], 0, 1),
    ("all-inputs-no-source", TRIANGLE, [0, 0, 0, 0], 0, 0),
    ("released-reverse", [], [0xFF, 0xFE, 0, 1], 0, 0),
]


def held_keys(source: Path, target: Path, keys: list[str]) -> None:
    """Extend the pinned sample's immutable KEYBOARD 1.1 fixture to chords."""
    data = bytearray(source.read_bytes())
    assert data[:19] == b"VICE Snapshot File\x1a"
    assert data[37:50] == b"VICE Version\x1a"
    offset, matches = 58, 0
    while offset < len(data):
        assert offset + 22 <= len(data)
        size = struct.unpack_from("<I", data, offset + 18)[0]
        assert size >= 22 and offset + size <= len(data)
        if data[offset : offset + 16].split(b"\0")[0] == b"KEYBOARD":
            assert data[offset + 16 : offset + 18] == b"\1\1" and size == 118
            matrix = [0] * 24
            for key in keys:
                row, col = KEYS[key]
                matrix[row] |= 1 << col
                matrix[16 + col] |= 1 << row
            struct.pack_into("<24I", data, offset + 22, *matrix)
            matches += 1
        offset += size
    assert matches == 1
    target.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emulator", required=True)
    parser.add_argument("--record-baseline", action="store_true")
    for name, default in (
        ("assembler", "asm198x"),
        ("acme", "acme"),
        ("vice", "x64sc"),
    ):
        parser.add_argument(f"--{name}", default=default)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("assembler", "acme", "vice", "emulator"):
        found = shutil.which(getattr(args, name))
        assert found is not None, name
        setattr(args, name, found)
    helper = (
        args.samples.resolve()
        / "commodore-64/patterns/assembly/input/joystick-reading/verification/verify.py"
    )
    spec = importlib.util.spec_from_file_location("joystick_probe", helper)
    assert spec is not None and spec.loader is not None
    sample = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample)
    prg, sym = sample.RUN.build(args, args.output, (ROOT / "probe.asm").read_text())
    rows: list[dict[str, Any]] = []
    for model in ("pal", "ntsc"):
        bases = {}
        for joystick in (False, True):
            dest = args.output / f"base-{model}-{joystick}"
            dest.mkdir()
            base = dest / "base.vsf"
            sample.vice(
                args,
                dest,
                model,
                [
                    f'load "{prg}" 0',
                    f"break exec ${sym['ready']:04x}",
                    "g $0810",
                    f'dump "{base}"',
                ],
                joystick=joystick,
            )
            bases[joystick] = base
        for name, keys, config, joy1, joy2 in CASES:
            dest = args.output / f"{model}-{name}"
            dest.mkdir()
            joystick = bool(joy1 or joy2)
            config = config + [0x1F if joystick else 0xFF]
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
                    for i, v in enumerate(config)
                ],
                {"action": "poke_byte", "addr": sym["request"], "value": 1},
                {"action": "run_until_pc", "addr": sym["done"]},
                {"action": "memory_read", "addr": sym["observed"], "len": 2},
            ]
            obs = sample.RUN.emu(args, dest, prg, model, script)
            reads = [r["bytes"] for r in obs if r["kind"] == "memory_read"]
            assert len(reads) == 1
            snap = dest / "keys.vsf"
            held_keys(bases[joystick], snap, keys)
            dump = dest / "pins.bin"
            sample.vice(
                args,
                dest,
                model,
                [
                    f'undump "{snap}"',
                    *(
                        [f"jpdb 0 ${joy1 ^ 255:02x}", f"jpdb 1 ${joy2 ^ 255:02x}"]
                        if joystick
                        else []
                    ),
                    f"> ${sym['config']:04x} " + " ".join(f"{v:02x}" for v in config),
                    f"> ${sym['request']:04x} 01",
                    f"break exec ${sym['done']:04x}",
                    "x",
                    f'bsave "{dump}" 0 ${sym["observed"]:04x} ${sym["observed"] + 1:04x}',
                ],
                joystick=joystick,
            )
            reference = list(dump.read_bytes())
            assert len(reference) == 2
            row = {
                "model": model,
                "name": name,
                "keys": keys,
                "config": config,
                "joystick_pressed": [joy1, joy2],
                "emulator": reads[0],
                "reference": reference,
            }
            rows.append(row)
            print(model, name, reads[0], reference, flush=True)
    mismatches = [r for r in rows if r["emulator"] != r["reference"]]
    record = {
        "rows": rows,
        "mismatches": len(mismatches),
        "samples_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=args.samples, text=True
        ).strip(),
        "sources": {
            str(p): sample.sha(p)
            for p in (
                ROOT / "probe.asm",
                Path(__file__),
                helper,
                sample.HELPER,
                sample.RUN.HELPER,
            )
        },
        "tools": {
            name: sample.sha(Path(getattr(args, name)))
            for name in ("assembler", "acme", "vice", "emulator")
        },
        "prg_sha256": sample.sha(prg),
    }
    (args.output / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    assert len(rows) == len(CASES) * 2
    assert bool(mismatches) == args.record_baseline, f"{len(mismatches)} mismatches"
    print(f"{len(rows)} cases; {len(mismatches)} differences", flush=True)


if __name__ == "__main__":
    main()
