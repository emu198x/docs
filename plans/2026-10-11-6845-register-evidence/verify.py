"""Verify complete port sweeps, signal aliases and independent reference cases."""
from pathlib import Path
import copy
import csv
import gzip
import io

BASE = Path(__file__).parent

def rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(gzip.decompress((BASE / name).read_bytes()).decode())))

def verify(observed: list[dict[str, str]], failures: int) -> None:
    keys = {(v, "readback", r, d) for v in ("Mc6845", "Hd6845s")
            for r in (12, 14, 15, 16, 17) for d in range(256)
            if r != 12 or v == "Hd6845s"}
    keys |= {(v, "display_alias", 6, d) for v in ("Mc6845", "Hd6845s") for d in range(128, 256)}
    assert len(observed) == len(keys) == 2560
    assert {(r["variant"], r["kind"], int(r["register"]), int(r["value"])) for r in observed} == keys
    wrong = 0
    for row in observed:
        reg, value = int(row["register"]), int(row["value"])
        if row["kind"] == "display_alias":
            expected = (value & 0x7f) * 8 * 2
        else:
            expected = value & 0x3f if reg in (12, 14) else value if reg == 15 else 0
        assert int(row["expected"]) == expected
        matches = int(row["observed"]) == expected
        assert (row["passed"] == "true") == matches
        wrong += not matches
    assert wrong == failures

before, after, reference = rows("before.csv.gz"), rows("after.csv.gz"), rows("reference.csv.gz")
verify(before, 1852)
verify(after, 0)
assert len(reference) == 1536
assert {(int(r["register"]), int(r["value"])) for r in reference} == {(r, d) for r in (6, 12, 14, 15, 16, 17) for d in range(256)}
for row in reference:
    reg, value = int(row["register"]), int(row["value"])
    expected = value & 0x7f if reg == 6 else value & 0x3f if reg in (12, 14) else value if reg == 15 else 0x2a if reg == 16 else 0x59
    assert int(row["expected"]) == int(row["observed"]) == expected
mutants = [after[:-1], copy.deepcopy(after), copy.deepcopy(after)]
mutants[1][0]["observed"] = "255"
mutants[2][0]["value"] = "1"
for mutant in mutants:
    try:
        verify(mutant, 0)
    except AssertionError:
        continue
    raise AssertionError("checker accepted incomplete/corrupted evidence")
print("2560 complete cases: 1852 failures before, zero after; 1536 reference cases pass; three mutations rejected")
