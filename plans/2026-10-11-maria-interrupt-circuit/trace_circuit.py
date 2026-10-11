"""Trace the pinned MARIA controller under an explicit layer-role hypothesis."""

import argparse
import copy
import hashlib
import itertools
import json
import struct
import sys
import zipfile
from collections import Counter
from pathlib import Path

from layout_network import extract, pla_truth, require, routing_groups

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-layout-evidence")
)
import inspect_layout as g

PLA = "VCELL_VCELL_GINGER$LOE_RSYNCPLA"


def load_cells(path: Path) -> dict:
    require(
        hashlib.sha256(path.read_bytes()).hexdigest() == g.ARCHIVE_SHA,
        "unqualified archive",
    )
    with zipfile.ZipFile(path) as archive:
        data = archive.read(g.MEMBER)
    require(hashlib.sha256(data).hexdigest() == g.MEMBER_SHA, "unqualified member")
    cells, _ = g.scan(data)
    require(len(cells) == 563, "incomplete cell inventory")
    return cells


def groups(rs):
    cur = []
    for r in rs[2:-1]:
        cur.append(r)
        if r.kind == 17:
            yield cur
            cur = []
    require(not cur, "unterminated top element")


def top_routing(cells: dict) -> tuple[list, list, dict]:
    rects = []
    labels = []
    excluded = Counter()

    def rectangle(l, x0, y0, x1, y1):
        require(x1 > x0 and y1 > y0, "empty top rectangle")
        rects.append((l, x0, y0, x1, y1))

    def add_geometry(es, off=(0, 0), prefix=""):
        for e in es:
            if e["kind"] == "text":
                labels.append(
                    (
                        prefix + e["text"],
                        e["layer"],
                        e["xy"][0][0] + off[0],
                        e["xy"][0][1] + off[1],
                    )
                )
                continue
            if e["layer"] not in [1, 5, 6, 7]:
                continue
            xy = e["xy"]
            xs = sorted({x + off[0] for x, y in xy})
            ys = sorted({y + off[1] for x, y in xy})
            require(len(xs) == len(ys) == 2, "nonrectangular top boundary")
            rectangle(e["layer"], xs[0], ys[0], xs[1], ys[1])

    for rs in groups(cells["GINGER_GINGER"]):
        d = {r.kind: r.data for r in rs}
        kind = rs[0].kind
        if kind in [8, 12]:
            add_geometry(
                g.geometry(
                    cells["GINGER_GINGER"][:2] + rs + cells["GINGER_GINGER"][-1:]
                )
            )
        elif kind == 9:
            l = struct.unpack(">h", d[13])[0]
            w = struct.unpack(">i", d[15])[0]
            pt = struct.unpack(">h", d[33])[0]
            require(pt == 2 and w > 0 and w % 2 == 0, "unsupported top path")
            xy = list(struct.iter_unpack(">ii", d[16]))
            h = w // 2
            for a, b in itertools.pairwise(xy):
                require(a[0] == b[0] or a[1] == b[1], "diagonal top path")
                rectangle(
                    l,
                    min(a[0], b[0]) - h,
                    min(a[1], b[1]) - h,
                    max(a[0], b[0]) + h,
                    max(a[1], b[1]) + h,
                )
        elif kind == 10:
            name = g.string(d[18])
            off = struct.unpack(">ii", d[16])
            if name.startswith("VIPLIB_CH"):
                require(
                    set(d) == {10, 18, 26, 16, 17} and d[26] == b"\0\0",
                    "unsupported contact transform",
                )
                add_geometry(g.geometry(cells[name]), off)
            elif name == "RSYNC_RSYNCPLA" or name == g.TARGET:
                require(
                    set(d) == {10, 18, 26, 16, 17} and d[26] == b"\0\0",
                    "unsupported target transform",
                )
                cn = (
                    "VCELL_VCELL_GINGER$LOE_RSYNCPLA"
                    if name == "RSYNC_RSYNCPLA"
                    else name
                )
                add_geometry(
                    [
                        e
                        for e in g.geometry(cells[cn])
                        if e["kind"] == "text" or e["layer"] in [5, 6, 7]
                    ],
                    off,
                    prefix=("PLA." if name == "RSYNC_RSYNCPLA" else "RSYNC."),
                )
            else:
                excluded[name] += 1
        else:
            raise ValueError(kind)
    return rects, labels, dict(excluded)


