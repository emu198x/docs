"""Conditional circuit handoff; half-phase steps are not native tick claims."""

import argparse
import copy
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "2026-10-11-maria-physical-phase-branches"
    ),
)
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-phase-handoff")
)
from connect_layout import local_network
from layout_network import extract, require
from probe_controller_clock import ROOT, Transfer, flatten
from probe_pads import HALT, Pad
from probe_phases import isolate_output, latch_cone, named_node
from trace_circuit import PLA, g, load_cells, truth_rows

RCOUT = "VCELL_VCELL_GINGER$LOE_RCOUT_LY"


def model(network: dict, output: str) -> Pad:
    network = copy.deepcopy(network)
    node = named_node(network, output)
    network["labels"] = {
        n: ["cone/" + name for name in names] for n, names in network["labels"].items()
    }
    network["labels"][str(node)].append("cone/pad")
    return Pad(network)


def circuits(cells: dict) -> dict:
    rsync = extract(g.geometry(cells[g.TARGET]))
    halt = isolate_output(
        rsync, "halt", ["vdd", "vss", "ph2", "pckedge", "start", "eovb", "haltrst"]
    )
    # Only the request-latch fan-out uses this local ph1 branch. Its physical
    # connection to clock n12 was checked in the placed phase-route probe.
    require(len(halt["devices"]) == 32, "unexpected full HALT cone")
    named_node(halt, "ph1")
    output = extract(g.geometry(cells[RCOUT]))
    # Recover the slow-input pass gate, its sampled node and following inverter.
    slow = named_node(output, "slow")
    gates = [d for d in output["devices"] if slow in d["terminals"]]
    require(len(gates) == 1, "ambiguous slow sample gate")
    sampled = next(n for n in gates[0]["terminals"] if n != slow)
    drivers = [d for d in output["devices"] if d["gate"] == sampled]
    require(len(drivers) == 1, "ambiguous slow inverter")
    vss = named_node(output, "vss")
    require(vss in drivers[0]["terminals"], "slow inverter lacks ground")
    slowf = next(n for n in drivers[0]["terminals"] if n != vss)
    output["labels"].setdefault(str(slowf), []).append("slowf")
    # Unconnected named ph1 branches are irrelevant to these ten devices.
    nodes = {n for d in output["devices"] for n in [d["gate"], *d["terminals"]]}
    output["labels"] = {n: v for n, v in output["labels"].items() if int(n) in nodes}
    flat = extract(flatten(cells, ROOT)[0])
    transfer = Transfer(flat)
    slow_ports = [
        int(n)
        for n, names in flat["labels"].items()
        if any(name.endswith("/slow") for name in names)
    ]
    require(len(slow_ports) == 1, "ambiguous placed slow port")
    pass_gates = [d for d in flat["devices"] if slow_ports[0] in d["terminals"]]
    require(len(pass_gates) == 1, "ambiguous placed slow sampling gate")
    held = next(n for n in pass_gates[0]["terminals"] if n != slow_ports[0])
    require(
        any(
            d["gate"] == held
            and d["terminals"] == sorted([transfer.vss, transfer.labels["in5"]])
            for d in flat["devices"]
        ),
        "slow latch does not drive controller input 5",
    )
    clocks = {
        (state, slowf): transfer.row(state, (1, 1, 0, slowf))
        for state, slowf in itertools.product(range(64), range(2))
    }
    irq = {
        (r["state"], r["dli"], r["halt"], r["edge"]): r
        for r in truth_rows(extract(g.geometry(cells[PLA])))
    }
    return {
        "halt": halt,
        "nmi": latch_cone(rsync),
        "pad": local_network(cells, HALT)[1],
        "clock_output": output,
        "clocks": clocks,
        "irq": irq,
    }


def run_case(
    parts: dict,
    initial_slow: int,
    final_slow: int,
    release: int,
    mode_change: int,
    return_delay: int,
    dli: int,
    request: str = "start",
    slow_order: str = "control-first",
    cache: dict | None = None,
) -> dict:
    halt = model(parts["halt"], "halt")
    nmi = Pad(parts["nmi"])
    pad = Pad(parts["pad"])
    clock = model(parts["clock_output"], "pck0")
    require(
        slow_order in ["control-first", "data-first"], "unknown slow transition order"
    )

    def settle(name: str, circuit: Pad, inputs: dict) -> int:
        # Cache complete solver states, never only externally visible outputs.
        # The caller owns a cache for one immutable set of extracted circuits.
        if cache is None:
            return circuit.settle(inputs)
        key = (
            name,
            tuple(sorted(circuit.values.items())),
            tuple(sorted(inputs.items())),
        )
        if key not in cache:
            value = circuit.settle(inputs)
            cache[key] = (value, dict(circuit.values))
        value, state = cache[key]
        circuit.values = dict(state)
        return value

    halt.settle({"ph1": 0, "ph2": 1, "pckedge": 0, "start": 0, "eovb": 0, "haltrst": 1})
    nmi.settle({"ph2": 1, "intset": 0, "intrst": 0, "menblf": 1})
    pad.settle({"in": 0, "pck2f": 1})
    # Start in reset; warm-up precedes the requested transfer by many periods.
    rc = (0, 0, 0, 0, 0)
    rc_sample = (0, 1 - initial_slow)
    irq = {"next": 0, "set": 0, "reset": 0, "enable": 0}
    irq_sample = (0, 0, 0, 0)
    history = []
    rows = []
    old_slow = initial_slow
    old_ph2 = 1
    for step in range(240):
        ph2 = step % 2
        slow = initial_slow if step < mode_change else final_slow
        if slow_order == "data-first":
            settle("clock", clock, {"ph2": old_ph2, "epck0f": rc[3], "slow": slow})
        if not ph2:
            rc = parts["clocks"][rc_sample]
            irq = parts["irq"][irq_sample]
        if slow_order == "control-first":
            settle("clock", clock, {"ph2": ph2, "epck0f": rc[3], "slow": old_slow})
        pck0 = settle("clock", clock, {"ph2": ph2, "epck0f": rc[3], "slow": slow})
        old_slow, old_ph2 = slow, ph2
        internal = settle(
            "halt",
            halt,
            {
                "ph1": 1 - ph2,
                "ph2": ph2,
                "pckedge": rc[4],
                "start": int(request == "start" and 48 <= step < release),
                "eovb": int(request == "eovb" and 48 <= step < release),
                "haltrst": int(step < 24 or step >= release),
            },
        )
        history.append(pck0)
        # PCLK2 is a separate CPU return input. Delay is a swept hypothesis,
        # not a measured CPU or package propagation time.
        pck2 = history[max(0, step - return_delay)]
        halt_pad = settle("pad", pad, {"in": internal, "pck2f": 1 - pck2})
        intf = settle(
            "nmi",
            nmi,
            {
                "ph2": ph2,
                "intset": irq["set"],
                "intrst": irq["reset"],
                "menblf": int(step < 24),
            },
        )
        if ph2:
            rc_sample = (rc[0], clock.values[clock.node("slowf")])
            irq_sample = (irq["next"], dli if step >= 48 else 0, internal, rc[4])
        rows.append(
            {
                "step": step,
                "ph2": ph2,
                "slow": slow,
                "edge": rc[4],
                "epck0f": rc[3],
                "pck0": pck0,
                "pck2": pck2,
                "halt": internal,
                "halt_pad": halt_pad,
                "nmi": intf,
            }
        )
    return {
        "initial_slow": initial_slow,
        "final_slow": final_slow,
        "reset_step": release,
        "mode_change": mode_change,
        "return_delay": return_delay,
        "dli": dli,
        "request": request,
        "slow_order": slow_order,
        "rows": rows,
    }


