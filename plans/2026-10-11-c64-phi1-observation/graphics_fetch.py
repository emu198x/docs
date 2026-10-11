"""Capture seeded RAM graphics and matrix reads in all stable VIC display modes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capture import MODELS, digest
from fetch_trace_baseline import execute
from verify_fetch_trace import verify


def matrix_byte(bank: int, index: int) -> int:
    page, offset = divmod(index, 256)
    return (7 + bank * 29 + page * 61 + offset * 13) & 255


def graphics_byte(bank: int, index: int) -> int:
    page, offset = divmod(index, 256)
    return (bank * 41 + page * 17 + offset * 37) & 255


def guest(bank: int, mode: int) -> bytes:
    assert bank in range(4) and mode in range(8)
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
        branch(0x30, start)
        absolute(0xAD, 0xD012)
        code.extend([0xC9, line])
        branch(0xD0, start)

    def fill_page(address: int, seed: int, step: int) -> None:
        code.extend([0xA2, 0, 0xA9, seed])
        loop = len(code)
        absolute(0x9D, address)
        code.extend([0x18, 0x69, step, 0xE8])
        branch(0xD0, loop)

    for address, value in [
        (0x02FF, 0),
        (1, 0x35),
        (0xDC0D, 0x7F),
        (0xDD0D, 0x7F),
        (0xD015, 0),
        (0xD011, 0),
        (0xD016, 8 | ((mode & 1) << 4)),
        (0xD018, 0x18),
        (0xDD02, 3),
        (0xDD00, 3 - bank),
    ]:
        store(address, value)
    absolute(0xAD, 0xDD0D)
    base = bank * 0x4000
    for page in range(4):
        fill_page(base + 0x400 + page * 256, matrix_byte(bank, page * 256), 13)
    for page in range(32):
        fill_page(base + 0x2000 + page * 256, graphics_byte(bank, page * 256), 37)
    wait_line(0)
    store(0xD011, 0x1B | ((mode & 6) << 4))
    wait_line(40)
    store(0x02FF, 0xA5)
    wait_line(76)
    store(0x02FF, 0)
    store(0x02FE, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    assert len(code) < 0x1800
    return bytes([0, 8]) + code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ["binary", "data", "roms", "output"]:
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["pal"])
    parser.add_argument("--banks", nargs="+", type=int, default=[0])
    parser.add_argument("--modes", nargs="+", type=int, default=list(range(8)))
    args = parser.parse_args()
    assert args.models and set(args.models) <= {m for m, _, _ in MODELS}
    for values, allowed in [(args.banks, range(4)), (args.modes, range(8))]:
        assert (
            values and len(values) == len(set(values)) and set(values) <= set(allowed)
        )
    args.trace = True
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    rows = []
    for model, _, cycles in MODELS:
        if model not in args.models:
            continue
        for bank in args.banks:
            for mode in args.modes:
                stem = f"{model}-bank{bank}-mode{mode}"
                program = args.output / (stem + ".prg")
                program.write_bytes(guest(bank, mode))
                sentinel = args.output / (stem + ".bin")
                matrix = args.output / (stem + "-matrix.bin")
                graphics = args.output / (stem + "-graphics.bin")
                base = bank * 0x4000
                execute(
                    args,
                    model,
                    stem,
                    f'delete\nload "{program}" 0\nbreak store $d7ff\ng $0800\nr\n'
                    f'bsave "{sentinel}" 0 $02fe $02fe\n'
                    f'bsave "{matrix}" 0 ${base + 0x400:04x} ${base + 0x7FF:04x}\n'
                    f'bsave "{graphics}" 0 ${base + 0x2000:04x} ${base + 0x3FFF:04x}\nquit\n',
                    arm_in_monitor=False,
                )
                assert sentinel.read_bytes() == bytes([0xA5])
                assert matrix.read_bytes() == bytes(
                    matrix_byte(bank, i) for i in range(1024)
                )
                assert graphics.read_bytes() == bytes(
                    graphics_byte(bank, i) for i in range(8192)
                )
                path = args.output / (stem + ".csv")
                result = verify(path, cycles)
                rows.append(
                    {
                        "model": model,
                        "bank": bank,
                        "mode": mode,
                        "cycles": cycles,
                        "program_sha256": digest(program),
                        "trace_sha256": digest(path),
                        "matrix_sha256": digest(matrix),
                        "graphics_sha256": digest(graphics),
                        "trace": result,
                    }
                )
                print(stem, result["kinds"], flush=True)
    assert len(rows) == len(set(args.models)) * len(args.banks) * len(args.modes)
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": rows}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
