#!/usr/bin/env python3
"""Verify CPC qualification specimens and the resolved CPU adoption boundary."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    records = json.loads(Path(__file__).with_name("fixtures.json").read_text())
    if len(records) != 18:
        raise ValueError("expected six complete specimens for each of v4, v5 and v6")
    for relative, expected in records.items():
        actual = hashlib.sha256((args.checkout / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {relative}")
    tree = subprocess.run(
        ["cargo", "tree", "--locked", "-p", "runtime-amstrad-cpc", "--prefix", "none"],
        cwd=args.checkout,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout.splitlines()
    cpus = [line for line in tree if line.startswith("emu198x-zilog-z80 ")]
    if not cpus or any(line.split()[1] != "v0.9.0" for line in cpus):
        raise ValueError(f"unexpected CPC CPU graph: {cpus}")
    print("18 frozen files match; the CPC runtime resolves only Z80 0.9.0")


if __name__ == "__main__":
    main()
