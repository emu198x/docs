"""Routing diagnostics must not silently widen the digital device model."""

import unittest
from unittest.mock import patch

from connect_layout import local_network
from layout_network import extract, pla_truth
from probe_controller_clock import Transfer
from probe_pads import Pad


def box(layer: int, x0: int, y0: int, x1: int, y1: int) -> dict:
    return {
        "kind": "polygon",
        "layer": layer,
        "xy": [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
    }


def tied_diffusion() -> list[dict]:
    return [
        box(1, 0, 0, 12, 4),
        box(5, 5, -2, 7, 6),
        box(2, 4, -1, 8, 5),
        box(7, 0, 1, 12, 3),
        box(6, 1, 1, 2, 2),
        box(6, 10, 1, 11, 2),
    ]


class UnmodelledTests(unittest.TestCase):
    def test_default_still_rejects_single_terminal_region(self) -> None:
        with self.assertRaisesRegex(ValueError, "two distinct terminals"):
            extract(tied_diffusion())

    def test_diagnostic_retains_structure_without_shorting_gate(self) -> None:
        n = extract(tied_diffusion(), retain_single_terminal=True)
        self.assertEqual(n["devices"], [])
        self.assertEqual(len(n["unmodelled_structures"]), 1)
        s = n["unmodelled_structures"][0]
        self.assertEqual(s["kind"], "single_terminal_gate_region")
        self.assertEqual(len(s["terminals"]), 1)
        self.assertNotIn(s["gate"], s["terminals"])
        self.assertEqual(n["summary"]["devices"], 0)

    def test_local_anchors_keep_both_conductors_separate(self) -> None:
        with patch("connect_layout.flatten", return_value=(tied_diffusion(), {})):
            _, n, routes = local_network({}, "test", retain_single_terminal=True)
        s = n["unmodelled_structures"][0]
        self.assertEqual(routes[1], s["gate"])
        self.assertEqual(routes[3], s["terminals"][0])
        self.assertNotEqual(routes[1], routes[3])

    def test_no_digital_solver_accepts_unmodelled_structures(self) -> None:
        n = {"unmodelled_structures": [{"kind": "single_terminal_gate_region"}]}
        for solver in [Pad, Transfer, lambda n: pla_truth(n, [0] * 5)]:
            with (
                self.subTest(solver=solver),
                self.assertRaisesRegex(ValueError, "unmodelled structures"),
            ):
                solver(n)


if __name__ == "__main__":
    unittest.main()
