"""Recover complete named cells from the pinned, headerless MARIA GDS fragment.

Calma GDSII Stream Format 5.1 (August 1984), pp. 6-12, defines the framing
and records used here. This is not a repair of the absent library header.
Coordinates remain integers in unknown database units. No layer has an
assumed electrical meaning. Rendering is for inspection, not connectivity.
"""

import argparse
import hashlib
import json
import struct
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ARCHIVE_SHA = "849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48"
MEMBER_SHA = "9e9d9c2cff62357dadf9ef434a045efdfcc3014ae0f38bea6fb392b3e0df8db7"
MEMBER = "GCC_MARIA_Chip_Layout_and_Netlist_Artifacts/MARIAS/GDS/MARIAPAL.GDS"
TARGET = "VCELL_VCELL_GINGER$LOE_RSYNC_LY"
# Exact record/data-type pairs present in this fragment, not a general parser.
TYPES = {
    4: 0,
    5: 2,
    6: 6,
    7: 0,
    8: 0,
    9: 0,
    10: 0,
    12: 0,
    13: 2,
    14: 2,
    15: 3,
    16: 3,
    17: 0,
    18: 6,
    22: 2,
    23: 1,
    25: 6,
    26: 1,
    27: 5,
    28: 5,
    33: 2,
}


@dataclass(frozen=True)
class Record:
    offset: int
    kind: int
    data: bytes


def string(data: bytes) -> str:
    value = data.removesuffix(b"\0").decode("ascii")
    if not value or "\0" in value:
        raise ValueError("empty or embedded-null string")
    return value


def scan(
    data: bytes, start: int = 2
) -> tuple[dict[str, list[Record]], dict[str, object]]:
    offset = start
    cells: dict[str, list[Record]] = {}
    active: list[Record] | None = None
    name = ""
    counts: Counter[str] = Counter()
    partial_count = 0
    first_complete = None
    while offset + 4 <= len(data):
        length, kind, dtype = struct.unpack_from(">HBB", data, offset)
        if length < 4 or length % 2 or offset + length > len(data):
            raise ValueError(f"invalid record length at byte {offset}")
        if TYPES.get(kind) != dtype:
            raise ValueError(f"unsupported record {kind:02x}/{dtype} at byte {offset}")
        payload = data[offset + 4 : offset + length]
        if dtype == 0 and payload:
            raise ValueError(f"unexpected payload at byte {offset}")
        if (
            dtype in {1, 2}
            and len(payload) % 2
            or dtype == 3
            and len(payload) % 4
            or dtype == 5
            and len(payload) % 8
        ):
            raise ValueError(f"misaligned payload at byte {offset}")
        record = Record(offset, kind, payload)
        counts[f"{kind:02x}/{dtype}"] += 1
        if kind == 5:
            if active is not None or len(payload) != 24:
                raise ValueError(f"invalid structure start at byte {offset}")
            active = [record]
            name = ""
            if first_complete is None:
                first_complete = offset
        elif kind == 6:
            if active is None or name or len(active) != 1:
                raise ValueError(f"misplaced structure name at byte {offset}")
            name = string(payload)
            if name in cells:
                raise ValueError(f"duplicate structure {name}")
            active.append(record)
        elif kind == 7:
            if active is None:
                if cells or first_complete is not None:
                    raise ValueError(f"unmatched structure end at byte {offset}")
                partial_count += 1
            else:
                if not name:
                    raise ValueError("structure has no name")
                active.append(record)
                cells[name] = active
                active = None
        elif kind == 4:
            if active is not None or not cells:
                raise ValueError("library end before complete structures")
            end = offset + length
            return cells, {
                "record_start": start,
                "first_complete_structure": first_complete,
                "endlib_offset": offset,
                "record_end": end,
                "leading_fragment_records": partial_count,
                "trailing_bytes": len(data) - end,
                "trailing_sha256": hashlib.sha256(data[end:]).hexdigest(),
                "complete_named_cells": len(cells),
                "records": sum(counts.values()),
                "record_types": dict(sorted(counts.items())),
            }
        elif active is not None:
            if not name:
                raise ValueError("structure content before name")
            active.append(record)
        elif not cells and first_complete is None:
            partial_count += 1
        else:
            raise ValueError(f"record outside a structure at byte {offset}")
        offset += length
    raise ValueError("missing ENDLIB or truncated record")


