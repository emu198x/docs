"""Extract observable pin/consumption events from qualified handoff traces."""

import argparse
import itertools
import re
from pathlib import Path


def events(text: str, full_reads: bool = False) -> list[str]:
    result = []
    for line in text.splitlines():
        kind = line.split()[0]
        if kind not in {"PHASE", "BUS", "HALT", "ADDRESS", "READ", "HPOS", "GFX"}:
            continue
        fields = dict(re.findall(r"(\w+)=\s*([0-9a-f]+)", line))
        tick = int(fields["tick"])
        full = full_reads and kind in {"HALT", "READ", "HPOS", "GFX"}
        if not ((full and tick > 256) or 14000 < tick < 18000):
            continue
        if kind == "PHASE":
            values = [
                fields[key]
                for key in ("phase", "halt", "released", "drive", "noslow", "address")
            ]
            tag = "P"
        elif kind == "BUS":
            values = [
                fields[key]
                for key in ("halt", "released", "drive", "noslow", "address")
            ]
            tag = "B"
        elif kind == "HALT":
            values = [fields["level"]]
            tag = "H"
        elif kind == "ADDRESS":
            values = [fields["address"]]
            tag = "A"
        else:
            values = [
                fields["address"] if kind == "HPOS" else fields["ab"],
                fields["data"],
            ]
            tag = "R"
        result.append(f"{tick} {tag} " + " ".join(values))
    return sorted(result, key=lambda row: (int(row.split()[0]), row.split()[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    rows = [
        "# Qualified Atari7800_MiSTer 29aaacbbed127c670972c8a0a950ca82dc87e5df.",
        "# Absolute native ticks; P is pre-edge, B/H/A are post-edge, R consumes pre-edge data.",
        "# Own harness: docs plans/2026-10-10-maria-native-dma-stages/capture_vectors.py.",
    ]
    total = 0
    for slow, height, pal in itertools.product(range(2), [1, 2], range(2)):
        name = f"s{slow}-h{height}-p{pal}"
        text = (args.traces / f"{name}.log").read_text()
        if text.count("FETCH_RESULT ") != 1:
            raise RuntimeError(f"{name}: missing result")
        trace = events(text)
        if not all(any(f" {kind} " in row for row in trace) for kind in "PBHAR"):
            raise RuntimeError(f"{name}: incomplete trace")
        rows.extend([f"CASE {slow} {height} {pal}", *trace])
        total += len(trace)
    args.fixture.write_text("\n".join(rows) + "\n")
    print(f"CASES=8 EVENTS={total}")


if __name__ == "__main__":
    main()
