"""Observe CPU PRA bank writes during native sprite DMA with seeded banks."""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS, digest
from fetch_trace_baseline import execute
from sprite_fetch import pattern
from verify_fetch_trace import verify


def pointer(bank: int, sprite: int) -> int:
    return 0x80 + (sprite + bank) % 8


def guest(old: int, new: int, sprite: int, delay: int, phase: int) -> bytes:
    assert old in range(4) and new in range(4) and sprite in range(8)
    assert delay in range(64) and phase in (0, 3)
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
        (0xDD00, 3 - old),
    ]:
        store(address, value)
    absolute(0xAD, 0xDD0D)
    for s in range(8):
        store(0xD000 + 2 * s, 48 + 24 * s)
        store(0xD001 + 2 * s, 80)
        store(0xD027 + s, s + 1)
        for bank in range(4):
            store(bank * 0x4000 + 0x7F8 + s, pointer(bank, s))
            code.extend([0xA2, 0, 0xA9, pattern(bank, s, 0)])
            loop = len(code)
            absolute(0x9D, bank * 0x4000 + 0x2000 + s * 64)
            code.extend([0x18, 0x69, 37, 0xE8, 0xE0, 64])
            branch(0xD0, loop)
    store(0xD015, 1 << sprite)
    wait_line(72)
    store(0x02FF, 0xA5)
    wait_line(90)
    if phase:
        code.extend([0x24, 0])
    code.extend([0xEA] * delay)
    store(0xDD00, 3 - new)
    wait_line(112)
    store(0x02FF, 0)
    store(0x02FE, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    assert len(code) < 0x1800
    return bytes([0, 8]) + code


def stem(c: dict) -> str:
    return f"{c['model']}-glue{c['glue']}-{c['old']}-{c['new']}-sprite{c['sprite']}-delay{c['delay']:02d}-phase{c['phase']}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "data", "roms", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["pal"])
    parser.add_argument("--glues", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--old", nargs="+", type=int, default=[1])
    parser.add_argument("--new", nargs="+", type=int, default=[2])
    parser.add_argument("--sprites", nargs="+", type=int, default=[0])
    parser.add_argument("--delays", nargs="+", type=int, default=list(range(15, 24)))
    parser.add_argument("--phases", nargs="+", type=int, default=[0, 3])
    args = parser.parse_args()
    for values, allowed in [
        (args.models, [m for m, _, _ in MODELS]),
        (args.glues, (0, 1)),
        (args.old, range(4)),
        (args.new, range(4)),
        (args.sprites, range(8)),
        (args.delays, range(64)),
        (args.phases, (0, 3)),
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
        for glue, old, new, sprite, delay, phase in itertools.product(
            args.glues, args.old, args.new, args.sprites, args.delays, args.phases
        ):
            c = {
                "model": model,
                "cycles": cycles,
                "glue": glue,
                "old": old,
                "new": new,
                "sprite": sprite,
                "delay": delay,
                "phase": phase,
            }
            name = stem(c)
            program = args.output / (name + ".prg")
            program.write_bytes(guest(old, new, sprite, delay, phase))
            sentinel = args.output / (name + ".bin")
            commands = f'delete\nload "{program}" 0\nresourceget "GlueLogic"\ntrace store $dd00\nbreak store $d7ff\ng $0800\nr\nbsave "{sentinel}" 0 $02fe $02fe\n'
            for bank in range(4):
                start = bank * 0x4000 + 0x2000
                commands += f'bsave "{args.output / (name + f"-bank{bank}.bin")}" 0 ${start:04x} ${start + 511:04x}\n'
                p = bank * 0x4000 + 0x7F8
                commands += f'bsave "{args.output / (name + f"-pointers{bank}.bin")}" 0 ${p:04x} ${p + 7:04x}\n'
            log = execute(
                args,
                model,
                name,
                commands + "quit\n",
                arm_in_monitor=False,
                glue=glue,
            )
            assert f"GlueLogic={glue}" in log
            assert sentinel.read_bytes() == bytes([0xA5])
            for bank in range(4):
                assert (
                    args.output / (name + f"-bank{bank}.bin")
                ).read_bytes() == bytes(
                    pattern(bank, s, i) for s in range(8) for i in range(64)
                )
                assert (
                    args.output / (name + f"-pointers{bank}.bin")
                ).read_bytes() == bytes(pointer(bank, s) for s in range(8))
            writes = [
                [int(y), int(cycle), int(a, 16), int(t)]
                for y, cycle, a, t in re.findall("Trace store dd00" + EVENT, log)
            ]
            assert len(writes) == 2 and [w[2] for w in writes] == [
                3 - old,
                3 - new,
            ]
            trace = args.output / (name + ".csv")
            c.update(
                writes=writes,
                program_sha256=digest(program),
                trace_sha256=digest(trace),
                trace=verify(trace, cycles),
            )
            cases.append(c)
            print(name, writes[-1], flush=True)
    assert len(cases) == len(args.models) * len(args.glues) * len(args.old) * len(
        args.new
    ) * len(args.sprites) * len(args.delays) * len(args.phases)
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": cases}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
