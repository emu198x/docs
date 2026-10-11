"""Trace physical phase branches and exercise the extracted NMI latch cone.

The phase sweep assumes alternating, nonoverlapping phases and constant edge
periods. It does not assign those phases to native ticks in a production chip.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-phase-handoff")
)
from connect_layout import (
    CLOCK,
    HANDOFF_WIRING,
    PHASE_BRANCHES,
    TARGETS,
    connect,
    report,
    shared_route,
)
from layout_network import extract, require
from probe_pads import Pad
from trace_circuit import PLA, check_latch, g, load_cells, truth_rows


def named_node(network: dict, name: str) -> int:
    matches = [int(n) for n, names in network["labels"].items() if name in names]
    require(len(matches) == 1, "ambiguous cone boundary " + name)
    return matches[0]


def isolate_output(network: dict, output: str, boundary: list[str]) -> dict:
    """Walk incoming channel drivers; stop at externally fixed port nodes."""
    require(
        not network.get("unmodelled_structures"), "unmodelled structures in cone source"
    )
    fixed = {named_node(network, name) for name in boundary}
    nodes = {named_node(network, output)}
    pending = list(nodes)
    selected = set()
    while pending:
        node = pending.pop()
        if node in fixed:
            continue
        for index, device in enumerate(network["devices"]):
            if node not in device["terminals"]:
                continue
            selected.add(index)
            for other in [device["gate"], *device["terminals"]]:
                if other not in nodes:
                    nodes.add(other)
                    pending.append(other)
    return {
        "devices": [network["devices"][i] for i in sorted(selected)],
        "labels": {
            n: names
            for n, names in network["labels"].items()
            if int(n) in nodes | fixed
        },
    }


def latch_cone(network: dict) -> dict:
    check_latch(network)
    cone = isolate_output(
        network, "intf", ["vdd", "vss", "ph2", "menblf", "intset", "intrst"]
    )
    require(len(cone["devices"]) == 13, "unexpected interrupt latch cone")
    output = named_node(cone, "intf")
    cone["labels"] = {
        n: ["latch/" + name for name in names] for n, names in cone["labels"].items()
    }
    cone["labels"][str(output)].append("latch/pad")
    return cone


def run_case(
    cone: dict, truth: dict, period: int, release_phase: int, dli: int
) -> dict:
    latch = Pad(cone)
    require(
        latch.settle({"ph2": 1, "intset": 0, "intrst": 0, "menblf": 1}) == 1,
        "latch disable failed",
    )
    outputs = {"next": 0, "set": 0, "reset": 0, "enable": 0}
    sampled = (0, 0, 0, 0)
    old_nmi = 1
    events = []
    cycle_steps = period * 2
    release = cycle_steps * 6 + release_phase
    for tick in range(cycle_steps * 12):
        ph2 = tick % 2
        edge = int((tick // 2) % period == 0)
        halt = int(cycle_steps * 2 <= tick < release)
        if ph2:
            sampled = (outputs["next"], dli, halt, edge)
        else:
            outputs = truth[sampled]
        nmi = latch.settle(
            {
                "ph2": ph2,
                "intset": outputs["set"],
                "intrst": outputs["reset"],
                "menblf": 0,
            }
        )
        if nmi != old_nmi:
            events.append(
                {
                    "phase_step": tick,
                    "phase": 2 if ph2 else 1,
                    "level": nmi,
                    "halt": halt,
                    "since_internal_halt_release": tick - release,
                }
            )
        old_nmi = nmi
    return {
        "period_maria_cycles": period,
        "release_phase_step": release_phase,
        "dli": dli,
        "events": events,
        "final_nmi": old_nmi,
    }


def validate_case(row: dict) -> None:
    events = row["events"]
    require(
        [e["level"] for e in events] == [0, 1] * row["dli"] and row["final_nmi"] == 1,
        "wrong phase-sweep pulse inventory",
    )
    require(all(e["phase"] == 2 for e in events), "interrupt edge outside phase 2")
    require(
        all(e["halt"] == 0 and e["since_internal_halt_release"] >= 0 for e in events),
        "interrupt before internal HALT release",
    )
    if events:
        require(
            events[1]["phase_step"] - events[0]["phase_step"]
            == 2 * row["period_maria_cycles"],
            "interrupt width differs from edge period",
        )


def phase_sweep(cells: dict) -> dict:
    latch = latch_cone(extract(g.geometry(cells[g.TARGET])))
    rows = truth_rows(extract(g.geometry(cells[PLA])))
    truth = {(r["state"], r["dli"], r["halt"], r["edge"]): r for r in rows}
    cases = [
        run_case(latch, truth, period, release, dli)
        for period in [4, 6]
        for release in range(2 * period)
        for dli in [0, 1]
    ]
    require(len(cases) == 40, "incomplete phase sweep")
    for row in cases:
        validate_case(row)
    broken = copy.deepcopy(latch)
    model = Pad(broken)
    gates = [d for d in broken["devices"] if d["gate"] == model.node("ph2")]
    require(len(gates) == 2, "unexpected NMI input sampling gates")
    for device in gates:
        device["gate"] = model.node("vdd")
    try:
        validate_case(run_case(broken, truth, 4, 0, 1))
    except ValueError as error:
        require(
            str(error) == "interrupt edge outside phase 2",
            "wrong transparent-latch negative",
        )
        failure = str(error)
    else:
        raise ValueError("transparent latch passed phase check")
    return {
        "latch_devices": len(latch["devices"]),
        "controller_truth_rows": len(rows),
        "cases": cases,
        "transparent_latch_negative": failure,
        "scope": "conditional alternating-phase/constant-period sweep; no native alignment or analogue timing claim",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cells = load_cells(args.archive)
    base = (
        list(TARGETS)
        + [
            "PADLAY_HPAD06I__",
            "PADLAY_HPAD06M__",
            "PADLAY_HPAD06__",
            "VCELL_VCELL_GINGER$LOE_HVSYNC_L",
            "VCELL_VCELL_GINGER$LOE_RLOG_LY_",
            CLOCK,
        ]
        + HANDOFF_WIRING
        + [name for name in cells if name.startswith("LARRY2_LRC_")]
    )
    network = connect(
        cells, base + PHASE_BRANCHES, single_terminal_cells=frozenset([CLOCK])
    )
    summary = report(network)
    (args.output / "network.json").write_text(json.dumps(network, indent=2) + "\n")
    incomplete = connect(cells, base, single_terminal_cells=frozenset([CLOCK]))
    failures = {}
    for clock, phase in [("n12", "ph1"), ("n13", "ph2")]:
        try:
            shared_route(
                incomplete,
                CLOCK + "::" + CLOCK + "/" + clock,
                g.TARGET + "::" + g.TARGET + "/" + phase,
            )
        except ValueError as error:
            require(
                str(error) == "missing physical port route",
                "wrong missing-branch negative",
            )
            failures[phase] = str(error)
        else:
            raise ValueError("phase route unexpectedly survived missing branches")
    summary["missing_branch_negatives"] = failures
    summary["phase_sweep"] = phase_sweep(cells)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "routes": summary["verified_routes"],
                "missing_branch_negatives": failures,
                "phase_cases": len(summary["phase_sweep"]["cases"]),
                "latch_negative": summary["phase_sweep"]["transparent_latch_negative"],
            }
        )
    )


if __name__ == "__main__":
    main()
