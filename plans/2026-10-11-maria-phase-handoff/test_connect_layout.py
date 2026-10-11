"""Parent routing must preserve geometry and explicit local-net identity."""

import unittest

from connect_layout import join_rectangles


class ConnectTests(unittest.TestCase):
    def test_same_layer_edge_connects_but_corner_does_not(self) -> None:
        rects = [(5, 0, 0, 4, 4), (5, 4, 0, 8, 4), (5, 8, 4, 12, 8)]
        union = join_rectangles(rects, [], 3)
        self.assertEqual(union.find(0), union.find(1))
        self.assertNotEqual(union.find(1), union.find(2))

    def test_crossing_layers_need_contact(self) -> None:
        rects = [(5, 0, 0, 6, 2), (7, 2, -2, 4, 4)]
        union = join_rectangles(rects, [], 2)
        self.assertNotEqual(union.find(0), union.find(1))
        rects.append((6, 2, 0, 4, 2))
        union = join_rectangles(rects, [], 3)
        self.assertEqual(union.find(0), union.find(1))

    def test_proven_local_net_joins_separate_parent_footprints(self) -> None:
        rects = [(5, 0, 0, 4, 4), (7, 10, 0, 14, 4), (5, 14, 0, 18, 4)]
        isolated = join_rectangles(rects, [], 4)
        self.assertNotEqual(isolated.find(0), isolated.find(1))
        # Node 3 is the separately extracted local net, not a shared label.
        joined = join_rectangles(rects, [(0, 3), (1, 3)], 4)
        self.assertEqual(joined.find(0), joined.find(1))
        self.assertNotEqual(joined.find(1), joined.find(2))

    def test_missing_contact_does_not_join_nearby_shape(self) -> None:
        rects = [(5, 0, 0, 4, 4), (7, 8, 0, 12, 4), (6, 4, 0, 8, 4)]
        union = join_rectangles(rects, [], 3)
        self.assertEqual(len({union.find(i) for i in range(3)}), 3)


class BindingTests(unittest.TestCase):
    def test_missing_physical_route_fails_even_when_both_ports_exist(self) -> None:
        from connect_layout import shared_route

        with self.assertRaisesRegex(ValueError, "missing physical port route"):
            shared_route({"labels": {"1": ["a"], "2": ["b"]}}, "a", "b")
        self.assertEqual(shared_route({"labels": {"1": ["a", "b"]}}, "a", "b"), 1)

    def test_same_name_on_distinct_nodes_cannot_supply_a_phase_binding(self) -> None:
        from connect_layout import named_binding

        with self.assertRaisesRegex(ValueError, "ambiguous named binding"):
            named_binding({"labels": {"1": ["TOP/ph1"], "2": ["TOP/ph1"]}}, "TOP/ph1")
        self.assertEqual(named_binding({"labels": {"1": ["TOP/ph1"]}}, "TOP/ph1"), 1)


if __name__ == "__main__":
    unittest.main()
