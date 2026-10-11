"""State retention and rejection controls independent of the historical pad."""

import unittest

from probe_pads import Pad


def sampled_inverter() -> dict:
    return {
        "labels": {
            "1": ["test/in"],
            "20": ["test/pck2f"],
            "4": ["test/pad"],
            "10": ["test/vdd"],
            "11": ["test/vss"],
        },
        "devices": [
            {"gate": 20, "terminals": [1, 3], "implant": 3},
            {"gate": 3, "terminals": [4, 11], "implant": 3},
            {"gate": 4, "terminals": [4, 10], "implant": 2},
        ],
    }


class PadModelTests(unittest.TestCase):
    def test_closed_sample_gate_preserves_both_logic_levels(self) -> None:
        pad = Pad(sampled_inverter())
        for control, value, expected in [
            (1, 0, 1),
            (0, 1, 1),
            (1, 1, 0),
            (0, 0, 0),
            (1, 0, 1),
        ]:
            self.assertEqual(pad.settle({"in": value, "pck2f": control}), expected)

    def test_always_open_sample_gate_loses_hold(self) -> None:
        n = sampled_inverter()
        n["devices"][0]["gate"] = 10
        pad = Pad(n)
        self.assertEqual(pad.settle({"in": 0, "pck2f": 0}), 1)
        self.assertEqual(pad.settle({"in": 1, "pck2f": 0}), 0)

    def test_conflicting_driver_and_unqualified_load_bias_fail(self) -> None:
        n = sampled_inverter()
        n["devices"].append({"gate": 10, "terminals": [4, 10], "implant": 0})
        with self.assertRaisesRegex(ValueError, "conflicting settled"):
            Pad(n).settle({"in": 1, "pck2f": 1})
        n = sampled_inverter()
        n["devices"][-1]["gate"] = 1
        with self.assertRaisesRegex(ValueError, "depletion bias"):
            Pad(n).settle({"in": 0, "pck2f": 1})


if __name__ == "__main__":
    unittest.main()
