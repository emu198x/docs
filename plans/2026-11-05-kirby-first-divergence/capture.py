"""Rebuild the retained diagnosis from bounded, local-only probe outputs."""

import hashlib
import json
import sys
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(a: bytes, b: bytes) -> dict[str, str | int]:
    return {
        "emu_sha256": digest(a),
        "sameboy_sha256": digest(b),
        "mismatches": sum(x != y for x, y in zip(a, b, strict=True)),
    }


def capture(root: Path) -> dict:
    baseline = []
    for game in ("kirby", "tetris", "mario"):
        for field in (240, 480, 720):
            a = (root / f"emu-{game}-{field}.gray").read_bytes()
            b = (root / f"sameboy-{game}-{field}.gray").read_bytes()
            assert len(a) == len(b) == 23040
            baseline.append({"game": game, "field": field, **compare(a, b)})
    fields = []
    for field in range(1, 721):
        row = {
            "field": field,
            **compare(
                (root / f"emu-all-{field}.gray").read_bytes(),
                (root / f"sameboy-all-{field}.gray").read_bytes(),
            ),
        }
        a = (root / f"emu-all-{field}.mem").read_bytes()
        b = (root / f"sameboy-all-{field}.mem").read_bytes()
        assert len(a) == len(b) == 16544
        for region, start, end in (
            ("vram", 0, 8192),
            ("wram", 8192, 16384),
            ("oam", 16384, 16544),
        ):
            row[region] = compare(a[start:end], b[start:end])
        fields.append(row)
    counterfactual = []
    for field in (240, 480, 720):
        counterfactual.append(
            {
                "field": field,
                **compare(
                    (root / f"forced-{field}.gray").read_bytes(),
                    (root / f"sameboy-kirby-{field}.gray").read_bytes(),
                ),
            }
        )
    for engine in ("emu", "sameboy"):
        for field in (240, 480, 720):
            expected = (root / f"{engine}-kirby-{field}.gray").read_bytes()
            for probe in ("all", "cpu", "bus"):
                assert (
                    root / f"{engine}-{probe}-{field}.gray"
                ).read_bytes() == expected
            name = "ly-baseline" if engine == "emu" else "sameboy-ly"
            assert (root / f"{name}-{field}.gray").read_bytes() == expected
    return {
        "source_commit": "9d9f756a681c9a04a64f44fbd18ad05f52e82895",
        "baseline": baseline,
        "fields": fields,
        "counterfactual": counterfactual,
        "observer_check": "all/cpu/bus/ly probes preserve all six Kirby checkpoint hashes",
        "first_cpu_records": {
            engine: [
                line
                for line in (root / f"{engine}-cpu.log").read_text().splitlines()
                if line.startswith("CPU ")
            ][:7]
            for engine in ("emu", "sameboy")
        },
        "first_ly_reads": {
            engine: (root / filename).read_text().splitlines()[0]
            for engine, filename in (
                ("emu", "ly-baseline.log"),
                ("sameboy", "sameboy-ly.log"),
                ("forced", "forced.log"),
            )
        },
        "div_guest_reads": {
            "emu": sum(
                line.startswith("DIV ")
                for line in (root / "emu-bus.log").read_text().splitlines()
            ),
            # Three reads are the checkpoint printouts, not CPU instructions.
            "sameboy": sum(
                line.startswith("DIV ")
                for line in (root / "sameboy-bus.log").read_text().splitlines()
            )
            - 3,
        },
    }


if __name__ == "__main__":
    print(json.dumps(capture(Path(sys.argv[1])), indent=2))
