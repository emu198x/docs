"""Execute all generated guest cases and require stable reference observations."""

import argparse
import json
import subprocess
from pathlib import Path


def observe(command: list[str], directory: Path) -> list[int] | None:
    result = subprocess.run(
        command, cwd=directory, capture_output=True, text=True, check=True
    )
    if result.stdout.strip() == "panic":
        if "the len is 2048 but the index is 2048" not in result.stderr:
            raise ValueError(f"Unexpected panic: {result.stderr}")
        return None
    values = [int(value) for value in result.stdout.strip().split(",")]
    if len(values) != 4 or any(not 0 <= value <= 255 for value in values):
        raise ValueError("Expected four observed bytes")
    return values


def require_reference(actual: list[int] | None, expected: list[int]) -> None:
    if actual != expected:
        raise ValueError(f"Reference mismatch: {actual} != {expected}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("guest", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("roms", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    guest, reference, roms, output = (
        path.resolve() for path in (args.guest, args.reference, args.roms, args.output)
    )
    output.mkdir(parents=True, exist_ok=True)
    home = output / "mesen-home"
    home.mkdir(exist_ok=True)
    cases = json.loads((roms / "cases.json").read_text())
    identities = {
        (c["mapper"], c["nes2"], c["four_screen"], c["mirror_write"]) for c in cases
    }
    expected_ids = {
        (m, n, f, w)
        for m in [0, 4]
        for n in [False, True]
        for f in [False, True]
        for w in [0, 1]
    }
    if len(cases) != 16 or identities != expected_ids:
        raise ValueError("Missing, duplicate or unexpected cases")
    rows = []
    for case in cases:
        image = roms / case["file"]
        command = [str(reference), str(home), str(image)]
        first = observe(command, reference.parent)
        require_reference(first, case["expected"])
        require_reference(observe(command, reference.parent), case["expected"])
        actual = observe([str(guest), str(image)], guest.parent)
        if not case["four_screen"] and actual != case["expected"]:
            raise ValueError(f"Ordinary mirroring control failed: {case}")
        rows.append({**case, "emu198x": actual, "mesen": first})

    # A valid reference image whose four-screen flag is cleared must disagree
    # with the four-independent-page expectation. Prove the comparator rejects it.
    original = roms / "m0-nes20-four1-mirror0.nes"
    image = bytearray(original.read_bytes())
    image[6] &= ~8
    bad = output / "negative-two-screen.nes"
    bad.write_bytes(image)
    negative = observe([str(reference), str(home), str(bad)], reference.parent)
    try:
        require_reference(negative, [17, 34, 51, 68])
    except ValueError:
        pass
    else:
        raise ValueError("Comparator accepted a deliberately aliased reference image")

    counts = {
        "cases": len(rows),
        "panics": sum(row["emu198x"] is None for row in rows),
        "wrong_data": sum(
            row["emu198x"] is not None and row["emu198x"] != row["expected"]
            for row in rows
        ),
        "controls": sum(not row["four_screen"] for row in rows),
    }
    result = {
        "counts": counts,
        "reference_repeats_identical": True,
        "negative_control_rejected": True,
        "negative_observed": negative,
        "rows": rows,
    }
    (output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
