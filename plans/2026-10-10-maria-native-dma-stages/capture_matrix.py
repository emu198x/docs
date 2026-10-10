"""Capture complete read/HALT streams and the detailed ownership window.

Store count plus FNV-1a of each independently observed stream to keep the
768-case fixture small. Detailed raw traces are retained in the output folder;
the eight human-readable handoff vectors provide precise edge diagnostics.
"""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from capture_vectors import events


def signature(rows: list[str], kind: str) -> str:
    selected = [row for row in rows if row.split()[1] == kind]
    value = 0xCBF29CE484222325
    for byte in "".join(row + "\n" for row in selected).encode():
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{kind}:{len(selected)}:{value:016x}"


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> str:
    mode, index, height, flag, slow, pal = case
    width = [1, 2, 8, 31 if mode == 1 else 32][index]
    name = f"o{mode}-w{width}-h{height}-f{flag}-s{slow}-p{pal}"
    command = [
        "vvp",
        str(binary),
        f"+object={mode}",
        f"+width={width}",
        f"+height={height}",
        f"+flag={flag}",
        f"+slow={slow}",
        "+trace_reads",
        "+trace_clocks",
    ]
    if pal:
        command.append("+pal")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    (output / f"{name}.log").write_text(result.stdout)
    if result.stdout.count("FETCH_RESULT ") != 1 or result.stdout.count("RESULT ") != 2:
        raise RuntimeError(f"{name}: missing or duplicate result")
    rows = events(result.stdout, full_reads=True)
    return (
        " ".join(map(str, [mode, width, height, flag, slow, pal]))
        + " "
        + " ".join(signature(rows, kind) for kind in "ABHPR")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="fresh checked handoff.vvp build")
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(
        itertools.product(
            range(1, 5), range(4), [1, 2, 3, 16], range(3), range(2), range(2)
        )
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(
            pool.map(lambda case: capture(args.binary, args.output, case), cases)
        )
    if len(rows) != 768 or len(set(rows)) != 768:
        raise RuntimeError("incomplete or duplicate matrix")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# All reads/HALT: ticks 257..36319; address/bus/phase: ticks 14001..17999.\n"
        "# mode width height flag slow pal kind:count:fnv1a64 ...\n"
        + "\n".join(rows)
        + "\n"
    )
    print("CASES=768 CAPTURED=768")


if __name__ == "__main__":
    main()
