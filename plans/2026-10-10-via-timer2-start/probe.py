"""Generate and run a synthetic VIC-20 KERNAL measuring T1/T2 start timing."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xvic", default="xvic")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    xvic = shutil.which(args.xvic)
    assert xvic is not None
    code = bytearray([0x78])  # SEI
    rows = []

    def lda(value: int) -> None:
        code.extend([0xA9, value])

    def absolute(op: int, address: int) -> None:
        code.extend([op, address & 255, address >> 8])

    def write(address: int, value: int) -> None:
        lda(value)
        absolute(0x8D, address)

    def record(name: str) -> None:
        absolute(0x8D, 0x0200 + len(rows))
        rows.append(name)

    write(0x912E, 0x7F)  # Disable all VIA2 IRQ enables.
    write(0x912B, 0)  # Both interval timers, no serial shift modes.
    for timer, low in [(1, 0x9124), (2, 0x9128)]:
        write(low, 0xFE)
        write(low + 1, 0xFE)
        code.extend([0xA2, 20, 0xCA, 0xD0, 0xFD])  # LDX #20; DEX/BNE loop
        absolute(0xAD, low)  # Read W+105; high byte stays FE for this delay.
        record(f"T{timer}-counter-low-W105")
        absolute(0xAD, low + 1)
        record(f"T{timer}-counter-high")
    for timer, low, mask in [(1, 0x9124, 0x40), (2, 0x9128, 0x20)]:
        for value in range(8):
            for delay in range(4):
                write(low, value)
                write(low + 1, 0)
                code.extend([0xEA] * delay)  # Each NOP delays two clocks.
                absolute(0xAD, 0x912D)
                code.extend([0x29, mask])  # AND #IRQ_Tn, without clearing it.
                record(f"T{timer}-N{value}-IFR-W{4 + 2 * delay}")
    done = 0xE000 + len(code)
    absolute(0x4C, done)
    assert len(rows) == 68 and len(code) < 0x1FFA
    kernal = bytearray([0xEA] * 8192)
    kernal[: len(code)] = code
    for vector in [0x1FFA, 0x1FFC, 0x1FFE]:
        kernal[vector : vector + 2] = bytes([0, 0xE0])
    rom = out / "probe.rom"
    rom.write_bytes(kernal)
    config = out / "empty.cfg"
    config.write_text("")
    results = {}
    for model in ["vic20pal", "vic20ntsc"]:
        dump = out / f"{model}.bin"
        monitor = out / f"{model}.mon"
        monitor.write_text(
            f'break exec ${done:04x}\ng $e000\nbsave "{dump}" 0 $0200 $0243\nquit\n'
        )
        command = [
            xvic,
            "-config",
            str(config),
            "-default",
            "-console",
            "-silent",
            "-sounddev",
            "dummy",
            "-warp",
            "-model",
            model,
            "-memory",
            "none",
            "-kernal",
            str(rom),
            "-limitcycles",
            "100000",
            "-nativemonitor",
            "-moncommands",
            str(monitor),
        ]
        result = subprocess.run(command, capture_output=True, timeout=45, check=True)
        (out / f"{model}.log").write_bytes(result.stdout + result.stderr)
        values = dump.read_bytes()
        assert len(values) == len(rows)
        results[model] = dict(zip(rows, values, strict=True))
    assert results["vic20pal"] == results["vic20ntsc"]
    (out / "reference.json").write_text(
        json.dumps(
            {
                "done": done,
                "rows": rows,
                "results": results,
                "sha256": {
                    "probe": hashlib.sha256(kernal).hexdigest(),
                    "xvic": hashlib.sha256(Path(xvic).read_bytes()).hexdigest(),
                    "generator": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(f"68 reads per model, matching PAL/NTSC; done=${done:04X}")
    for name, value in results["vic20pal"].items():
        print(f"{name}: ${value:02X}")


if __name__ == "__main__":
    main()
