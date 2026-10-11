"""Derive the raster-control PLA clock outputs from the pinned layout.

Sample inputs are held independently while the output bank is open. This
recovers combinational transfer functions, not analogue phase simulation.
"""

import argparse
import copy
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

from flatten_layout import flatten, reference_matrix, transform
from layout_network import Union, extract, rectangle, require, routing_groups
from trace_circuit import g, groups, load_cells, top_routing

ROOT = "RCPLA_RCPLA"
CORE = "$1_331_HPLA32_HPLA32_PLA_FILE_G"
LRIC = "VCELL_VCELL_GINGER$LOE_LRIC_LY_"


def core_labels(network: dict) -> dict[str, int]:
    return {
        name.split("/")[-1]: int(node)
        for node, names in network["labels"].items()
        for name in names
        if CORE in name and len(name.split("/")) == 3
    }


class Transfer:
    def __init__(self, network: dict) -> None:
        require(
            not network.get("unmodelled_structures"),
            "unmodelled structures in transfer network",
        )
        self.labels = core_labels(network)
        self.vdd, self.vss = self.labels["vdd"], self.labels["vss"]
        devices = network["devices"]
        self.loads = {d["gate"] for d in devices if d["implant"] == 2}
        require(
            all(
                self.vdd in d["terminals"]
                and d["gate"] in d["terminals"]
                and d["gate"] != self.vdd
                for d in devices
                if d["implant"] == 2
            ),
            "invalid depletion-load connection",
        )
        require(
            all(d["implant"] in [0, 2, 3] for d in devices),
            "unsupported transistor class",
        )
        self.logic = [d for d in devices if d["implant"] != 2]
        self.nodes = {n for d in devices for n in [d["gate"], *d["terminals"]]}
        self.ph1s = {
            int(n)
            for n, names in network["labels"].items()
            if any(name.endswith("/ph1") for name in names)
        } & self.nodes
        self.sampled = []
        for index in range(1, 12):
            port = self.labels[f"in{index}"]
            matches = [
                d
                for d in self.logic
                if d["gate"] == self.labels["clkin"]
                and port in d["terminals"]
                and d["implant"] == 3
            ]
            require(len(matches) == 1, "ambiguous input sample gate")
            self.sampled.append(next(n for n in matches[0]["terminals"] if n != port))

    def solve(self, bits: list[int]) -> list[int]:
        require(
            len(bits) == 11 and all(b in [0, 1] for b in bits),
            "expected eleven binary inputs",
        )
        fixed = {
            self.vdd: 1,
            self.vss: 0,
            self.labels["clkin"]: 0,
            self.labels["clk"]: 1,
            **{n: 1 for n in self.ph1s},
            **dict(zip(self.sampled, bits, strict=True)),
        }
        values = dict.fromkeys(self.nodes, 0)
        values.update(fixed)
        rails = {self.vdd, self.vss}
        nonrails = self.nodes - rails
        for _ in range(100):
            union = Union(max(self.nodes) + 1)
            active = [d for d in self.logic if values[d["gate"]]]
            for device in active:
                if not rails.intersection(device["terminals"]):
                    union.join(device["terminals"])
            drivers = defaultdict(set)
            for node, value in fixed.items():
                if node not in rails:
                    drivers[union.find(node)].add(value)
            for device in active:
                powered = rails.intersection(device["terminals"])
                if powered:
                    require(len(powered) == 1, "transistor shorts supply rails")
                    rail = next(iter(powered))
                    other = next(n for n in device["terminals"] if n != rail)
                    drivers[union.find(other)].add(int(rail == self.vdd))
            weak = {union.find(n) for n in self.loads}
            new = {self.vdd: 1, self.vss: 0}
            for node in nonrails:
                root = union.find(node)
                drive = drivers[root]
                # Iteration order is numerical only. At convergence both
                # strong values on a component are forbidden. Weak loads
                # lose to an active pulldown, as required for NMOS logic.
                new[node] = min(drive) if drive else 1 if root in weak else values[node]
            if new == values:
                require(
                    all(len(d) < 2 for d in drivers.values()),
                    "conflicting settled drivers",
                )
                return [values[self.labels[f"out{i}"]] for i in range(1, 11)]
            values = new
        raise ValueError("combinational network did not settle")

    def row(
        self, state: int, inputs: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int, int]:
        require(0 <= state < 64, "state outside six-bit controller")
        result = self.solve([1, *inputs, *[(state >> i) & 1 for i in range(5, -1, -1)]])
        return (sum(b << i for i, b in enumerate(result[:6])), *result[6:])


