"""Capture native sprite fetches with unique data, isolated enables and four banks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capture import MODELS, digest
from fetch_trace_baseline import execute
from verify_fetch_trace import verify

MASKS = [0, *(1 << i for i in range(8)), 255]


def pattern(bank: int, sprite: int, offset: int) -> int:
    return (bank * 41 + sprite * 17 + offset * 37) & 255


def guest(bank: int, mask: int) -> bytes:
    assert 0 <= bank < 4 and mask in MASKS
    code = bytearray([0x78])

    def absolute(op: int, address: int) -> None:
        code.extend([op, address & 255, address >> 8])

    def store(address: int, value: int) -> None:
        code.extend([0xA9, value])
        absolute(0x8D, address)

    def branch(op: int, target: int) -> None:
        offset = target - len(code) - 2
        assert -128 <= offset <= 127
        code.extend([op, offset & 255])

    def wait_line(line: int) -> None:
        start = len(code)
        absolute(0xAD, 0xD011)
        branch(0x30, start)  # BMI: exclude raster lines 256+.
        absolute(0xAD, 0xD012)
        code.extend([0xC9, line])
        branch(0xD0, start)

    for address, value in [
        (0x02FF, 0),
        (1, 0x35),
        (0xDC0D, 0x7F),
        (0xDD0D, 0x7F),
        (0xD015, 0),
        (0xD011, 0),
        (0xD016, 8),
        (0xD018, 0x18),
        (0xD017, 0),
        (0xD01D, 0),
        (0xD01C, 0),
        (0xD010, 0),
        (0xDD02, 3),
        (0xDD00, 3 - bank),
    ]:
        store(address, value)
    absolute(0xAD, 0xDD0D)
    for sprite in range(8):
        store(bank * 0x4000 + 0x07F8 + sprite, 0x80 + sprite)
        store(0xD000 + 2 * sprite, 48 + 24 * sprite)
        store(0xD001 + 2 * sprite, 80)
        store(0xD027 + sprite, sprite + 1)
        code.extend([0xA2, 0, 0xA9, pattern(bank, sprite, 0)])
        loop = len(code)
        absolute(0x9D, bank * 0x4000 + 0x2000 + sprite * 64)
        code.extend([0x18, 0x69, 37, 0xE8, 0xE0, 64])
        branch(0xD0, loop)
    store(0xD015, mask)
    wait_line(72)
    store(0x02FF, 0xA5)
    wait_line(112)
    store(0x02FF, 0)
    store(0x02FE, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    assert len(code) < 0x1800
    return bytes([0, 8]) + code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=[m for m, _, _ in MODELS])
    parser.add_argument("--banks", nargs="+", type=int, default=list(range(4)))
    args = parser.parse_args()
    assert set(args.models) <= {m for m, _, _ in MODELS}
    assert args.banks and set(args.banks) <= set(range(4))
    args.trace = True
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    rows = []
    for model, _, cycles in MODELS:
        if model not in args.models:
            continue
        for bank in args.banks:
            for mask in MASKS:
                stem = f"{model}-bank{bank}-mask{mask:02x}"
                program = args.output / f"{stem}.prg"
                program.write_bytes(guest(bank, mask))
                sentinel = args.output / f"{stem}.bin"
                ram = args.output / f"{stem}-ram.bin"
                start = bank * 0x4000 + 0x2000
                execute(
                    args,
                    model,
                    stem,
                    f'delete\nload "{program}" 0\nbreak store $d7ff\ng $0800\nr\n'
                    f'bsave "{sentinel}" 0 $02fe $02fe\n'
                    f'bsave "{ram}" 0 ${start:04x} ${start + 511:04x}\nquit\n',
                    arm_in_monitor=False,
                )
                assert sentinel.read_bytes() == bytes([0xA5])
                expected = bytes(
                    pattern(bank, sprite, offset)
                    for sprite in range(8)
                    for offset in range(64)
                )
                assert ram.read_bytes() == expected, "guest source RAM"
                trace = verify(args.output / f"{stem}.csv", cycles)
                rows.append(
                    {
                        "model": model,
                        "bank": bank,
                        "mask": mask,
                        "cycles": cycles,
                        "program_sha256": digest(program),
                        "ram": list(expected),
                        "trace": trace,
                        "trace_sha256": digest(args.output / f"{stem}.csv"),
                    }
                )
                print(stem, trace["records"], trace["kinds"], flush=True)
    assert len(rows) == len(set(args.models)) * len(args.banks) * len(MASKS)
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": rows}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
