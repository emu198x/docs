"""Check finite, nonempty reference evidence for the retained clock stage."""
import csv
import json
from pathlib import Path

root = Path(__file__).parent

def read(name):
    with (root / name).open() as stream:
        return list(csv.DictReader(stream))

def key(row):
    return tuple(row[f] for f in ("mode", "white", "period", "event"))

reference = read("ares.csv")
all_baseline = read("baseline.csv")
assert len(all_baseline) == 2304
baseline = [row for row in all_baseline if row["variant"] == "sega"]
assert len(reference) == len(baseline) == 1152
by_key = {key(row): row for row in reference}
assert len(by_key) == 1152
assert len({key(row) for row in baseline}) == 1152
assert {key(row) for row in baseline} == set(by_key)
result = {
    "rows": 1152,
    "rate_mismatches": sum(row["interval"] != by_key[key(row)]["interval"] for row in baseline),
    "lfsr_sequence_mismatches": sum(row["lfsr"] != by_key[key(row)]["lfsr"] for row in baseline),
    "output_bit_mismatches": sum(row["noise_output"] != by_key[key(row)]["noise_output"] for row in baseline),
    "ares_mode3_nonrising_events": sum(row["mode"] == "3" and row["rising"] == "0" for row in reference),
}
assert result == {"rows": 1152, "rate_mismatches": 896,
                  "lfsr_sequence_mismatches": 0, "output_bit_mismatches": 234,
                  "ares_mode3_nonrising_events": 768}
collision = read("collision.csv")
assert len(collision) == 8
states = {(int(row["earlier_mode"]), int(row["tick"])): row for row in collision}
assert len(states) == 8
for mode in (0, 1):
    row = states[mode, 512]
    assert (row["counter"], row["lfsr"], row["output"]) == ("16", "16384", "0")
assert states[0, 512]["clock_level"] != states[1, 512]["clock_level"]
assert states[0, 768]["lfsr"] != states[1, 768]["lfsr"]
assert states[0, 7424]["output"] != states[1, 7424]["output"]
(root / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
