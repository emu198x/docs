"""Qualify the handoff's sampled stages and deliberately break their gates."""

import argparse
import copy
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-phase-handoff")
)
from connect_layout import report
from probe_handoff import (
    Pad,
    check_case,
    circuits,
    isolate_output,
    load_cells,
    model,
    named_node,
    require,
    run_case,
)


def clock_checks(network: dict) -> list[dict]:
    rows = []
    for initial in [0, 1]:
        clock = model(network, "pck0")
        clock.settle({"ph2": 1, "epck0f": 0, "slow": initial})
        sampled_edge, sampled_slow = 0, initial
        old_slow = initial
        inputs = list(itertools.product([0, 1], repeat=3))
        for ph2, edge, slow in inputs + inputs[::-1]:
            # Establish the gate level before changing its data. Simultaneous
            # closure/data changes are a setup/hold question, not this check.
            clock.settle({"ph2": ph2, "epck0f": edge, "slow": old_slow})
            if ph2:
                sampled_edge = edge
            if not edge:
                sampled_slow = slow
            out = clock.settle({"ph2": ph2, "epck0f": edge, "slow": slow})
            old_slow = slow
            actual_slowf = clock.values[clock.node("slowf")]
            require(out == 1 - sampled_edge, "PCLK0 sampling mismatch")
            require(actual_slowf == 1 - sampled_slow, "slow latch sampling mismatch")
            rows.append(
                {
                    "initial": initial,
                    "ph2": ph2,
                    "epck0f": edge,
                    "slow": slow,
                    "pck0": out,
                    "slowf": actual_slowf,
                }
            )
    require(len(rows) == 32, "incomplete clock stage checks")
    return rows


def pad_clock(network: dict) -> dict:
    # Retain only this unit cell's devices, with actual placed-node identity.
    # Other cells' unsupported clock structures cannot be silently modelled.
    report(network)
    cell = "VCELL_VCELL_GINGER$LOE_HVSYNC_L"
    require(
        not any(d["cell"] == cell for d in network["unmodelled_structures"]),
        "unmodelled pad-clock driver",
    )
    devices = [d for d in network["devices"] if d["cell"] == cell]
    require(len(devices) == 885, "unexpected pad-clock cell inventory")
    labels = {
        str(
            named_node(
                network,
                (cell + "::" + cell + "/" if name in ["vdd", "vss"] else "TOP/") + name,
            )
        ): [name]
        for name in ["vdd", "vss", "pck2", "pck2f"]
    }
    cone = isolate_output(
        {"devices": devices, "labels": labels}, "pck2f", ["vdd", "vss", "pck2"]
    )
    require(len(cone["devices"]) == 4, "unexpected PCLK2 inverter cone")
    inverter = model(cone, "pck2f")
    rows = []
    for value in [0, 1, 1, 0, 0, 1]:
        out = inverter.settle({"pck2": value})
        require(out == 1 - value, "HALT pad clock inversion mismatch")
        rows.append({"pck2": value, "pck2f": out})
    broken = copy.deepcopy(cone)
    pulldowns = [
        d
        for d in broken["devices"]
        if d["gate"] == named_node(cone, "pck2")
        and named_node(cone, "pck2f") in d["terminals"]
    ]
    require(len(pulldowns) == 1, "ambiguous pad-clock pulldown")
    broken["devices"].remove(pulldowns[0])
    bad = model(broken, "pck2f")
    require(
        bad.settle({"pck2": 0}) == 1, "inverter negative lacks charged starting node"
    )
    require(bad.settle({"pck2": 1}) != 0, "missing inverter device passed")
    return {
        "devices": 4,
        "rows": rows,
        "negative": "missing pulldown fails PCLK2 inversion",
    }


def negatives(parts: dict) -> dict:
    failures = {}
    for target, expected in [
        ("halt", "HALT changes outside phase 1"),
        ("pad", "HALT pad changes during CPU phase 2"),
    ]:
        broken = copy.deepcopy(parts)
        n = broken[target]
        m = model(n, "halt") if target == "halt" else Pad(n)
        control = m.node("haltclk" if target == "halt" else "pck2f")
        gates = [d for d in n["devices"] if d["gate"] == control and d["implant"] == 3]
        require(len(gates) == 1, "ambiguous handoff sampling gate")
        gates[0]["gate"] = next(n for n, v in m.rails.items() if v == 1)
        try:
            check_case(run_case(broken, 0, 0, 100, 100, 2, 1))
        except ValueError as error:
            require(str(error) == expected, "wrong handoff negative: " + str(error))
            failures[target] = str(error)
        else:
            raise ValueError("open sampling gate passed handoff check")
    for name in ["slow", "ph2"]:
        broken = copy.deepcopy(parts["clock_output"])
        control = named_node(broken, name)
        gates = [
            d
            for d in broken["devices"]
            if (control in d["terminals"] if name == "slow" else control == d["gate"])
        ]
        require(len(gates) == 1, "ambiguous clock sampling gate")
        gates[0]["gate"] = named_node(broken, "vdd")
        expected = (
            "slow latch sampling mismatch"
            if name == "slow"
            else "PCLK0 sampling mismatch"
        )
        try:
            clock_checks(broken)
        except ValueError as error:
            require(str(error) == expected, "wrong clock-stage negative: " + str(error))
            failures[name] = str(error)
        else:
            raise ValueError("open clock gate passed")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("placed_network", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    parts = circuits(load_cells(args.archive))
    result = {
        "clock_stages": clock_checks(parts["clock_output"]),
        "pad_clock": pad_clock(json.loads(args.placed_network.read_text())),
        "negatives": negatives(parts),
    }
    # Keep complete representative traces for reproducible guard mutation tests.
    samples = [
        run_case(parts, a, b, 100, 100, 0, 1)
        for a, b in [(0, 0), (1, 1), (0, 1), (1, 0)]
    ]
    for case in samples:
        check_case(case)
    result["samples"] = samples
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "clock_rows": len(result["clock_stages"]),
                "negatives": result["negatives"],
                "pad_clock": result["pad_clock"],
            }
        )
    )


if __name__ == "__main__":
    main()
