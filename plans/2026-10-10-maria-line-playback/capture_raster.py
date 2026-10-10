"""Capture full-clock playback windows without using the Rust renderer."""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> str:
    wm, rm, position, slow, pal, live = case
    name = f"w{wm}-r{rm}-h{position}-s{slow}-p{pal}-l{live}"
    command = [
        "vvp",
        str(binary),
        f"+wm={wm}",
        f"+rm={rm}",
        f"+hpos={position}",
        f"+slow={slow}",
        f"+live={live}",
    ]
    if pal:
        command.append("+pal")
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    (output / f"{name}.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    rows = [row for row in result.stdout.splitlines() if row.startswith("ROW ")]
    if len(rows) != 6:
        raise RuntimeError(f"{name}: missing rows")
    width = 368 if pal else 374
    for index, row in enumerate(rows):
        _, number, data = row.split()
        if int(number) != 16 + index or len(data) != 2 * width:
            raise RuntimeError(f"{name}: incomplete row {index}")
        bytes.fromhex(data)
    if result.stdout.count(f"RESULT pixels={6 * width} transfers=6") != 1:
        raise RuntimeError(f"{name}: incomplete capture")
    transfers = [
        row for row in result.stdout.splitlines() if row.startswith("TRANSFER ")
    ]
    if len(transfers) != 6 or len(set(transfers)) != 6:
        raise RuntimeError(f"{name}: missing transfer edges")
    registers = [
        row for row in result.stdout.splitlines() if row.startswith("REGISTER ")
    ]
    if len(registers) != 3 * live:
        raise RuntimeError(f"{name}: missing register changes")
    return (
        "CASE "
        + " ".join(map(str, case))
        + "\n"
        + "\n".join(rows + transfers + registers)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "raster.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        Path(__file__).with_name("raster_tb.sv"),
    ]
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "raster_tb", "-o", str(binary), *map(str, files)],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    cases = list(
        itertools.product(range(2), range(4), [0, 1, 158, 255], range(2), range(2), [0])
    )
    cases.extend(itertools.product(range(2), range(4), [0], range(2), range(2), [1]))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(rows) != 160 or len(set(rows)) != 160:
        raise RuntimeError("incomplete or duplicate inventory")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# CASE write-mode read-mode hpos slow pal live; rows 16..21, current viewport width.\n"
        + "\n".join(rows)
        + "\n"
    )
    print("CASES=160 ROWS=960 PIXELS=356160 LIVE_REGISTER_EVENTS=96")


if __name__ == "__main__":
    main()
