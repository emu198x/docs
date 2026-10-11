"""Bounded rectangular layout probe, not a qualified foundry extraction deck.

Hypothesis: 1=diffusion, 5=poly, 7=metal, 6=cut, 4=buried contact;
2/3 mark depletion/enhancement gates. Report geometry separately from roles.
Uses installed NumPy/SciPy; adds no emulator dependency.
"""

import itertools
from collections import Counter, defaultdict

import numpy as np
from scipy import ndimage


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rectangle(element: dict) -> tuple[int, int, int, int, int]:
    xy = element["xy"]
    xs = sorted({x for x, _ in xy})
    ys = sorted({y for _, y in xy})
    require(
        len(xy) == 5
        and xy[0] == xy[-1]
        and len(xs) == len(ys) == 2
        and len(set(xy[:-1])) == 4
        and all(a[0] == b[0] or a[1] == b[1] for a, b in itertools.pairwise(xy)),
        "expected closed axis-aligned rectangle",
    )
    return element["layer"], xs[0], ys[0], xs[1], ys[1]


class Union:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        value = int(value)
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def join(self, nodes: list[int]) -> None:
        require(len(nodes) >= 2, "contact must join at least two components")
        root = self.find(min(nodes))
        for node in nodes:
            self.parent[self.find(node)] = root


def extract(elements: list[dict], *, retain_single_terminal: bool = False) -> dict:
    """Separate channels before joining conductors; never snap coordinates."""
    rects = [rectangle(e) for e in elements if e["kind"] == "polygon"]
    require(bool(rects), "empty geometry")
    xs = sorted({x for _, x0, _, x1, _ in rects for x in [x0, x1]})
    ys = sorted({y for _, _, y0, _, y1 in rects for y in [y0, y1]})
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: i for i, y in enumerate(ys)}
    shape = (len(ys) - 1, len(xs) - 1)
    masks = {layer: np.zeros(shape, dtype=bool) for layer in range(1, 8)}
    for layer, x0, y0, x1, y1 in rects:
        require(layer in masks, f"unsupported layer {layer}")
        masks[layer][yi[y0] : yi[y1], xi[x0] : xi[x1]] = True
    gates = masks[1] & masks[5] & ~masks[4]
    components = {}
    size = 1
    for layer, mask in [(1, masks[1] & ~gates), (5, masks[5]), (7, masks[7])]:
        array, count = ndimage.label(mask)  # Four-way connectivity; no corner join.
        array[array != 0] += size - 1
        components[layer] = array
        size += count
    union = Union(size)
    contact_counts = {}
    for layer in [4, 6]:
        regions, count = ndimage.label(masks[layer])
        contact_counts[layer] = count
        for index in range(1, count + 1):
            selected = regions == index
            nets = {l: sorted(set(a[selected]) - {0}) for l, a in components.items()}
            if layer == 4:
                require(bool(nets[1] and nets[5]), "buried contact misses conductor")
                nodes = nets[1] + nets[5]
            else:
                require(
                    bool(nets[7] and (nets[1] or nets[5])),
                    "cut misses metal or underlying conductor",
                )
                nodes = nets[1] + nets[5] + nets[7]
            union.join(nodes)
    lookup = np.array([union.find(i) for i in range(size)])
    components = {l: lookup[a] for l, a in components.items()}
    labels = defaultdict(set)
    for element in elements:
        if element["kind"] != "text":
            continue
        require(len(element["xy"]) == 1, "text must have one anchor")
        x, y = element["xy"][0]
        layer = element["layer"]
        require(layer in components, "label is not on a conductor layer")
        ix = int(np.searchsorted(xs, x, side="right")) - 1
        iy = int(np.searchsorted(ys, y, side="right")) - 1
        xx = [j for j in ([ix - 1, ix] if x in xi else [ix]) if 0 <= j < shape[1]]
        yy = [j for j in ([iy - 1, iy] if y in yi else [iy]) if 0 <= j < shape[0]]
        require(xs[0] <= x <= xs[-1] and ys[0] <= y <= ys[-1], "anchor outside layout")
        nodes = set(components[layer][np.ix_(yy, xx)].flat) - {0}
        require(len(nodes) == 1, f"ambiguous or unconnected anchor {element['text']}")
        labels[int(next(iter(nodes)))].add(element["text"])
    regions, count = ndimage.label(gates)
    devices = []
    unmodelled = []
    for index in range(1, count + 1):
        selected = regions == index
        gate_nodes = set(components[5][selected]) - {0}
        terminals = set(components[1][ndimage.binary_dilation(selected)]) - {0}
        require(
            len(gate_nodes) == 1
            and (
                len(terminals) == 2 or (retain_single_terminal and len(terminals) == 1)
            ),
            "gate needs two distinct terminals",
        )
        implants = [layer for layer in [2, 3] if (selected & masks[layer]).any()]
        require(len(implants) <= 1, "overlapping implant types")
        if implants:
            require((masks[implants[0]][selected]).all(), "partially implanted gate")
        yy, xx = np.where(selected)
        item = {
            "gate": int(next(iter(gate_nodes))),
            "terminals": sorted(map(int, terminals)),
            "implant": implants[0] if implants else 0,
            "xy": [xs[xx.min()], ys[yy.min()]],
        }
        if len(terminals) == 1:
            unmodelled.append({**item, "kind": "single_terminal_gate_region"})
        else:
            devices.append(item)
    result = {
        "labels": {str(n): sorted(v) for n, v in labels.items()},
        "devices": devices,
        "summary": {
            "devices": len(devices),
            "implants": dict(Counter(d["implant"] for d in devices)),
            "contact_regions": contact_counts,
            "nets": len({union.find(i) for i in range(1, size)}),
        },
    }
    if unmodelled:
        result["unmodelled_structures"] = unmodelled
        result["summary"]["unmodelled_structures"] = len(unmodelled)
    return result


