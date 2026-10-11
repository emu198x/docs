"""Join placed candidate networks through geometry, never equal text labels.

Diagnostic rectangle-centre anchors expose existing local conductor nets.
They do not change masks, and are excluded from the reported chip labels.
"""

import argparse
import json
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-controller-clock")
)
from flatten_layout import flatten, reference_matrix, transform
from layout_network import Union, extract, rectangle, require
from trace_circuit import g, groups, load_cells, top_routing

TARGETS = ["RCPLA_RCPLA", "RSYNC_RSYNCPLA", g.TARGET, "VCELL_VCELL_GINGER$LOE_LRIC_LY_"]
CLOCK = "VCELL_VCELL_GINGER$LOE_CLKGEN_L"
HANDOFF_WIRING = ["VCELL_VCELL_GINGER$LOE_LM_LY_", "VCELL_VCELL_GINGER$LOE_GBFM2_LY"]
PHASE_BRANCHES = [
    "VCELL_VCELL_GINGER$LOE_" + suffix
    for suffix in ["CTRL_LY_", "ADDINV_L", "LUM_LY_", "LUM2_LY_", "BURSTFOR"]
]


def local_network(
    cells: dict, root: str, *, retain_single_terminal: bool = False
) -> tuple[list[dict], dict, dict[int, int]]:
    elements, _ = flatten(cells, root)
    # Layer 8 appears only as a pad opening in these added cells. Its role is
    # unqualified: exclude it from the candidate electrical deck only after
    # proving it cannot bridge distinct metal shapes in this geometry.
    for e in elements:
        if e["layer"] <= 7:
            continue
        require(e["kind"] == "polygon" and e["layer"] == 8, "unsupported pad layer")
        _, x0, y0, x1, y1 = rectangle(e)
        covering = [
            rectangle(p) for p in elements if p["kind"] == "polygon" and p["layer"] == 7
        ]
        require(
            any(
                r[1] <= x0 and r[2] <= y0 and r[3] >= x1 and r[4] >= y1
                for r in covering
            ),
            "unqualified layer 8 bridges metal shapes",
        )
    elements = [e for e in elements if e["layer"] <= 7]
    anchors = []
    for index, e in enumerate(elements):
        if e["kind"] == "polygon" and e["layer"] in [5, 7]:
            layer, x0, y0, x1, y1 = rectangle(e)
            anchors.append(
                {
                    "kind": "text",
                    "layer": layer,
                    "xy": [(Fraction(x0 + x1, 2), Fraction(y0 + y1, 2))],
                    "text": f"@@route:{index}",
                }
            )
    network = extract(elements + anchors, retain_single_terminal=retain_single_terminal)
    routes = {}
    for node, names in network["labels"].items():
        for name in names:
            if name.startswith("@@route:"):
                routes[int(name.split(":")[1])] = int(node)
    require(len(routes) == len(anchors), "missing diagnostic conductor anchor")
    network["labels"] = {
        n: [s for s in names if not s.startswith("@@route:")]
        for n, names in network["labels"].items()
    }
    return elements, network, routes


def join_rectangles(
    rects: list[tuple], links: list[tuple[int, int]], size: int
) -> Union:
    union = Union(size)
    for first, second in links:
        union.join([first, second])
    array = np.array(rects)
    indices = np.arange(len(array))
    for i, (layer, x0, y0, x1, y1) in enumerate(array):
        dx = np.minimum(x1, array[:, 3]) - np.maximum(x0, array[:, 1])
        dy = np.minimum(y1, array[:, 4]) - np.maximum(y0, array[:, 2])
        same = (array[:, 0] == layer) & (
            ((dx > 0) & (dy >= 0)) | ((dy > 0) & (dx >= 0))
        )
        cut = (
            (
                ((array[:, 0] == 6) & np.isin(layer, [1, 5, 7]))
                | ((layer == 6) & np.isin(array[:, 0], [1, 5, 7]))
            )
            & (dx > 0)
            & (dy > 0)
        )
        for j in np.flatnonzero((same | cut) & (indices > i)):
            union.join([i, int(j)])
    return union


