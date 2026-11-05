"""Verify the retained Kirby diagnosis; corrupt or incomplete evidence fails."""

import hashlib
import json
import sys
from pathlib import Path


def verify(report: dict, root: Path) -> None:
    identity = json.loads((root / "identity.json").read_text())
    assert report["source_commit"] == identity["source_commit"]
    for name, expected in identity["probe_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    baseline = report["baseline"]
    assert [(r["game"], r["field"]) for r in baseline] == [
        (g, f) for g in ("kirby", "tetris", "mario") for f in (240, 480, 720)
    ]
    assert [r["mismatches"] for r in baseline] == [201, 135, 177, 0, 0, 0, 0, 0, 0]
    fields = report["fields"]
    assert [r["field"] for r in fields] == list(range(1, 721))
    assert all(r["vram"]["mismatches"] == 0 for r in fields[1:])
    for checkpoint in baseline[:3]:
        field = fields[checkpoint["field"] - 1]
        for key in ("mismatches", "emu_sha256", "sameboy_sha256"):
            assert field[key] == checkpoint[key], (checkpoint["field"], key)
    assert [r["field"] for r in report["counterfactual"]] == [240, 480, 720]
    for original, corrected in zip(baseline[:3], report["counterfactual"], strict=True):
        assert (
            corrected["emu_sha256"]
            == corrected["sameboy_sha256"]
            == original["sameboy_sha256"]
        )
        assert corrected["mismatches"] == 0
    records = report["first_cpu_records"]
    assert len(records["emu"]) == len(records["sameboy"]) == 7
    for a, b in zip(records["emu"][:3], records["sameboy"][:3], strict=True):
        assert a.split()[2:9] == b.split()[2:9]
    assert records["emu"][3].split()[2:5] == ["0152", "fe", "99b0"]
    assert records["sameboy"][3].split()[2:5] == ["0152", "fe", "00b0"]
    assert records["emu"][5].split()[2] == "0156"
    assert records["sameboy"][5].split()[2] == "0150"
    assert "value=99 internal=153 dot=424" in report["first_ly_reads"]["emu"]
    assert "value=00 internal=153" in report["first_ly_reads"]["sameboy"]
    assert "value=00 internal=153 dot=424" in report["first_ly_reads"]["forced"]
    assert report["div_guest_reads"] == {"emu": 0, "sameboy": 0}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else root / "report.json"
    verify(json.loads(path.read_text()), root)
    print(
        "720 paired fields, nine baseline checkpoints, causal LY read and three exact counterfactual matches verified"
    )
