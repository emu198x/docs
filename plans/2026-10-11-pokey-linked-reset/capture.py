"""Check both linked timer borrows, resets and waveform delivery together."""

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path


def replace_one(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("ambiguous linked scaffold boundary")
    return text.replace(old, new, 1)


def pair_events(
    first_low: int, high: int, divisor: int, period: int, lo: int, end: int
) -> list[tuple[int, int]]:
    result = []
    for start in range(first_low, end + 1, period):
        result.extend(
            (time, lo)
            for n in range(high + 1)
            if (time := start + n * 256 * divisor) <= end
        )
        hi_time = start + high * 256 * divisor + 3
        if hi_time <= end:
            result.append((hi_time, lo + 1))
    return result


def verify(lines: Iterable[str]) -> dict[str, object]:
    keys = set()
    event_count = irq_count = reset_count = transitions = 0
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode())
        fields = line.split()
        if len(fields) < 15 or fields[0] != "CASE":
            raise ValueError("malformed linked reset capture")
        key = tuple(map(int, fields[1:8]))
        if key in keys:
            raise ValueError("duplicate linked reset case")
        keys.add(key)
        pair, mode, low, high, anchor, offset, action = key
        divisor = (28, 114, 1)[mode]
        lo = pair * 2
        first_low = 1000 + (low + 1) * divisor + 3
        first_high = first_low + high * 256 * divisor + 3
        period = low + high * 256 + 7 if mode == 2 else (low + high * 256 + 1) * divisor
        write = (first_high if anchor else first_low) + period + offset
        end = write + 20 + 4 * period
        if list(map(int, fields[8:13])) != [first_low, first_high, period, write, end]:
            raise ValueError("linked input coordinates mismatch")
        events, irqs, resets, observed = [], [], [], []
        for field in fields[13:]:
            if field.startswith("R"):
                resets.append(int(field[1:]))
            elif field[0] in ("E", "I", "O"):
                item = tuple(map(int, field[1:].split(":")))
                if len(item) != 2:
                    raise ValueError("malformed linked observation")
                {"E": events, "I": irqs, "O": observed}[field[0]].append(item)
            else:
                raise ValueError("unknown linked observation")
        if action:
            reload = write + max(0, action - 1) + 4
            expected_resets = [reload]
            expected = pair_events(first_low, high, divisor, period, lo, reload - 1)
            next_low = (
                reload + low + 4
                if mode == 2
                else 1000 + ((reload - 1000) // divisor + low + 1) * divisor + 3
            )
            expected.extend(pair_events(next_low, high, divisor, period, lo, end))
        else:
            expected_resets = []
            expected = pair_events(first_low, high, divisor, period, lo, end)
        expected.sort()
        if resets != expected_resets:
            raise ValueError(f"linked reset delivery mismatch: {key}")
        if events != expected:
            raise ValueError(
                f"linked borrow sequence mismatch: {key}: first observed {events[:8]} expected {expected[:8]}"
            )
        masks = {0: 254, 1: 253, 3: 251}
        expected_irqs = [(t, masks[c]) for t, c in expected if c in masks]
        if irqs != expected_irqs:
            raise ValueError("linked IRQ mismatch")
        operations = [(t * 2 + 4, 1) for t, c in expected if c == lo + anchor]
        operations.extend((t * 2, 0) for t in expected_resets)
        state, latch = 0, int(pair == 0)
        output = [(2000, latch)]
        for time, toggle in sorted(operations):
            state = state ^ 1 if toggle else 1
            level = state ^ latch
            if output[-1][0] == time:
                output[-1] = (time, level)
                if len(output) > 1 and output[-2][1] == level:
                    output.pop()
            elif output[-1][1] != level:
                output.append((time, level))
        if observed != output:
            raise ValueError(f"linked waveform mismatch: {key}")
        event_count += len(events)
        irq_count += len(irqs)
        reset_count += len(resets)
        transitions += len(observed) - 1
    expected_keys = set(
        itertools.product(
            range(2),
            range(3),
            (0, 1, 15, 255),
            (0, 1, 2, 255),
            range(2),
            range(-6, 3),
            range(4),
        )
    )
    if keys != expected_keys:
        raise ValueError("incomplete linked reset inventory")
    return {
        "cases": len(keys),
        "timer_events": event_count,
        "irq_calls": irq_count,
        "reset_calls": reset_count,
        "output_transitions": transitions,
        "capture_sha256": digest.hexdigest(),
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
            str(here.parent / "2026-10-11-pokey-reset-output/connected.py"),
            str(args.reference),
            str(args.scratch / "reset"),
        ],
        check=True,
    )
    base = (args.scratch / "reset/connected.cpp").read_text()
    if base.count("// Own driver. Initial loaded count") != 1:
        raise ValueError("ambiguous original driver boundary")
    base = base.split("// Own driver. Initial loaded count")[0]
    driver = (here / "driver.cpp").read_text()
    source = base + driver
    summary: dict[str, object] = {
        "assembled_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.encode()).hexdigest(),
    }
    for name, content in (
        ("baseline", source),
        ("no-high12", replace_one(source, "FireTimer<1>();", "(void)0;")),
        ("no-high34", replace_one(source, "FireTimer<3>();", "(void)0;")),
        ("no-cancel", replace_one(source, "if (dt == 1)", "if (dt == 999999)")),
    ):
        cpp, exe, capture = (
            args.scratch / f"{name}.cpp",
            args.scratch / name,
            args.scratch / f"{name}.txt",
        )
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
        with capture.open("w") as output:
            subprocess.run([str(exe)], stdout=output, check=True)
        with capture.open() as rows:
            if name == "baseline":
                summary[name] = verify(rows)
            else:
                try:
                    verify(rows)
                except ValueError as error:
                    summary[name] = {"rejected": str(error)}
                else:
                    raise ValueError("linked mutation escaped verifier")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
