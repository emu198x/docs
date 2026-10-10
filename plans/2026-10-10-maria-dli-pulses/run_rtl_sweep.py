"""Run the diagnostic DMA harness; a failed row is not reference evidence."""

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="unmodified MiSTer DMA.sv")
    parser.add_argument(
        "output", type=Path, help="directory for logs and compiled harness"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "dma_tb.vvp"
    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "dma_tb",
            "-o",
            str(binary),
            str(Path(__file__).with_name("dma_tb.sv")),
            str(args.reference),
        ],
        check=True,
    )
    results: list[str] = []
    failures = 0
    cases = 0
    for height in (1, 2, 3, 16):
        for flag in (0, 1, 2):
            for phase in (0, 2, 4, 6):
                cases += 1
                run = subprocess.run(
                    [
                        "vvp",
                        str(binary),
                        f"+height={height}",
                        f"+flag={flag}",
                        f"+phase={phase}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                name = f"rtl-h{height}-f{flag}-p{phase}.log"
                (args.output / name).write_text(run.stdout + run.stderr)
                rows = [
                    line
                    for line in run.stdout.splitlines()
                    if line.startswith("RESULT")
                ]
                passed = run.returncode == 0 and len(rows) == 1
                if not passed:
                    failures += 1
                results.append(
                    f"height={height} flag={flag} phase={phase} exit={run.returncode} passed={passed}"
                )
    summary = f"CASES={cases} PASSED={cases - failures} FAILED={failures}"
    (args.output / "rtl-sweep.log").write_text(
        "\n".join(results) + "\n" + summary + "\n"
    )
    print(summary)
    return int(failures != 0 or cases != 48)


if __name__ == "__main__":
    raise SystemExit(main())
