"""Capture repeated-object DMA cutoff against the qualified full-clock RTL."""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> str:
    mode, width, height, slow, pal, objects = case
    name = f"m{mode}-w{width}-h{height}-s{slow}-p{pal}-o{objects}"
    command = [
        "vvp",
        str(binary),
        f"+mode={mode}",
        f"+width={width}",
        f"+height={height}",
        f"+slow={slow}",
        f"+objects={objects}",
    ]
    if pal:
        command.append("+pal")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    (output / f"{name}.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    rows = result.stdout.splitlines()
    events = sorted(
        (row for row in rows if row.split()[0].isdigit()),
        key=lambda row: (int(row.split()[0]), row.split()[1]),
    )
    if sum(" H " in row for row in events) != 16:
        raise RuntimeError(f"{name}: incomplete HALT cycles")
    if not all(any(f" {kind} " in row for row in events) for kind in "ABHLRZ"):
        raise RuntimeError(f"{name}: missing event stream")
    banks = [row.split() for row in events if " L " in row]
    if len(banks) != 8 or any(
        len(row) != 4 or len(row[2]) != 320 or len(row[3]) != 320 for row in banks
    ):
        raise RuntimeError(f"{name}: incomplete line RAM banks")
    for row in banks:
        if any(cell > 31 for cell in bytes.fromhex(row[2] + row[3])):
            raise RuntimeError(f"{name}: invalid line RAM cell")
    reads = sum(" R " in row for row in events)
    if rows.count(f"RESULT reads={reads} starts=8 releases=8") != 1:
        raise RuntimeError(f"{name}: incomplete reads")
    return "CASE " + " ".join(map(str, case)) + "\n" + "\n".join(events)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "cutoff.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        Path(__file__).with_name("cutoff_tb.sv"),
    ]
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "cutoff_tb", "-o", str(binary), *map(str, files)],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    cases = [
        (mode, width, height, slow, pal, 128)
        for mode in range(1, 5)
        for width, height, slow, pal in itertools.product(
            [1, 2, 8, 31 if mode == 1 else 32], [1, 2, 3, 16], range(2), range(2)
        )
    ]
    for mode in range(1, 5):
        for width, height, slow, pal in itertools.product(
            [1, 2, 8, 31 if mode == 1 else 32], [1, 2], range(2), range(2)
        ):
            cost = (16 if mode == 1 else 20) + width * (
                6 if mode < 3 else 12 if mode == 3 else 18
            )
            edge = max(3, 836 // cost)
            for objects in range(edge - 2, edge + 3):
                cases.append((mode, width, height, slow, pal, objects))
    if len(cases) != 896 or len(set(cases)) != 896:
        raise RuntimeError("incomplete case inventory")
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(rows) != 896 or len(set(rows)) != 896:
        raise RuntimeError("incomplete or duplicate inventory")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# CASE mode width height slow pal objects.\n"
        "# Native ticks. R consumes pre-edge data; A/B/H/Z are post-edge.\n"
        + "\n".join(rows)
        + "\n"
    )
    matrix = []
    detailed = []
    for block in rows:
        name, events = block.split("\n", 1)
        signatures = []
        for kind in "ABHLRZ":
            stream = [row for row in events.splitlines() if row.split()[1] == kind]
            digest = 0xCBF29CE484222325
            for byte in ("\n".join(stream) + "\n").encode():
                digest = ((digest ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
            signatures.append(f"{kind}:{len(stream)}:{digest:016x}")
        matrix.append(name.removeprefix("CASE ") + " " + " ".join(signatures))
        if name in {
            "CASE 1 2 1 0 0 128",
            "CASE 1 31 2 1 1 128",
            "CASE 3 8 1 0 0 128",
            "CASE 4 8 2 0 0 128",
            "CASE 1 1 1 0 0 37",
            "CASE 4 8 2 1 1 4",
        }:
            detailed.append(block)
    args.fixture.with_name("cutoff-matrix.txt").write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# mode width height slow pal objects; native-tick event count/FNV1a, streams A B H L R Z.\n"
        + "\n".join(matrix)
        + "\n"
    )
    args.fixture.with_name("cutoff-vectors.txt").write_text(
        "# Qualified Atari7800_MiSTer: detailed cutoff cases.\n"
        + "\n".join(detailed)
        + "\n"
    )
    print(f"CASES={len(rows)} EVENTS={sum(row.count(chr(10)) for row in rows)}")


if __name__ == "__main__":
    main()
