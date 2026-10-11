"""Reject incomplete handoff matrices before retaining bounded observations."""

import argparse
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

from probe_handoff import require
from trace_circuit import g

FIELDS = (
    "initial_slow",
    "final_slow",
    "reset_step",
    "mode_change",
    "return_delay",
    "dli",
    "request",
    "slow_order",
)


def summarize(rows: list[dict]) -> dict:
    expected = set()
    for initial, final in itertools.product([0, 1], repeat=2):
        changes = [96] if initial == final else range(96, 152)
        expected.update(
            (initial, final, *rest)
            for rest in itertools.product(
                range(96, 108),
                changes,
                [0, 1, 2],
                [0, 1],
                ["start", "eovb"],
                ["control-first", "data-first"],
            )
        )
    keys = [tuple(row[field] for field in FIELDS) for row in rows]
    require(
        len(rows) == len(expected) == 32832
        and len(set(keys)) == len(rows)
        and set(keys) == expected,
        "incomplete or duplicate handoff matrix",
    )
    groups = defaultdict(list)
    by_key = dict(zip(keys, rows, strict=True))
    order_changes = 0
    for key, row in by_key.items():
        require(
            len(row["internal_halt_edges"]) == len(row["pad_halt_edges"]) == 2,
            "missing HALT edges in matrix",
        )
        require(len(row["nmi_edges"]) == 2 * row["dli"], "missing NMI edges in matrix")
        if row["dli"]:
            a, b = row["nmi_edges"]
            require(
                b - a == row["width"] > 0
                and a - row["internal_halt_edges"][1] == row["delay_from_internal"] > 0
                and a - row["pad_halt_edges"][1] == row["delay_from_pad"] > 0,
                "inconsistent handoff edge measurements",
            )
        group = (
            row["initial_slow"],
            row["final_slow"],
            row["return_delay"],
            row["slow_order"],
        )
        groups[group].append(row)
        if key[-1] == "control-first":
            other = by_key[(*key[:-1], "data-first")]
            order_changes += any(
                row[k] != other[k]
                for k in ["internal_halt_edges", "pad_halt_edges", "nmi_edges"]
            )
    summaries = []
    for key, cases in sorted(groups.items()):
        pulses = [row for row in cases if row["dli"]]
        summaries.append(
            {
                "initial_slow": key[0],
                "final_slow": key[1],
                "return_delay": key[2],
                "slow_order": key[3],
                "cases": len(cases),
                "pulses": len(pulses),
                **{
                    field: dict(sorted(Counter(row[field] for row in pulses).items()))
                    for field in ["width", "delay_from_internal", "delay_from_pad"]
                },
            }
        )
    return {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "cases": len(rows),
        "pulses": sum(row["dli"] for row in rows),
        "matrix_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "order_pairs_with_changed_edges": order_changes,
        "groups": summaries,
        "scope": "conditional half-phase coordinates; no measured CPU return delay, native alignment or production revision",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = summarize(json.loads(args.matrix.read_text())["cases"])
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "groups"}))


if __name__ == "__main__":
    main()
