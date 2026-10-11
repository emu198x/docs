"""Trace late matrix bus ownership after CPU-created active-display badlines."""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS, digest
from fetch_trace_baseline import execute
from graphics_fetch import graphics_byte, matrix_byte
from graphics_fetch import guest as graphics_guest
from verify_fetch_trace import verify

# Calibrated CPU stores at the first requested delay and cycles 51–54.
BOUNDARIES = {
    63: ((0, 0), (14, 0), (13, 3), (15, 0), (14, 3)),
    65: ((0, 0), (17, 3), (19, 0), (18, 3), (20, 0)),
    64: ((0, 0), (14, 3), (16, 0), (15, 3), (17, 0)),
}


def guest(bank: int, delay: int, phase: int, force: bool) -> bytes:
    assert bank in range(4) and delay in range(40) and phase in (0, 3)
    original = graphics_guest(bank, 0)
    marker = bytes([0xA9, 0xA5, 0x8D, 0xFF, 0x02])
    assert original.count(marker) == 1
    code = bytearray(original[2 : original.index(marker) + len(marker)])

    def absolute(op: int, address: int) -> None:
        code.extend([op, address & 255, address >> 8])

    def store(address: int, value: int) -> None:
        code.extend([0xA9, value])
        absolute(0x8D, address)

    def branch(op: int, target: int) -> None:
        offset = target - len(code) - 2
        assert -128 <= offset <= 127
        code.extend([op, offset & 255])

    def wait(line: int) -> None:
        start = len(code)
        absolute(0xAD, 0xD011)
        branch(0x30, start)
        absolute(0xAD, 0xD012)
        code.extend([0xC9, line])
        branch(0xD0, start)

    wait(60)
    if phase:
        code.extend([0x24, 0])
    code.extend([0xEA] * delay)
    store(0xD011, 0x1C if force else 0x1B)
    wait(70)
    store(0x02FF, 0)
    store(0x02FE, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x800 + len(code))
    assert len(code) < 0x1800
    return bytes([0, 8]) + code


def stem(c: dict) -> str:
    return f"{c['model']}-bank{c['bank']}-delay{c['delay']:02d}-phase{c['phase']}-force{int(c['force'])}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for n in ("binary", "data", "roms", "output"):
        parser.add_argument("--" + n, type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["pal"])
    parser.add_argument("--banks", nargs="+", type=int, default=[0])
    parser.add_argument("--delays", nargs="+", type=int, default=list(range(24)))
    parser.add_argument("--phases", nargs="+", type=int, default=[0, 3])
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--boundary-sweep", action="store_true")
    args = parser.parse_args()
    for values, allowed in [
        (args.models, [m for m, _, _ in MODELS]),
        (args.banks, range(4)),
        (args.delays, range(40)),
        (args.phases, (0, 3)),
    ]:
        assert (
            values and len(values) == len(set(values)) and set(values) <= set(allowed)
        )
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    args.trace = True
    cases = []
    for model, _, cycles in MODELS:
        if model not in args.models:
            continue
        for bank, (delay, phase) in itertools.product(
            args.banks,
            BOUNDARIES[cycles]
            if args.boundary_sweep
            else itertools.product(args.delays, args.phases),
        ):
            c = {
                "model": model,
                "cycles": cycles,
                "bank": bank,
                "delay": delay,
                "phase": phase,
                "force": not args.control,
            }
            name = stem(c)
            program = args.output / (name + ".prg")
            program.write_bytes(guest(bank, delay, phase, not args.control))
            sentinel = args.output / (name + ".bin")
            matrix = args.output / (name + "-matrix.bin")
            graphics = args.output / (name + "-graphics.bin")
            base = bank * 0x4000
            log = execute(
                args,
                model,
                name,
                f'delete\nload "{program}" 0\ntrace store $d011\nbreak store $d7ff\ng $0800\nr\nbsave "{sentinel}" 0 $02fe $02fe\nbsave "{matrix}" 0 ${base + 0x400:04x} ${base + 0x7FF:04x}\nbsave "{graphics}" 0 ${base + 0x2000:04x} ${base + 0x3FFF:04x}\nquit\n',
                arm_in_monitor=False,
            )
            assert sentinel.read_bytes() == bytes([0xA5])
            assert matrix.read_bytes() == bytes(
                matrix_byte(bank, i) for i in range(1024)
            )
            assert graphics.read_bytes() == bytes(
                graphics_byte(bank, i) for i in range(8192)
            )
            writes = [
                [int(y), int(c), int(a, 16), int(t)]
                for y, c, a, t in re.findall("Trace store d011" + EVENT, log)
            ]
            assert len(writes) == 3 and [w[2] for w in writes] == [
                0,
                0x1B,
                0x1C if c["force"] else 0x1B,
            ]
            trace = args.output / (name + ".csv")
            c.update(
                writes=writes,
                program_sha256=digest(program),
                trace_sha256=digest(trace),
                trace=verify(trace, cycles),
                matrix_sha256=digest(matrix),
                graphics_sha256=digest(graphics),
            )
            cases.append(c)
            print(name, writes[-1], c["trace"]["kinds"], flush=True)
    assert len(cases) == len(args.models) * len(args.banks) * (
        5 if args.boundary_sweep else len(args.delays) * len(args.phases)
    )
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": cases}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
