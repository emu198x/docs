import unittest

from capture import verify


def documented_rows() -> str:
    rows = []
    for channel in range(4):
        for mode in range(3):
            for frequency in range(256):
                period = (
                    frequency + 4
                    if mode == 2 and channel in (0, 2)
                    else (frequency + 1) * (114 if mode == 1 else 28)
                )
                rows.append(f"{channel} {mode} {frequency} {period}")
    return "\n".join(rows) + "\n"


class PeriodGuards(unittest.TestCase):
    def test_complete_inventory(self) -> None:
        self.assertEqual(verify(documented_rows()), 3072)

    def test_missing_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete period inventory"):
            verify("\n".join(documented_rows().splitlines()[1:]))

    def test_duplicate_case(self) -> None:
        rows = documented_rows().splitlines()
        rows[1] = rows[0]
        with self.assertRaisesRegex(ValueError, "incomplete period inventory"):
            verify("\n".join(rows))

    def test_missing_fast_propagation(self) -> None:
        with self.assertRaisesRegex(ValueError, "documented period"):
            verify(documented_rows().replace("0 2 0 4\n", "0 2 0 1\n"))


if __name__ == "__main__":
    unittest.main()
