"""Execute immutable Altirra pot methods in scratch; check all grounded-input clocks."""

import argparse
import gzip
import hashlib
import itertools
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

SOURCE_SHA = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
WRAP_SHA = "895788d911d5573fd9383d5bc5c0f2c109b7f515b3797e0d52e978c30ca90851"
HERE = Path(__file__).resolve().parent
MODES = (0, 3, 4, 7)
PHASES = (0, 16, 57, 110)


def pinned(path: Path, digest: str) -> str:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"source identity changed: {path}")
    return raw.decode().replace("\r\n", "\n")


def between(source: str, start: str, stop: str) -> str:
    a = source.index(start)
    return source[a : source.index(stop, a)]


def expected(mode: int, phase: int, tick: int) -> tuple[int, int]:
    if mode & 4:
        if tick >= 231:
            return 229, 0
        count = max(0, tick - 2)
        return count & (count + 1), 255
    if mode == 0:
        return 0, 255
    first = 114 - phase
    last = first + 227 * 114
    if tick > last:
        return 228, 0
    count = (tick + phase) // 114
    if (tick + phase) % 114 == 113:
        count &= count + 1
    return count, 255


def verify(lines: Iterable[str]) -> dict[str, int]:
    seen: set[tuple[int, int]] = set()
    observations = 0
    for line in lines:
        fields = line.split()
        if len(fields) != 26006 or fields[0] != "CASE":
            raise ValueError("incomplete cycle trace")
        mode, phase = map(int, fields[1:3])
        key = mode, phase
        if key in seen:
            raise ValueError("duplicate pot case")
        if key not in set(itertools.product(MODES, PHASES)):
            raise ValueError("unknown pot case")
        seen.add(key)
        for tick, pair in enumerate(fields[3:]):
            actual = tuple(map(int, pair.split(":")))
            if actual != expected(mode, phase, tick):
                raise ValueError(
                    f"pot trace mismatch {key} t={tick}: {actual} != {expected(mode, phase, tick)}"
                )
            observations += 1
    if seen != set(itertools.product(MODES, PHASES)):
        raise ValueError("incomplete pot inventory")
    return {"cases": len(seen), "cycles": observations, "pot_reads": observations * 8}


def run(root: Path, scratch: Path) -> None:
    scratch.mkdir(parents=True, exist_ok=False)
    source = pinned(root / "src/ATAudio/source/pokey.cpp", SOURCE_SHA)
    wrap = pinned(root / "src/h/at/atcore/wraptime.h", WRAP_SHA)
    methods = between(
        source,
        "uint32 ATPokeyEmulator::UpdateLast15KHzTime()",
        "uint32 ATPokeyEmulator::UpdateLast64KHzTime()",
    )
    methods += between(
        source,
        "void ATPokeyEmulator::StartPotScan()",
        "void ATPokeyEmulator::UpdateAddressDecoding()",
    )
    methods += between(
        source,
        "uint8 ATPokeyEmulator::ReadByte(uint8 reg)",
        "\t\tcase 0x09:\t// $D209 KBCODE",
    )
    methods += '\tdefault: throw std::runtime_error("unsupported read");\n}\n}\n'
    scaffold = (
        (HERE / "scaffold.cpp")
        .read_text()
        .replace("/* WRAP */", between(wrap, "struct ATWrapTime", "#endif"))
    )
    assembled = scaffold + methods + (HERE / "driver.cpp").read_text()
    variants = {
        "baseline": assembled,
        "slow-only": assembled.replace(
            "const bool fastPotScan = (mSKCTL & 4) != 0;",
            "const bool fastPotScan = false;",
        ),
        "stable-reads": assembled.replace(
            "return count & (count + 1);", "return count;"
        ),
        "wrong-limit": assembled.replace(
            "fastPotScan ? 229 : 228", "fastPotScan ? 228 : 228"
        ),
    }
    summary: dict[str, object] = {}
    for name, text in variants.items():
        if name != "baseline" and text == assembled:
            raise ValueError("mutation did not apply")
        cpp, binary, output = (
            scratch / f"{name}{suffix}" for suffix in (".cpp", "", ".txt")
        )
        cpp.write_text(text)
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(cpp),
                "-o",
                str(binary),
            ],
            check=True,
        )
        with output.open("w") as stream:
            subprocess.run([str(binary)], stdout=stream, check=True)
        try:
            with output.open() as stream:
                result = verify(stream)
        except ValueError as error:
            if name == "baseline":
                raise
            summary[name] = str(error)
        else:
            if name != "baseline":
                raise ValueError(f"negative control passed: {name}")
            summary.update(result)
            summary["capture_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
            (scratch / "baseline.txt.gz").write_bytes(
                gzip.compress(output.read_bytes(), mtime=0)
            )
    summary["source_sha256"] = SOURCE_SHA
    summary["assembled_sha256"] = hashlib.sha256(assembled.encode()).hexdigest()
    (scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    run(args.reference, args.scratch)
