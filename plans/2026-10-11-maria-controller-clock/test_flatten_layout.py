"""Independent geometry controls for the hierarchy probe."""

import struct
import unittest
from fractions import Fraction

from flatten_layout import (
    compose,
    flatten,
    g,
    orthogonal_rectangles,
    path_rectangles,
    real64,
    reference_matrix,
    transform,
)


def reference(
    name: bytes, x: int, y: int, flags: int = 0, angle: bytes | None = None
) -> list:
    items = [
        g.Record(0, 10, b""),
        g.Record(0, 18, name),
        g.Record(0, 26, struct.pack(">H", flags)),
        g.Record(0, 16, struct.pack(">ii", x, y)),
    ]
    if angle is not None:
        items.append(g.Record(0, 28, angle))
    return items + [g.Record(0, 17, b"")]


def cell(name: bytes, contents: list) -> list:
    return [
        g.Record(0, 5, bytes(24)),
        g.Record(0, 6, name),
        *contents,
        g.Record(0, 7, b""),
    ]


class FlattenTests(unittest.TestCase):
    def test_exact_real_and_reflection_before_rotation(self) -> None:
        ninety = bytes.fromhex("425a000000000000")
        self.assertEqual(real64(ninety), Fraction(90))
        records = {r.kind: r.data for r in reference(b"LEAF", 100, 200, 0x8000, ninety)}
        # Reflect (2,3)->(2,-3), rotate CCW ->(3,2), then translate.
        self.assertEqual(transform((2, 3), reference_matrix(records)), (103, 202))
        self.assertEqual(real64(bytes.fromhex("c25a000000000000")), Fraction(-90))
        self.assertEqual(real64(bytes(8)), Fraction(0))

    def test_nested_composition_matches_sequential_coordinates(self) -> None:
        outer = (0, -1, 1, 0, 100, 200)
        inner = (-1, 0, 0, 1, 13, -7)
        for point in [(0, 0), (3, 5), (-12, 9)]:
            self.assertEqual(
                transform(point, compose(outer, inner)),
                transform(transform(point, inner), outer),
            )

    def test_unsupported_transform_fails(self) -> None:
        for flags, angle in [(2, None), (0, bytes.fromhex("422d000000000000"))]:
            records = {r.kind: r.data for r in reference(b"L", 0, 0, flags, angle)}
            with self.assertRaises(ValueError):
                reference_matrix(records)

    def test_square_extended_path_retains_bend_and_end_caps(self) -> None:
        records = {
            9: b"",
            13: struct.pack(">h", 5),
            14: b"\0\0",
            33: struct.pack(">h", 2),
            15: struct.pack(">i", 4),
            16: struct.pack(">iiiiii", 0, 0, 10, 0, 10, 8),
            17: b"",
        }
        shapes = path_rectangles(records)
        self.assertEqual(
            shapes[0]["xy"], [(-2, -2), (12, -2), (12, 2), (-2, 2), (-2, -2)]
        )
        self.assertEqual(
            shapes[1]["xy"], [(8, -2), (12, -2), (12, 10), (8, 10), (8, -2)]
        )
        records[33] = b"\0\1"
        with self.assertRaises(ValueError):
            path_rectangles(records)

    def test_concave_boundary_preserves_shape(self) -> None:
        e = {
            "kind": "polygon",
            "layer": 1,
            "xy": [(0, 0), (6, 0), (6, 2), (2, 2), (2, 5), (0, 5), (0, 0)],
        }
        result = orthogonal_rectangles(e)
        self.assertEqual(
            [s["xy"] for s in result],
            [
                [(0, 0), (6, 0), (6, 2), (0, 2), (0, 0)],
                [(0, 2), (2, 2), (2, 5), (0, 5), (0, 2)],
            ],
        )

    def test_collinear_spur_changes_no_filled_area(self) -> None:
        plain = {
            "kind": "polygon",
            "layer": 1,
            "xy": [(0, 0), (6, 0), (6, 4), (0, 4), (0, 0)],
        }
        spur = {**plain, "xy": [(0, 0), (6, 0), (6, 4), (0, 4), (0, -2), (0, 0)]}
        self.assertEqual(orthogonal_rectangles(spur), orthogonal_rectangles(plain))

    def test_proper_crossing_and_diagonal_boundary_fail(self) -> None:
        for points in [
            [(0, 0), (6, 0), (6, 6), (2, 6), (2, -2), (4, -2), (4, 4), (0, 4), (0, 0)],
            [(0, 0), (6, 0), (2, 3), (0, 4), (0, 0)],
        ]:
            with self.assertRaises(ValueError):
                orthogonal_rectangles({"kind": "polygon", "layer": 1, "xy": points})

    def test_nested_reference_geometry_and_missing_cells(self) -> None:
        ninety = bytes.fromhex("425a000000000000")
        polygon = [
            g.Record(0, 8, b""),
            g.Record(0, 13, struct.pack(">h", 5)),
            g.Record(0, 14, b"\0\0"),
            g.Record(0, 16, struct.pack(">iiiiiiiiii", 0, 0, 4, 0, 4, 2, 0, 2, 0, 0)),
            g.Record(0, 17, b""),
        ]
        cells = {
            "ROOT": cell(b"ROOT", reference(b"MID", 100, 200, 0x8000, ninety)),
            "MID": cell(b"MID", reference(b"LEAF", 10, 20)),
            "LEAF": cell(b"LEAF", polygon),
        }
        elements, inv = flatten(cells, "ROOT")
        self.assertEqual(inv, {"ROOT": 1, "MID": 1, "LEAF": 1})
        self.assertEqual(
            elements[0]["xy"],
            [(120, 210), (122, 210), (122, 214), (120, 214), (120, 210)],
        )
        del cells["LEAF"]
        with self.assertRaisesRegex(ValueError, "missing cell"):
            flatten(cells, "ROOT")
        cells["LEAF"] = cell(b"LEAF", reference(b"ROOT", 0, 0))
        with self.assertRaisesRegex(ValueError, "recursive cell"):
            flatten(cells, "ROOT")


if __name__ == "__main__":
    unittest.main()
