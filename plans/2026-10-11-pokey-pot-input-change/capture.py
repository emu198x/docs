"""Qualify live pot inputs against closed-form charge intervals."""

import argparse
import gzip
import hashlib
import itertools
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

HERE = Path(__file__).resolve().parent
THRESHOLD = 0x40000000
LIMIT = 0x96666666
DISCHARGE = 0x03936C71
SOURCE_SHA = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
WRAP_SHA = "895788d911d5573fd9383d5bc5c0f2c109b7f515b3797e0d52e978c30ca90851"
OFFSETS = (0, 1, 2, 3, 64, 114, 230, 231, 232, 1024, 8192, 25992, 26002, 27002)


def cases() -> Iterable[tuple[int, ...]]:
    return itertools.product(
        (0, 3, 4, 7), (0, 57), (64, 200), range(5), (64, 8192, 27000), range(8)
    )


def points(action: int, change: int) -> list[tuple[int, int]]:
    times = (
        set(OFFSETS)
        | {change + x for x in OFFSETS}
        | {change - 1, change, change + 1, change + 63, change + 64, change + 65}
    )
    result = [(t, 0) for t in times] + [(change, 1)]
    if action >= 3:
        result.append((change + 64, 1))
    return sorted(result)


def counter(mode: int, phase: int, tick: int) -> int:
    if mode & 4:
        return min(229, max(0, tick - 2))
    return min(228, (tick + phase) // 114) if mode == 3 else 0


def input_state(
    mode: int,
    phase: int,
    position: int,
    action: int,
    change: int,
    tick: int,
    after: int,
) -> tuple[int, bool, int]:
    end = 231 if mode & 4 else (228 * 114 - phase + 1 if mode == 3 else 1 << 60)
    rate, level, latch, waiting = THRESHOLD // (position * 114), 0, 42, True
    start = 2
    events = [(change, action)] if action else []
    if action >= 3:
        events.append((change + 64, 5))
    events = [(t, kind) for t, kind in events if t < tick or (t == tick and after)]
    events.append((tick, -1))
    for stop, kind in events:
        active_stop = min(stop, end)
        duration = max(0, active_stop - start)
        if waiting and rate and level < THRESHOLD:
            crossing = start + (THRESHOLD - level + rate - 1) // rate
            if crossing <= active_stop:
                latch, waiting = counter(mode, phase, crossing), False
        level = min(LIMIT, level + rate * duration)
        if stop >= end and waiting:
            latch, waiting = (229 if mode & 4 else 228), False
        inactive = max(0, stop - max(start, end))
        level = (
            min(LIMIT, level + rate * inactive)
            if mode & 4
            else max(0, level - DISCHARGE * inactive)
        )
        if kind == 1:
            rate = THRESHOLD // 114
        elif kind == 2:
            rate = THRESHOLD // (200 * 114)
        elif kind == 3:
            level, rate = 0, 0
            waiting = stop < end
        elif kind == 4:
            rate = 0
        elif kind == 5:
            rate = THRESHOLD // (position * 114)
        start = max(2, stop)
    value = latch
    if waiting:
        value = counter(mode, phase, tick)
        if mode & 4 or (mode == 3 and (tick + phase) % 114 == 113):
            value &= value + 1
    return value, waiting, level


def expected(case: tuple[int, ...], tick: int, after: int) -> tuple[int, ...]:
    mode, phase, position, action, change, selected = case
    target = input_state(mode, phase, position, action, change, tick, after)
    other = input_state(mode, phase, position, 0, change, tick, after)
    allpot = (1 << selected if target[1] else 0) | (
        (255 ^ (1 << selected)) if other[1] else 0
    )
    end = 231 if mode & 4 else (228 * 114 - phase + 1 if mode == 3 else 1 << 60)
    return (
        target[0],
        other[0],
        allpot,
        counter(mode, phase, tick),
        int(tick < end),
        target[2],
        other[2],
    )


def verify(lines: Iterable[str]) -> dict[str, int]:
    inventory = {
        (case, tick, after)
        for case in cases()
        for tick, after in points(case[3], case[4])
    }
    seen: set[tuple[tuple[int, ...], int, int]] = set()
    for line in lines:
        fields = tuple(map(int, line.split()))
        if len(fields) != 15:
            raise ValueError("malformed input observation")
        case, tick, after = fields[:6], fields[6], fields[7]
        key = case, tick, after
        if key not in inventory:
            raise ValueError("unknown input observation")
        if key in seen:
            raise ValueError("duplicate input observation")
        seen.add(key)
        wanted = expected(case, tick, after)
        if fields[8:] != wanted:
            raise ValueError(f"input mismatch {key}: {fields[8:]} != {wanted}")
    if seen != inventory:
        raise ValueError("incomplete input inventory")
    return {"cases": len(list(cases())), "observations": len(seen)}


def between(source: str, start: str, stop: str) -> str:
    a = source.index(start)
    return source[a : source.index(stop, a)]


def run(reference: Path, scratch: Path) -> None:
    scratch.mkdir(parents=True, exist_ok=False)
    chip_raw = (reference / "src/ATAudio/source/pokey.cpp").read_bytes()
    wrap_raw = (reference / "src/h/at/atcore/wraptime.h").read_bytes()
    if (
        hashlib.sha256(chip_raw).hexdigest() != SOURCE_SHA
        or hashlib.sha256(wrap_raw).hexdigest() != WRAP_SHA
    ):
        raise ValueError("reference identity changed")
    source, wrap = (raw.decode().replace("\r\n", "\n") for raw in (chip_raw, wrap_raw))
    scaffold = (HERE.parent / "2026-10-11-pokey-pot-scan/scaffold.cpp").read_text()
    scaffold = scaffold.replace(
        "/* WRAP */", between(wrap, "struct ATWrapTime", "#endif")
    )
    extra = """
    static constexpr int kPotHiPosGrounded = 0x7fffffff, kPotHiPosUnconnected = 0x7ffffffe;
    std::array<uint32, 8> mPotHiPositions{};
    bool mbAllowImmediatePotUpdate = false;
    void SetPotPosHires(unsigned, int);
"""
    scaffold = scaffold.replace(
        "    uint8 ReadByte(uint8);", "    uint8 ReadByte(uint8);\n" + extra
    )
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
    setter = between(
        source,
        "void ATPokeyEmulator::SetPotPosHires(unsigned",
        "void ATPokeyEmulator::AdvanceScanLine()",
    )
    assembled = scaffold + methods + setter + (HERE / "driver.cpp").read_text()
    variants = {
        "baseline": assembled,
        "lost-charge": assembled.replace(
            "mPotGroundedMask &= ~potBit;",
            "mPotGroundedMask &= ~potBit; mPotChargeLevels[idx] = 0;",
        ),
        "lost-rearm": assembled.replace("mALLPOT |= potBit;", "mALLPOT |= 0;"),
        "immediate-workaround": assembled.replace(
            "mbAllowImmediatePotUpdate = false", "mbAllowImmediatePotUpdate = true"
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
    summary["setter_sha256"] = hashlib.sha256(setter.encode()).hexdigest()
    summary["assembled_sha256"] = hashlib.sha256(assembled.encode()).hexdigest()
    (scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    run(args.reference, args.scratch)
