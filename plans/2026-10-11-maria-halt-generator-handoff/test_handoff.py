"""The handoff guards must reject plausible traces with missing/wrong edges."""

import json
import unittest
from pathlib import Path

from probe_handoff import check_case
from summarize import summarize


def sample() -> dict:
    return json.loads(Path(__file__).with_name("sample-fast.json").read_text())


class HandoffTests(unittest.TestCase):
    def test_complete_sample_and_missing_trace(self) -> None:
        row = sample()
        self.assertEqual(check_case(row)["width"], 8)
        row["rows"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete handoff trace"):
            check_case(row)

    def test_warmup_is_a_measured_gate(self) -> None:
        row = sample()
        row["rows"][40]["halt"] = 1
        with self.assertRaisesRegex(ValueError, "warm-up did not reach idle"):
            check_case(row)

    def test_suppressed_nmi_fails(self) -> None:
        row = sample()
        for r in row["rows"]:
            r["nmi"] = 1
        with self.assertRaisesRegex(ValueError, "wrong NMI inventory"):
            check_case(row)

    def test_wrong_latch_phase_fails(self) -> None:
        row = sample()
        first = next(r for r in row["rows"] if r["nmi"] == 0)
        first["ph2"] = 0
        with self.assertRaisesRegex(ValueError, "NMI changes outside phase 2"):
            check_case(row)

    def test_pad_must_change_outside_cpu_phase2(self) -> None:
        row = sample()
        first = next(r for r in row["rows"][32:] if r["halt_pad"] == 0)
        first["pck2"] = 1
        with self.assertRaisesRegex(ValueError, "HALT pad changes during CPU phase 2"):
            check_case(row)

    def test_no_clock_edges_cannot_prove_a_cycle(self) -> None:
        row = sample()
        for r in row["rows"]:
            r["pck0"] = 1
        with self.assertRaisesRegex(ValueError, "span one CPU clock falling edge"):
            check_case(row)

    def test_idle_before_dma_is_not_mistaken_for_release(self) -> None:
        row = sample()
        for r in row["rows"][49:123]:
            r["nmi"] = 0
        with self.assertRaisesRegex(ValueError, "NMI precedes HALT release"):
            check_case(row)

    def test_empty_or_repeated_matrix_cannot_pass(self) -> None:
        row = check_case(sample())
        for rows in [[], [row], [row] * 32832]:
            with self.assertRaisesRegex(ValueError, "incomplete or duplicate"):
                summarize(rows)


if __name__ == "__main__":
    unittest.main()
