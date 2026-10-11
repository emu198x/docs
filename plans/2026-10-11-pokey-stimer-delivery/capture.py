"""Execute the original STIMER write and both timer reset stages."""

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

CHIP_HASH = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
SCHEDULER_HASH = "b0e31fa465bc1b5382c8792ee17106a607d35636aa791981ad404256dda67948"


def extract(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("ambiguous reference boundary")
    return text[text.index(start) : text.index(end)]


def replace_one(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("ambiguous scaffold extension")
    return text.replace(old, new, 1)


def verify(text: str) -> dict[str, object]:
    keys = set()
    event_count = irq_count = reset_count = 0
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 10 or fields[0] != "CASE":
            raise ValueError("malformed STIMER capture")
        key = tuple(map(int, fields[1:6]))
        if key in keys:
            raise ValueError("duplicate STIMER case")
        keys.add(key)
        channel, mode, audf, offset, action = key
        divisor = (28, 114, 1)[mode]
        first = 1000 + 32 * divisor + 3
        period = audf + 4 if mode == 2 else (audf + 1) * divisor
        write, end = first + offset, first + 20 + 4 * period
        if list(map(int, fields[6:9])) != [first, write, end]:
            raise ValueError("wrong STIMER input coordinates")
        events, irqs, resets = [], [], []
        for field in fields[9:]:
            if field.startswith("R"):
                resets.append(int(field[1:]))
            elif field[0] in ("E", "I"):
                value = tuple(map(int, field[1:].split(":")))
                if len(value) != 2:
                    raise ValueError("malformed STIMER observation")
                (events if field[0] == "E" else irqs).append(value)
            else:
                raise ValueError("unknown STIMER observation")
        if not action:
            expected_times = list(range(first, end + 1, period))
            expected_resets = []
        else:
            last_write = write + max(0, action - 1)
            reload = last_write + 4
            expected_resets = [reload]
            # First stage is at reload-1. Its one-clock-away cancellation
            # removes a borrow due at reload; coincident first-stage events fire.
            expected_times = list(range(first, reload, period))
            next_borrow = (
                reload + period
                if mode == 2
                else 1000 + ((reload - 1000) // divisor + audf + 1) * divisor + 3
            )
            expected_times += list(range(next_borrow, end + 1, period))
        if resets != expected_resets:
            raise ValueError(f"reset delivery mismatch: {key}: {resets}")
        if events != [(time, channel) for time in expected_times]:
            raise ValueError(f"reset borrow mismatch: {key}: {events}")
        expected_irqs = (
            []
            if channel == 2
            else [(time, {0: 254, 1: 253, 3: 251}[channel]) for time in expected_times]
        )
        if irqs != expected_irqs:
            raise ValueError("STIMER IRQ delivery mismatch")
        event_count += len(events)
        irq_count += len(irqs)
        reset_count += len(resets)
    expected = {
        (channel, mode, audf, offset, action)
        for channel, mode, audf, offset, action in itertools.product(
            range(4), range(3), (0, 1, 15, 255), range(-6, 3), range(4)
        )
        if mode != 2 or channel % 2 == 0
    }
    if keys != expected:
        raise ValueError("incomplete STIMER case inventory")
    return {
        "cases": len(keys),
        "timer_events": event_count,
        "irq_calls": irq_count,
        "reset_calls": reset_count,
        "capture_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    here = Path(__file__).parent
    subprocess.run(
        [
            sys.executable,
            str(here.parent / "2026-10-11-pokey-borrow-output/capture.py"),
            str(args.reference),
            str(args.scratch / "borrow"),
        ],
        check=True,
    )
    raw = (args.reference / "src/ATAudio/source/pokey.cpp").read_bytes()
    if hashlib.sha256(raw).hexdigest() != CHIP_HASH:
        raise ValueError("chip source hash mismatch")
    chip = raw.decode().replace("\r\n", "\n")
    write = extract(
        chip[chip.index("void ATPokeyEmulator::WriteByte(") :],
        "\t\tcase 0x09:",
        "\t\tcase 0x0A:",
    )
    resets = extract(
        chip,
        "\t\tcase kATPokeyEventResetTimers:",
        "\t\tcase kATPokeyEventSerialOutput:",
    )
    base = (args.scratch / "borrow/baseline.cpp").read_text()
    if base.count("\nint main() {") != 1:
        raise ValueError("ambiguous driver boundary")
    base = base.split("\nint main() {")[0]
    scheduler = (here / "scheduler.cpp").read_text()
    driver = (here / "driver.cpp").read_text()
    old_scheduler = extract(base, "struct Event {", "struct TimerRenderer {")
    base = replace_one(base, old_scheduler, scheduler + "\n")
    base = replace_one(
        base,
        "struct TimerRenderer {",
        "struct TimerRenderer {\n    std::vector<uint32> resets;\n    void ResetTimers() { resets.push_back(output.scheduler); }",
    )
    base = replace_one(
        base,
        "    void dispatch(uint32 event) {",
        "    Event *mpResetTimersEvent = nullptr, *mpResetTimers2Event = nullptr;\n    void writeStimer();\n    void dispatch(uint32 event) {",
    )
    base = replace_one(
        base,
        "            default: unsupported();",
        resets + "\n            default: unsupported();",
    )
    source = (
        base
        + "\nvoid ATPokeyEmulator::writeStimer() { switch (0x09) {\n"
        + write
        + "\ndefault: unsupported(); } }\n"
        + driver
    )
    scheduler_raw = (args.reference / "src/ATCore/source/scheduler.cpp").read_bytes()
    if hashlib.sha256(scheduler_raw).hexdigest() != SCHEDULER_HASH:
        raise ValueError("reference scheduler hash mismatch")
    summary: dict[str, object] = {
        "chip_sha256": CHIP_HASH,
        "reference_scheduler_sha256": hashlib.sha256(scheduler_raw).hexdigest(),
        "write_case_sha256": hashlib.sha256(write.encode()).hexdigest(),
        "reset_cases_sha256": hashlib.sha256(resets.encode()).hexdigest(),
        "scheduler_sha256": hashlib.sha256(scheduler.encode()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.encode()).hexdigest(),
    }
    for name, content in (
        ("baseline", source),
        (
            "reverse-fifo",
            replace_one(
                source, "e.sequence < found->sequence", "e.sequence > found->sequence"
            ),
        ),
        ("no-cancel", replace_one(source, "if (dt == 1)", "if (dt == 999999)")),
        (
            "late-reload",
            replace_one(
                source,
                "SetEvent(1, this, kATPokeyEventResetTimers2",
                "SetEvent(2, this, kATPokeyEventResetTimers2",
            ),
        ),
        (
            "early-reset",
            replace_one(
                source,
                "SetEvent(3, this, kATPokeyEventResetTimers,",
                "SetEvent(2, this, kATPokeyEventResetTimers,",
            ),
        ),
    ):
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
        if name == "reverse-fifo":
            result = subprocess.run(
                [str(exe)], text=True, capture_output=True, check=False
            )
            if (
                result.returncode == 0
                or "scheduler FIFO order mismatch" not in result.stderr
            ):
                raise ValueError("scheduler mutation escaped verifier")
            summary[name] = {"rejected": "scheduler FIFO order mismatch"}
            continue
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
                raise ValueError("reset mutation escaped verifier")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
