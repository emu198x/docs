"""Sweep CPU sprite enables across DMA startup in the isolated native observer."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from bank_phase import EVENT
from capture import MODELS, digest
from fetch_trace_baseline import execute
from sprite_fetch import guest as sprite_guest
from sprite_fetch import pattern
from verify_fetch_trace import verify


def guest(bank: int, delay: int, phase: int = 0) -> bytes:
    original = sprite_guest(bank, 1)
    tail = bytes.fromhex("a9 01 8d 15 d0 ad 11 d0")
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

    assert 0 <= delay < 64
    wait_line(72)
    store(0x02FF, 0xA5)
    wait_line(80)
    assert phase in {0, 3}
    if phase:
        code.extend([0x24, 0x00])  # BIT zp: three clocks select the other phase.
    code.extend([0xEA] * delay)
    store(0xD015, 1)
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
    parser.add_argument("--delays", nargs="+", type=int, default=list(range(32)))
    parser.add_argument("--monitor-stores", action="store_true")
    parser.add_argument("--phase", type=int, choices=[0, 3], default=0)
    args = parser.parse_args()
    assert set(args.models) <= {m for m, _, _ in MODELS}
    assert set(args.banks) <= set(range(4)) and args.banks
    assert len(set(args.delays)) == len(args.delays) and args.delays
    args.trace = True
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    cases = []
    for model, _, cycles in MODELS:
        if model not in args.models:
            continue
        for bank in args.banks:
            for delay in args.delays:
                stem = f"{model}-bank{bank}-delay{delay:02d}"
                program = args.output / (stem + ".prg")
                program.write_bytes(guest(bank, delay, args.phase))
                sentinel = args.output / (stem + ".bin")
                ram = args.output / (stem + "-ram.bin")
                start = bank * 0x4000 + 0x2000
                tracing = "trace store $d015\n" if args.monitor_stores else ""
                log = execute(
                    args,
                    model,
                    stem,
                    f'delete\nload "{program}" 0\n{tracing}break store $d7ff\ng $0800\nr\n'
                    f'bsave "{sentinel}" 0 $02fe $02fe\n'
                    f'bsave "{ram}" 0 ${start:04x} ${start + 63:04x}\nquit\n',
                    arm_in_monitor=False,
                )
                assert sentinel.read_bytes() == bytes([0xA5])
                assert ram.read_bytes() == bytes(pattern(bank, 0, i) for i in range(64))
                writes = [
                    [int(y), int(c), int(a, 16), int(t)]
                    for y, c, a, t in re.findall("Trace store d015" + EVENT, log)
                ]
                if args.monitor_stores:
                    assert len(writes) == 2 and [w[2] for w in writes] == [0, 1]
                path = args.output / (stem + ".csv")
                result = verify(path, cycles)
                with path.open() as stream:
                    invalid = [
                        r for r in csv.reader(stream) if r[0] in {"S0I", "S2I", "MI"}
                    ]
                cases.append(
                    {
                        "model": model,
                        "bank": bank,
                        "delay": delay,
                        "phase": args.phase,
                        "cycles": cycles,
                        "program_sha256": digest(program),
                        "trace_sha256": digest(path),
                        "trace": result,
                        "invalid": invalid,
                        "ram": list(ram.read_bytes()),
                        "writes": writes,
                    }
                )
                print(stem, result["kinds"], invalid, flush=True)
    assert len(cases) == len(set(args.models)) * len(set(args.banks)) * len(args.delays)
    (args.output / "capture.json").write_text(
        json.dumps({"binary_sha256": digest(args.binary), "rows": cases}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