def connect(
    cells: dict,
    targets: list[str] = TARGETS,
    *,
    single_terminal_cells: frozenset[str] = frozenset(),
) -> dict:
    rects, parent_labels, excluded = top_routing(cells)
    require(
        single_terminal_cells <= set(targets), "diagnostic cell missing from targets"
    )
    cache = {
        root: local_network(
            cells, root, retain_single_terminal=root in single_terminal_cells
        )
        for root in targets
    }
    raw_placements = []
    for index, records in enumerate(groups(cells["GINGER_GINGER"])):
        mapping = {r.kind: r.data for r in records}
        if records[0].kind != 10:
            continue
        name = g.string(mapping[18])
        if name in cache:
            raw_placements.append((name, index, reference_matrix(mapping)))
    require(
        {name for name, _, _ in raw_placements} == set(targets),
        "missing target placement",
    )
    local = {}
    placements = {}
    for name, index, matrix in raw_placements:
        repeated = sum(root == name for root, _, _ in raw_placements) > 1
        key = f"{name}@{index}" if repeated else name
        local[key] = cache[name]
        placements[key] = matrix
    pending = []
    keys = set()
    for root, (elements, network, routes) in local.items():
        keys.update((root, int(n)) for n in network["labels"])
        keys.update(
            (root, n) for d in network["devices"] for n in [d["gate"], *d["terminals"]]
        )
        keys.update(
            (root, n)
            for d in network.get("unmodelled_structures", [])
            for n in [d["gate"], *d["terminals"]]
        )
        for index, node in routes.items():
            e = elements[index]
            placed = {**e, "xy": [transform(p, placements[root]) for p in e["xy"]]}
            pending.append((len(rects), (root, node)))
            rects.append(rectangle(placed))
    node_ids = {key: len(rects) + i for i, key in enumerate(sorted(keys))}
    union = join_rectangles(
        rects, [(i, node_ids[key]) for i, key in pending], len(rects) + len(keys)
    )
    labels = defaultdict(set)
    device_list = []
    unmodelled = []
    for root, (_, network, _) in local.items():
        for node, names in network["labels"].items():
            labels[union.find(node_ids[root, int(node)])].update(
                root + "::" + name for name in names
            )
        for d in network["devices"]:
            converted = {
                **d,
                "gate": union.find(node_ids[root, d["gate"]]),
                "terminals": sorted(
                    union.find(node_ids[root, n]) for n in d["terminals"]
                ),
                "cell": root,
                "xy": transform(tuple(d["xy"]), placements[root]),
            }
            require(
                len(set(converted["terminals"])) == 2,
                "parent routing shorts transistor channel",
            )
            device_list.append(converted)
        for d in network.get("unmodelled_structures", []):
            unmodelled.append(
                {
                    **d,
                    "gate": union.find(node_ids[root, d["gate"]]),
                    "terminals": sorted(
                        union.find(node_ids[root, n]) for n in d["terminals"]
                    ),
                    "cell": root,
                    "xy": transform(tuple(d["xy"]), placements[root]),
                }
            )
    a = np.array(rects)
    unconnected = []
    for name, layer, x, y in parent_labels:
        hits = np.flatnonzero(
            (a[:, 0] == layer)
            & (a[:, 1] <= x)
            & (a[:, 3] >= x)
            & (a[:, 2] <= y)
            & (a[:, 4] >= y)
        )
        roots = {union.find(i) for i in hits}
        require(len(roots) <= 1, f"ambiguous parent label {name}")
        if roots:
            labels[next(iter(roots))].add("TOP/" + name)
        else:
            unconnected.append(name)
    result = {
        "labels": {str(n): sorted(names) for n, names in labels.items() if names},
        "devices": device_list,
        "unconnected_parent_labels": sorted(unconnected),
        "summary": {
            "rectangles": len(rects),
            "candidate_devices": len(device_list),
            "local_networks": {root: n["summary"] for root, (_, n, _) in local.items()},
            "parent_instances_not_expanded": sum(excluded.values())
            - sum(excluded.get(root, 0) for root in targets),
        },
    }
    if unmodelled:
        result["unmodelled_structures"] = unmodelled
        result["summary"]["unmodelled_structures"] = len(unmodelled)
    return result


def named_binding(network: dict, alias: str) -> int:
    matches = [int(node) for node, names in network["labels"].items() if alias in names]
    require(
        len(matches) == 1, f"ambiguous named binding {alias}: {len(matches)} components"
    )
    return matches[0]


def shared_route(network: dict, first: str, second: str) -> int:
    """Check two exact port identities against geometry-derived components."""
    node = named_binding(network, first)
    require(node == named_binding(network, second), "missing physical port route")
    return node


