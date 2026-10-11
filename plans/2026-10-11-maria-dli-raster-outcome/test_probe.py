"""Reject incomplete or falsely green raster captures."""

from __future__ import annotations

import itertools
import unittest

from run_probe import summarize


def green_log() -> str:
    rows = []
    for region, height, flags in itertools.product(
        ("Ntsc", "Pal"), (1, 2, 3, 16), range(4)
    ):
        requests = (0, 240 // height, 120 // height, 1)[flags]
        rows.append(
            f"region={region} height={height} flags={flags} requests={requests} "
            f"handlers={requests} writes={requests + 1} pixels=192 "
            f"wrong_pixels=0 wrong_bus_pixels=0 wrong_previous=0 "
            f"min_age={500 if flags else 0}"
        )
    return "\n".join(
        rows + ["cases=32 failures=0", "test result: ok. 1 passed; 0 failed"]
    )


class CaptureTests(unittest.TestCase):
    def test_complete_green_is_accepted(self) -> None:
        self.assertEqual(summarize(green_log(), 0)["failures"], 0)

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete case inventory"):
            summarize("\n".join(green_log().splitlines()[1:]), 0)

    def test_duplicate_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            summarize(green_log() + "\n" + green_log().splitlines()[0], 0)

    def test_missing_pixels(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete pixels"):
            summarize(green_log().replace("pixels=192", "pixels=0", 1), 0)

    def test_deadline_too_close(self) -> None:
        with self.assertRaisesRegex(ValueError, "insufficient pixel deadline"):
            summarize(green_log().replace("min_age=500", "min_age=10", 1), 0)

    def test_missing_requests(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing active requests"):
            summarize(green_log().replace("requests=240", "requests=0", 1), 0)

    def test_compile_failure(self) -> None:
        with self.assertRaisesRegex(ValueError, "cargo status differs"):
            summarize(green_log(), 101)

    def test_missing_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing executed test result"):
            summarize(green_log().replace("test result:", "not executed:"), 0)

    def test_false_summary(self) -> None:
        with self.assertRaisesRegex(ValueError, "inconsistent completion summary"):
            summarize(green_log().replace("failures=0", "failures=1"), 0)


if __name__ == "__main__":
    unittest.main()
