"""Capture clock/ownership boundaries using the qualified populated harness."""

import argparse
import itertools
import re
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent
    binary = args.output / "handoff.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        here.parent / "2026-10-10-maria-fetch-traces/fetch_tb.sv",
    ]
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "fetch_tb", "-o", str(binary), *map(str, files)],
        check=False,
        capture_output=True,
        text=True,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    count = 0
    for slow, height, pal in itertools.product(range(2), [1, 2], range(2)):
        command = [
            "vvp",
            str(binary),
            "+object=1",
            "+width=2",
            f"+slow={slow}",
            f"+height={height}",
            "+flag=1",
            "+trace_reads",
            "+trace_clocks",
        ]
        if pal:
            command.append("+pal")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout.count("FETCH_RESULT ") != 1:
            raise RuntimeError("missing or duplicate complete result")
        compact = []
        for line in result.stdout.splitlines():
            tick = re.search(r"tick=(\d+)", line)
            if (tick and 14000 < int(tick[1]) < 18000) or line.startswith(
                ("RESULT ", "FETCH_RESULT ")
            ):
                compact.append(line)
        if not any(line.startswith("BUS ") for line in compact):
            raise RuntimeError("missing ownership trace")
        if not any(line.startswith("PHASE ") for line in compact):
            raise RuntimeError("missing phase trace")
        name = f"s{slow}-h{height}-p{pal}"
        (args.output / f"{name}.log").write_text("\n".join(compact) + "\n")
        count += 1
    if count != 8:
        raise RuntimeError("incomplete inventory")
    summary = "HANDOFF_TRACES=8 COMPLETE=8\n"
    (args.output / "summary.log").write_text(summary)
    print(summary, end="")


if __name__ == "__main__":
    main()