def report(network: dict) -> dict:
    aliases = ["TOP/ph1", "TOP/ph2", "TOP/halt", "TOP/intf", "TOP/pck2f"]
    groups = {
        alias: [
            {"node": int(node), "labels": names}
            for node, names in network["labels"].items()
            if alias in names
        ]
        for alias in aliases
    }
    try:
        named_binding(network, "TOP/ph1")
        named_binding(network, "TOP/ph2")
        named_binding(network, "TOP/halt")
    except ValueError as error:
        failure = str(error)
    else:
        failure = None
    rsync = g.TARGET + "::" + g.TARGET
    nmi = "PADLAY_HPAD06M__@35::PADLAY_HPAD06M__/0:VCELL_VCELL_GINGER$LOE_HPAD06M_"
    halt = "PADLAY_HPAD06I__::PADLAY_HPAD06I__/0:VCELL_VCELL_GINGER$LOE_HPAD06I_"
    routes = (
        {}
        if "PADLAY_HPAD06I__" not in network["summary"]["local_networks"]
        else {
            "interrupt_latch_to_nmi_pad": shared_route(
                network, rsync + "/intf", nmi + "/in"
            ),
            "top_pck2f_to_halt_sample_gate": shared_route(
                network, "TOP/pck2f", halt + "/pck2f"
            ),
        }
    )
    if CLOCK in network["summary"]["local_networks"]:
        clock = CLOCK + "::" + CLOCK
        core = "RCPLA_RCPLA::RCPLA_RCPLA/0:$1_331_HPLA32_HPLA32_PLA_FILE_G"
        routes["clock_n12_to_controller_output_phase"] = shared_route(
            network, clock + "/n12", core + "/clk"
        )
        routes["clock_n13_to_controller_input_phase"] = shared_route(
            network, clock + "/n13", core + "/clkin"
        )
    if all(root in network["summary"]["local_networks"] for root in HANDOFF_WIRING):
        routes["internal_halt_to_halt_pad"] = shared_route(
            network, rsync + "/halt", halt + "/in"
        )
    if all(root in network["summary"]["local_networks"] for root in PHASE_BRANCHES):
        routes["clock_n12_to_rsync_phase1"] = shared_route(
            network, CLOCK + "::" + CLOCK + "/n12", rsync + "/ph1"
        )
        routes["clock_n13_to_rsync_phase2"] = shared_route(
            network, CLOCK + "::" + CLOCK + "/n13", rsync + "/ph2"
        )
        require(
            routes["clock_n12_to_rsync_phase1"] != routes["clock_n13_to_rsync_phase2"],
            "physical phases are shorted",
        )
    return {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "inventory": network["summary"],
        "alias_groups": groups,
        "verified_routes": routes,
        "unmodelled_structure_ports": [
            {
                "cell": d["cell"],
                "kind": d["kind"],
                "gate_labels": network["labels"].get(str(d["gate"]), []),
                "terminal_labels": [
                    network["labels"].get(str(n), []) for n in d["terminals"]
                ],
            }
            for d in network.get("unmodelled_structures", [])
        ],
        "name_only_binding_rejection": failure,
        "phase_schedule_qualified": False,
        "scope": "partial placed network; remaining driver paths and analogue phase relationships are not qualified",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--scope",
        choices=["controllers", "pads", "routing", "clock", "phases"],
        default="routing",
    )
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    cells = load_cells(args.archive)
    targets = list(TARGETS)
    if args.scope in ["pads", "routing", "clock", "phases"]:
        targets += ["PADLAY_HPAD06I__", "PADLAY_HPAD06M__", "PADLAY_HPAD06__"]
    if args.scope in ["routing", "clock", "phases"]:
        targets += ["VCELL_VCELL_GINGER$LOE_HVSYNC_L"]
        targets += [name for name in cells if name.startswith("LARRY2_LRC_")]
    if args.scope in ["clock", "phases"]:
        targets += ["VCELL_VCELL_GINGER$LOE_RLOG_LY_", CLOCK, *HANDOFF_WIRING]
    if args.scope == "phases":
        targets += PHASE_BRANCHES
    result = connect(
        cells,
        targets,
        single_terminal_cells=frozenset([CLOCK])
        if args.scope in ["clock", "phases"]
        else frozenset(),
    )
    if args.scope in ["clock", "phases"]:
        inventory = result["summary"]["local_networks"][CLOCK]
        require(inventory["devices"] == 114, "clock transistor inventory changed")
        require(
            inventory.get("unmodelled_structures") == 2,
            "clock diagnostic inventory changed",
        )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if args.summary:
        args.summary.write_text(json.dumps(report(result), indent=2) + "\n")
    print(json.dumps(result["summary"]))
    for node, names in result["labels"].items():
        if any(
            s in names
            for s in ["TOP/ph1", "TOP/ph2", "TOP/pckedge", "TOP/halt", "TOP/intf"]
        ):
            print(node, names)


if __name__ == "__main__":
    main()
