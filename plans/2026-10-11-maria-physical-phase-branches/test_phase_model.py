"""Extraction boundaries and phase checks must reject plausible wrong results."""

import copy
import unittest

from probe_phases import isolate_output, validate_case


def small_network() -> dict:
    return {
        "labels": {
            "0": ["vss"],
            "1": ["out"],
            "2": ["other"],
            "10": ["input"],
            "11": ["vdd"],
        },
        "devices": [
            {"gate": 10, "terminals": [0, 1], "implant": 3},
            {"gate": 1, "terminals": [0, 2], "implant": 3},
            {"gate": 1, "terminals": [1, 11], "implant": 2},
            {"gate": 2, "terminals": [0, 10], "implant": 3},
        ],
    }


def complete_case() -> dict:
    return {
        "period_maria_cycles": 4,
        "dli": 1,
        "final_nmi": 1,
        "events": [
            {
                "level": 0,
                "phase": 2,
                "phase_step": 11,
                "halt": 0,
                "since_internal_halt_release": 3,
            },
            {
                "level": 1,
                "phase": 2,
                "phase_step": 19,
                "halt": 0,
                "since_internal_halt_release": 11,
            },
        ],
    }


class PhaseTests(unittest.TestCase):
    def test_cone_excludes_fanout_and_external_input_drivers(self) -> None:
        network = small_network()
        cone = isolate_output(network, "out", ["vss", "vdd", "input"])
        self.assertEqual(
            cone["devices"], [network["devices"][0], network["devices"][2]]
        )
        self.assertNotIn("2", cone["labels"])

    def test_missing_ambiguous_and_unmodelled_boundaries_fail(self) -> None:
        for name in ["missing", "input"]:
            n = small_network()
            if name == "input":
                n["labels"]["20"] = ["input"]
            with self.assertRaisesRegex(ValueError, "ambiguous cone boundary"):
                isolate_output(n, "out", ["vss", "vdd", name])
        n = small_network()
        n["unmodelled_structures"] = [{"kind": "unknown"}]
        with self.assertRaisesRegex(ValueError, "unmodelled structures"):
            isolate_output(n, "out", ["vss", "vdd", "input"])

    def test_complete_case_passes_and_missing_pulse_fails(self) -> None:
        validate_case(complete_case())
        n = complete_case()
        n["events"] = []
        with self.assertRaisesRegex(ValueError, "pulse inventory"):
            validate_case(n)

    def test_transparent_or_short_pulse_fails(self) -> None:
        n = complete_case()
        n["events"][0]["phase"] = 1
        with self.assertRaisesRegex(ValueError, "outside phase 2"):
            validate_case(n)
        n = complete_case()
        n["events"][1]["phase_step"] = 17
        with self.assertRaisesRegex(ValueError, "width differs"):
            validate_case(n)

    def test_pulse_before_halt_start_is_not_mistaken_for_completed_dma(self) -> None:
        n = copy.deepcopy(complete_case())
        n["events"][0]["since_internal_halt_release"] = -10
        with self.assertRaisesRegex(ValueError, "before internal HALT release"):
            validate_case(n)


if __name__ == "__main__":
    unittest.main()
