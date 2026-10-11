"""Small circuit invariants independent of the archived layout."""

import copy
import itertools
import unittest

from layout_network import extract, pla_truth, rectangle, routing_groups


def box(layer: int, x0: int, y0: int, x1: int, y1: int) -> dict:
    return {
        "kind": "polygon",
        "layer": layer,
        "xy": [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
    }


def label(name: str, layer: int, x: int, y: int) -> dict:
    return {"kind": "text", "layer": layer, "xy": [(x, y)], "text": name}


def transistor() -> list[dict]:
    return [
        box(1, 0, 0, 12, 4),
        box(5, 5, -2, 7, 6),
        box(3, 4, -1, 8, 5),
        label("drain", 1, 1, 1),
        label("source", 1, 10, 1),
        label("gate", 5, 6, -1),
    ]


def nodes(network: dict) -> dict[str, int]:
    return {name: int(n) for n, names in network["labels"].items() for name in names}


class NetworkTests(unittest.TestCase):
    def test_gate_separates_diffusion_and_does_not_short_to_poly(self) -> None:
        result = extract(transistor())
        names = nodes(result)
        self.assertEqual(len(set(names.values())), 3)
        self.assertEqual(
            result["devices"],
            [
                {
                    "gate": names["gate"],
                    "terminals": sorted([names["drain"], names["source"]]),
                    "implant": 3,
                    "xy": [5, 0],
                }
            ],
        )

    def test_metal_crossing_connects_only_with_cut(self) -> None:
        elements = transistor() + [box(7, 0, 0, 3, 4), label("metal", 7, 1, 2)]
        disconnected = nodes(extract(elements))
        self.assertNotEqual(disconnected["metal"], disconnected["drain"])
        connected = nodes(extract(elements + [box(6, 1, 1, 2, 2)]))
        self.assertEqual(connected["metal"], connected["drain"])
        self.assertNotEqual(connected["metal"], connected["gate"])

    def test_buried_contact_connects_poly_without_creating_gate(self) -> None:
        result = extract(transistor() + [box(4, 5, 0, 7, 4)])
        self.assertEqual(result["devices"], [])
        self.assertEqual(len(set(nodes(result).values())), 1)

    def test_nonuniform_integer_coordinates_do_not_snap(self) -> None:
        elements = transistor()
        for element in elements:
            element["xy"] = [
                (x * 1000 + (8 if x >= 7 else 0) - 229508, y * 750)
                for x, y in element["xy"]
            ]
        result = extract(elements)
        self.assertEqual(len(result["devices"]), 1)
        self.assertEqual(result["devices"][0]["xy"], [-224508, 0])
        self.assertEqual(len(set(nodes(result).values())), 3)

    def test_missing_contact_and_ambiguous_anchor_fail(self) -> None:
        for elements in [
            transistor() + [box(6, 1, 1, 2, 2)],
            transistor() + [label("outside", 7, 100, 100)],
            [box(5, 0, 0, 2, 2), box(5, 2, 2, 4, 4), label("corner", 5, 2, 2)],
        ]:
            with self.subTest(elements=elements), self.assertRaises(ValueError):
                extract(elements)

    def test_corner_only_touch_is_not_a_route(self) -> None:
        labels = [("a", 5, 1, 1), ("b", 5, 3, 3)]
        groups, _ = routing_groups([(5, 0, 0, 2, 2), (5, 2, 2, 4, 4)], labels)
        self.assertEqual(groups, [["a"], ["b"]])
        labels[1] = ("b", 5, 3, 1)
        groups, _ = routing_groups([(5, 0, 0, 2, 2), (5, 2, 0, 4, 2)], labels)
        self.assertEqual(groups, [["a", "b"]])

    def test_nonrectangular_or_diagonal_polygon_fails(self) -> None:
        bad = box(1, 0, 0, 2, 2)
        bad["xy"][1], bad["xy"][2] = bad["xy"][2], bad["xy"][1]
        with self.assertRaisesRegex(ValueError, "axis-aligned"):
            rectangle(bad)

    def test_five_independent_inverters_match_boolean_complements(self) -> None:
        network = {
            "labels": {
                "0": ["pla_vdd/1"],
                "11": ["pla_vss/1"],
                "12": ["pla_clkin/1"],
                "13": ["pla_clk/1"],
            },
            "devices": [],
        }
        for index in range(1, 6):
            output = index + 5
            network["labels"][str(index)] = [f"pla_in{index}/1"]
            network["labels"][str(output)] = [f"pla_out{index}/1"]
            network["devices"] += [
                {"gate": index, "terminals": [output, 11], "implant": 3},
                {"gate": output, "terminals": [0, output], "implant": 2},
            ]
        for bits in itertools.product(range(2), repeat=5):
            self.assertEqual(pla_truth(network, list(bits)), [1 - b for b in bits])
        broken = copy.deepcopy(network)
        broken["devices"][1]["gate"] = 1
        with self.assertRaisesRegex(ValueError, "depletion load"):
            pla_truth(broken, [0] * 5)


if __name__ == "__main__":
    unittest.main()
