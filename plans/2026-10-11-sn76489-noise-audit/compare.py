"""Validate captured generator traces; fail on empty or incomplete evidence."""
import csv
import json
from pathlib import Path

root = Path(__file__).parent

def rows(name):
    with (root / name).open() as stream:
        return list(csv.DictReader(stream))

def key(row):
    return tuple(row[column] for column in ("mode", "white", "period", "event"))

reference = rows("reference.csv")
baseline = rows("baseline.csv")
corrected = rows("corrected.csv")
assert len(reference) == 1152
assert len(baseline) == len(corrected) == 2304
by_key = {key(row): row for row in reference}
assert len(by_key) == 1152
for capture in (baseline, corrected):
    for variant in ("ti", "sega"):
        selected = [row for row in capture if row["variant"] == variant]
        assert len(selected) == len({key(row) for row in selected}) == 1152
        assert {key(row) for row in selected} == set(by_key)
fields = ("interval", "lfsr", "tone3", "rising")
slaved = lambda row: row["variant"] == "ti" and row["mode"] == "3"
old = [row for row in baseline if slaved(row)]
new = [row for row in corrected if slaved(row)]
assert len(old) == len(new) == 768
assert sum(any(row[f] != by_key[key(row)][f] for f in fields) for row in old) == 768
for row in new:
    assert all(row[f] == by_key[key(row)][f] for f in fields), row
assert [r for r in baseline if not slaved(r)] == [r for r in corrected if not slaved(r)]
# The period-one control matches the rate even on baseline, but never the edge.
control = [row for row in old if row["period"] == "1"]
assert len(control) == 128
assert all(row["interval"] == "32" and row["rising"] == "0" for row in control)
result = {"reference_rows": 1152, "baseline_rows": 2304, "corrected_rows": 2304,
          "ti_slaved_mismatches_before": 768, "ti_slaved_mismatches_after": 0,
          "rate_only_false_positive_controls": 128, "unchanged_other_rows": 1536}
(root / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
