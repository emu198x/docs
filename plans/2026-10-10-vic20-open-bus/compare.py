"""Compare full completed VIC-20 measurements without normalizing input bytes."""

import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--emulated", type=Path, required=True)
parser.add_argument("--native", type=Path, required=True)
parser.add_argument(
    "--testbench", type=Path, default=Path.home() / ".emu198x/test-suites/vic20"
)
args = parser.parse_args()
references = args.testbench / "vice-testprogs/split-tests/timing/dumps"
records = []
for model, names in [
    ("pal", ["dump6561e.prg", "dump6561-101.prg"]),
    ("ntsc", ["dump6560.prg", "dump6560-101.prg"]),
]:
    native = (args.native / model / "measurement.bin").read_bytes()
    emulated = (args.emulated / f"{model}.bin").read_bytes()
    assert len(native) == len(emulated) == 1088
    assert native[40] == emulated[40] == 1, "stable-raster completion guard"
    inputs = [("emu198x", emulated)]
    for name in names:
        prg = (references / name).read_bytes()
        assert len(prg) == 1090 and prg[:2] == bytes([0xC0, 0x17])
        inputs.append((name, prg[2:]))
    for label, other in inputs:
        sections = []
        for name, start, end in [
            ("header", 0, 64),
            ("9003", 64, 320),
            ("9004", 320, 576),
            ("9100", 576, 832),
            ("9200", 832, 1088),
        ]:
            differences = [
                {"offset": i, "native": native[i], "other": other[i]}
                for i in range(start, end)
                if native[i] != other[i]
            ]
            print(model, label, name, len(differences), "/", end - start)
            sections.append(
                {"section": name, "samples": end - start, "differences": differences}
            )
        records.append(
            {
                "model": model,
                "other": label,
                "native_sha256": hashlib.sha256(native).hexdigest(),
                "other_payload_sha256": hashlib.sha256(other).hexdigest(),
                "sections": sections,
            }
        )
with args.output.open("x") as output:
    json.dump(records, output, indent=2)
    output.write("\n")