EXPECTED_PORTS = {
    "pla_out5/1": "intrst",
    "pla_out4/1": "intset",
    "pla_out3/1": "rsyncenable",
    "pla_out2/1": "PLA.pla_in4/1",
    "pla_out1/1": "PLA.pla_in5/1",
    "pla_in3/1": "dlireq",
    "pla_in2/1": "halt",
    "pla_in1/1": "pckedge",
    "pla_clkin/1": "ph2",
    "pla_clk/1": "ph1",
    "pla_vss/1": "vss",
    "pla_vdd/1": "vdd",
}


def check_ports(groups: list[list[str]]) -> list[list[str]]:
    selected = []
    for port, signal in EXPECTED_PORTS.items():
        matches = [names for names in groups if "PLA." + port in names]
        require(
            len(matches) == 1 and signal in matches[0],
            f"missing routing {port} -> {signal}",
        )
        selected.append(matches[0])
    return sorted(selected)


def expected_row(state: int, dli: int, halt: int, edge: int) -> dict:
    """Independently expressed controller equations, not calls into the solver."""
    next_state = 0
    if state == 0:
        next_state = 2 if halt and edge else 0
    elif state == 2:
        next_state = 2 if halt or dli and not edge else 3 if dli else 0
    elif state == 3:
        next_state = 0 if edge else 3
    return {
        "state": state,
        "dli": dli,
        "halt": halt,
        "edge": edge,
        "next": next_state,
        "enable": int(state == 0 and halt and edge),
        "set": int(state == 3 and edge),
        "reset": int(state == 0 and edge),
    }


def truth_rows(network: dict) -> list[dict]:
    rows = []
    for state, dli, halt, edge in itertools.product(
        range(4), range(2), range(2), range(2)
    ):
        output = pla_truth(network, [edge, halt, dli, (state >> 1) & 1, state & 1])
        row = {
            "state": state,
            "dli": dli,
            "halt": halt,
            "edge": edge,
            "next": output[0] + 2 * output[1],
            "enable": output[2],
            "set": output[3],
            "reset": output[4],
        }
        require(
            row == expected_row(state, dli, halt, edge), f"PLA equation mismatch: {row}"
        )
        rows.append(row)
    require(len(rows) == 32, "empty or incomplete PLA truth table")
    return rows


def check_primitives(cells: dict) -> dict:
    """Check geometry evidence for the proposed layer roles, not a foundry key."""
    observed = {}
    for name, expected in {
        "VIPLIB_CHD2HM": [1, 6, 7],
        "VIPLIB_CHM2HP1A": [5, 6, 7],
        "VIPLIB_HMOSXIST_2_6_1_": [1, 3, 5],
        "VIPLIB_HMOSXIST_6_4_2_": [1, 2, 5],
        "VIPLIB_HMOSXIST_3_18_4_": [1, 5],
    }.items():
        elements = g.geometry(cells[name])
        layers = sorted(e["layer"] for e in elements)
        require(layers == expected, f"unexpected primitive layers: {name}")
        observed[name] = layers
    return observed


