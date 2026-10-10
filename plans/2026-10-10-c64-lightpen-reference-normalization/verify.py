"""Compile the upstream light-pen converter and check every prepared byte."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--testbench", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()
    bench = args.testbench.resolve(strict=True) / "split-tests/lightpen"
    fixtures = args.source.resolve(strict=True) / "test-data/commodore/c64/lightpen"
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    executable = output / "makeref"
    command = [
        args.cc,
        "-Wall",
        "-Wextra",
        "-O2",
        str(bench / "makeref.c"),
        "-o",
        str(executable),
    ]
    compiled = subprocess.run(command, capture_output=True, check=True)
    (output / "compiler.log").write_bytes(compiled.stdout + compiled.stderr)
    guest = (bench / "lightpen.prg").read_bytes()
    load_address = int.from_bytes(guest[:2], "little")
    rows = []
    for chip in ["6569", "8565", "6567", "8562r4"]:
        raw_path = bench / "dumps" / f"dump{chip}.prg"
        converted_path = output / f"{chip}.bin"
        process = subprocess.run(
            [str(executable), str(raw_path), str(converted_path)],
            capture_output=True,
            check=True,
            text=True,
        )
        raw = raw_path.read_bytes()
        assert raw[:2] == b"\x00\x40" and len(raw) == 1282
        converted = converted_path.read_bytes()
        native = (fixtures / f"{chip}.bin").read_bytes()
        assert len(converted) == 1280 and converted == native, chip
        offset = guest[2:].find(converted)
        assert offset >= 0, f"{chip}: prepared reference missing from the R04 guest"
        changes = [
            (i, a, b)
            for i, (a, b) in enumerate(zip(raw[2:], converted, strict=True))
            if a != b
        ]
        assert [(i, (b - a) & 255) for i, a, b in changes] == [(766, 4), (767, 4)]
        # The upstream converter expects a two-byte PRG prefix even when its
        # payload is already prepared. Its guard must leave these bytes intact.
        prepared_prg = output / f"{chip}-prepared.prg"
        prepared_prg.write_bytes(raw[:2] + converted)
        twice = output / f"{chip}-twice.bin"
        second = subprocess.run(
            [str(executable), str(prepared_prg), str(twice)],
            capture_output=True,
            check=True,
            text=True,
        )
        assert second.stdout == "" and twice.read_bytes() == converted
        rows.append(
            {
                "chip": chip,
                "raw_sha256": digest(raw_path),
                "prepared_sha256": digest(converted_path),
                "changes": changes,
                "embedded_address": load_address + offset,
                "converter_output": process.stdout,
                "prepared_pass_through": True,
            }
        )
    assert len(rows) == 4
    (output / "comparison.json").write_text(
        json.dumps(
            {
                "compiler_command": command,
                "source_sha256": {
                    name: digest(bench / name)
                    for name in [
                        "Makefile",
                        "makeref.c",
                        "lightpen.asm",
                        "lightpen.prg",
                    ]
                },
                "comparisons": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "4 models, 5120 converted bytes: native and embedded references exact; prepared inputs unchanged"
    )


if __name__ == "__main__":
    main()