def geometry(records: list[Record]) -> list[dict[str, object]]:
    elements = []
    current = None
    for record in records[2:-1]:
        kind, payload = record.kind, record.data
        if kind in {8, 12}:
            if current is not None:
                raise ValueError("nested element")
            current = {"kind": "polygon" if kind == 8 else "text"}
        elif kind == 17:
            if current is None or "xy" not in current or "layer" not in current:
                raise ValueError("incomplete element")
            xy = current["xy"]
            if current["kind"] == "polygon" and (len(xy) < 4 or xy[0] != xy[-1]):
                raise ValueError("unclosed polygon")
            if current["kind"] == "text" and (len(xy) != 1 or "text" not in current):
                raise ValueError("incomplete text")
            elements.append(current)
            current = None
        elif current is None:
            raise ValueError(f"unsupported flat-cell record {kind:02x}")
        elif kind == 13:
            if len(payload) != 2 or "layer" in current:
                raise ValueError("invalid layer")
            current["layer"] = struct.unpack(">h", payload)[0]
        elif kind == 16:
            if not payload or len(payload) % 8 or "xy" in current:
                raise ValueError("invalid coordinates")
            current["xy"] = list(struct.iter_unpack(">ii", payload))
        elif kind == 25 and current["kind"] == "text":
            current["text"] = string(payload)
        elif kind not in {14, 15, 22, 23, 26, 27, 28, 33}:
            raise ValueError(f"unsupported element record {kind:02x}")
    if current is not None or not elements:
        raise ValueError("unterminated or empty geometry")
    return elements


def render(elements: list[dict[str, object]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Polygon

    layers = sorted({element["layer"] for element in elements})
    colors = {layer: plt.get_cmap("tab10")(index) for index, layer in enumerate(layers)}
    figure, axes = plt.subplots(figsize=(18, 12))
    for element in elements:
        if element["kind"] == "polygon":
            axes.add_patch(
                Polygon(
                    element["xy"],
                    facecolor=colors[element["layer"]],
                    edgecolor=colors[element["layer"]],
                    alpha=0.35,
                    linewidth=0.3,
                )
            )
    for element in elements:
        if element["kind"] == "text":
            x, y = element["xy"][0]
            axes.text(x, y, element["text"], fontsize=5, color="black")
    axes.autoscale_view()
    axes.set_aspect("equal")
    axes.set_title(TARGET + " — layer numbers only; connectivity unqualified")
    axes.set_xlabel("native database coordinates (units absent)")
    axes.legend(
        handles=[
            Patch(color=colors[layer], label=f"Layer {layer}") for layer in layers
        ],
        loc="upper left",
        bbox_to_anchor=(1, 1),
    )
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--render", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("unqualified archive")
    with zipfile.ZipFile(args.archive) as archive:
        data = archive.read(MEMBER)
    if hashlib.sha256(data).hexdigest() != MEMBER_SHA:
        raise ValueError("unqualified layout member")
    cells, summary = scan(data)
    if len(cells) != 563 or TARGET not in cells:
        raise ValueError("incomplete pinned cell inventory")
    elements = geometry(cells[TARGET])
    kinds = Counter(element["kind"] for element in elements)
    if kinds != {"polygon": 1050, "text": 45}:
        raise ValueError(f"incomplete target geometry: {kinds}")
    labels = {element["text"] for element in elements if element["kind"] == "text"}
    if not {"dlireq", "haltclk", "intf"} <= labels:
        raise ValueError("missing interrupt labels")
    summary.update(
        {
            "archive_sha256": ARCHIVE_SHA,
            "member_sha256": MEMBER_SHA,
            "target": TARGET,
            "target_elements": dict(kinds),
            "target_layers": dict(Counter(element["layer"] for element in elements)),
            "target_labels": sorted(labels),
            "references": "none: flat target cell",
        }
    )
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    if args.render:
        render(elements, args.render)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in [
                    "complete_named_cells",
                    "records",
                    "target_elements",
                    "trailing_bytes",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
