import unittest
from pathlib import Path

from connected import verify


class ConnectedGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = Path(__file__).with_name("connected.txt").read_text()

    def test_complete(self) -> None:
        result = verify(self.capture)
        self.assertEqual(result["cases"], 1440)
        self.assertEqual(result["output_transitions"], 7808)
        self.assertEqual(
            result["capture_sha256"],
            "d9fd1e7b52360bd39c7f040ddc37d6f6a89ee3c8c9bdaed92bd0b2debf7bf71c",
        )

    def test_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete STIMER case inventory"):
            verify("")

    def test_missing_row(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete STIMER case inventory"):
            verify("\n".join(self.capture.splitlines()[1:]))

    def test_missing_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "connected reset waveform mismatch"):
            verify(self.capture.replace(" O2000:1", "", 1))

    def test_irq_loss_with_correct_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "STIMER IRQ delivery mismatch"):
            verify(self.capture.replace(" I1899:254", "", 1))


if __name__ == "__main__":
    unittest.main()
