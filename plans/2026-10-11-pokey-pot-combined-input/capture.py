"""Check same-timestamp SKCTL/input ordering with retained charge."""

import argparse
import gzip
import hashlib
import itertools
import json
import runpy
import subprocess
from collections.abc import Iterable
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOCK = runpy.run_path(
    str(HERE.parent / "2026-10-11-pokey-pot-clock-switch/capture.py")
)["expected"]
THRESHOLD, LIMIT, DISCHARGE = 0x40000000, 0x96666666, 0x03936C71
SOURCE_SHA = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
WRAP_SHA = "895788d911d5573fd9383d5bc5c0f2c109b7f515b3797e0d52e978c30ca90851"


def cases() -> Iterable[tuple[int, ...]]:
    raw = itertools.product(
        (0, 3, 4, 7), (0, 3, 4, 7), (0, 57), (64, 128), range(3), range(2), range(2)
    )
    return (case + (index % 8,) for index, case in enumerate(raw))


def points(change: int) -> list[tuple[int, int]]:
    return [(change, 0), (change, 1)] + [
        (change + offset, 0) for offset in (1, 2, 3, 114, 27000)
    ]


def expected(case: tuple[int, ...], tick: int, after: int) -> tuple[int, ...]:
    old, new, phase, change, action, charged, order, selected = case
    old_rate = THRESHOLD // (64 * 114)
    initial = THRESHOLD + 100 if charged else 0
    before = tick == change and not after
    if before:
        clock = CLOCK(old, old, phase, change, tick)
        level = min(LIMIT, initial + old_rate * (tick - 2))
        waiting = not charged
        pot = clock[0] if waiting else 42
    else:
        clock = CLOCK(old, new, phase, change, tick)
        rate = THRESHOLD // 114 if action == 0 else 0
        processed = change + (2 if old != new else 0)
        level = min(LIMIT, initial + old_rate * (change - 2))
        if action == 1:
            level = 0
        elif old != new:
            level = min(LIMIT, level + 2 * (rate if order == 0 else old_rate))
        waiting = not charged or action == 1
        # Master lifetime comes from the independently qualified digital oracle.
        if CLOCK(old, new, phase, change, change + 100000)[3]:
            end = 1 << 60
        else:
            low, high = change, change + 100000
            while high - low > 1:
                middle = (low + high) // 2
                if CLOCK(old, new, phase, change, middle)[3]:
                    low = middle
                else:
                    high = middle
            end = high
        pot = 42
        if waiting:
            crossing = (
                processed + (THRESHOLD - level + rate - 1) // rate if rate else 1 << 61
            )
            if crossing <= min(tick, end):
                pot, waiting = CLOCK(old, new, phase, change, crossing)[2], False
            elif tick >= end:
                pot, waiting = (229 if new & 4 else 228), False
            else:
                pot = clock[0]
        level = min(LIMIT, level + rate * max(0, min(tick, end) - processed))
        inactive = max(0, tick - max(end, processed))
        level = (
            min(LIMIT, level + rate * inactive)
            if new & 4
            else max(0, level - DISCHARGE * inactive)
        )
    allpot = (1 << selected if waiting else 0) | (
        (255 ^ (1 << selected)) if clock[3] else 0
    )
    return pot, clock[0], allpot, clock[2], clock[3], level


def verify(lines: Iterable[str]) -> dict[str, int]:
    inventory = {
        (case, tick, after) for case in cases() for tick, after in points(case[3])
    }
    seen: set[tuple[tuple[int, ...], int, int]] = set()
    for line in lines:
        fields = tuple(map(int, line.split()))
        if len(fields) != 16:
            raise ValueError("malformed combined observation")
        case, tick, after = fields[:8], fields[8], fields[9]
        key = case, tick, after
        if key not in inventory:
            raise ValueError("unknown combined observation")
        if key in seen:
            raise ValueError("duplicate combined observation")
        seen.add(key)
        wanted = expected(case, tick, after)
        if fields[10:] != wanted:
            raise ValueError(f"combined mismatch {key}: {fields[10:]} != {wanted}")
    if seen != inventory:
        raise ValueError("incomplete combined inventory")
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
    scaffold = (
        (HERE.parent / "2026-10-11-pokey-pot-scan/scaffold.cpp")
        .read_text()
        .replace("/* WRAP */", between(wrap, "struct ATWrapTime", "#endif"))
    )
    scaffold = scaffold.replace(
        "uint32 now = 1000;",
        "void UnsetEvent(int &event) { event = 0; }\n    uint32 now = 1000;",
    )
    scaffold = scaffold.replace(
        "class ATPokeyEmulator {",
        '#define VDASSERT(x) do { if (!(x)) throw std::runtime_error("assertion"); } while (false)\nunsigned VDFindLowestSetBitFast(unsigned) { throw std::runtime_error("key lookup"); }\nclass ATPokeyEmulator {',
    )
    extra = (HERE.parent / "2026-10-11-pokey-pot-clock-switch/extra.cpp").read_text()
    extra += """
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
    start = source.index(
        "\t\tcase 0x0F:", source.index("void ATPokeyEmulator::WriteByte(")
    )
    case = source[start : source.index("\n\t\tdefault:", start)]
    write = (
        'void ATPokeyEmulator::WriteByte(uint8 reg, uint8 value) {\nif (reg != 15 || (value & ~7)) throw std::runtime_error("unsupported write");\nswitch (reg) {\n'
        + case
        + '\ndefault: throw std::runtime_error("unsupported register");\n}\n}\n'
    )
    assembled = scaffold + methods + setter + write + (HERE / "driver.cpp").read_text()
    variants = {
        "baseline": assembled,
        "lost-delivery": assembled.replace("UpdatePots(2);", "UpdatePots(0);"),
        "lost-charge": assembled.replace(
            "mPotGroundedMask &= ~potBit;",
            "mPotGroundedMask &= ~potBit; mPotChargeLevels[idx] = 0;",
        ),
        "lost-order": assembled.replace("if (order == 0)", "if (false)"),
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
    summary["skctl_case_sha256"] = hashlib.sha256(case.encode()).hexdigest()
    summary["assembled_sha256"] = hashlib.sha256(assembled.encode()).hexdigest()
    (scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    run(args.reference, args.scratch)
