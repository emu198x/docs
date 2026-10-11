"""Measure the qualified reference controller input without changing the RTL."""

import argparse
import hashlib
import itertools
import json
import re
import subprocess
from pathlib import Path

from flatten_layout import require

HASHES = {
    "maria.sv": "2069171f3fbfdfe067fd6bdcaf355936440c5d7fbb209f065526b4685ab372a7",
    "video_sync.sv": "cfa7caf057629c700ad824f9678ffa0bfeee2995701ab55fcdd4705e572c8216",
    "DMA.masked.sv": "b055738d86d2d936044b158fb280789df04961a284687c1ff7908b01ad620704",
    "control.sv": "b1b7a06f61bc9ce0e43740df77658342c15c4ad251deb3f6791d59d6cc6bfa77",
    "line_ram.sv": "fb0fbd9046aedbb808b1b7d5bb346a97a99277606bff1f817bccb9c8a11c43fb",
}


def measure(output: str) -> dict:
    rows = [
        tuple(map(int, match))
        for match in re.findall(r"CLOCK_INPUT tick=(\d+) level=(\d+)", output)
    ]
    require(len(rows) >= 200, "missing clock-input observations")
    require(
        all(b[0] - a[0] == 2 for a, b in itertools.pairwise(rows)),
        "missing native-clock sample",
    )
    starts = [i for i in range(1, len(rows)) if rows[i - 1][1] == 0 and rows[i][1] == 1]
    periods = []
    widths = []
    for first, last in itertools.pairwise(starts):
        cycle = rows[first:last]
        require(cycle[0][1] == 1 and cycle[-1][1] == 0, "incomplete input cycle")
        falling = next(i for i, row in enumerate(cycle) if row[1] == 0)
        require(
            all(row[1] == 0 for row in cycle[falling:]),
            "extra transition within period",
        )
        periods.append(last - first)
        widths.append(falling)
    require(len(periods) >= 30, "missing complete input periods")
    return {
        "observations": len(rows),
        "complete_periods": len(periods),
        "period_maria_cycles": sorted(set(periods)),
        "high_maria_cycles": sorted(set(widths)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = [
        (args.reference if name in ["maria.sv", "video_sync.sv"] else args.qualified)
        / name
        for name in HASHES
    ]
    for path in files:
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == HASHES[path.name],
            f"unqualified source {path}",
        )
    original = (
        Path(__file__).resolve().parent.parent
        / "2026-10-11-maria-nmi-selector/selector_tb.sv"
    )
    bench = original.read_text()
    anchor = "       if(t>256 && mclk0)begin"
    require(bench.count(anchor) == 1, "observer insertion is ambiguous")
    injection = """       if(t>=512 && t<1024 && mclk0 && !$test$plusargs("suppress_clock_trace")) begin
         if(dut.dma_inst.PCLKEDGE!==1'b0 && dut.dma_inst.PCLKEDGE!==1'b1) $fatal(1,"unknown edge input");
         $display("CLOCK_INPUT tick=%0d level=%b",t,dut.dma_inst.PCLKEDGE);
       end
"""
    observer = args.output / "clock_input_tb.sv"
    observer.write_text(bench.replace(anchor, injection + anchor))
    binary = args.output / "clock_input.vvp"
    build = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "fetch_tb",
            "-o",
            str(binary),
            *map(str, files),
            str(observer),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(build.stdout + build.stderr)
    build.check_returncode()
    results = []
    for slow in [0, 1]:
        for pal in [0, 1]:
            command = [
                "vvp",
                str(binary),
                "+object=0",
                "+width=0",
                "+height=1",
                "+flag=0",
                f"+slow={slow}",
            ]
            if pal:
                command.append("+pal")
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            (args.output / f"{slow}-{pal}.log").write_text(
                result.stdout + result.stderr
            )
            result.check_returncode()
            row = measure(result.stdout)
            require(
                row["period_maria_cycles"] == [6 if slow else 4]
                and row["high_maria_cycles"] == [3 if slow else 2],
                "unexpected reference clock period or duty",
            )
            results.append({"slow": slow, "pal": pal, **row})
    negative = subprocess.run(
        [
            "vvp",
            str(binary),
            "+object=0",
            "+width=0",
            "+height=1",
            "+flag=0",
            "+slow=0",
            "+suppress_clock_trace",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "negative.log").write_text(negative.stdout + negative.stderr)
    negative.check_returncode()
    try:
        measure(negative.stdout)
    except ValueError as error:
        negative_message = str(error)
    else:
        raise ValueError("suppressed observation passed")
    summary = {
        "source_sha256": HASHES,
        "bench_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "observer_sha256": hashlib.sha256(observer.read_bytes()).hexdigest(),
        "cases": results,
        "negative": negative_message,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
