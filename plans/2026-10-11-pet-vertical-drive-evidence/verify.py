"""Check complete CPU polling captures; this is a wiring, not board-clock oracle."""

import copy
import csv
import gzip
import io
from pathlib import Path


def verify(rows: list[dict[str, str]], expected: tuple[int, int]) -> None:
    clocks = list(range(19, 80_000, 23))
    cases = [(columns, edge) for columns in (40, 80) for edge in (0, 2)]
    assert len(rows) == len(clocks) * len(cases) == 13_912
    assert [(int(r["columns"]), int(r["edge"]), int(r["clock"])) for r in rows] == [
        (columns, edge, clock) for columns, edge in cases for clock in clocks
    ]
    mismatches = [0, 0]
    levels = {case: set() for case in cases}
    for row in rows:
        columns, edge, clock = (int(row[k]) for k in ("columns", "edge", "clock"))
        via, pia = int(row["via_high"]), int(row["pia_flag"])
        assert via in (0, 1) and pia in (0, 1)
        # Constructor register values and the current character-clock cadence.
        # These intervals intentionally do not certify either physical board.
        period, start, end = (20_032, 17_408, 18_432) if columns == 40 else (
            16_200, 14_500, 15_300
        )
        expected_via = int(not start <= (clock - 1) % period < end)
        edge_at = start if edge == 0 else end
        expected_pia = int(any(
            clock - 8 < edge_at + frame * period <= clock + 7
            for frame in range(6)
        ))
        mismatches[0] += via != expected_via
        mismatches[1] += pia != expected_pia
        levels[columns, edge].add(via)
    assert all(values == {0, 1} for values in levels.values())
    assert tuple(mismatches) == expected, mismatches


def read(name: str) -> list[dict[str, str]]:
    data = gzip.decompress(Path(__file__).with_name(name).read_bytes()).decode()
    return list(csv.DictReader(io.StringIO(data)))


before, prototype = read("before.csv.gz"), read("prototype.csv.gz")
verify(before, (3332, 18))
verify(prototype, (0, 0))
mutants = [prototype[:-1], copy.deepcopy(prototype), copy.deepcopy(prototype)]
mutants[1][0]["via_high"] = "0"
mutants[2][0]["pia_flag"] = "1"
for mutant in mutants:
    try:
        verify(mutant, (0, 0))
    except AssertionError:
        continue
    raise AssertionError("checker accepted incomplete or corrupted evidence")
print("13,912 samples each; baseline VIA/PIA mismatches 3332/18; prototype 0/0")
print("Missing sample and corrupted VIA/PIA negative controls rejected")
