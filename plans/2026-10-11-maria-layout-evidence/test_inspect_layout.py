"""Framing and geometry controls independent of the historical layout."""

import struct
import unittest

from inspect_layout import Record, geometry, scan


def record(kind: int, dtype: int = 0, payload: bytes = b"") -> bytes:
    return struct.pack(">HBB", len(payload) + 4, kind, dtype) + payload


def cell(name: bytes = b"TEST") -> bytes:
    return record(5, 2, bytes(24)) + record(6, 6, name) + record(7)


class LayoutTests(unittest.TestCase):
    def test_complete_cell_excludes_initial_fragment_and_trailer(self) -> None:
        # Starting in a prior boundary's datatype is the explicit input shape.
        prefix = b"\x00\x05" + record(14, 2, b"\x00\x00") + record(7)
        data = prefix + cell() + record(4) + b"TRAILER"
        cells, summary = scan(data)
        self.assertEqual(list(cells), ["TEST"])
        self.assertEqual(summary["first_complete_structure"], len(prefix))
        self.assertEqual(summary["leading_fragment_records"], 2)
        self.assertEqual(summary["trailing_bytes"], 7)
        self.assertEqual(summary["records"], 6)

    def test_invalid_lengths_types_and_missing_end_fail(self) -> None:
        for data in [
            b"\x00\x02\x04\x00",
            b"\x00\x05\x06\x06X",
            b"\x00\x08\x06\x06AB",
            record(5, 0),
            record(5, 2, b"\0\0"),
            cell(),
            record(4),
            record(5, 2, bytes(24)) + record(4),
        ]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                scan(data, start=0)

    def test_duplicate_and_misplaced_names_fail(self) -> None:
        for data in [
            cell() + cell() + record(4),
            record(6, 6, b"TEST") + record(4),
            record(5, 2, bytes(24))
            + record(8)
            + record(6, 6, b"TEST")
            + record(7)
            + record(4),
        ]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                scan(data, start=0)

    def test_polygon_coordinates_and_text_are_retained(self) -> None:
        points = [(0, 0), (100, 0), (100, 50), (0, 50), (0, 0)]
        polygon = [
            Record(0, 8, b""),
            Record(0, 13, struct.pack(">h", 3)),
            Record(0, 14, b"\0\0"),
            Record(0, 16, b"".join(struct.pack(">ii", *p) for p in points)),
            Record(0, 17, b""),
        ]
        text = [
            Record(0, 12, b""),
            Record(0, 13, struct.pack(">h", 7)),
            Record(0, 16, struct.pack(">ii", 20, 25)),
            Record(0, 25, b"signal"),
            Record(0, 17, b""),
        ]
        cells = [
            Record(0, 5, bytes(24)),
            Record(0, 6, b"TEST"),
            *polygon,
            *text,
            Record(0, 7, b""),
        ]
        result = geometry(cells)
        self.assertEqual(result[0], {"kind": "polygon", "layer": 3, "xy": points})
        self.assertEqual(
            result[1], {"kind": "text", "layer": 7, "xy": [(20, 25)], "text": "signal"}
        )
        for bad in [
            [Record(0, 10, b"")],  # Reference needs an explicit transform model.
            polygon[:-1],
            [
                polygon[0],
                polygon[1],
                Record(0, 16, struct.pack(">iiiiiiii", 0, 0, 10, 0, 10, 10, 0, 10)),
                polygon[-1],
            ],
            [Record(0, 17, b"")],
        ]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                geometry(cells[:2] + bad + cells[-1:])


if __name__ == "__main__":
    unittest.main()
