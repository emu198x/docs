"""Require every byte and both profiles, including guest completion controls."""

import copy
import csv
import gzip
import io
from pathlib import Path


def verify(rows: list[dict[str, str]]) -> None:
    expected = {(columns, value) for columns in (40, 80) for value in range(256)}
    assert len(rows) == len(expected) == 512
    assert {(int(row["columns"]), int(row["value"])) for row in rows} == expected
    failures = 0
    for row in rows:
        value = int(row["value"])
        assert row["done"] == "true"
        assert int(row["expected"]) == value
        assert int(row["data_port"]) == 255
        assert int(row["address_port"]) == value
        failures += int(row["data_port"]) != value
    assert failures == 510


source = Path(__file__).with_name("before.csv.gz")
rows = list(csv.DictReader(io.StringIO(gzip.decompress(source.read_bytes()).decode())))
verify(rows)
mutants = [rows[:-1], copy.deepcopy(rows), copy.deepcopy(rows)]
mutants[1][0]["done"] = "false"
mutants[2][0]["data_port"] = "0"
for mutant in mutants:
    try:
        verify(mutant)
    except AssertionError:
        continue
    raise AssertionError("checker accepted an incomplete or corrupted capture")
print("512 completed guests; 510 failures and two controls; three mutations rejected")
