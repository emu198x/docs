"""Check static CHR first-page expectations with unchanged Mesen2 code."""

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesen", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    folder = Path(__file__).parent
    reference = args.mesen / "Core/NES/Mappers/Nintendo/MMC5.h"
    text = reference.read_text()
    start = text.index("void UpdateChrBanks(bool forceUpdate)")
    end = text.index("{", start) + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    host = (folder / "reference_host.cpp.in").read_text()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.output / "reference.cpp"
    source.write_text(host.replace("@UPDATE_CHR_BANKS@", text[start:end]))
    binary = args.output / "reference"
    subprocess.run(
        ["clang++", "-std=c++20", str(source), "-o", str(binary)], check=True
    )
    output = subprocess.check_output([str(binary)], text=True)
    (args.output / "reference.csv").write_text(output)
    expected = list(csv.DictReader(io.StringIO(output)))
    with (folder / "baseline.csv").open() as stream:
        baseline = list(csv.DictReader(stream))
    if len(expected) != 64 or len(baseline) != 64:
        raise ValueError("Expected 64 reference and 64 baseline rows")
    for ref, actual in zip(expected, baseline, strict=True):
        if any(ref[key] != actual[key] for key in ["mode", "bank", "first_expected"]):
            raise ValueError(f"Reference mismatch: {ref}, {actual}")
    result = {
        "matching_reference_expectations": len(expected),
        "baseline_mismatches": sum(
            row["first_actual"] != row["first_expected"] for row in baseline
        ),
        "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
    }
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
