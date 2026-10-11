"""Qualify unchanged AUDF write paths against pending timer borrows."""

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

CHIP_HASH = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"


def extract(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("ambiguous reference boundary")
    return text[text.index(start) : text.index(end)]


def verify(text: str) -> dict[str, object]:
    keys = set()
    event_count = irq_count = output_count = 0
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 16 or fields[0] != "CASE":
            raise ValueError("malformed AUDF capture")
        key = tuple(map(int, fields[1:6]))
        if key in keys:
            raise ValueError("duplicate AUDF case")
        keys.add(key)
        channel, mode, old, new, offset = key
        divisor = (28, 114, 1)[mode]
        first = 1000 + (old + 1) * divisor + 3
        if int(fields[6]) != first + offset:
            raise ValueError("wrong AUDF write time")
        selected = new if offset <= -2 else old
        selected_period = selected + 4 if mode == 2 else (selected + 1) * divisor
        new_period = new + 4 if mode == 2 else (new + 1) * divisor
        second = first + selected_period
        times = [first, second, second + new_period, second + 2 * new_period]
        groups: dict[str, list[tuple[int, int]]] = {"E": [], "I": [], "O": []}
        for field in fields[7:]:
            if field[0] not in groups:
                raise ValueError("unknown observation type")
            parts = tuple(map(int, field[1:].split(":")))
            if len(parts) != 2:
                raise ValueError("malformed observation")
            groups[field[0]].append(parts)
        if groups["E"] != [(t, channel) for t in times]:
            raise ValueError(f"AUDF borrow/reload mismatch: {key}: {groups['E']}")
        expected_irqs = (
            []
            if channel == 2
            else [(t, {0: 254, 1: 253, 3: 251}[channel]) for t in times]
        )
        if groups["I"] != expected_irqs:
            raise ValueError("AUDF IRQ delivery mismatch")
        initial = int(channel < 2)
        expected_output = [(2000, initial)] + [
            (time * 2 + 4, initial ^ ((n + 1) & 1)) for n, time in enumerate(times)
        ]
        if groups["O"] != expected_output:
            raise ValueError("AUDF output delivery mismatch")
        event_count += len(groups["E"])
        irq_count += len(groups["I"])
        output_count += len(groups["O"]) - 1
    expected = {
        (channel, mode, old, new, offset)
        for channel, mode, old, new, offset in itertools.product(
            range(4), range(3), (0, 1, 15, 255), (0, 1, 15, 255), (-3, -2, -1)
        )
        if mode != 2 or channel % 2 == 0
    }
    if keys != expected:
        raise ValueError("incomplete AUDF case inventory")
    return {
        "cases": len(keys),
        "timer_events": event_count,
        "irq_calls": irq_count,
        "output_transitions": output_count,
        "capture_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    here = Path(__file__).parent
    # Rebuild and verify the prerequisite before reusing its assembled methods.
    subprocess.run(
        [
            sys.executable,
            str(here.parent / "2026-10-11-pokey-borrow-output/capture.py"),
            str(args.reference),
            str(args.scratch / "borrow"),
        ],
        check=True,
    )
    chip_raw = (args.reference / "src/ATAudio/source/pokey.cpp").read_bytes()
    if hashlib.sha256(chip_raw).hexdigest() != CHIP_HASH:
        raise ValueError("chip source hash mismatch")
    chip = chip_raw.decode().replace("\r\n", "\n")
    writes = chip[chip.index("void ATPokeyEmulator::WriteByte(") :]
    cases = "\n".join(
        extract(writes, f"\t\tcase 0x{reg:02X}:", f"\t\tcase 0x{reg + 1:02X}:")
        for reg in (0, 2, 4, 6)
    )
    setter = chip[
        chip.index("template<unsigned T_Ch>\nvoid ATPokeyEmulator::SetAUDFP1(") :
    ]
    # This method is the final definition in the pinned source; exact file hash
    # and closing brace ensure appended reference content cannot pass unnoticed.
    if not setter.rstrip().endswith("}"):
        raise ValueError("unterminated AUDF setter")
    base = (args.scratch / "borrow/baseline.cpp").read_text()
    if base.count("\nint main() {") != 1:
        raise ValueError("ambiguous driver boundary")
    base = base.split("\nint main() {")[0]
    anchor = "    void (*mpNotifyBiClockChangeFn)() = unsupported;"
    if base.count(anchor) != 1:
        raise ValueError("ambiguous class extension")
    base = base.replace(
        anchor,
        anchor
        + "\n    bool mbSerialRateChanged = false;\n    template<unsigned channel> void SetAUDFP1(int);\n    void writeAudf(uint8, uint8);",
    )
    driver = (here / "driver.cpp").read_text()
    source = (
        base
        + setter
        + "\nvoid ATPokeyEmulator::writeAudf(uint8 reg, uint8 value) { switch (reg) {\n"
        + cases
        + "\ndefault: unsupported(); } }\n"
        + driver
    )
    summary: dict[str, object] = {
        "chip_sha256": CHIP_HASH,
        "write_cases_sha256": hashlib.sha256(cases.encode()).hexdigest(),
        "setter_sha256": hashlib.sha256(setter.encode()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.encode()).hexdigest(),
    }
    for name, content in (
        ("baseline", source),
        (
            "immediate",
            source.replace(
                "const uint32 effectiveTime = t + 2;", "const uint32 effectiveTime = t;"
            ),
        ),
        (
            "late",
            source.replace(
                "const uint32 effectiveTime = t + 2;",
                "const uint32 effectiveTime = t + 3;",
            ),
        ),
    ):
        if name != "baseline" and content == source:
            raise ValueError("mutation did not change source")
        cpp, exe = args.scratch / f"{name}.cpp", args.scratch / name
        cpp.write_text(content)
        subprocess.run(
            [
                "clang++",
                "-std=c++20",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-O2",
                str(cpp),
                "-o",
                str(exe),
            ],
            check=True,
        )
        output = subprocess.check_output([str(exe)], text=True)
        (args.scratch / f"{name}.txt").write_text(output)
        if name == "baseline":
            summary[name] = verify(output)
        else:
            try:
                verify(output)
            except ValueError as error:
                summary[name] = {"rejected": str(error)}
            else:
                raise ValueError("delivery mutation escaped verifier")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
