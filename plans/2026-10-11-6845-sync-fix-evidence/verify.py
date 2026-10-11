"""Check complete captured coverage and compare production pulse lengths to MAME."""
from pathlib import Path
import copy
import csv
import io

BASE = Path(__file__).parent

def verify(after: list[dict[str, str]], reference: list[dict[str, str]]) -> None:
    assert len(after) == 64
    assert {(row["variant"], row["signal"], int(row["width"])) for row in after} == {
        (variant, signal, width)
        for variant in ("Mc6845", "Hd6845s")
        for signal in ("h", "v") for width in range(16)
    }
    assert len(reference) == 62
    expected_keys = {(str(v), s, w) for v in range(2) for s in ("h", "v")
                     for w in range(16) if s == "v" or w != 0}
    assert {(row["variant"], row["signal"], int(row["width"])) for row in reference} == expected_keys
    lookup = {(row["variant"], row["signal"], int(row["width"])): row for row in reference}
    for row in after:
        width = int(row["width"])
        expected = width if row["signal"] == "h" else 64 * (
            16 if row["variant"] == "Mc6845" or width == 0 else width)
        assert int(row["expected_clocks"]) == expected
        assert row["passed"] == "true"
        runs = [int(n) for n in row["observed_clocks"].split(":") if n]
        assert len(runs) == int(row["complete_pulses"])
        if expected:
            assert len(runs) >= 2 and all(n == expected for n in runs)
            ref = lookup[(str(int(row["variant"] == "Hd6845s")), row["signal"], width)]
            scale = 1 if row["signal"] == "h" else 64
            assert int(ref["observed"]) == int(ref["expected"])
            assert int(ref["observed"]) * scale == expected
        else:
            assert not runs

after = list(csv.DictReader(io.StringIO((BASE / "sync-after.csv").read_text())))
reference = list(csv.DictReader(io.StringIO((BASE / "reference.csv").read_text())))
verify(after, reference)
mutants = [after[:-1], copy.deepcopy(after), copy.deepcopy(after)]
mutants[1][1]["observed_clocks"] = "0"
mutants[2][0]["complete_pulses"] = "1"
for mutant in mutants:
    try:
        verify(mutant, reference)
    except AssertionError:
        continue
    raise AssertionError("checker accepted an incomplete or corrupted capture")
print("64 production rows agree with 62 legal reference-stage rows; three checker mutations rejected")
