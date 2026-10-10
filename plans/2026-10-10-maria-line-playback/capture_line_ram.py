"""Compile own line RAM probe and preserve measured playback vectors."""

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "line_ram.vvp"
    bench = Path(__file__).with_name("line_ram_tb.sv")
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "line_ram_tb",
            "-o",
            str(binary),
            str(args.qualified / "line_ram.sv"),
            str(bench),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    result = subprocess.run(
        ["vvp", str(binary)], capture_output=True, text=True, check=True
    )
    (args.output / "capture.log").write_text(result.stdout)
    if result.stdout.count("RESULT cases=32768 pixels=277504") != 1:
        raise RuntimeError("incomplete capture")
    rows = [
        row
        for row in result.stdout.splitlines()
        if row.startswith(("VECTOR ", "BOUND "))
    ]
    if len(rows) != 176 or len({row.rsplit(" ", 1)[0] for row in rows}) != 176:
        raise RuntimeError("missing or duplicate vectors")
    for row in rows:
        data = row.split()[-1]
        if len(data) != (4096 if row.startswith("VECTOR ") else 640):
            raise RuntimeError("wrong output count")
        bytes.fromhex(data)
    result = subprocess.run(
        ["vvp", str(binary), "+drop_pixel"], capture_output=True, text=True, check=False
    )
    (args.output / "negative.log").write_text(result.stdout + result.stderr)
    if result.returncode == 0 or "transparent byte erased" not in result.stdout:
        raise RuntimeError("suppressed output did not fail the reference gate")
    args.fixture.write_text(
        "# Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df, qualified line_ram.\n"
        "# VECTOR wm kangaroo palette rm: eight output pixels per byte, bytes 0..255.\n"
        "# BOUND wm rm position-index [1,158,159,160,254,255]: whole 320-pixel line.\n"
        + "\n".join(rows)
        + "\n"
    )
    print("CASES=32768 BOUNDARIES=48 PIXELS=277504 NEGATIVE=REJECTED")


if __name__ == "__main__":
    main()
