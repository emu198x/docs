"""Trace the clock/HALT routes without simulating unsupported clock devices."""

import argparse
import json
from pathlib import Path

from connect_layout import (
    CLOCK,
    HANDOFF_WIRING,
    TARGETS,
    connect,
    report,
    shared_route,
)
from layout_network import pla_truth, require
from probe_controller_clock import Transfer
from probe_pads import Pad
from trace_circuit import g, load_cells


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
        + [name for name in cells if name.startswith("LARRY2_LRC_")]
    )
    network = connect(
        cells, base + HANDOFF_WIRING, single_terminal_cells=frozenset([CLOCK])
    )
    inventory = network["summary"]["local_networks"][CLOCK]
    require(inventory["devices"] == 114, "clock transistor inventory changed")
    require(
        inventory.get("unmodelled_structures") == 2,
        "clock diagnostic inventory changed",
    )
    summary = report(network)
    require(
        "internal_halt_to_halt_pad" in summary["verified_routes"],
        "missing HALT acceptance check",
    )
    for root in HANDOFF_WIRING:
        require(
            network["summary"]["local_networks"][root]["devices"] == 0,
            "handoff wiring contains devices",
        )
    (args.output / "network.json").write_text(json.dumps(network, indent=2) + "\n")

    negatives = {}
    for name, solver in [
        ("pad", Pad),
        ("transfer", Transfer),
        ("pla", lambda n: pla_truth(n, [0] * 5)),
    ]:
        try:
            solver(network)
        except ValueError as error:
            require("unmodelled structures" in str(error), "wrong solver rejection")
            negatives[name] = str(error)
        else:
            raise ValueError("digital solver accepted unmodelled clock structures")
    incomplete = connect(cells, base, single_terminal_cells=frozenset([CLOCK]))
    try:
        shared_route(
            incomplete,
            g.TARGET + "::" + g.TARGET + "/halt",
            "PADLAY_HPAD06I__::PADLAY_HPAD06I__/0:VCELL_VCELL_GINGER$LOE_HPAD06I_/in",
        )
    except ValueError as error:
        require(
            str(error) == "missing physical port route", "wrong HALT route negative"
        )
        negatives["without_handoff_wiring"] = str(error)
    else:
        raise ValueError("HALT route unexpectedly survived omitted wiring")
    summary["negative_controls"] = negatives
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "verified_routes": summary["verified_routes"],
                "negative_controls": negatives,
            }
        )
    )


if __name__ == "__main__":
    main()
