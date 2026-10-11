"""Execute unchanged Altirra output stages with supplied pure-tone events."""

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

SOURCE_HASH = "d79effe1aa9967e50bb189ebec6fd1cb850e29e63d78ae878695409da9b29aa6"
WRAP_HASH = "895788d911d5573fd9383d5bc5c0f2c109b7f515b3797e0d52e978c30ca90851"


def extract(source: str, start: str, end: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("ambiguous source boundary")
    return source[source.index(start) : source.index(end)]


def verify(text: str) -> dict[str, object]:
    rows = {}
    half_cycle = 0
    short_pulses = 0
    total_events = 0
    for line in text.splitlines():
        values = line.split()
        if len(values) < 10 or values[0] != "CASE":
            raise ValueError("malformed case")
        key = tuple(map(int, values[1:7]))
        if key in rows:
            raise ValueError("duplicate case")
        events, calls = map(int, values[7:9])
        changes = [tuple(map(int, value.split(":"))) for value in values[9:]]
        if events != 12 or calls < len(changes) or changes[0][0] != 2000:
            raise ValueError("missing event inventory")
        total_events += events
        pair, phase, previous, filtering, volume, _ = key
        if pair not in (0, 1) or any(level not in (0, 1) for _, level in changes):
            raise ValueError("invalid digital level")
        if any(a[0] >= b[0] or a[1] == b[1] for a, b in itertools.pairwise(changes)):
            raise ValueError("unordered or redundant transition")
        if any(time > 2240 for time, _ in changes):
            raise ValueError("output beyond flush boundary")
        if volume:
            if changes != [(2000, 1)]:
                raise ValueError("volume-only failed to override output")
        elif not filtering:
            expected = [(2000, 1 - previous)] + [
                (2 * (1012 + i * 16), previous ^ (i & 1)) for i in range(6)
            ]
            if changes != expected:
                raise ValueError("unfiltered tone timing mismatch")
        else:
            half_cycle += sum(time % 2 for time, _ in changes)
            # At this supplied-event offset, each settled pulse spans half
            # a renderer cycle. This does not map event input to raw underflow.
            if phase == 2:
                widths = [
                    b[0] - a[0]
                    for a, b in itertools.pairwise(changes)
                    if a[1] == 1 and a[0] >= 2056
                ]
                if widths != [1] * 5:
                    raise ValueError("missing settled half-cycle pulses")
                short_pulses += len(widths)
        rows[key] = changes
    expected_keys = set(
        itertools.product(
            range(2), range(-4, 5), range(2), range(3), range(2), (1, 7, 120)
        )
    )
    if set(rows) != expected_keys:
        raise ValueError("incomplete case inventory")
    for key, changes in rows.items():
        if changes != rows[(*key[:5], 120)]:
            raise ValueError("output depends on flush partition")
    if not half_cycle or not short_pulses:
        raise ValueError("no active filter timing observed")
    return {
        "cases": len(rows),
        "input_events": total_events,
        "half_cycle_transitions": half_cycle,
        "settled_half_cycle_pulses": short_pulses,
        "rows_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Altirra tree containing src/")
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    source_bytes = (
        args.reference / "src/ATAudio/source/pokeyrenderer.cpp"
    ).read_bytes()
    wrap_bytes = (args.reference / "src/h/at/atcore/wraptime.h").read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_HASH:
        raise ValueError("renderer source hash mismatch")
    if hashlib.sha256(wrap_bytes).hexdigest() != WRAP_HASH:
        raise ValueError("wrapped-time source hash mismatch")
    source = source_bytes.decode().replace("\r\n", "\n")
    wrap = wrap_bytes.decode().replace("\r\n", "\n")
    methods = "\n".join(
        (
            extract(wrap, "struct ATWrapTime {", "\n#endif"),
            extract(
                source,
                "namespace {\n\tconstexpr uint32 kAudioDelay",
                "\nATPokeyRenderer::ATPokeyRenderer()",
            ),
            extract(
                source,
                "void ATPokeyRenderer::AddChannelEvent(",
                "\nvoid ATPokeyRenderer::SetChannelDeferredEvents(",
            ),
            extract(
                source,
                "void ATPokeyRenderer::Flush2(",
                "\nvoid ATPokeyRenderer::UpdateVolume(",
            ),
        )
    )
    harness = Path(__file__).with_name("harness.cpp").read_text()
    if harness.count("// REFERENCE_METHODS") != 1:
        raise ValueError("missing harness insertion boundary")
    args.scratch.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "renderer_sha256": SOURCE_HASH,
        "wraptime_sha256": WRAP_HASH,
        "methods_sha256": hashlib.sha256(methods.encode()).hexdigest(),
        "harness_sha256": hashlib.sha256(harness.encode()).hexdigest(),
    }
    offset = "0x4000 + (i + 2) - (baseTime << 15)"
    if methods.count(offset) != 1:
        raise ValueError("mutation target missing")
    for label, body in (
        ("baseline", methods),
        ("integer-filter", methods.replace(offset, "0 + (i + 2) - (baseTime << 15)")),
    ):
        cpp = args.scratch / f"{label}.cpp"
        binary = args.scratch / label
        cpp.write_text(harness.replace("// REFERENCE_METHODS", body))
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
        if label == "baseline":
            summary[label] = verify(captured)
        else:
            try:
                verify(captured)
            except ValueError as error:
                summary[label] = {"rejected": str(error)}
            else:
                raise ValueError("integer-cycle mutation escaped timing checks")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
