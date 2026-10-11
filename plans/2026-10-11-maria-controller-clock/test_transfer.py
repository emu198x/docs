"""Transfer solver checks against explicit Boolean inverter behaviour."""

import copy
import unittest

from probe_controller_clock import CORE, ROOT, Transfer


def inverters() -> dict:
    prefix = ROOT + "/0:" + CORE + "/"
    labels = {str(i): [prefix + f"in{i}"] for i in range(1, 12)}
    labels.update({str(40 + i): [prefix + f"out{i}"] for i in range(1, 11)})
    labels.update(
        {
            "100": [prefix + "vdd"],
            "101": [prefix + "vss"],
            "102": [prefix + "clk"],
            "103": [prefix + "clkin"],
        }
    )
    devices = [
        {"gate": 103, "terminals": [i, 20 + i], "implant": 3} for i in range(1, 12)
    ]
    for i in range(1, 11):
        devices.extend(
            [
                {"gate": 20 + i, "terminals": [40 + i, 101], "implant": 3},
                {"gate": 40 + i, "terminals": [40 + i, 100], "implant": 2},
            ]
        )
    return {"labels": labels, "devices": devices}


class TransferTests(unittest.TestCase):
    def test_sampled_inputs_drive_inverters_without_feedback_race(self) -> None:
        transfer = Transfer(inverters())
        patterns = [[0] * 11, [1] * 11, [i % 2 for i in range(11)]]
        patterns += [[int(i == selected) for i in range(11)] for selected in range(11)]
        for bits in patterns:
            with self.subTest(bits=bits):
                self.assertEqual(transfer.solve(bits), [1 - b for b in bits[:10]])

    def test_settled_supply_conflict_fails(self) -> None:
        network = inverters()
        network["devices"].append({"gate": 100, "terminals": [41, 100], "implant": 0})
        with self.assertRaisesRegex(ValueError, "conflicting settled"):
            Transfer(network).solve([1] * 11)

    def test_missing_sample_gate_and_invalid_load_fail(self) -> None:
        network = inverters()
        broken = copy.deepcopy(network)
        broken["devices"].pop(0)
        with self.assertRaisesRegex(ValueError, "input sample gate"):
            Transfer(broken)
        broken = copy.deepcopy(network)
        broken["devices"][-1]["gate"] = 1
        with self.assertRaisesRegex(ValueError, "depletion-load"):
            Transfer(broken)


if __name__ == "__main__":
    unittest.main()
