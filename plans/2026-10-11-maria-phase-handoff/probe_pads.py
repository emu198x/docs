"""Conditional digital behaviour of the recovered HALT and NMI pad cells.

Supply branches are independently driven at their named rail levels. This
checks the unit cells, not their complete chip wiring or analogue delay.
"""

import argparse
import copy
import json
from collections import defaultdict
from pathlib import Path

from connect_layout import local_network
from layout_network import Union, require
from trace_circuit import g, load_cells

HALT = "PADLAY_HPAD06I__"
NMI = "PADLAY_HPAD06M__"


class Pad:
    def __init__(self, network: dict) -> None:
        self.network = network
        self.nodes = {
            n for d in network["devices"] for n in [d["gate"], *d["terminals"]]
        }
        self.labels = network["labels"]
        self.nodes.update(map(int, self.labels))
        self.rails = {
            int(n): int(name.split("/")[-1].startswith("vdd"))
            for n, names in self.labels.items()
            for name in names
            if name.split("/")[-1] in ["vdd", "vss", "vss1"]
        }
        require(set(self.rails.values()) == {0, 1}, "missing supply branches")
        self.values = dict.fromkeys(self.nodes, 0)
        self.values.update(self.rails)
        self.loads = []
        self.logic = []
        for d in network["devices"]:
            if d["implant"] == 2:
                rail = [n for n in d["terminals"] if self.rails.get(n) == 1]
                require(len(rail) == 1, "load lacks one supply terminal")
                self.loads.append(
                    (d["gate"], next(n for n in d["terminals"] if n != rail[0]))
                )
            else:
                require(d["implant"] in [0, 3], "unsupported pad device")
                self.logic.append(d)

    def node(self, name: str) -> int:
        matches = [
            int(n)
            for n, names in self.labels.items()
            if any(s.endswith("/" + name) for s in names)
        ]
        require(len(matches) == 1, f"ambiguous pad port {name}")
        return matches[0]

    def settle(self, inputs: dict[str, int]) -> int:
        fixed = {
            **self.rails,
            **{self.node(name): value for name, value in inputs.items()},
        }
        require(all(value in [0, 1] for value in fixed.values()), "nonbinary pad input")
        values = {**self.values, **fixed}
        rails = set(self.rails)
        for _ in range(100):
            union = Union(max(self.nodes) + 1)
            active = [d for d in self.logic if values[d["gate"]]]
            for d in active:
                if not rails.intersection(d["terminals"]):
                    union.join(d["terminals"])
            drivers = defaultdict(set)
            for n, v in fixed.items():
                if n not in rails:
                    drivers[union.find(n)].add(v)
            for d in active:
                powered = rails.intersection(d["terminals"])
                if powered:
                    require(len(powered) == 1, "directly switched supply rails")
                    rail = next(iter(powered))
                    other = next(n for n in d["terminals"] if n != rail)
                    drivers[union.find(other)].add(self.rails[rail])
            weak = {union.find(n) for _, n in self.loads}
            new = dict(self.rails)
            for n in self.nodes - rails:
                root = union.find(n)
                drive = drivers[root]
                new[n] = min(drive) if drive else 1 if root in weak else values[n]
            if new == values:
                require(
                    all(len(v) < 2 for v in drivers.values()),
                    "conflicting settled pad drivers",
                )
                # Avoid relying on an always-on weak-load approximation where
                # a low gate would need to sustain a high source.
                require(
                    all(values[source] <= values[gate] for gate, source in self.loads),
                    "unqualified depletion bias",
                )
                components = defaultdict(set)
                for n in self.nodes - rails:
                    components[union.find(n)].add(values[n])
                require(
                    all(len(v) == 1 for v in components.values()),
                    "unresolved floating charge sharing",
                )
                self.values = values
                return values[self.node("pad")]
            values = new
        raise ValueError("pad network did not settle")


def verify(networks: dict) -> dict:
    halt_rows = []
    nmi_rows = []
    for initial in [0, 1]:
        halt = Pad(networks[HALT])
        nmi = Pad(networks[NMI])
        for step, (control, value) in enumerate(
            [
                (1, initial),
                (0, 1 - initial),
                (0, initial),
                (0, 1 - initial),
                (1, 1 - initial),
                (0, initial),
            ]
        ):
            out = halt.settle({"in": value, "pck2f": control})
            expected = 1 - (initial if step < 4 else 1 - initial)
            require(out == expected, "HALT sampling/holding mismatch")
            halt_rows.append(
                {
                    "initial": initial,
                    "step": step,
                    "pck2f": control,
                    "input": value,
                    "pad": out,
                }
            )
        for value in [initial, 1 - initial, initial, 1 - initial]:
            out = nmi.settle({"in": value})
            require(out == value, "NMI direct pad polarity mismatch")
            nmi_rows.append({"initial": initial, "input": value, "pad": out})
    return {"halt": halt_rows, "nmi": nmi_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cells = load_cells(args.archive)
    networks = {root: local_network(cells, root)[1] for root in [HALT, NMI]}
    require(
        networks[HALT]["summary"]["devices"] == 29
        and networks[NMI]["summary"]["devices"] == 28,
        "pad inventory mismatch",
    )
    results = verify(networks)
    broken = copy.deepcopy(networks)
    halt = Pad(broken[HALT])
    gates = [
        d
        for d in broken[HALT]["devices"]
        if d["gate"] == halt.node("pck2f") and halt.node("in") in d["terminals"]
    ]
    require(len(gates) == 1, "ambiguous pad sample-gate negative")
    gates[0]["gate"] = next(n for n, value in halt.rails.items() if value == 1)
    try:
        verify(broken)
    except ValueError as error:
        negative = str(error)
    else:
        raise ValueError("always-open sample gate passed retention check")
    require(negative == "HALT sampling/holding mismatch", "wrong negative failure")
    summary = {
        "archive_sha256": g.ARCHIVE_SHA,
        "member_sha256": g.MEMBER_SHA,
        "inventory": {root: n["summary"] for root, n in networks.items()},
        "results": results,
        "negative": negative,
        "scope": "unit-cell Boolean/retention model; analogue delays and global phase mapping unqualified",
    }
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