def edges(rows: list[dict], signal: str) -> list[dict]:
    return [r for before, r in itertools.pairwise(rows) if before[signal] != r[signal]]


def check_case(case: dict) -> dict:
    rows = case["rows"]
    require(len(rows) == 240, "incomplete handoff trace")
    require(
        all(r["halt"] == 0 and r["halt_pad"] == r["nmi"] == 1 for r in rows[32:48]),
        "handoff warm-up did not reach idle",
    )
    # Arbitrary retained-node power-up values are outside this experiment.
    # Require an observed idle interval before counting the requested transfer.
    rows = rows[32:]
    he, pe, ne = [edges(rows, s) for s in ["halt", "halt_pad", "nmi"]]
    require([r["halt"] for r in he] == [1, 0], "wrong internal HALT inventory")
    require([r["halt_pad"] for r in pe] == [0, 1], "wrong HALT pad inventory")
    require([r["nmi"] for r in ne] == [0, 1] * case["dli"], "wrong NMI inventory")
    require(all(r["ph2"] == 0 for r in he), "HALT changes outside phase 1")
    require(all(r["pck2"] == 0 for r in pe), "HALT pad changes during CPU phase 2")
    require(all(r["ph2"] == 1 for r in ne), "NMI changes outside phase 2")
    require(
        all(
            r["halt"] == 0
            and r["halt_pad"] == 1
            and r["step"] >= max(he[1]["step"], pe[1]["step"])
            for r in ne
        ),
        "NMI precedes HALT release",
    )
    require(
        all(r["halt"] == 0 and r["halt_pad"] == r["nmi"] == 1 for r in rows[-24:]),
        "handoff did not return to idle",
    )
    result = {k: v for k, v in case.items() if k != "rows"}
    result.update(
        internal_halt_edges=[r["step"] for r in he],
        pad_halt_edges=[r["step"] for r in pe],
        nmi_edges=[r["step"] for r in ne],
    )
    if ne:
        falls = [
            r
            for r in edges(rows, "pck0")
            if r["pck0"] == 0 and ne[0]["step"] < r["step"] <= ne[1]["step"]
        ]
        require(len(falls) == 1, "NMI does not span one CPU clock falling edge")
        result.update(
            delay_from_internal=ne[0]["step"] - he[1]["step"],
            delay_from_pad=ne[0]["step"] - pe[1]["step"],
            width=ne[1]["step"] - ne[0]["step"],
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    parts = circuits(load_cells(args.archive))
    results = []
    cache = {}
    for initial, final in itertools.product([0, 1], repeat=2):
        changes = [96] if initial == final else range(96, 152)
        for release, change, delay, dli, request, order in itertools.product(
            range(96, 108),
            changes,
            [0, 1, 2],
            [0, 1],
            ["start", "eovb"],
            ["control-first", "data-first"],
        ):
            case = run_case(
                parts,
                initial,
                final,
                release,
                change,
                delay,
                dli,
                request,
                order,
                cache,
            )
            if (
                release == 100
                and change in [96, 100, 124, 140]
                and delay == 0
                and dli == 1
            ):
                plain = run_case(
                    parts, initial, final, release, change, delay, dli, request, order
                )
                require(case == plain, "cached solver changed a handoff trace")
            try:
                results.append(check_case(case))
            except ValueError:
                args.output.with_suffix(".failure.json").write_text(
                    json.dumps(case, indent=2) + "\n"
                )
                raise
        print(
            json.dumps({"initial": initial, "final": final, "completed": len(results)}),
            flush=True,
        )
    require(len(results) == 32832, "incomplete handoff matrix")
    args.output.write_text(json.dumps({"cases": results}, indent=2) + "\n")
    print(json.dumps({"cases": len(results)}))


if __name__ == "__main__":
    main()
