"""Export digital controller inputs/outputs from the retained circuit matrix."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "2026-10-11-maria-halt-generator-handoff"
    ),
)
from probe_handoff import check_case, circuits, load_cells, run_case


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    parts = circuits(load_cells(args.archive))
    baseline = json.loads(args.matrix.read_text())["cases"]
    assert len(baseline) == 32832
    vectors = {}
    cache = {}
    pulses = 0
    keys = [
        "initial_slow",
        "final_slow",
        "reset_step",
        "mode_change",
        "return_delay",
        "dli",
        "request",
        "slow_order",
    ]
    for index, expected in enumerate(baseline):
        case = run_case(parts, *[expected[k] for k in keys], cache=cache)
        assert check_case(case) == expected, (index, "circuit replay changed")
        encoded = []
        for previous, row in zip(case["rows"], case["rows"][1:]):
            # Fixed phases map to one native observation per phase. The CPU
            # falling edge is observable independently of the internal pckedge.
            edge = previous["pck0"] == 1 and row["pck0"] == 0
            packed = (
                row["ph2"]
                | int(edge) << 1
                | (1 - row["halt_pad"]) << 2
                | (expected["dli"] if row["step"] >= 48 else 0) << 3
                | (1 - row["nmi"]) << 4
            )
            encoded.append(f"{packed:02x}")
        vector = "".join(encoded)
        vectors[vector] = vectors.get(vector, 0) + 1
        pulses += len(expected["nmi_edges"]) // 2
        if (index + 1) % 4000 == 0:
            print(index + 1, "cases checked", flush=True)
    text = "".join(f"{count} {vector}\n" for vector, count in sorted(vectors.items()))
    args.output.write_text(text)
    args.output.with_suffix(".json").write_text(
        json.dumps(
            {
                "cases": len(baseline),
                "unique_vectors": len(vectors),
                "pulses": pulses,
                "vector_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "matrix_sha256": hashlib.sha256(args.matrix.read_bytes()).hexdigest(),
                "archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
                "scope": "digital circuit replay; not physical pin measurement",
            },
            indent=2,
        )
        + "\n"
    )
    print(len(vectors), "unique vectors", pulses, "pulses", flush=True)


if __name__ == "__main__":
    main()
