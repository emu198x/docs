"""Compare independent selector observers without altering reference signals."""

import argparse
import hashlib
import itertools
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-11-maria-interrupt-circuit"))
from layout_network import require
from trace_circuit import expected_row

sys.path.insert(0, str(HERE.parent / "2026-10-11-maria-nmi-selector"))
from capture_selector import fields

HASHES = [
    "2069171f3fbfdfe067fd6bdcaf355936440c5d7fbb209f065526b4685ab372a7",
    "cfa7caf057629c700ad824f9678ffa0bfeee2995701ab55fcdd4705e572c8216",
    "b055738d86d2d936044b158fb280789df04961a284687c1ff7908b01ad620704",
    "b1b7a06f61bc9ce0e43740df77658342c15c4ad251deb3f6791d59d6cc6bfa77",
    "fb0fbd9046aedbb808b1b7d5bb346a97a99277606bff1f817bccb9c8a11c43fb",
    "6578fdfae8ea0d8cc860510c12b36af96e2e32bd10d670b5b8fde9e09d695ff9",
]


def qualify_polarity(source: str) -> dict:
    terms = re.findall(
        r"assign sel\[(\d)\] = \(\(cond & 5'h([0-9a-f]+)\) == 5'h([0-9a-f]+)\);",
        source,
    )
    require(
        len(terms) == 7 and {int(t[0]) for t in terms} == set(range(7)),
        "selector term inventory",
    )
    masks = {int(i): (int(mask, 16), int(value, 16)) for i, mask, value in terms}
    recovered = json.loads(
        (HERE.parent / "2026-10-11-maria-interrupt-circuit/summary.json").read_text()
    )["truth_rows"]
    rows = [
        expected_row(*case)
        for case in itertools.product(range(4), range(2), range(2), range(2))
    ]
    require(len(rows) == 32 and recovered == rows, "recovered truth rows changed")
    mismatches = []
    for invert in [0, 1]:
        wrong = 0
        for row in rows:
            cond = (
                ((row["edge"] ^ invert) << 4)
                | ((1 - row["halt"]) << 3)
                | ((1 - row["dli"]) << 2)
                | (3 - row["state"])
            )
            bits = {i: int(cond & mask == value) for i, (mask, value) in masks.items()}
            actual = {
                "next": int(bool(bits[1] or bits[2]))
                + 2 * int(any(bits[i] for i in range(1, 6))),
                "set": bits[6],
                "reset": bits[0],
                "enable": bits[5],
            }
            wrong += any(actual[k] != row[k] for k in actual)
        mismatches.append(wrong)
    require(
        mismatches[1] == 0 and mismatches[0] > 0,
        "selector polarity qualification failed",
    )
    return {
        "rows": len(rows),
        "direct_input_mismatches": mismatches[0],
        "inverted_input_mismatches": mismatches[1],
    }


def replace_once(source: str, anchor: str, replacement: str) -> str:
    require(source.count(anchor) == 1, "ambiguous bench instrumentation")
    return source.replace(anchor, replacement)


def make_bench(base: str) -> str:
    anchor = " reg selector_nmi_n=1, last_selector_nmi_n=1;"
    result = replace_once(
        base, anchor, (HERE / "observers.sv.inc").read_text() + "\n" + anchor
    )
    anchor = "       clk_sys=1;#1;"
    result = replace_once(
        result, anchor, anchor + "\n" + (HERE / "monitor.sv.inc").read_text()
    )
    anchor = '   $display("SELECTOR_RESULT assertions=%0d releases=%0d final=%b",selector_edges,selector_releases,selector_nmi_n);'
    report = """   for(monitor_index=0;monitor_index<3;monitor_index=monitor_index+1)
     $display("EDGE_RESULT observer=%0d assertions=%0d releases=%0d final=%b samples=%0d events=%0d high=%0d",monitor_index,edge_assertions[monitor_index],edge_releases[monitor_index],observed_nmi[monitor_index],sample_count,event_count[monitor_index],event_high[monitor_index]);
"""
    return replace_once(result, anchor, report + anchor)


