"""A missing, shifted or altered clock trace must not become a green check."""

import copy
import unittest

from probe_raster import compare


def trace() -> list[dict]:
    return [
        {
            "step": i,
            "edge": int(i % 8 < 2),
            "epck0f": int(i % 8 < 4),
            "pck0": int(i % 8 >= 4),
        }
        for i in range(240)
    ]


class ComparisonTests(unittest.TestCase):
    def test_equal_trace_and_changed_clock(self) -> None:
        expected = trace()
        self.assertEqual(compare(expected, expected), [])
        actual = copy.deepcopy(expected)
        actual[104]["edge"] ^= 1
        result = compare(actual, expected)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["step"], 104)
        self.assertEqual(result[0]["fields"], ["edge"])

    def test_empty_and_short_trace_fail(self) -> None:
        for actual in [[], trace()[:-1]]:
            with self.assertRaisesRegex(ValueError, "incomplete raster comparison"):
                compare(actual, trace())

    def test_shifted_steps_fail(self) -> None:
        actual = trace()
        actual[100]["step"] = 99
        with self.assertRaisesRegex(ValueError, "step alignment differs"):
            compare(actual, trace())


if __name__ == "__main__":
    unittest.main()
