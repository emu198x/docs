"""Bounded GDS hierarchy expansion; no invented units or electrical layers.

Calma Stream Format 5.1 pp. 11-13: reflect about X before rotation; positive
angles are counterclockwise. Support unit magnification, orthogonal SREFs
and square-extended Manhattan paths only. Unsupported forms fail explicitly.
"""

import struct
import sys
from collections import Counter
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-interrupt-circuit"),
)
from layout_network import require
from trace_circuit import g, groups

IDENTITY = (1, 0, 0, 1, 0, 0)


def real64(data: bytes) -> Fraction:
    require(len(data) == 8, "expected eight-byte GDS real")
    sign = -1 if data[0] & 0x80 else 1
    mantissa = int.from_bytes(data[1:], "big")
    return sign * Fraction(mantissa, 1 << 56) * Fraction(16) ** ((data[0] & 0x7F) - 64)


def transform(point: tuple[int, int], matrix: tuple) -> tuple[int, int]:
    a, b, c, d, x, y = matrix
    return a * point[0] + b * point[1] + x, c * point[0] + d * point[1] + y


def compose(outer: tuple, inner: tuple) -> tuple:
    a, b, c, d, x, y = outer
    e, f, h, i, u, v = inner
    return (
        a * e + b * h,
        a * f + b * i,
        c * e + d * h,
        c * f + d * i,
        a * u + b * v + x,
        c * u + d * v + y,
    )


def reference_matrix(records: dict[int, bytes]) -> tuple:
    require(
        set(records) <= {10, 18, 26, 27, 28, 16, 17}
        and {10, 18, 16, 17} <= set(records),
        "unsupported SREF records",
    )
    flags = struct.unpack(">H", records.get(26, b"\0\0"))[0]
    require(flags in [0, 0x8000], "absolute or reserved transform flags")
    require(
        real64(records[27]) == 1 if 27 in records else True, "unsupported magnification"
    )
    angle = real64(records[28]) if 28 in records else Fraction(0)
    require(angle.denominator == 1 and angle % 90 == 0, "nonorthogonal rotation")
    rotation = [(1, 0, 0, 1), (0, -1, 1, 0), (-1, 0, 0, -1), (0, 1, -1, 0)][
        int(angle // 90) % 4
    ]
    a, b, c, d = rotation
    if flags & 0x8000:
        b, d = -b, -d
    x, y = struct.unpack(">ii", records[16])
    return a, b, c, d, x, y


def path_rectangles(records: dict[int, bytes]) -> list[dict]:
    require(set(records) == {9, 13, 14, 33, 15, 16, 17}, "unsupported path records")
    layer = struct.unpack(">h", records[13])[0]
    style = struct.unpack(">h", records[33])[0]
    width = struct.unpack(">i", records[15])[0]
    require(
        style == 2 and width > 0 and width % 2 == 0, "unsupported path style or width"
    )
    points = list(struct.iter_unpack(">ii", records[16]))
    require(len(points) >= 2, "path has fewer than two points")
    result = []
    half = width // 2
    for (x0, y0), (x1, y1) in pairwise(points):
        require(x0 == x1 or y0 == y1, "non-Manhattan path")
        left, right = min(x0, x1) - half, max(x0, x1) + half
        bottom, top = min(y0, y1) - half, max(y0, y1) + half
        result.append(
            {
                "kind": "polygon",
                "layer": layer,
                "xy": [
                    (left, bottom),
                    (right, bottom),
                    (right, top),
                    (left, top),
                    (left, bottom),
                ],
            }
        )
    return result


def orthogonal_rectangles(element: dict) -> list[dict]:
    """Decompose a simple Manhattan boundary exactly into horizontal bands."""
    points = element["xy"]
    require(len(points) >= 5 and points[0] == points[-1], "unclosed boundary")
    # Legacy boundaries include collinear zero-area spurs. Removing a
    # middle collinear vertex changes no filled area, including a backtrack.
    original_area2 = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in pairwise(points)))
    vertices = list(points[:-1])
    while len(vertices) >= 3:
        removed = False
        for index, point in enumerate(vertices):
            before, after = vertices[index - 1], vertices[(index + 1) % len(vertices)]
            if before[0] == point[0] == after[0] or before[1] == point[1] == after[1]:
                vertices.pop(index)
                removed = True
                break
        if not removed:
            break
    require(len(vertices) >= 4, "boundary has no filled area")
    points = vertices + vertices[:1]
    segments = list(pairwise(points))
    require(len(set(points[:-1])) == len(points) - 1, "repeated boundary vertex")
    require(
        all(a != b and (a[0] == b[0] or a[1] == b[1]) for a, b in segments),
        "non-Manhattan boundary",
    )
    for i, (a, b) in enumerate(segments):
        for j, (c, d) in enumerate(segments[i + 1 :], i + 1):
            if j == i + 1 or (i == 0 and j == len(segments) - 1):
                continue
            intersects = max(min(a[0], b[0]), min(c[0], d[0])) <= min(
                max(a[0], b[0]), max(c[0], d[0])
            ) and max(min(a[1], b[1]), min(c[1], d[1])) <= min(
                max(a[1], b[1]), max(c[1], d[1])
            )
            require(not intersects, "self-touching or crossing boundary")
    ys = sorted({y for x, y in points})
    result = []
    for bottom, top in pairwise(ys):
        middle = bottom + top
        xs = sorted(
            a[0]
            for a, b in segments
            if a[0] == b[0] and 2 * min(a[1], b[1]) < middle < 2 * max(a[1], b[1])
        )
        require(len(xs) % 2 == 0, "odd boundary intersections")
        for left, right in zip(xs[::2], xs[1::2], strict=True):
            require(right > left, "empty boundary band")
            result.append(
                {
                    "kind": "polygon",
                    "layer": element["layer"],
                    "xy": [
                        (left, bottom),
                        (right, bottom),
                        (right, top),
                        (left, top),
                        (left, bottom),
                    ],
                }
            )
    area2 = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in segments))
    split_area2 = 2 * sum(
        (e["xy"][1][0] - e["xy"][0][0]) * (e["xy"][2][1] - e["xy"][1][1])
        for e in result
    )
    require(
        area2 > 0 and area2 == split_area2 == original_area2, "boundary area changed"
    )
    return result


def flatten(cells: dict, root: str) -> tuple[list[dict], dict]:
    inventory = Counter()
    output = []

    def visit(
        name: str, matrix: tuple, ancestors: tuple[str, ...], prefix: str
    ) -> None:
        require(name in cells, f"missing cell {name}")
        require(name not in ancestors, f"recursive cell {name}")
        inventory[name] += 1
        for index, records in enumerate(groups(cells[name])):
            mapping = {r.kind: r.data for r in records}
            require(len(mapping) == len(records), "duplicate element attribute")
            kind = records[0].kind
            if kind == 10:
                child = g.string(mapping[18])
                visit(
                    child,
                    compose(matrix, reference_matrix(mapping)),
                    (*ancestors, name),
                    prefix + f"{index}:{child}/",
                )
                continue
            if kind in [8, 12]:
                elements = g.geometry(cells[name][:2] + records + cells[name][-1:])
            elif kind == 9:
                elements = path_rectangles(mapping)
            else:
                raise ValueError(f"unsupported hierarchical element {kind:02x}")
            for element in elements:
                element["xy"] = [transform(point, matrix) for point in element["xy"]]
                if element["kind"] == "polygon":
                    output.extend(orthogonal_rectangles(element))
                    continue
                else:
                    element["text"] = prefix + element["text"]
                output.append(element)

    visit(root, IDENTITY, (), root + "/")
    return output, dict(inventory)
