"""Reject missing observations and partial-cycle pulses independently of RTL."""

import unittest

from probe_edge import parse, qualify_polarity, replace_once

CASE = (1, 2, 1, 2, 0, 0)


def fixture() -> str:
    rows = ["RESULT ok=1", "FETCH_RESULT ok=1", "SELECTOR_RESULT ok=1"]
    for observer in range(3):
        start = 1000 + observer * 4
        width = 2 if observer == 0 else 8
        for level, tick in [(0, start), (1, start + width)]:
            event = f"tick={tick} row=17 col=20 level={level} halt=1 delay=9 width={width if level else 0} cpu_cycles={int(observer > 0)} same_phase={int(observer > 0)}"
            rows.append(f"EDGE_NMI observer={observer} {event}")
            if observer == 0:
                rows.append("SELECTOR " + event)
        rows.append(
            f"EDGE_RESULT observer={observer} assertions=1 releases=1 final=1 samples=2000 events=500 high=500"
        )
    return "\n".join(rows)


class ProbeTests(unittest.TestCase):
    def test_complete_observations_pass(self) -> None:
        result = parse(fixture(), CASE)
        self.assertEqual([r["widths"] for r in result["observers"]], [[2], [8], [8]])

    def test_one_edge_without_returning_to_same_phase_fails(self) -> None:
        bad = fixture().replace(
            "cpu_cycles=1 same_phase=1", "cpu_cycles=1 same_phase=0"
        )
        with self.assertRaisesRegex(ValueError, "different CPU phase"):
            parse(bad, CASE)

    def test_wrong_cycle_count_fails(self) -> None:
        bad = fixture().replace(
            "cpu_cycles=1 same_phase=1", "cpu_cycles=2 same_phase=1"
        )
        with self.assertRaisesRegex(ValueError, "one live CPU cycle"):
            parse(bad, CASE)

    def test_research_capture_preserves_failed_cycle_qualification(self) -> None:
        bad = fixture().replace(
            "cpu_cycles=1 same_phase=1", "cpu_cycles=1 same_phase=0"
        )
        results = parse(bad, CASE, record_cycle_failures=True)["observers"]
        self.assertEqual(
            results[1]["cycle_qualification_failure"],
            "NMI release has different CPU phase",
        )
        self.assertEqual(results[1]["phase_mismatches"], 1)

    def test_zero_or_missing_observations_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing clock observations"):
            parse(fixture().replace("samples=2000", "samples=0"), CASE)
        bad = "\n".join(
            s
            for s in fixture().splitlines()
            if not s.startswith("EDGE_RESULT observer=2")
        )
        with self.assertRaisesRegex(ValueError, "missing observer outcomes"):
            parse(bad, CASE)

    def test_suppressed_flagged_pulse_fails(self) -> None:
        bad = "\n".join(
            s for s in fixture().splitlines() if not s.startswith("EDGE_NMI observer=1")
        )
        bad = bad.replace(
            "observer=1 assertions=1 releases=1", "observer=1 assertions=0 releases=0"
        )
        with self.assertRaisesRegex(ValueError, "wrong observer pulse inventory"):
            parse(bad, CASE)

    def test_baseline_trace_change_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "baseline edge trace differs"):
            parse(fixture().replace("SELECTOR tick=1000", "SELECTOR tick=999"), CASE)

    def test_empty_equations_and_ambiguous_instrumentation_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "selector term inventory"):
            qualify_polarity("")
        for source in ["", "anchor anchor"]:
            with self.assertRaisesRegex(ValueError, "ambiguous bench instrumentation"):
                replace_once(source, "anchor", "replacement")


if __name__ == "__main__":
    unittest.main()