def check_latch(network: dict) -> dict:
    labels = network["labels"]

    def node(name: str) -> int:
        matches = [int(n) for n, names in labels.items() if name in names]
        require(len(matches) == 1, f"ambiguous latch node {name}")
        return matches[0]

    devices = network["devices"]
    vdd, vss = node("vdd"), node("vss")
    loads = [d for d in devices if d["implant"] == 2]
    require(
        len(loads) == 25
        and all(
            vdd in d["terminals"] and d["gate"] in d["terminals"] and d["gate"] != vdd
            for d in loads
        ),
        "invalid RSYNC depletion-load hypothesis",
    )

    def has(gate: int, first: int, second: int, implant: int = 3) -> None:
        matches = [
            d
            for d in devices
            if d["gate"] == gate
            and d["terminals"] == sorted([first, second])
            and d["implant"] == implant
        ]
        require(len(matches) == 1, "latch topology mismatch")

    for signal, drain in [("intset", "intqf"), ("intrst", "intq")]:
        ports = [
            d
            for d in devices
            if d["gate"] == node("ph2")
            and node(signal) in d["terminals"]
            and d["implant"] == 3
        ]
        require(len(ports) == 1, f"missing sampled latch input {signal}")
        sampled = next(n for n in ports[0]["terminals"] if n != node(signal))
        has(sampled, node(drain), vss)
    has(node("intq"), node("intqf"), vss)
    has(node("intqf"), node("intq"), vss)
    has(node("menblf"), node("intq"), vss)
    has(node("intq"), node("intf"), vss)
    pullups = [
        d
        for d in devices
        if d["implant"] == 0 and d["terminals"] == sorted([vdd, node("intf")])
    ]
    require(len(pullups) == 1, "missing interrupt output pullup")
    inversion = pullups[0]["gate"]
    has(node("intq"), inversion, vss)
    has(inversion, inversion, vdd, 2)
    return {
        "sample_phase": "ph2",
        "set_pulldown": "intqf",
        "reset_pulldown": "intq",
        "disable_pulldown": "intq",
        "output_polarity": "intf low when intq high",
        "self_gated_loads": len(loads),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cells = load_cells(args.archive)
    networks = {name: extract(g.geometry(cells[name])) for name in [g.TARGET, PLA]}
    require(
        networks[g.TARGET]["summary"]["implants"] == {3: 68, 2: 25, 0: 4},
        "RSYNC device inventory mismatch",
    )
    require(
        networks[PLA]["summary"]["implants"] == {3: 60, 2: 29},
        "PLA device inventory mismatch",
    )
    primitives = check_primitives(cells)
    latch = check_latch(networks[g.TARGET])
    rects, labels, excluded = top_routing(cells)
    groups, unconnected = routing_groups(rects, labels)
    require(
        [n for n in unconnected if n.startswith(("RSYNC.", "PLA."))] == ["RSYNC.dliqf"],
        f"unexpected missing routing anchors: {unconnected}",
    )
    ports = check_ports(groups)
    rows = truth_rows(networks[PLA])
    # Remove the output anchor's poly route from a copy of the routing input.
    missing_route = [
        r
        for r in rects
        if not (r[0] == 5 and r[1] <= -1410000 <= r[3] and r[2] <= 396750 <= r[4])
    ]
    require(len(missing_route) < len(rects), "route negative did not modify input")
    try:
        check_ports(routing_groups(missing_route, labels)[0])
    except ValueError as error:
        route_negative = str(error)
    else:
        raise ValueError("missing-route control survived")
    # Remove the gate that feeds the set output's second PLA plane.
    broken = copy.deepcopy(networks[PLA])
    set_node = next(
        int(n) for n, names in broken["labels"].items() if "pla_out4/1" in names
    )
    removed = [
        d for d in broken["devices"] if d["implant"] == 3 and set_node in d["terminals"]
    ]
    require(len(removed) == 1, "ambiguous set-output negative")
    broken["devices"].remove(removed[0])
    try:
        truth_rows(broken)
    except ValueError as error:
        device_negative = str(error)
    else:
        raise ValueError("missing-device control survived")
    summary = {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "electrical_roles": "hypothesis; no foundry deck or revision qualification",
        "networks": {n: net["summary"] for n, net in networks.items()},
        "primitives": primitives,
        "latch": latch,
        "top_rectangles": len(rects),
        "excluded_other_cell_instances": sum(excluded.values()),
        "unconnected": unconnected,
        "ports": ports,
        "truth_rows": rows,
        "negatives": {
            "missing_route": route_negative,
            "missing_device": device_negative,
        },
    }
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "networks": summary["networks"],
                "ports": len(ports),
                "truth_rows": len(rows),
                "negatives": summary["negatives"],
            }
        )
    )


if __name__ == "__main__":
    main()
