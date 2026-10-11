"""Check the staged raster clock against its full retained device network."""

import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "2026-10-11-maria-halt-generator-handoff"
    ),
)
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-controller-clock")
)
from probe_controller_clock import core_labels
from probe_handoff import (
    ROOT,
    Pad,
    Transfer,
    circuits,
    extract,
    flatten,
    load_cells,
    require,
    run_case,
)
from trace_circuit import g


def raster_network(cells: dict) -> tuple[dict, list[int]]:
    network = extract(flatten(cells, ROOT)[0])
    require(len(network["devices"]) == 341, "unexpected raster device inventory")
    transfer = Transfer(network)
    labels = core_labels(network)
    require(labels["in1"] == labels["vdd"], "raster input 1 is not tied high")
    for phase, count in [("clk", 10), ("clkin", 12)]:
        gates = [d for d in network["devices"] if d["gate"] == labels[phase]]
        require(
            len(gates) == count and all(d["implant"] == 3 for d in gates),
            "unexpected raster phase gates",
        )
    for i in range(1, 7):
        require(
            labels[f"out{i}"] == labels[f"in{12 - i}"],
            "missing raster feedback conductor",
        )
    aliases = {**labels, "ph1": labels["clk"], "ph2": labels["clkin"]}
    for name in ["slow", "pck0"]:
        nodes = [
            int(n)
            for n, names in network["labels"].items()
            if any(s.endswith("/" + name) for s in names)
        ]
        require(len(nodes) == 1, "ambiguous raster output-stage port")
        aliases[name] = nodes[0]
    active = {n for d in network["devices"] for n in [d["gate"], *d["terminals"]]}
    phase_nodes = {
        int(n)
        for n, names in network["labels"].items()
        if any(s.endswith("/ph1") for s in names)
    } & active
    require(phase_nodes == {labels["clk"]}, "unqualified active phase-1 branch")
    network["labels"] = {}
    for name, node in aliases.items():
        network["labels"].setdefault(str(node), []).append("raster/" + name)
    network["labels"][str(aliases["pck0"])].append("raster/pad")
    return network, transfer.sampled


def replay(
    network: dict, sampled: list[int], initial: int, final: int, change: int, order: str
) -> list[dict]:
    c = Pad(network)
    # Match the staged experiment's sampled state 0 and slow value. This is
    # an explicit retained-node initial condition, not power-up qualification.
    for node, value in zip(
        sampled, [1, 1, 1, 0, 1 - initial, 0, 0, 0, 0, 0, 0], strict=True
    ):
        c.values[node] = value
    gate = [d for d in network["devices"] if c.node("slow") in d["terminals"]]
    require(len(gate) == 1, "ambiguous slow capture gate")
    held = next(n for n in gate[0]["terminals"] if n != c.node("slow"))
    c.values[held] = initial
    fixed = {"in2": 1, "in3": 1, "in4": 0}
    c.settle({"ph1": 0, "ph2": 0, "slow": initial, **fixed})
    old_ph1, old_ph2, old_slow = 0, 0, initial
    rows = []
    for step in range(240):
        ph2 = step % 2
        slow = initial if step < change else final
        if order == "data-first":
            c.settle({"ph1": old_ph1, "ph2": old_ph2, "slow": slow, **fixed})
        c.settle(
            {
                "ph1": 0,
                "ph2": 0,
                "slow": old_slow if order == "control-first" else slow,
                **fixed,
            }
        )
        if order == "control-first":
            c.settle({"ph1": 1 - ph2, "ph2": ph2, "slow": old_slow, **fixed})
        pck0 = c.settle({"ph1": 1 - ph2, "ph2": ph2, "slow": slow, **fixed})
        rows.append(
            {
                "step": step,
                "edge": c.values[c.node("out10")],
                "epck0f": c.values[c.node("out9")],
                "pck0": pck0,
            }
        )
        old_ph1, old_ph2, old_slow = 1 - ph2, ph2, slow
    return rows


def compare(actual: list[dict], expected: list[dict]) -> list[dict]:
    require(len(actual) == len(expected) == 240, "incomplete raster comparison")
    mismatches = []
    for a, b in zip(actual, expected, strict=True):
        require(a["step"] == b["step"], "raster step alignment differs")
        fields = [name for name in ["edge", "epck0f", "pck0"] if a[name] != b[name]]
        if fields:
            mismatches.append(
                {
                    "step": a["step"],
                    "fields": fields,
                    "actual": {k: a[k] for k in fields},
                    "staged": {k: b[k] for k in fields},
                }
            )
    return mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args()
    cells = load_cells(args.archive)
    parts = circuits(cells)
    network, sampled = raster_network(cells)
    results = []
    for initial, final in itertools.product([0, 1], repeat=2):
        changes = [96] if initial == final else range(96, 152)
        for change, order in itertools.product(
            changes, ["control-first", "data-first"]
        ):
            actual = replay(network, sampled, initial, final, change, order)
            staged = run_case(
                parts, initial, final, 100, change, 0, 1, slow_order=order
            )["rows"]
            diff = compare(actual, staged)
            results.append(
                {
                    "initial_slow": initial,
                    "final_slow": final,
                    "change": change,
                    "order": order,
                    "mismatches": len(diff),
                    "first_mismatches": diff[:3],
                }
            )
    require(len(results) == 228, "incomplete raster matrix")
    result = {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "cases": results,
        "matching_cases": sum(r["mismatches"] == 0 for r in results),
        "mismatching_cases": sum(r["mismatches"] > 0 for r in results),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
    if args.require_match:
        require(
            result["mismatching_cases"] == 0, "dynamic raster differs from staged clock"
        )


if __name__ == "__main__":
    main()
