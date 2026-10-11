"""Capture pinned phi1timing guests through I/O1 and colour RAM."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MODELS = [
    ("pal", "phi1timing", 63),
    ("c64c", "phi1timing", 63),
    ("ntsc", "phi1timing_ntsc", 65),
    ("c64cntsc", "phi1timing_ntsc", 65),
    ("oldntsc", "phi1timing_ntscold", 64),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def layout(program: bytes, cycles: int) -> tuple[int, int, int]:
    assert program[:2] == bytes([1, 8]) and program[-132:] == bytes(132)
    memory = program[2:]
    result = memory.index(b"?" * cycles)
    prefix = bytes([0x33, 9, 0x34, 9]) if cycles != 65 else bytes([9, 0x34, 9, 0x35])
    reference = memory.index(prefix)
    measured = len(memory) - 132
    assert (0x0801 + measured) & 255 == 0
    assert set(memory[reference : reference + cycles]) <= {7, 9, 18, *range(48, 56)}
    return result, reference, measured


def expected_bytes(reference: bytes) -> bytes:
    values = {7: 0xAA, 9: 0xFF, 18: 0x55, **{48 + i: i for i in range(8)}}
    return bytes(values[b] for b in reference)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--testbench", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", type=Path, default=Path("/opt/homebrew/bin/x64sc"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    (output / "empty.cfg").write_text("")
    rows = []
    for model, name, cycles in MODELS:
        original = (args.testbench / f"{name}.prg").read_bytes()
        assert original.count(bytes.fromhex("ad ad de")) == 1
        result_at, reference_at, measured_at = layout(original, cycles)
        reference = original[2 + reference_at : 2 + reference_at + cycles]
        expected = expected_bytes(reference)
        for endpoint in ["io1", "colour"]:
            data = (
                original
                if endpoint == "io1"
                else original.replace(
                    bytes.fromhex("ad ad de"), bytes.fromhex("ad 00 d8")
                )
            )
            stem = f"{model}-{endpoint}"
            program = output / f"{stem}.prg"
            program.write_bytes(data)
            dump = output / f"{stem}.bin"
            regs = output / f"{stem}-registers.bin"
            monitor = output / f"{stem}.mon"
            end = 0x0801 + len(original) - 3
            monitor.write_text(
                f'delete\nload "{program}" 0\nbreak store $d7ff\ng $080d\nr\nbsave "{dump}" 0 $0801 ${end:04x}\nbsave "{regs}" 0 $d020 $d020\nquit\n'
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
            ]
            for rom in ["kernal", "basic", "chargen"]:
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
            (output / f"{stem}.log").write_text(log)
            assert "Stop on store d7ff" in log and "Unexpected token" not in log
            actual = dump.read_bytes()
            assert len(actual) == len(original) - 2
            samples = actual[measured_at : measured_at + cycles]
            wanted = (
                expected
                if endpoint == "io1"
                else bytes((v & 0xF0) | 0x0E for v in expected)
            )
            differences = [
                (i, a, e)
                for i, (a, e) in enumerate(zip(samples, wanted, strict=True))
                if a != e
            ]
            if endpoint == "io1":
                assert actual[result_at : result_at + cycles] == reference, (
                    stem,
                    "translated results",
                )
            rows.append(
                {
                    "model": model,
                    "endpoint": endpoint,
                    "cycles": cycles,
                    "source_sha256": hashlib.sha256(original).hexdigest(),
                    "program_sha256": digest(program),
                    "dump_sha256": digest(dump),
                    "expected": list(wanted),
                    "actual": list(samples),
                    "differences": differences,
                    "layout": {
                        "result": result_at,
                        "reference": reference_at,
                        "measured": measured_at,
                    },
                    "command": cmd,
                }
            )
            print(stem, len(differences), "differences", flush=True)
    identities = {
        p.name: digest(p)
        for p in [
            args.x64sc,
            *(args.roms / f"{n}.rom" for n in ["kernal", "basic", "chargen"]),
            *(
                args.testbench / n
                for n in [
                    "README.txt",
                    "core.asm",
                    "phi1timing.asm",
                    "phi1timing_ntsc.asm",
                    "phi1timing_ntscold.asm",
                ]
            ),
        ]
    }
    (output / "comparison.json").write_text(
        json.dumps({"identities": identities, "rows": rows}, indent=2) + "\n"
    )
    assert len(rows) == 10 and all(not r["differences"] for r in rows)


if __name__ == "__main__":
    main()
