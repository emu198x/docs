"""Qualify the original SKCTL pot clock path with unrelated subsystem observers."""

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
SOURCE_SHA = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
MODES = (0, 3, 4, 7)
PHASES = (0, 57, 110)
WRITES = (16, 64, 128)


def expected(old: int, new: int, phase: int, change: int, tick: int) -> tuple[int, ...]:
    mode, anchor = old, -phase
    if tick < change or old == new:
        if old & 4:
            count, end = min(229, max(0, tick - 2)), 231
        elif old == 0:
            count, end = 0, 1 << 60
        else:
            count, end = min(228, (tick + phase) // 114), 228 * 114 - phase + 1
    else:
        mode = new
        seed = change if old & 4 else ((change + phase) // 114 if old == 3 else 0)
        if old & 3 == 0 and new & 3:
            anchor = change - 33
        if new & 4:
            count = min(229, seed + max(0, tick - change - 2))
            end = change + 2 + 229 - seed
        elif new == 0:
            count, end = seed, 1 << 60
        else:
            base = (change - anchor) // 114
            increments = (tick - anchor) // 114 - base if tick > change + 2 else 0
            count = min(228, seed + increments)
            end = anchor + (base + 228 - seed) * 114 + 1
    active = tick < end
    if not active:
        return 229 if mode & 4 else 228, 0, count, 0
    pot = count
    if mode & 4 or (mode == 3 and (tick - anchor) % 114 == 113):
        pot &= count + 1
    return pot, 255, count, 1


def verify(lines: Iterable[str]) -> dict[str, int]:
    inventory = set(itertools.product(MODES, MODES, PHASES, WRITES))
    seen: set[tuple[int, ...]] = set()
    clocks = 0
    for line in lines:
        fields = line.split()
        if len(fields) != 27008 or fields[0] != "CASE":
            raise ValueError("incomplete clock trace")
        case = tuple(map(int, fields[1:5]))
        if case not in inventory:
            raise ValueError("unknown clock-switch case")
        if case in seen:
            raise ValueError("duplicate clock-switch case")
        seen.add(case)
        for tick, observation in enumerate(fields[5:]):
            actual = tuple(map(int, observation.split(":")))
            wanted = expected(*case, tick)
            if actual != wanted:
                raise ValueError(
                    f"clock-switch mismatch {case} t={tick}: {actual} != {wanted}"
                )
            clocks += 1
    if seen != inventory:
        raise ValueError("incomplete clock-switch inventory")
    return {"cases": len(seen), "clocks": clocks, "pot_reads": clocks * 8}


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
    source_bytes = (reference / "src/ATAudio/source/pokey.cpp").read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA:
        raise ValueError("chip source identity changed")
    source = source_bytes.decode().replace("\r\n", "\n")
    start = source.index(
        "\t\tcase 0x0F:", source.index("void ATPokeyEmulator::WriteByte(")
    )
    case = source[start : source.index("\n\t\tdefault:", start)]
    prior = (scratch / "prerequisite/baseline.cpp").read_text()
    assembled = prior[: prior.index("int main() {")]
    assembled = assembled.replace(
        "uint32 now = 1000;",
        "void UnsetEvent(int &event) { event = 0; }\n    uint32 now = 1000;",
    )
    assembled = assembled.replace(
        "class ATPokeyEmulator {",
        '#define VDASSERT(x) do { if (!(x)) throw std::runtime_error("assertion"); } while (false)\nunsigned VDFindLowestSetBitFast(unsigned) { throw std::runtime_error("key lookup"); }\nclass ATPokeyEmulator {',
    )
    assembled = assembled.replace(
        "    uint8 ReadByte(uint8);",
        "    uint8 ReadByte(uint8);\n" + (HERE / "extra.cpp").read_text(),
    )
    assembled += 'void ATPokeyEmulator::WriteByte(uint8 reg, uint8 value) {\nif (reg != 15 || (value & ~7)) throw std::runtime_error("unsupported write");\nswitch (reg) {\n'
    assembled += (
        case + '\ndefault: throw std::runtime_error("unsupported register");\n}\n}\n'
    )
    assembled += (HERE / "driver.cpp").read_text()
    variants = {
        "baseline": assembled,
        "base-clock-observer": assembled.replace(
            "void SetupTimers(unsigned) {}",
            "void SetupTimers(unsigned) { UpdateLast15KHzTime(); }",
        ),
        "no-delay": assembled.replace("UpdatePots(2);", "UpdatePots(0);"),
        "wrong-resume": assembled.replace("+ 81 - 114", "+ 80 - 114"),
        "lost-slow-phase": assembled.replace(
            "mPotLastTimeSlow = UpdateLast15KHzTime();",
            "mPotLastTimeSlow = ATSCHEDULER_GETTIME(mpScheduler);",
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
            if name in ("baseline", "base-clock-observer"):
                raise
            summary[name] = str(error)
        else:
            if name == "base-clock-observer":
                if output.read_bytes() != (scratch / "baseline.txt").read_bytes():
                    raise ValueError("base-clock observer changed output")
                summary[name] = "byte-identical complete trace"
                continue
            if name != "baseline":
                raise ValueError(f"negative control passed: {name}")
            summary.update(result)
            raw = output.read_bytes()
            summary["capture_sha256"] = hashlib.sha256(raw).hexdigest()
            (scratch / "baseline.txt.gz").write_bytes(gzip.compress(raw, mtime=0))
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
