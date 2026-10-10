"""Capture relative fetch vectors from the qualified full-clock reference.

Compile fetch.vvp with ../2026-10-10-maria-fetch-traces/run_fetch.py first.
This captures observable timestamps/addresses, not reference implementation code.
"""

import argparse
import itertools
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, int, int]) -> str:
    mode, index, height = case
    width = [1, 2, 8, 31 if mode == 1 else 32][index]
    name = f"o{mode}-w{width}-h{height}"
    result = subprocess.run(
        [
            "vvp",
            str(binary),
            f"+object={mode}",
            f"+width={width}",
            f"+height={height}",
            "+flag=0",
            "+trace_reads",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    (output / f"{name}.log").write_text(result.stdout)
    if result.stdout.count("FETCH_RESULT ") != 1:
        raise RuntimeError(f"{name}: missing or duplicate result")
    starts = 0
    events: list[tuple[int, int]] = []
    origin = None
    for line in result.stdout.splitlines():
        if line.startswith("HALT "):
            if "level=0" in line:
                starts += 1
            elif starts == 2:
                break
        if starts != 2 or not line.startswith(("READ ", "HPOS ", "GFX ")):
            continue
        # Height-one zones fetch the upcoming descriptor during shutdown.
        # Its first-byte strobe is outside the header/graphics engine's scope.
        if "reload=180 " in line:
            break
        match = re.search(r"tick=(\d+).*? (?:ab|address)=([0-9a-f]+)", line)
        if match is None:
            raise RuntimeError(line)
        tick, address = int(match[1]), int(match[2], 16)
        if origin is None:
            origin = tick
        events.append((tick - origin + 4, address))
    expected = (
        (4 if mode == 1 else 5)
        + width * (1 if mode < 3 else (3 if mode == 4 else 2))
        + 3
    )
    if len(events) != expected or events[0] != (4, 0x1C00):
        raise RuntimeError((name, events))
    return f"{mode} {width} {height - 1} " + ",".join(
        f"{tick}:{address:04x}" for tick, address in events
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path, help="directory for raw traces")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(itertools.product(range(1, 5), range(4), [1, 2, 3, 16]))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(
            pool.map(lambda case: capture(args.binary, args.output, case), cases)
        )
    if len(rows) != 64 or len(set(rows)) != 64:
        raise RuntimeError("incomplete or duplicate vector inventory")
    header = (
        "# First populated list; times in native ticks, first header byte normalized to tick 4.\n"
        "# Reference: Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df, qualified fetch_tb.\n"
        "# mode width zone-offset tick:address,...\n"
    )
    args.fixture.write_text(header + "\n".join(rows) + "\n")
    print("CASES=64 CAPTURED=64")


if __name__ == "__main__":
    main()
