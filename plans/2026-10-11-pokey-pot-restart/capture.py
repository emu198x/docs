"""Check retained charge and POTGO restarts through unchanged reference methods."""

import argparse
import gzip
import hashlib
import itertools
import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

HERE = Path(__file__).resolve().parent
THRESHOLD = 0x40000000
LIMIT = 0x96666666
DISCHARGE = 0x03936C71
OFFSETS = (
    0,
    1,
    2,
    3,
    4,
    7,
    8,
    9,
    15,
    63,
    64,
    65,
    127,
    128,
    129,
    230,
    231,
    232,
    511,
    512,
    513,
    1023,
    1024,
    1025,
    25991,
    25992,
    25993,
    26002,
    27000,
    27002,
)


def cases() -> Iterable[tuple[int, ...]]:
    return itertools.product(
        (0, 3, 4, 7), (0, 57, 110), (8, 128, 1024, 25992), (0, 1), (64, 512, 27000)
    )


def points(restart: int) -> list[tuple[int, int]]:
    times = (
        set(OFFSETS)
        | {restart + x for x in OFFSETS}
        | {restart - 1, restart, restart + 1}
    )
    return sorted([(t, 0) for t in times] + [(restart, 1)])


def segment(
    mode: int, phase: int, rate: int, start: int, charge: int, old_latch: int, tick: int
) -> tuple[int, int, int, int, int, int]:
    """Closed-form charge intervals; no per-cycle emulation or reference callbacks."""
    end = start + 231 if mode & 4 else ((start + phase) // 114 + 228) * 114 - phase + 1
    if mode == 0:
        end = 1 << 60
    active = tick < end
    elapsed = max(0, min(tick, end) - start - 2)
    level = min(LIMIT, charge + rate * elapsed)
    if tick > end:
        level = (
            min(LIMIT, level + rate * (tick - end))
            if mode & 4
            else max(0, level - DISCHARGE * (tick - end))
        )
    if mode & 4:
        count = min(229, max(0, tick - start - 2))
    elif mode == 0 or tick <= start + 2:
        count = 0
    else:
        count = min(228, (tick + phase) // 114 - (start + phase) // 114)
    crossing = start + 2 + max(0, (THRESHOLD - charge + rate - 1) // rate)
    latch = old_latch
    if charge < THRESHOLD:
        if crossing <= min(tick, end):
            latch = (
                crossing - start - 2
                if mode & 4
                else (crossing + phase) // 114 - (start + phase) // 114
            )
            if mode == 0:
                latch = 0
        elif not active:
            latch = 229 if mode & 4 else 228
    updating = active and charge < THRESHOLD and tick < crossing
    pot = latch
    if updating:
        pot = count
        if mode & 4 or (mode == 3 and (tick + phase) % 114 == 113):
            pot &= count + 1
    return pot, 255 if updating else 0, count, int(active), level, latch


def expected(case: tuple[int, ...], tick: int, after: int) -> tuple[int, ...]:
    mode, phase, duration, initial, restart = case
    rate = THRESHOLD // duration
    initial_charge = THRESHOLD + 100 if initial else 0
    if tick < restart or (tick == restart and not after):
        return segment(mode, phase, rate, 0, initial_charge, 42, tick)[:5]
    prior = segment(mode, phase, rate, 0, initial_charge, 42, restart)
    return segment(mode, phase, rate, restart, prior[4], prior[5], tick)[:5]


def verify(lines: Iterable[str]) -> dict[str, int]:
    inventory = {
        (case, tick, after) for case in cases() for tick, after in points(case[4])
    }
    seen: set[tuple[tuple[int, ...], int, int]] = set()
    for line in lines:
        fields = tuple(map(int, line.split()))
        if len(fields) != 12:
            raise ValueError("malformed observation")
        case, tick, after = fields[:5], fields[5], fields[6]
        key = case, tick, after
        if key not in inventory:
            raise ValueError("unknown observation")
        if key in seen:
            raise ValueError("duplicate observation")
        seen.add(key)
        wanted = expected(case, tick, after)
        if fields[7:] != wanted:
            raise ValueError(f"restart mismatch {key}: {fields[7:]} != {wanted}")
    if seen != inventory:
        raise ValueError("incomplete restart inventory")
    return {
        "cases": len(list(cases())),
        "observations": len(seen),
        "pot_reads": len(seen) * 8,
    }


def run(reference: Path, scratch: Path) -> None:
    scratch.mkdir(parents=True, exist_ok=False)
    subprocess.run(
        [
            sys.executable,
            str(HERE.parent / "2026-10-11-pokey-pot-scan/capture.py"),
            str(reference),
            str(scratch / "prerequisite"),
        ],
        check=True,
    )
    prior = (scratch / "prerequisite/baseline.cpp").read_text()
    assembled = prior[: prior.index("int main() {")] + (HERE / "driver.cpp").read_text()
    marker = "void ATPokeyEmulator::StartPotScan() {"
    variants = {
        "baseline": assembled,
        "discard-charge": assembled.replace(
            marker, marker + "\n mPotChargeLevels.fill(0);"
        ),
        "discard-latch": assembled.replace(marker, marker + "\n mPotLatches.fill(0);"),
        "premature-stop": assembled.replace(
            "if (!mbPotScanActive && mALLPOT)",
            "if (!mALLPOT) mbPotScanActive = false;\n if (!mbPotScanActive && mALLPOT)",
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
            raw = output.read_bytes()
            summary["capture_sha256"] = hashlib.sha256(raw).hexdigest()
            (scratch / "baseline.txt.gz").write_bytes(gzip.compress(raw, mtime=0))
    summary["assembled_sha256"] = hashlib.sha256(assembled.encode()).hexdigest()
    (scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    run(args.reference, args.scratch)
