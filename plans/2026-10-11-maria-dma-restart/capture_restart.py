"""Capture legal CPU CTRL writes and DMA restart at raster boundaries."""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> str:
    target, scenario, height, slow, pal, objects = case
    name = f"t{target}-c{scenario}-h{height}-s{slow}-p{pal}-o{objects}"
    command = [
        "vvp",
        str(binary),
        f"+target={target}",
        f"+scenario={scenario}",
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
    expected_writes = 2 if scenario == 0 else 1
    if sum(" W " in row for row in events) != expected_writes:
        raise RuntimeError(f"{name}: incomplete CPU writes")
    if sum(" S " in row for row in events) != expected_writes or sum(
        " C " in row for row in events
    ) not in ([0, 2] if scenario == 0 else [1]):
        raise RuntimeError(f"{name}: incomplete register delivery")
    if not all(any(f" {kind} " in row for row in events) for kind in "ABHLRSWZ"):
        raise RuntimeError(f"{name}: missing event stream")
    if rows.count(f"BASE 0003 0000 0 {0x60 if scenario == 1 else 0x40:02x}") != 1:
        raise RuntimeError(f"{name}: unexpected warm state")
    banks = [row.split() for row in events if " L " in row]
    if len(banks) != 8 or any(
        len(row) != 4 or len(row[2]) != 320 or len(row[3]) != 320 for row in banks
    ):
        raise RuntimeError(f"{name}: incomplete line RAM banks")
    for row in banks:
        if any(cell > 31 for cell in bytes.fromhex(row[2] + row[3])):
            raise RuntimeError(f"{name}: invalid line RAM cell")
    reads = sum(" R " in row for row in events)
    starts = sum(row.endswith(" H 0") for row in events)
    releases = sum(row.endswith(" H 1") for row in events)
    if (
        starts != releases
        or rows.count(
            f"RESULT reads={reads} starts={starts} releases={releases} writes={expected_writes}"
        )
        != 1
    ):
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
    binary = args.output / "restart.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        Path(__file__).with_name("restart_tb.sv"),
    ]
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "restart_tb", "-o", str(binary), *map(str, files)],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    cases = list(
        itertools.product(
            [
                edge + offset
                for edge in [14561, 15439]
                for offset in [-24, -16, -8, -4, 0, 4, 8, 16, 24]
            ],
            range(2),
            [1, 2],
            range(2),
            range(2),
            [1, 128],
        )
    )
    if len(cases) != 576 or len(set(cases)) != 576:
        raise RuntimeError("incomplete case inventory")
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(rows) != 576 or len(set(rows)) != 576:
        raise RuntimeError("incomplete or duplicate inventory")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# CASE target scenario height slow pal objects.\n"
        "# Native ticks. R consumes pre-edge data; A/B/C/H/L/S/W/Z are post-edge.\n"
        + "\n".join(rows)
        + "\n"
    )
    matrix = []
    detailed = []
    for block in rows:
        name, events = block.split("\n", 1)
        signatures = []
        for kind in "ABCHLRSWZ":
            stream = [row for row in events.splitlines() if row.split()[1] == kind]
            digest = 0xCBF29CE484222325
            for byte in "".join(row + "\n" for row in stream).encode():
                digest = ((digest ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
            signatures.append(f"{kind}:{len(stream)}:{digest:016x}")
        matrix.append(name.removeprefix("CASE ") + " " + " ".join(signatures))
        if name in {
            "CASE 15431 0 1 0 0 1",
            "CASE 15439 0 2 1 1 128",
            "CASE 14557 0 1 0 0 1",
            "CASE 14561 1 2 1 0 1",
        }:
            detailed.append(block)
    args.fixture.with_name("restart-matrix.txt").write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# target scenario height slow pal objects; native-tick event count/FNV1a, streams A B C H L R S W Z.\n"
        + "\n".join(matrix)
        + "\n"
    )
    args.fixture.with_name("restart-vectors.txt").write_text(
        "# Qualified Atari7800_MiSTer: detailed restart cases.\n"
        + "\n".join(detailed)
        + "\n"
    )
    print(f"CASES={len(rows)} EVENTS={sum(row.count(chr(10)) for row in rows)}")


if __name__ == "__main__":
    main()
