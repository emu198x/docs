"""Measure CPU clock phases with the qualified MARIA reference adapters."""

import argparse
import itertools
import re
import subprocess
from pathlib import Path


def measure(output: str, mode: int) -> list[tuple[int, int]]:
    if output.count("CLOCK_RESULT ") != 1:
        raise RuntimeError("missing or duplicate completion")
    events = [
        (int(tick), int(phase))
        for tick, phase in re.findall(r"PHASE tick=(\d+) phase=(\d+)", output)
    ]
    if len(events) < 120:
        raise RuntimeError("incomplete edge inventory")
    for before, after in itertools.pairwise(events):
        if before[1] == after[1] or after[0] - before[0] not in (4, 6):
            raise RuntimeError("invalid half-cycle")
    steady = [event for event in events if event[0] >= 300]
    intervals = {after[0] - before[0] for before, after in itertools.pairwise(steady)}
    expected = {4} if mode == 0 else {6} if mode == 1 else {4, 6}
    if intervals != expected:
        raise RuntimeError(f"wrong half-cycle inventory: {intervals} != {expected}")
    cycles = [tick for tick, phase in steady if phase == 1]
    periods = {after - before for before, after in itertools.pairwise(cycles)}
    if not periods <= {8, 10, 12}:
        raise RuntimeError(f"invalid CPU periods: {periods}")
    if mode == 4 and periods != {8, 10, 12}:
        raise RuntimeError(f"missing transition period: {periods}")
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path, help="checked run_fetch.py output")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent
    binary = args.output / "clock.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        here / "clock_tb.sv",
    ]
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "clock_tb", "-o", str(binary), *map(str, files)],
        check=False,
        capture_output=True,
        text=True,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    # Unknown selection must fail in HDL; a known but wrong divider must fail
    # the independent interval check even when simulation exits successfully.
    result = subprocess.run(
        ["vvp", str(binary), "+mode=1", "+unknown_clocks"],
        check=False,
        capture_output=True,
        text=True,
    )
    (args.output / "negative-unknown.log").write_text(result.stdout + result.stderr)
    if result.returncode == 0 or "unknown clock selection" not in result.stdout:
        raise RuntimeError("unknown-clock negative was ineffective")
    result = subprocess.run(
        ["vvp", str(binary), "+mode=1", "+force_fast"],
        capture_output=True,
        text=True,
        check=True,
    )
    try:
        measure(result.stdout, 1)
    except RuntimeError as error:
        if "wrong half-cycle inventory" not in str(error):
            raise
        (args.output / "negative-fast.log").write_text(str(error) + "\n")
    else:
        raise RuntimeError("wrong-divider negative was ineffective")
    rows = []
    for mode, pal, address in itertools.product(range(5), range(2), [0, 0x280]):
        for offset in range(12) if mode in (2, 3) else [0]:
            name = f"m{mode}-p{pal}-a{address:04x}-o{offset}"
            command = [
                "vvp",
                str(binary),
                f"+mode={mode}",
                f"+offset={offset}",
                f"+address={address:x}",
            ]
            if pal:
                command.append("+pal")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            (args.output / f"{name}.log").write_text(result.stdout)
            events = measure(result.stdout, mode)
            rows.append(
                name + " " + ",".join(f"{tick}:{phase}" for tick, phase in events)
            )
    if len(rows) != 108 or len(set(rows)) != 108:
        raise RuntimeError("incomplete matrix")
    (args.output / "vectors.txt").write_text("\n".join(rows) + "\n")
    summary = "CASES=108 PASSED=108 FAILED=0 NEGATIVES=REJECTED\n"
    (args.output / "summary.log").write_text(summary)
    print(summary, end="")


if __name__ == "__main__":
    main()
