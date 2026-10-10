"""Capture register commit edges across all MARIA CPU address mirrors."""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> str:
    target, mirror, slow, pal = case
    name = f"t{target}-m{mirror}-s{slow}-p{pal}"
    command = [
        "vvp",
        str(binary),
        f"+target={target}",
        f"+mirror={mirror}",
        f"+slow={slow}",
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
    if rows.count("RESULT writes=29 commits=29") != 1:
        raise RuntimeError(f"{name}: incomplete run")
    for kind in "GW":
        stream = [row.split() for row in events if row.split()[1] == kind]
        if len(stream) != 29:
            raise RuntimeError(f"{name}: incomplete {kind} stream")
        addresses = {
            int(row[2], 16) - (0x20 + mirror if kind == "W" else 0) for row in stream
        }
        if addresses != set(range(32)) - {4, 8, 24}:
            raise RuntimeError(f"{name}: incomplete register inventory")
        for row in stream:
            int(row[3], 16)
    return "CASE " + " ".join(map(str, case)) + "\n" + "\n".join(events)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "register.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        Path(__file__).with_name("register_tb.sv"),
    ]
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "register_tb",
            "-o",
            str(binary),
            *map(str, files),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    cases = list(
        itertools.product(
            range(11000, 11008, 2), range(0, 1024, 256), range(2), range(2)
        )
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(rows) != 64 or len(set(rows)) != 64:
        raise RuntimeError("incomplete or duplicate case inventory")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# CPU write selection W, register commit G; native ticks.\n"
        + "\n".join(rows)
        + "\n"
    )
    print("CASES=64 WRITES=1856 COMMITS=1856")


if __name__ == "__main__":
    main()
