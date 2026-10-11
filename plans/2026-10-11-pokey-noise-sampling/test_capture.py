import importlib.util
import itertools
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "capture", Path(__file__).with_name("capture.py")
)
assert spec is not None and spec.loader is not None
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        self.rows: list[tuple[int, ...]] = []
        for channel, mode, poly9, bits, previous, fire in itertools.product(
            range(4), range(8), range(2), range(16), range(2), range(2)
        ):
            clocked = fire and (mode & 4 or bits & 4)
            value = previous
            if clocked:
                value = (
                    1 - previous
                    if mode & 1
                    else (bits >> (3 if mode & 2 else (1 if poly9 else 0))) & 1
                )
            self.rows.append(
                (
                    channel,
                    mode,
                    poly9,
                    bits,
                    previous,
                    fire,
                    value,
                    int(value != previous),
                )
            )

    def test_complete_input_inventory(self) -> None:
        self.assertEqual(capture.verify(self.rows)["cases"], 4096)

    def test_missing_or_repeated_inputs_fail(self) -> None:
        for rows in [[], self.rows[:-1], self.rows[:-1] + self.rows[:1]]:
            with self.assertRaisesRegex(ValueError, "incomplete or duplicate"):
                capture.verify(rows)

    def test_always_hold_fails(self) -> None:
        rows = [r[:6] + (r[4], 0) for r in self.rows]
        with self.assertRaisesRegex(ValueError, "transfer disagrees"):
            capture.verify(rows)

    def test_suppressed_output_events_fail(self) -> None:
        rows = [r[:7] + (0,) for r in self.rows]
        with self.assertRaisesRegex(ValueError, "event count"):
            capture.verify(rows)


if __name__ == "__main__":
    unittest.main()
