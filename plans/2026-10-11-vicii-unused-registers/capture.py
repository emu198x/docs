"""Build an original unused-register guest and verify five native VICE models."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def guest(colour_bus: bool = False) -> bytes:
    """Read all 272 decoded unused addresses before and after a write."""
    code = bytearray([0x78])  # SEI

    def absolute(opcode: int, address: int) -> None:
        code.extend([opcode, address & 255, address >> 8])

    for address, value in [
        (1, 0x37),
        (0xDC0D, 0x7F),
        (0xDD0D, 0x7F),
        (0xD011, 0),
        (0xD015, 0),
        (0x3FFF, 0x96),
    ]:
        code.extend([0xA9, value])
        absolute(0x8D, address)
    output = 0x6000
    if colour_bus:
        # Every idle/refresh/sprite-pointer Phi1 source in bank zero is 96.
        # This makes the colour-RAM upper nibble independent of raster phase.
        for address in [0xD018, 0xDD02, 0xDD00, 0xD800]:
            value = {0xD018: 0x14, 0xDD02: 3, 0xDD00: 3, 0xD800: 0x0A}[address]
            code.extend([0xA9, value])
            absolute(0x8D, address)
        code.extend([0xA2, 0, 0xA9, 0x96])  # LDX #0; LDA #96
        absolute(0x9D, 0x3F00)  # STA 3F00,X
        absolute(0x9D, 0x0700)  # STA 0700,X
        code.extend([0xE8, 0xD0, 0xF7])  # INX; BNE loop
        for _ in range(544):
            absolute(0xAD, 0xD800)
            absolute(0x8D, output)
            output += 1
    else:
        for mirror in range(16):
            for register in range(0x2F, 0x40):
                address = 0xD000 + mirror * 64 + register
                absolute(0xAD, address)
                absolute(0x8D, output)
                code.extend([0xA9, (mirror * 17 + register) & 255])
                absolute(0x8D, address)
                absolute(0xAD, address)
                absolute(0x8D, output + 1)
                output += 2
    assert output == 0x6220
    code.extend([0xA9, 0xA5])
    absolute(0x8D, output)
    absolute(0x8D, 0xD7FF)
    absolute(0x4C, 0x0800 + len(code))
    return bytes([0, 8]) + code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", default="/opt/homebrew/bin/x64sc")
    parser.add_argument("--colour-bus", action="store_true")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(exist_ok=False)
    program = root / "unused-registers.prg"
    program.write_bytes(guest(args.colour_bus))
    expected = 0x9A if args.colour_bus else 0xFF
    (root / "empty.cfg").write_text("")
    rows = []
    for model in ["pal", "c64c", "ntsc", "c64cntsc", "oldntsc"]:
        output = root / f"{model}.bin"
        monitor = root / f"{model}.mon"
        monitor.write_text(
            f'delete\nload "{program}" 0\nbreak store $d7ff\ng $0800\n'
            f'r\nbsave "{output}" 0 $6000 $6220\nquit\n'
        )
        command = [
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
            command += [f"-{name}", str(args.roms.resolve() / f"{name}.rom")]
        command += [
            "-initbreak",
            "ready",
            "-limitcycles",
            "30000000",
            "-nativemonitor",
            "-moncommands",
            str(monitor),
        ]
        result = subprocess.run(command, capture_output=True, timeout=60, check=True)
        log = (result.stdout + result.stderr).decode(errors="replace")
        (root / f"{model}.log").write_text(log)
        assert "Stop on store d7ff" in log and "Unexpected token" not in log, log[
            -2000:
        ]
        actual = output.read_bytes()
        assert len(actual) == 545 and actual[-1] == 0xA5, (model, actual)
        differences = [
            (i, value) for i, value in enumerate(actual[:-1]) if value != expected
        ]
        rows.append(
            {
                "model": model,
                "samples": 544,
                "expected": expected,
                "differences": differences,
                "sha256": hashlib.sha256(actual).hexdigest(),
                "command": command,
            }
        )
        print(model, len(differences), "differences", flush=True)
    identities = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            program,
            Path(args.x64sc),
            *(args.roms / f"{n}.rom" for n in ["kernal", "basic", "chargen"]),
        ]
    }
    (root / "comparison.json").write_text(
        json.dumps({"identities": identities, "rows": rows}, indent=2) + "\n"
    )
    assert len(rows) == 5 and all(not row["differences"] for row in rows)


if __name__ == "__main__":
    main()
