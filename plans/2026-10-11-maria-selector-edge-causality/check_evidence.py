"""Check full case coverage, unchanged reference traces and deliberate failures."""

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

from probe_edge import parse, require

MARKERS = (
    "SETUP ",
    "HALT ",
    "NMI ",
    "WIDTH ",
    "SELECTOR ",
    "RESULT ",
    "FETCH_RESULT ",
    "SELECTOR_RESULT ",
)


def original_trace(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(MARKERS)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    matrix = json.loads((args.output / "matrix.json").read_text())
    objects = [(0, 0)] + [
        (mode, width)
        for mode in range(1, 5)
        for width in [1, 2, 8, 31 if mode == 1 else 32]
    ]
    expected = {
        (mode, width, *rest)
        for mode, width in objects
        for rest in itertools.product([1, 2, 3, 16], range(3), range(2), range(2))
    }
    require(
        len(matrix) == 816 and {tuple(r["case"]) for r in matrix} == expected,
        "incomplete case coverage",
    )
    trace_hash = hashlib.sha256()
    for row in matrix:
        case = tuple(row["case"])
        name = "-".join(map(str, case)) + ".log"
        current = (args.output / name).read_text()
        require(
            parse(current, case, record_cycle_failures=True) == row,
            "stored result differs from observed log",
        )
        old_trace = original_trace((args.baseline / name).read_text())
        require(len(old_trace) >= 50, "missing baseline observations")
        require(original_trace(current) == old_trace, "reference trace changed")
        trace_hash.update((name + "\n" + "\n".join(old_trace) + "\n").encode())
    groups = []
    for slow, pal, observer in itertools.product(range(2), range(2), range(3)):
        rows = [
            r["observers"][observer] for r in matrix if r["case"][-2:] == [slow, pal]
        ]
        require(len(rows) == 204, "incomplete region/speed group")
        groups.append(
            {
                "slow": slow,
                "pal": pal,
                "observer": observer,
                "cases": len(rows),
                "pulses": sum(r["pulses"] for r in rows),
                "widths": sorted({v for r in rows for v in r["widths"]}),
                "delays": sorted({v for r in rows for v in r["delays"]}),
                "cycle_qualification_applied": observer > 0,
                "cycle_qualification_failed_cases": sum(
                    r["cycle_qualification_failure"] is not None for r in rows
                ),
                "phase_mismatches": sum(r["phase_mismatches"] for r in rows),
            }
        )
    negatives = {}
    fixed = [
        "vvp",
        str(args.output / "edge.vvp"),
        "+object=1",
        "+width=2",
        "+height=1",
        "+flag=1",
    ]
    for control in ["wide_edge", "suppress_edge_observer"]:
        run = subprocess.run(
            [*fixed, "+" + control], capture_output=True, text=True, check=False
        )
        (args.output / (control + ".log")).write_text(run.stdout + run.stderr)
        if control == "wide_edge":
            require(
                run.returncode != 0
                and "candidate edge wider than one MARIA step" in run.stdout,
                "wide-edge control did not fail its gate",
            )
            negatives[control] = "candidate edge wider than one MARIA step"
        else:
            run.check_returncode()
            try:
                parse(run.stdout, (1, 2, 1, 1, 0, 0), record_cycle_failures=True)
            except ValueError as error:
                require(
                    str(error) == "wrong observer pulse inventory",
                    "wrong suppressed-observer failure",
                )
                negatives[control] = str(error)
            else:
                raise ValueError("suppressed observer passed the pulse inventory")
    comparison = {
        "unchanged_reference_cases": len(matrix),
        "original_trace_sha256": trace_hash.hexdigest(),
        "matrix_sha256": hashlib.sha256(
            (args.output / "matrix.json").read_bytes()
        ).hexdigest(),
        "groups": groups,
        "negative_controls": negatives,
        "cycle_qualification_failures": [
            {
                "case": r["case"],
                "observer": o["observer"],
                "failure": o["cycle_qualification_failure"],
                "mismatches": o["phase_mismatches"],
            }
            for r in matrix
            for o in r["observers"]
            if o["cycle_qualification_failure"] is not None
        ],
        "scope": "Observer-only causal comparison; physical phase alignment remains unqualified",
    }
    (args.output / "comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "unchanged_reference_cases": len(matrix),
                "groups": groups,
                "negative_controls": negatives,
            }
        )
    )


if __name__ == "__main__":
    main()
