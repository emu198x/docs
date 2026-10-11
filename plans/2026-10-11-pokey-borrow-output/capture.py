"""Execute original timer/borrow paths into the qualified reference renderer."""

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

CHIP_HASH = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
RENDER_HASH = "d79effe1aa9967e50bb189ebec6fd1cb850e29e63d78ae878695409da9b29aa6"
WRAP_HASH = "895788d911d5573fd9383d5bc5c0f2c109b7f515b3797e0d52e978c30ca90851"


def extract(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("ambiguous reference boundary")
    return text[text.index(start) : text.index(end)]


def read_source(path: Path, digest: str) -> str:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"source hash mismatch: {path.name}")
    return raw.decode().replace("\r\n", "\n")


def verify(text: str) -> dict[str, object]:
    keys = set()
    counts = {"timer_events": 0, "irq_calls": 0, "output_transitions": 0}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 13 or fields[0] != "CASE":
            raise ValueError("malformed timer capture")
        key = tuple(map(int, fields[1:7]))
        if key in keys:
            raise ValueError("duplicate case")
        keys.add(key)
        pair, linked, mode, low, high, phase = key
        start, first_low, first_high, period_low, period_high = map(int, fields[7:12])
        lo, hi = pair * 2, pair * 2 + 1
        divisor = 114 if mode == 1 else 28
        raw_low = low + 1 if mode == 2 else (low + 1) * divisor - phase
        full_low = 256 if mode == 2 else 256 * divisor
        expected_first_low = start + raw_low + 3
        expected_first_high = (
            expected_first_low + high * full_low + 3
            if linked
            else start + (high + 1) * divisor - phase + 3
        )
        if start != 1000 + phase or (first_low, first_high) != (
            expected_first_low,
            expected_first_high,
        ):
            raise ValueError("first borrow deadline mismatch")
        expected_low_period = low + 4 if mode == 2 else (low + 1) * divisor
        combined = low + high * 256
        expected_high_period = (
            (combined + 7 if mode == 2 else (combined + 1) * divisor)
            if linked
            else (high + 1) * divisor
        )
        if (period_low, period_high) != (expected_low_period, expected_high_period):
            raise ValueError("settled period mismatch")
        groups: dict[str, list[tuple[int, int]]] = {"E": [], "I": [], "O": []}
        for field in fields[12:]:
            if field[0] not in groups:
                raise ValueError("unknown observation type")
            parts = tuple(map(int, field[1:].split(":")))
            if len(parts) != 2:
                raise ValueError("malformed observation")
            groups[field[0]].append(parts)
        events = groups["E"]
        if linked:
            expected_events = [
                (first_low + cycle * period_high + n * full_low, lo)
                for cycle in range(4)
                for n in range(high + 1)
            ]
            expected_events += [
                (first_high + cycle * period_high, hi) for cycle in range(4)
            ]
        else:
            end = max(first_low + period_low * 3, first_high + period_high * 3)
            expected_events = [
                (first + n * period, channel)
                for first, period, channel in (
                    (first_low, period_low, lo),
                    (first_high, period_high, hi),
                )
                for n in range((end - first) // period + 1)
            ]
        expected_events.sort()
        if sorted(events) != expected_events or any(
            a[0] > b[0] for a, b in itertools.pairwise(events)
        ):
            raise ValueError(f"borrow delivery/order mismatch: {key}")
        irq_masks = {0: 0xFE, 1: 0xFD, 3: 0xFB}
        expected_irqs = [
            (time, irq_masks[channel])
            for time, channel in events
            if channel in irq_masks
        ]
        if sorted(groups["I"]) != sorted(expected_irqs):
            raise ValueError("IRQ delivery differs from borrow events")
        initial = int(hi == 1)
        expected_output = [(start * 2, initial)]
        for time, channel in events:
            if channel == hi:
                initial ^= 1
                expected_output.append((time * 2 + 4, initial))
        if groups["O"] != expected_output:
            raise ValueError("borrow-to-output delay mismatch")
        counts["timer_events"] += len(events)
        counts["irq_calls"] += len(groups["I"])
        counts["output_transitions"] += len(groups["O"]) - 1
    expected_keys = {
        (pair, linked, mode, low, high, phase)
        for pair, linked, mode, low, high in itertools.product(
            range(2), range(2), range(3), (0, 1, 15, 255), (0, 1, 2, 255)
        )
        for phase in (0, 1, 113 if mode == 1 else 27)
    }
    if keys != expected_keys or not all(counts.values()):
        raise ValueError("incomplete timer case inventory")
    return {
        "cases": len(keys),
        **counts,
        "capture_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    chip = read_source(args.reference / "src/ATAudio/source/pokey.cpp", CHIP_HASH)
    renderer = read_source(
        args.reference / "src/ATAudio/source/pokeyrenderer.cpp", RENDER_HASH
    )
    wrap = read_source(args.reference / "src/h/at/atcore/wraptime.h", WRAP_HASH)
    render_methods = "\n".join(
        (
            extract(wrap, "struct ATWrapTime {", "\n#endif"),
            extract(
                renderer,
                "namespace {\n\tconstexpr uint32 kAudioDelay",
                "\nATPokeyRenderer::ATPokeyRenderer()",
            ),
            extract(
                renderer,
                "void ATPokeyRenderer::AddChannelEvent(",
                "\nvoid ATPokeyRenderer::SetChannelDeferredEvents(",
            ),
            extract(
                renderer,
                "void ATPokeyRenderer::Flush2(",
                "\nvoid ATPokeyRenderer::UpdateVolume(",
            ),
        )
    )
    timer_methods = "\n".join(
        (
            extract(
                chip,
                "template<uint8 activeChannel>\nvoid ATPokeyEmulator::FireTimer()",
                "\nuint32 ATPokeyEmulator::UpdateLast15KHzTime()",
            ),
            extract(
                chip,
                "uint32 ATPokeyEmulator::UpdateLast15KHzTime()",
                "\nvoid ATPokeyEmulator::UpdatePolyTime()",
            ),
            extract(
                chip,
                "template<int channel>\nvoid ATPokeyEmulator::RecomputeTimerPeriod()",
                "\nvoid ATPokeyEmulator::RecomputeAllowedDeferredTimers()",
            ),
            extract(
                chip,
                "template<int channel>\nvoid ATPokeyEmulator::UpdateTimerCounter()",
                "\nsint32 ATPokeyEmulator::ReadBackWriteRegister(",
            ),
            extract(
                chip,
                "template<unsigned T_Ch>\nint ATPokeyEmulator::GetAUDFP1(uint32 t) const",
                "\ntemplate<unsigned T_Ch>\nvoid ATPokeyEmulator::SetAUDFP1(",
            ),
        )
    )
    cases = extract(
        chip,
        "\t\tcase kATPokeyEventTimer1Borrow:",
        "\t\tcase kATPokeyEventResetTwoTones1:",
    )
    enums = extract(chip, "\tenum : uint32 {", "\n\tconst bool kForceActiveTimers")
    here = Path(__file__).parent
    renderer_scaffold = (
        here.parent / "2026-10-11-pokey-filter-timing/harness.cpp"
    ).read_text()
    if renderer_scaffold.count("\nint main() {") != 1:
        raise ValueError("ambiguous renderer scaffold")
    renderer_scaffold = renderer_scaffold.split("\nint main() {")[0]
    timer_scaffold = (here / "timers.cpp").read_text()
    if any(
        timer_scaffold.count(marker) != 1
        for marker in ("// BORROW_CASES", "// TIMER_METHODS")
    ):
        raise ValueError("ambiguous timer scaffold")
    prefix = renderer_scaffold.replace("// REFERENCE_METHODS", render_methods) + enums
    source = prefix + timer_scaffold.replace("// BORROW_CASES", cases).replace(
        "// TIMER_METHODS", timer_methods
    )
    args.scratch.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "chip_sha256": CHIP_HASH,
        "renderer_sha256": RENDER_HASH,
        "timer_methods_sha256": hashlib.sha256(timer_methods.encode()).hexdigest(),
        "borrow_cases_sha256": hashlib.sha256(cases.encode()).hexdigest(),
        "scaffold_sha256": hashlib.sha256(
            (renderer_scaffold + timer_scaffold).encode()
        ).hexdigest(),
    }
    mutations = (
        ("baseline", source),
        (
            "reverse-ties",
            source.replace("event.time < found->time", "event.time <= found->time"),
        ),
        ("no-borrow-delay", source.replace("ticks += 3;", "ticks += 0;")),
        (
            "no-delivery",
            source.replace(
                "mpRenderer->AddChannelEvent(activeChannel);", "(void)activeChannel;"
            ),
        ),
    )
    for label, content in mutations:
        if label != "baseline" and content == source:
            raise ValueError("mutation did not change source")
        cpp, binary = args.scratch / f"{label}.cpp", args.scratch / label
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
                str(binary),
            ],
            check=True,
        )
        captured = subprocess.check_output([str(binary)], text=True)
        (args.scratch / f"{label}.txt").write_text(captured)
        if label in ("baseline", "reverse-ties"):
            summary[label] = verify(captured)
        else:
            try:
                verify(captured)
            except ValueError as error:
                summary[label] = {"rejected": str(error)}
            else:
                raise ValueError("fault escaped verifier")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
