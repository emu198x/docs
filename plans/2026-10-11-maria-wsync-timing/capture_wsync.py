"""Capture WSYNC/READY edges with variable CPU clocks and DMA ownership."""

import argparse
import itertools
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> tuple[str, str]:
    target, mirror, slow, pal, mode, burst = case
    name = "-".join(map(str, case))
    command = ["vvp", str(binary)] + [
        f"+{key}={value}"
        for key, value in zip(
            ("target", "mirror", "slow", "mode", "burst"),
            (target, mirror, slow, mode, burst),
            strict=True,
        )
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
    if sum(row.startswith("RESULT ") for row in rows) != 1:
        raise RuntimeError(f"{name}: incomplete run")
    if len([row for row in events if row.split()[1] == "W"]) != burst:
        raise RuntimeError(f"{name}: missing writes")
    ready = [row.split()[2] for row in events if row.split()[1] == "Q"]
    if (
        not ready
        or ready != [str(i % 2) for i in range(len(ready))]
        or ready[-1] != "1"
    ):
        raise RuntimeError(f"{name}: missing READY cycle")
    fields = []
    for kind in "BHPQW":
        stream = [row for row in events if row.split()[1] == kind]
        if kind in "PQW" and not stream:
            raise RuntimeError(f"{name}: missing {kind}")
        if kind in "BH" and bool(stream) != (mode != 0):
            raise RuntimeError(f"{name}: wrong DMA activity")
        value = 0xCBF29CE484222325
        for row in stream:
            for byte in (row + "\n").encode():
                value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        fields.append(f"{kind}:{len(stream)}:{value:016x}")
    header = " ".join(map(str, case))
    return header + " " + " ".join(fields), "CASE " + header + "\n" + "\n".join(events)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output / "wsync.vvp"
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        Path(__file__).with_name("wsync_tb.sv"),
    ]
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "wsync_tb",
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
            [14556, *range(15348, 15405, 8), 15436],
            range(0, 1024, 256),
            range(2),
            range(2),
            range(3),
            [1, 2],
        )
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(rows) != 960 or len(set(cases)) != 960:
        raise RuntimeError("incomplete or duplicate case inventory")
    args.fixture.write_text(
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.\n"
        "# target mirror slow pal mode burst; B/H/P/Q/W count:FNV1a.\n"
        + "\n".join(row[0] for row in rows)
        + "\n"
    )
    detailed = {
        (15372, 0, 0, 0, 0, 1),
        (15380, 256, 1, 1, 0, 2),
        (14556, 512, 0, 1, 1, 2),
        (15436, 768, 1, 0, 2, 2),
    }
    args.fixture.with_name("wsync-vectors.txt").write_text(
        "\n".join(
            row[1] for case, row in zip(cases, rows, strict=True) if case in detailed
        )
        + "\n"
    )
    print("CASES=960")


if __name__ == "__main__":
    main()
