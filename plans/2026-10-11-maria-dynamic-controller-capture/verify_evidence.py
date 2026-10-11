"""Check replay acceptance guards and the layout's available date metadata."""

import argparse
import copy
import json
import struct
from collections import Counter
from pathlib import Path

from probe_capture import (
    circuits,
    controller_network,
    load_cells,
    replay,
    require,
    run_case,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cells = load_cells(args.archive)
    parts = circuits(cells)
    network = controller_network(cells, feedback=True)
    case = run_case(parts, 0, 0, 100, 100, 0, 1)
    positive = replay(network, parts["nmi"], case)
    failures = {}
    for name, message in [
        ("empty", "incomplete dynamic replay"),
        ("changed", "dynamic NMI differs from staged model at step 110"),
    ]:
        bad = copy.deepcopy(case)
        if name == "empty":
            bad["rows"] = []
        else:
            require(bad["rows"][110]["nmi"] == 1, "negative input not idle")
            bad["rows"][110]["nmi"] = 0
        try:
            replay(network, parts["nmi"], bad)
        except ValueError as error:
            require(str(error) == message, "wrong replay guard failure")
            failures[name] = str(error)
        else:
            raise ValueError("broken replay evidence passed")
    dates = Counter(
        struct.unpack(">12h", record.data)
        for records in cells.values()
        for record in records
        if record.kind == 5
    )
    require(
        sum(dates.values()) == 563 and len(dates) == 1, "unexpected structure dates"
    )
    fields = next(iter(dates))
    require(fields[1] == fields[7] == 13, "date-field observation changed")
    result = {
        "positive": positive,
        "negatives": failures,
        "structure_dates": {
            "records": 563,
            "distinct_payloads": 1,
            "fields": fields,
            "calendar_month_valid": False,
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