def parse(
    text: str, case: tuple[int, ...], *, record_cycle_failures: bool = False
) -> dict:
    _, _, height, flag, _, _ = case
    lines = text.splitlines()
    for marker in ["RESULT ", "FETCH_RESULT ", "SELECTOR_RESULT "]:
        require(
            sum(s.startswith(marker) for s in lines) == 1, "missing original outcome"
        )
    summaries = [fields(s) for s in lines if s.startswith("EDGE_RESULT ")]
    require(
        len(summaries) == 3 and {r["observer"] for r in summaries} == {0, 1, 2},
        "missing observer outcomes",
    )
    edges = [fields(s) for s in lines if s.startswith("EDGE_NMI ")]
    expected = 0 if flag == 0 else 1 + 23 // height if flag == 1 else 1
    result = {"case": list(case), "expected": expected, "observers": []}
    for observer in range(3):
        summary = next(r for r in summaries if r["observer"] == observer)
        events = [e for e in edges if e["observer"] == observer]
        assertions = [e for e in events if e["level"] == 0]
        releases = [e for e in events if e["level"] == 1]
        require(
            summary["samples"] > 1000 and summary["events"] > 100,
            "missing clock observations",
        )
        require(
            summary["assertions"] == len(assertions)
            and summary["releases"] == len(releases),
            "observer edge inventory mismatch",
        )
        require(
            len(assertions) == expected
            and len(releases) == expected
            and summary["final"] == 1,
            "wrong observer pulse inventory",
        )
        require(all(e["halt"] == 1 for e in assertions), "observer NMI during HALT")
        require(
            flag != 2 or all(e["row"] == 16 + height for e in assertions),
            "wrong observer zone",
        )
        require(
            [e["level"] for e in events] == [0, 1] * expected,
            "nonalternating observer edges",
        )
        cycle_failure = None
        if observer:
            require(
                summary["events"] == summary["high"],
                "candidate input is not a one-step pulse",
            )
            try:
                require(
                    all(e["cpu_cycles"] == 1 for e in releases),
                    "NMI pulse is not one live CPU cycle",
                )
                require(
                    all(e["same_phase"] == 1 for e in releases),
                    "NMI release has different CPU phase",
                )
            except ValueError as error:
                if not record_cycle_failures:
                    raise
                cycle_failure = str(error)
        result["observers"].append(
            {
                "observer": observer,
                "pulses": expected,
                "widths": sorted({e["width"] for e in releases}),
                "cpu_cycles": sorted({e["cpu_cycles"] for e in releases}),
                "cycle_qualification_failure": cycle_failure,
                "phase_mismatches": sum(e["same_phase"] != 1 for e in releases),
                "delays": sorted({e["delay"] for e in assertions}),
                "clock_samples": summary["samples"],
                "input_events": summary["events"],
                "input_high_samples": summary["high"],
            }
        )
    baseline = [fields(s) for s in lines if s.startswith("SELECTOR ")]
    shadow = [e for e in edges if e["observer"] == 0]
    keys = ["tick", "row", "col", "level", "halt", "delay", "width"]
    require(
        [{k: e[k] for k in keys} for e in baseline]
        == [{k: e[k] for k in keys} for e in shadow],
        "baseline edge trace differs",
    )
    return result


def capture(binary: Path, output: Path, case: tuple[int, ...]) -> dict:
    mode, width, height, flag, slow, pal = case
    args = [
        "vvp",
        str(binary),
        f"+object={mode}",
        f"+width={width}",
        f"+height={height}",
        f"+flag={flag}",
        f"+slow={slow}",
    ]
    if pal:
        args.append("+pal")
    run = subprocess.run(args, capture_output=True, text=True, check=False)
    (output / ("-".join(map(str, case)) + ".log")).write_text(run.stdout + run.stderr)
    run.check_returncode()
    return parse(run.stdout, case, record_cycle_failures=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("qualified", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = [
        args.reference / "maria.sv",
        args.reference / "video_sync.sv",
        args.qualified / "DMA.masked.sv",
        args.qualified / "control.sv",
        args.qualified / "line_ram.sv",
        HERE.parent / "2026-10-11-maria-nmi-selector/selector_tb.sv",
    ]
    for path, digest in zip(files, HASHES, strict=True):
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == digest,
            f"unqualified input {path}",
        )
    polarity = qualify_polarity(files[2].read_text())
    bench = args.output / "edge_tb.sv"
    bench.write_text(make_bench(files[-1].read_text()))
    binary = args.output / "edge.vvp"
    build = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "fetch_tb",
            "-o",
            str(binary),
            *map(str, files[:-1]),
            str(bench),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    (args.output / "build.log").write_text(build.stdout + build.stderr)
    build.check_returncode()
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
    require(len(cases) == len(set(cases)) == 816, "case inventory")
    if args.smoke:
        cases = [
            (1, 2, 1, 1, slow, pal)
            for slow, pal in itertools.product(range(2), range(2))
        ]
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(lambda c: capture(binary, args.output, c), cases):
            results.append(row)
            if len(results) % 64 == 0:
                print(f"captured {len(results)}/{len(cases)}", flush=True)
    require(len(results) == len(cases), "incomplete results")
    (args.output / "matrix.json").write_text(json.dumps(results, indent=2) + "\n")
    summary = {
        "cases": len(results),
        "smoke": args.smoke,
        "polarity": polarity,
        "observers": [
            {
                "observer": observer,
                "pulses": sum(r["observers"][observer]["pulses"] for r in results),
                "cycle_qualification_failed_cases": sum(
                    r["observers"][observer]["cycle_qualification_failure"] is not None
                    for r in results
                ),
                "phase_mismatches": sum(
                    r["observers"][observer]["phase_mismatches"] for r in results
                ),
                "widths": sorted(
                    {v for r in results for v in r["observers"][observer]["widths"]}
                ),
                "delays": sorted(
                    {v for r in results for v in r["observers"][observer]["delays"]}
                ),
            }
            for observer in range(3)
        ],
        "inputs": dict(zip(map(str, files), HASHES, strict=True)),
        "bench_sha256": hashlib.sha256(bench.read_bytes()).hexdigest(),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