def routed_ports(cells: dict, elements: list[dict]) -> list[list[str]]:
    rects, labels, _ = top_routing(cells)
    wanted = {ROOT: elements, LRIC: g.geometry(cells[LRIC])}
    found = set()
    for records in groups(cells["GINGER_GINGER"]):
        mapping = {r.kind: r.data for r in records}
        if records[0].kind != 10 or g.string(mapping[18]) not in wanted:
            continue
        name = g.string(mapping[18])
        require(name not in found, "duplicate target placement")
        found.add(name)
        matrix = reference_matrix(mapping)
        for e in wanted[name]:
            if e["kind"] == "polygon" and e["layer"] in [5, 6, 7]:
                rects.append(
                    rectangle({**e, "xy": [transform(p, matrix) for p in e["xy"]]})
                )
            elif e["kind"] == "text":
                x, y = transform(e["xy"][0], matrix)
                labels.append((name + "/" + e["text"], e["layer"], x, y))
    require(found == set(wanted), "missing controller placements")
    result, _ = routing_groups(rects, labels)
    important = ["pckedge", "pck0", "epck0f", "slow", "ph1", "ph2"]
    selected = [
        names
        for names in result
        if any(
            name.startswith(ROOT + "/") and name.endswith("/" + p)
            for name in names
            for p in important
        )
    ]
    for pin in ["pckedge", "pck0", "epck0f", "slow"]:
        matches = [
            names
            for names in selected
            if any(
                name.startswith(ROOT + "/") and name.endswith("/" + pin)
                for name in names
            )
        ]
        require(
            len(matches) == 1 and pin in matches[0], f"missing physical route {pin}"
        )
    require(
        any(
            "RSYNC.pckedge" in names
            and any(
                name.startswith(ROOT + "/") and name.endswith("/pckedge")
                for name in names
            )
            for names in selected
        ),
        "edge does not reach interrupt controller",
    )
    return selected


def clock_sequence(transfer: Transfer, fast: bool) -> dict:
    state = 0
    rows = []
    # rprstf=1, lrwaf=1, elrr=0; in5 is the inverted slow latch.
    for cycle in range(48):
        result = transfer.row(state, (1, 1, 0, int(fast)))
        rows.append(
            {
                "cycle": cycle,
                "state": state,
                "next": result[0],
                "epck0f": result[3],
                "pckedge": result[4],
            }
        )
        state = result[0]
    edges = [r["cycle"] for r in rows if r["pckedge"]]
    period = 4 if fast else 6
    require(
        len(edges) >= 7 and all(b - a == period for a, b in itertools.pairwise(edges)),
        f"wrong {period}-cycle edge period",
    )
    require(
        all(r["epck0f"] for r in rows if r["pckedge"]),
        "edge does not start inverse-clock high interval",
    )
    require(
        sum(r["epck0f"] for r in rows) == 24, "CPU clock duty differs from half period"
    )
    return {
        "mode": "fast" if fast else "slow",
        "edge_cycles": edges,
        "period_maria_cycles": period,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cells = load_cells(args.archive)
    elements, inventory = flatten(cells, ROOT)
    network = extract(elements)
    require(
        network["summary"]["implants"] == {2: 71, 0: 33, 3: 237},
        "controller device inventory mismatch",
    )
    ports = routed_ports(cells, elements)
    transfer = Transfer(network)
    truth = []
    for external in range(16):
        inputs = tuple((external >> i) & 1 for i in range(4))
        truth.append([list(transfer.row(state, inputs)) for state in range(64)])
    require(
        len(truth) == 16 and all(len(rows) == 64 for rows in truth),
        "incomplete transfer sweep",
    )
    sequences = [clock_sequence(transfer, fast) for fast in [True, False]]
    broken = copy.deepcopy(network)
    edge = core_labels(broken)["out10"]
    devices = [
        d for d in broken["devices"] if d["implant"] == 0 and edge in d["terminals"]
    ]
    require(len(devices) == 1, "missing edge pullup")
    broken["devices"].remove(devices[0])
    try:
        clock_sequence(Transfer(broken), True)
    except ValueError as error:
        negative = str(error)
    else:
        raise ValueError("missing-edge-device negative survived")
    summary = {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "geometry_elements": len(elements),
        "unique_cells": len(inventory),
        "cell_instances": sum(inventory.values()),
        "network": network["summary"],
        "ports": ports,
        "input_combinations": sum(len(rows) for rows in truth),
        "truth_sha256": hashlib.sha256(
            json.dumps(truth, separators=(",", ":")).encode()
        ).hexdigest(),
        "clock_sequences": sequences,
        "negative": negative,
        "scope": "candidate electrical interpretation; combinational transfer, not physical phase simulation",
    }
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: summary[k]
                for k in [
                    "geometry_elements",
                    "unique_cells",
                    "cell_instances",
                    "network",
                    "input_combinations",
                    "negative",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
