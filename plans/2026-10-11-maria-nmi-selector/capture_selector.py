"""Observe the reference's bypassed selector latch without changing its output."""

import argparse
import hashlib
import itertools
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def fields(line: str) -> dict[str, int]:
    return {key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)}


def require_events(observed: dict[str, int], expected: int) -> None:
    if observed != {"assertions": expected, "releases": expected, "final": 1}:
        raise RuntimeError(
            f"selector inventory: expected {expected} complete pulses, got {observed}"
        )


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> dict[str, object]:
    mode, width, height, flag, slow, pal = case
    command = [
        "vvp",
        str(binary),
        f"+object={mode}",
        f"+width={width}",
        f"+height={height}",
        f"+flag={flag}",
        f"+slow={slow}",
    ]
    if pal:
        command.append("+pal")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    name = "-".join(map(str, case))
    (output / f"{name}.log").write_text(result.stdout + result.stderr)
    lines = result.stdout.splitlines()
    for marker in ["RESULT ", "FETCH_RESULT ", "SELECTOR_RESULT "]:
        if sum(line.startswith(marker) for line in lines) != 1:
            raise RuntimeError(f"{name}: incomplete result inventory")
    candidate = [fields(line) for line in lines if line.startswith("SELECTOR ")]
    actual = [fields(line) for line in lines if line.startswith("NMI ")]
    expected = 0 if flag == 0 else 1 + 23 // height if flag == 1 else 1
    assertions = [event for event in candidate if event["level"] == 0]
    releases = [event for event in candidate if event["level"] == 1]
    summary = fields(
        next(line for line in lines if line.startswith("SELECTOR_RESULT "))
    )
    if summary["assertions"] != len(assertions) or summary["releases"] != len(releases):
        raise RuntimeError(f"{name}: observer inventory disagrees with edges")
    if len(actual) != expected * 2:
        raise RuntimeError(f"{name}: active reference event inventory changed")
    return {
        "case": list(case),
        "expected": expected,
        "candidate_assertions": len(assertions),
        "candidate_releases": len(releases),
        "candidate_final": summary["final"],
        "candidate_delays": sorted({event["delay"] for event in assertions}),
        "candidate_widths": sorted({event["width"] for event in releases}),
        "assertions_during_halt": sum(event["halt"] == 0 for event in assertions),
        "wrong_single_zone": flag == 2
        and any(event["row"] != 16 + height for event in assertions),
        "active_delays": sorted(
            {event["release_delay"] for event in actual if event["level"] == 0}
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        here / "selector_tb.sv",
    ]
    expected_hashes = [
        "2069171f3fbfdfe067fd6bdcaf355936440c5d7fbb209f065526b4685ab372a7",
        "cfa7caf057629c700ad824f9678ffa0bfeee2995701ab55fcdd4705e572c8216",
        "b055738d86d2d936044b158fb280789df04961a284687c1ff7908b01ad620704",
        "b1b7a06f61bc9ce0e43740df77658342c15c4ad251deb3f6791d59d6cc6bfa77",
        "fb0fbd9046aedbb808b1b7d5bb346a97a99277606bff1f817bccb9c8a11c43fb",
    ]
    hashes = [hashlib.sha256(file.read_bytes()).hexdigest() for file in files]
    for file, actual_hash, expected_hash in zip(
        files, hashes, expected_hashes, strict=False
    ):
        if actual_hash != expected_hash:
            raise RuntimeError(f"unqualified source {file}: {actual_hash}")
    (args.output / "hashes.json").write_text(
        json.dumps(dict(zip(map(str, files), hashes, strict=True)), indent=2) + "\n"
    )
    binary = args.output / "selector.vvp"
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "fetch_tb", "-o", str(binary), *map(str, files)],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    objects = [(0, 0)] + [
        (mode, width)
        for mode in range(1, 5)
        for width in [1, 2, 8, 31 if mode == 1 else 32]
    ]
    cases = [
        (mode, width, *rest)
        for mode, width in objects
        for rest in itertools.product([1, 2, 3, 16], range(3), range(2), range(2))
    ]
    if len(cases) != 816 or len(set(cases)) != 816:
        raise RuntimeError("incomplete case inventory")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda case: capture(binary, args.output, case), cases))
    if len(results) != 816:
        raise RuntimeError("incomplete result inventory")
    (args.output / "matrix.json").write_text(json.dumps(results, indent=2) + "\n")
    mismatch = [
        row
        for row in results
        if row["candidate_assertions"] != row["expected"]
        or row["candidate_releases"] != row["expected"]
        or row["candidate_final"] != 1
        or row["wrong_single_zone"]
        or row["assertions_during_halt"]
    ]
    summary = {
        "cases": len(results),
        "candidate_inventory_mismatches": len(mismatch),
        "candidate_assertions": sum(row["candidate_assertions"] for row in results),
        "delays": sorted(
            {value for row in results for value in row["candidate_delays"]}
        ),
        "widths": sorted(
            {value for row in results for value in row["candidate_widths"]}
        ),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    # A deliberate disconnected observer must fail the event-count outcome gate.
    result = subprocess.run(
        [
            "vvp",
            str(binary),
            "+object=1",
            "+width=2",
            "+height=1",
            "+flag=1",
            "+suppress_selector",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    (args.output / "negative.log").write_text(result.stdout + result.stderr)
    observed = fields(
        next(
            line
            for line in result.stdout.splitlines()
            if line.startswith("SELECTOR_RESULT ")
        )
    )
    positive = next(row for row in results if row["case"] == [1, 2, 1, 1, 0, 0])
    require_events(
        {
            "assertions": positive["candidate_assertions"],
            "releases": positive["candidate_releases"],
            "final": positive["candidate_final"],
        },
        24,
    )
    try:
        require_events(observed, 24)
    except RuntimeError as error:
        (args.output / "negative-result.txt").write_text(str(error) + "\n")
    else:
        raise RuntimeError("suppressed observer unexpectedly passed the event gate")
    if mismatch:
        raise RuntimeError(
            f"selector event gate failed in {len(mismatch)} cases; see matrix.json"
        )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
