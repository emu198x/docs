"""Observe CPU pointer writes during active native sprite DMA."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS, digest
from fetch_trace_baseline import execute
from sprite_fetch import guest as sprite_guest
from sprite_fetch import pattern
from verify_fetch_trace import verify


def guest(
    bank: int,
    sprite: int,
    delay: int,
    phase: int,
    reverse: bool,
    disable_dma: bool = False,
) -> bytes:
    assert bank in range(4) and sprite in range(8) and 0 <= delay < 64
    assert phase in {0, 3}
    mask = 1 << sprite
    original = sprite_guest(bank, mask)
    tail = bytes([0xA9, mask, 0x8D, 0x15, 0xD0, 0xAD, 0x11, 0xD0])
    assert original.count(tail) == 1
    code = bytearray(original[2 : original.index(tail)])

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

    old, new = 0x80 + sprite, 0x80 + (sprite + 1) % 8
    if reverse:
        old, new = new, old
    pointer = bank * 0x4000 + 0x07F8 + sprite
    store(pointer, old)
    store(0xD015, 0 if disable_dma else mask)
    wait_line(72)
    store(0x02FF, 0xA5)
    wait_line(90)
    if phase:
        code.extend([0x24, 0])
    code.extend([0xEA] * delay)
    store(pointer, new)
    wait_line(112)
    store(0x02FF, 0)
    store(0x02FE, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    return bytes([0, 8]) + code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ["binary", "data", "roms", "output"]:
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["pal"])
    parser.add_argument("--banks", nargs="+", type=int, default=[0])
    parser.add_argument("--sprites", nargs="+", type=int, default=[0])
    parser.add_argument("--delays", nargs="+", type=int, default=list(range(32)))
    parser.add_argument("--phase", type=int, choices=[0, 3], default=0)
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--disable-dma", action="store_true")
    args = parser.parse_args()
    assert args.models and set(args.models) <= {m for m, _, _ in MODELS}
    for values, allowed in [
        (args.banks, range(4)),
        (args.sprites, range(8)),
        (args.delays, range(64)),
    ]:
        assert (
            values and len(values) == len(set(values)) and set(values) <= set(allowed)
        )
    args.trace = True
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    cases = []
    for model, _, cycles in MODELS:
        if model not in args.models:
            continue
        for bank in args.banks:
            for sprite in args.sprites:
                for delay in args.delays:
                    stem = f"{model}-bank{bank}-sprite{sprite}-delay{delay:02d}-phase{args.phase}-reverse{int(args.reverse)}"
                    program = args.output / (stem + ".prg")
                    program.write_bytes(
                        guest(
                            bank,
                            sprite,
                            delay,
                            args.phase,
                            args.reverse,
                            args.disable_dma,
                        )
                    )
                    sentinel = args.output / (stem + ".bin")
                    ram = args.output / (stem + "-ram.bin")
                    pointer = bank * 0x4000 + 0x7F8 + sprite
                    start = bank * 0x4000 + 0x2000
                    log = execute(
                        args,
                        model,
                        stem,
                        f'delete\nload "{program}" 0\ntrace store ${pointer:04x}\nbreak store $d7ff\ng $0800\nr\n'
                        f'bsave "{sentinel}" 0 $02fe $02fe\nbsave "{ram}" 0 ${start:04x} ${start + 511:04x}\nquit\n',
                        arm_in_monitor=False,
                    )
                    assert sentinel.read_bytes() == bytes([0xA5])
                    assert ram.read_bytes() == bytes(
                        pattern(bank, s, i) for s in range(8) for i in range(64)
                    )
                    writes = [
                        [int(y), int(c), int(a, 16), int(t)]
                        for y, c, a, t in re.findall(
                            f"Trace store {pointer:04x}" + EVENT, log
                        )
                    ]
                    assert len(writes) == 3, "CPU pointer stores"
                    old, new = 0x80 + sprite, 0x80 + (sprite + 1) % 8
                    if args.reverse:
                        old, new = new, old
                    assert [w[2] for w in writes] == [0x80 + sprite, old, new]
                    trace = args.output / (stem + ".csv")
                    result = verify(trace, cycles)
                    cases.append(
                        {
                            "model": model,
                            "bank": bank,
                            "sprite": sprite,
                            "delay": delay,
                            "phase": args.phase,
                            "reverse": args.reverse,
                            "dma_enabled": not args.disable_dma,
                            "cycles": cycles,
                            "program_sha256": digest(program),
                            "trace_sha256": digest(trace),
                            "trace": result,
                            "ram": list(ram.read_bytes()),
                            "writes": writes,
                        }
                    )
                    print(stem, writes[-1], result["kinds"], flush=True)
    assert len(cases) == len(set(args.models)) * len(args.banks) * len(
        args.sprites
    ) * len(args.delays)
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": cases}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
