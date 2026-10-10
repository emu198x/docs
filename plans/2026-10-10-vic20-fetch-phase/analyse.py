"""Check the observed VIC-20 guest bus phases against each physical dump."""

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def predict(row: dict[str, Any], phase_offset: int) -> tuple[str, int]:
    """Reconstruct this fixed guest's addresses; this is not a chip model."""
    cpl, lines = (71, 312) if row["model"] == "Pal" else (65, 261)
    regs = row["registers"]
    assert regs[2:4] == [22, 46] and regs[5] == 255
    line = row["clock"] // cpl % lines
    cycle = row["clock"] % cpl
    phase = cycle - ((regs[0] & 127) + phase_offset)
    raster_row = line - regs[1] * 2
    if not (0 <= raster_row < (regs[3] >> 1) * 8 and 0 <= phase < regs[2] * 2):
        return "idle", row["address"] >> 8
    cell = raster_row // 8 * regs[2] + phase // 2
    char = row["memory"][cell]
    if phase % 2:
        return "glyph", row["memory"][char * 8 + raster_row % 8]
    return "matrix", char


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument(
        "--testbench", type=Path, default=Path.home() / ".emu198x/test-suites/vic20"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.trace.read_bytes()
    text = (gzip.decompress(raw) if args.trace.suffix == ".gz" else raw).decode()
    rows = [
        json.loads(line.removeprefix("FETCH_TRACE "))
        for line in text.splitlines()
        if line.startswith("FETCH_TRACE ")
    ]
    assert len(rows) == 2048
    for model in ["Pal", "Ntsc"]:
        for address in [0x9003, 0x9004, 0x9100, 0x9200]:
            samples = [
                r["sample"]
                for r in rows
                if r["model"] == model and r["address"] == address
            ]
            assert sorted(samples) == list(range(256)), (
                model,
                address,
                "missing or duplicated reads",
            )
    fixtures = args.testbench / "vice-testprogs/split-tests/timing/dumps"
    records = []
    for model, files in [
        (
            "Pal",
            [
                (
                    "dump6561e.prg",
                    "393ef771096e5be15dd6652bede9ee3f8187614a6dab1c90baff3f819d83a437",
                ),
                (
                    "dump6561-101.prg",
                    "fa855211dc2c8805c9527a33b45b85e85da28efe9a0fe86f7a0fcc23e92a0390",
                ),
            ],
        ),
        (
            "Ntsc",
            [
                (
                    "dump6560-101.prg",
                    "382aef40a44e33a0debbeb9279a3faa711b23ce363a4dc881300d63e9d56f54c",
                ),
                (
                    "dump6560.prg",
                    "3ff4fb3d149e964ade6412d13840e7f4cb2f87a1934ec8bcf519d0bca93dd27b",
                ),
            ],
        ),
    ]:
        for name, digest in files:
            prg = (fixtures / name).read_bytes()
            assert hashlib.sha256(prg).hexdigest() == digest
            assert len(prg) == 1090 and prg[:2] == bytes([0xC0, 0x17])
            hardware = prg[2:]
            for offset in [4, 3, 5]:
                counts: Counter[str] = Counter()
                differences = []
                for row in rows:
                    if row["model"] != model:
                        continue
                    column = [0x9003, 0x9004, 0x9100, 0x9200].index(row["address"])
                    expected = hardware[64 + column * 256 + row["sample"]]
                    if column < 2:
                        assert row["actual"] == expected, "raster control moved"
                        continue
                    kind, predicted = predict(row, offset)
                    counts[kind] += 1
                    if predicted != expected:
                        differences.append(
                            {
                                "address": row["address"],
                                "sample": row["sample"],
                                "clock": row["clock"],
                                "kind": kind,
                                "predicted": predicted,
                                "hardware": expected,
                            }
                        )
                assert sum(counts.values()) == 512
                if offset == 4:
                    assert all(
                        d["kind"] == "idle" and d["hardware"] == 0x20
                        for d in differences
                    )
                    if name in ["dump6561e.prg", "dump6560-101.prg"]:
                        assert not differences
                else:
                    assert differences, "phase-error negative control failed"
                print(
                    model,
                    name,
                    "phase",
                    offset,
                    dict(counts),
                    "differences",
                    len(differences),
                )
                records.append(
                    {
                        "model": model,
                        "reference": name,
                        "reference_sha256": digest,
                        "phase_offset": offset,
                        "samples": dict(counts),
                        "differences": differences,
                    }
                )
    with args.output.open("x") as output:
        json.dump(
            {"trace_sha256": hashlib.sha256(raw).hexdigest(), "comparisons": records},
            output,
            indent=2,
        )
        output.write("\n")


if __name__ == "__main__":
    main()