def routing_groups(
    rects: list[tuple], labels: list[tuple]
) -> tuple[list[list[str]], list[str]]:
    """Trace supplied top wires/cuts only; other active cells remain excluded."""
    require(bool(rects), "empty routing")
    array = np.array(rects)
    union = Union(len(array))
    indices = np.arange(len(array))
    for i, (layer, x0, y0, x1, y1) in enumerate(array):
        require(x1 > x0 and y1 > y0, "empty routing rectangle")
        dx = np.minimum(x1, array[:, 3]) - np.maximum(x0, array[:, 1])
        dy = np.minimum(y1, array[:, 4]) - np.maximum(y0, array[:, 2])
        same = (array[:, 0] == layer) & (
            ((dx > 0) & (dy >= 0)) | ((dy > 0) & (dx >= 0))
        )
        cut = (
            (
                (array[:, 0] == 6) & np.isin(layer, [1, 5, 7])
                | (layer == 6) & np.isin(array[:, 0], [1, 5, 7])
            )
            & (dx > 0)
            & (dy > 0)
        )
        for j in np.flatnonzero((same | cut) & (indices > i)):
            union.join([i, int(j)])
    groups = defaultdict(set)
    unconnected = []
    for name, layer, x, y in labels:
        hits = np.flatnonzero(
            (array[:, 0] == layer)
            & (array[:, 1] <= x)
            & (array[:, 3] >= x)
            & (array[:, 2] <= y)
            & (array[:, 4] >= y)
        )
        roots = {union.find(i) for i in hits}
        require(len(roots) <= 1, f"ambiguous routing anchor {name}")
        if not roots:
            unconnected.append(name)
        else:
            groups[next(iter(roots))].add(name)
    return sorted(sorted(names) for names in groups.values()), sorted(unconnected)


def pla_truth(network: dict, bits: list[int]) -> list[int]:
    """Combinational evaluation with both pass banks open, not phase simulation."""
    require(
        not network.get("unmodelled_structures"),
        "unmodelled structures in logic network",
    )
    labels = {
        label: int(node) for node, names in network["labels"].items() for label in names
    }
    vdd, vss = labels["pla_vdd/1"], labels["pla_vss/1"]
    devices = network["devices"]
    require(all(d["implant"] in [2, 3] for d in devices), "unsupported PLA transistor")
    loads = set()
    for device in devices:
        if device["implant"] == 2:
            require(
                vdd in device["terminals"] and device["gate"] in device["terminals"],
                "invalid depletion load",
            )
            loads.add(next(n for n in device["terminals"] if n != vdd))
    logic = [d for d in devices if d["implant"] == 3]
    nodes = {n for d in devices for n in [d["gate"], *d["terminals"]]}
    fixed = {vdd: 1, vss: 0, labels["pla_clkin/1"]: 1, labels["pla_clk/1"]: 1}
    require(
        len(bits) == 5 and all(b in [0, 1] for b in bits), "expected five binary inputs"
    )
    fixed.update({labels[f"pla_in{i + 1}/1"]: b for i, b in enumerate(bits)})
    values = {n: 0 for n in nodes}
    values.update(fixed)
    for _ in range(40):
        union = Union(max(nodes) + 1)
        for device in logic:
            if values[device["gate"]]:
                union.join(device["terminals"])
        groups = defaultdict(list)
        for node in nodes:
            groups[union.find(node)].append(node)
        new = {}
        for group in groups.values():
            strong = {fixed[n] for n in group if n in fixed}
            require(len(strong) <= 1, "shorted fixed PLA inputs")
            value = (
                next(iter(strong))
                if strong
                else 1
                if loads.intersection(group)
                else values[group[0]]
            )
            new.update({n: value for n in group})
        if new == values:
            return [values[labels[f"pla_out{i + 1}/1"]] for i in range(5)]
        values = new
    raise ValueError("PLA did not settle")
