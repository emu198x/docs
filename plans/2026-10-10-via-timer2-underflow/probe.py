"""Generate and run a synthetic VIC-20 KERNAL measuring T2 post-underflow counting."""

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

    def sample(name: str) -> None:
        for suffix, register in [("ifr", 0x912D), ("low", 0x9128), ("high", 0x9129), ("ack", 0x912D)]:
            absolute(0xAD, register)
            if register == 0x912D:
                code.extend([0x29, 0x20])
            record(f"{name}-{suffix}")

    def wait_wrap() -> None:
        # LDX #0; DEX/BNE 256 times, repeated 52 times: over 65536 clocks.
        code.extend([0xA0, 52, 0xA2, 0, 0xCA, 0xD0, 0xFD, 0x88, 0xD0, 0xF8])

    write(0x912E, 0x7F)
    write(0x912B, 0)
    for value in [0, 1, 7, 255, 256, 65535]:
        write(0x9128, value & 255)
        write(0x9129, value >> 8)
        code.extend([0xEA] * 4)
        sample(f"N{value}-short")
        wait_wrap()
        sample(f"N{value}-first-wrap")
        # Low-latch writes and acknowledgements must not rearm interrupts.
        write(0x9128, 0x80)
        write(0x912D, 0x20)
        wait_wrap()
        sample(f"N{value}-second-wrap")
        write(0x9128, 0)
        write(0x9129, 0)
        code.extend([0xEA] * 4)
        sample(f"N{value}-restart")
    done = 0xE000 + len(code)
    absolute(0x4C, done)
    assert len(rows) == 96 and len(code) < 0x1FFA
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
            f'break exec ${done:04x}\ng $e000\nbsave "{dump}" 0 $0200 $025f\nquit\n'
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
            "2000000",
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
    print(f"{len(rows)} reads per model, matching PAL/NTSC; done=${done:04X}")
    for name, value in results["vic20pal"].items():
        print(f"{name}: ${value:02X}")


if __name__ == "__main__":
    main()
