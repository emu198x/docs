#!/usr/bin/env python3
"""Check nonempty CPC traces and the independently retained divergence edges."""

import argparse
import json
from itertools import pairwise
from pathlib import Path


def verify(path: Path) -> None:
    traces = json.loads(path.read_text())
    models = {"Cpc464", "Cpc664", "Cpc6128"}
    if set(traces) != {"0.8", "0.9"}:
        raise ValueError("both CPU versions are required")
    for version, boards in traces.items():
        if set(boards) != models:
            raise ValueError(f"{version}: all three boards are required")
        for model, rows in boards.items():
            if [row["hc"] for row in rows] != list(range(100)):
                raise ValueError(f"{version}/{model}: expected exactly 100 edges")
            for row in rows:
                if row["crtc_phase"] != (row["hc"] // 2) % 4:
                    raise ValueError("CRTC clock phase changed")
                if row["tstates"] != row["hc"] // 2:
                    raise ValueError("machine clock changed")
                if row["wait"] != (row["crtc_phase"] != 2):
                    raise ValueError("WAIT waveform changed")

    physical = [
        "pc",
        "addr",
        "input",
        "data",
        "m1",
        "mreq",
        "iorq",
        "rd",
        "wr",
        "rfsh",
        "retired",
    ]
    for model in sorted(models):
        old, new = traces["0.8"][model], traces["0.9"][model]
        for a, b in zip(old, new, strict=True):
            for key in ["hc", "crtc_phase", "tstates", "wait", "irq"]:
                if a[key] != b[key]:
                    raise ValueError(f"{model}: machine input {key} changed")
        internal = next((a["hc"] for a, b in zip(old, new) if a != b), None)
        bus = next(
            (
                a["hc"]
                for a, b in zip(old, new)
                if any(a[key] != b[key] for key in physical)
            ),
            None,
        )
        releases = []
        for rows in [old, new]:
            releases.append(
                next(
                    (
                        b["hc"]
                        for a, b in pairwise(rows)
                        if a["iorq"] and a["wr"] and not b["iorq"] and not b["wr"]
                    ),
                    None,
                )
            )
        if (internal, bus, releases) != (2, 81, [81, 87]):
            raise ValueError(f"{model}: changed divergence {internal, bus, releases}")
        print(f"{model}: internal edge 2; bus edge 81; write releases 81/87")
    print("600 edges checked; machine clocks and WAIT/IRQ inputs agree")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "trace", nargs="?", type=Path, default=Path(__file__).with_name("trace.json")
    )
    verify(parser.parse_args().trace)


if __name__ == "__main__":
    main()
