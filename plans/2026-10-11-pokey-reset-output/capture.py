"""Execute original renderer reset queue and output changes around timer events."""

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

RENDER_HASH = "d79effe1aa9967e50bb189ebec6fd1cb850e29e63d78ae878695409da9b29aa6"


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
    transitions = 0
    states = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 11 or fields[0] != "CASE":
            raise ValueError("malformed reset-output capture")
        key = tuple(map(int, fields[1:7]))
        if key in keys:
            raise ValueError("duplicate reset-output case")
        keys.add(key)
        channel, filt, previous, volume, offset, _partition = key
        latch = int(channel < 2 and filt != 1)
        events = int(offset != 99)
        event_time = 2 * (1016 + offset + 2)
        final = 1 if not events or event_time < 2032 else 0
        if list(map(int, fields[7:10])) != [events, final, latch]:
            raise ValueError(f"reset hidden-state mismatch: {key}")
        # Independent digital invariant: reset presets the waveform latch;
        # a subsequently delivered pure-tone event toggles that retained latch.
        operations = [(2032, 0)]
        if events:
            operations.append((event_time, 1))
        operations.sort()
        output = [(2000, 1 if volume else previous ^ latch)]
        state = previous
        for time, operation in operations:
            state = state ^ 1 if operation else 1
            level = 1 if volume else state ^ latch
            if output[-1][0] == time:
                output[-1] = (time, level)
                if len(output) > 1 and output[-2][1] == level:
                    output.pop()
            elif output[-1][1] != level:
                output.append((time, level))
        observed = [tuple(map(int, item.split(":"))) for item in fields[10:]]
        if observed != output:
            raise ValueError(
                f"reset output timing mismatch: {key}: {observed} != {output}"
            )
        transitions += len(observed) - 1
        state_key = key[:-1]
        record = (tuple(observed), final, latch)
        if state_key in states and states[state_key] != record:
            raise ValueError("flush partition changes output")
        states[state_key] = record
    expected = {
        (channel, filt, previous, volume, offset, partition)
        for channel, filt, previous, volume, offset, partition in itertools.product(
            range(4), range(3), range(2), range(2), (*range(-4, 5), 99), (1, 7, 64)
        )
        if channel < 2 or filt == 0
    }
    if keys != expected:
        raise ValueError("incomplete reset-output inventory")
    return {
        "cases": len(keys),
        "output_transitions": transitions,
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
    raw = (args.reference / "src/ATAudio/source/pokeyrenderer.cpp").read_bytes()
    if hashlib.sha256(raw).hexdigest() != RENDER_HASH:
        raise ValueError("renderer source hash mismatch")
    renderer = raw.decode().replace("\r\n", "\n")
    methods = "\n".join(
        (
            extract(
                renderer,
                "void ATPokeyRenderer::ResetTimers()",
                "\nvoid ATPokeyRenderer::SetAUDCx(",
            ),
            extract(
                renderer,
                "void ATPokeyRenderer::QueueChangeEvent(",
                "\nvoid ATPokeyRenderer::FlushDeferredEvents(",
            ),
            extract(
                renderer,
                "void ATPokeyRenderer::Flush(const uint32 t)",
                "\nvoid ATPokeyRenderer::Flush2(",
            ),
            extract(
                renderer,
                "void ATPokeyRenderer::UpdateOutput(uint32 t)",
                "\nvoid ATPokeyRenderer::UpdateOutput2(uint32 t2)",
            ),
        )
    )
    base = (args.scratch / "borrow/baseline.cpp").read_text()
    if base.count("// Own bounded scheduler/observers.") != 1:
        raise ValueError("ambiguous renderer boundary")
    base = base.split("// Own bounded scheduler/observers.")[0]
    declarations = """
    enum class ChangeType : uint8 { Audc0, Audc1, Audc2, Audc3, Audctl, Init, ResetOutputs, Flush };
    struct ChangeEvent { uint32 mTime; ChangeType mType; uint8 mValue = 0; };
    std::deque<ChangeEvent> mChangeQueue;
    void ResetTimers();
    void QueueChangeEvent(ChangeType, uint8);
    void ProcessChangeEvents(uint32);
    void Flush(uint32);
    void UpdateOutput(uint32);
    void UpdateVolume(int) { unsupported(); }
"""
    base = "#include <algorithm>\n#include <deque>\n" + base
    base = replace_one(
        base, "struct ATPokeyRenderer {", "struct ATPokeyRenderer {" + declarations
    )
    base = replace_one(
        base,
        "    } mPolyState;",
        "        uint32 mInitMask = 0, mLastPoly4Time = 0, mLastPoly5Time = 0, mLastPoly9Time = 0, mLastPoly17Time = 0;\n    } mPolyState;",
    )
    driver = (here / "driver.cpp").read_text()
    source = base + methods + "\n" + driver
    summary: dict[str, object] = {
        "renderer_sha256": RENDER_HASH,
        "reset_methods_sha256": hashlib.sha256(methods.encode()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.encode()).hexdigest(),
    }
    for name, content in (
        ("baseline", source),
        (
            "no-reset",
            replace_one(
                source,
                "QueueChangeEvent(ChangeType::ResetOutputs, 0);",
                "QueueChangeEvent(ChangeType::Flush, 0);",
            ),
        ),
        (
            "wrong-preset",
            replace_one(source, "mNoiseFlipFlops = 0xF;", "mNoiseFlipFlops = 0;"),
        ),
        (
            "late-reset",
            replace_one(
                source,
                "const uint32 t = ATSCHEDULER_GETTIME(mpScheduler);\n\tmChangeQueue",
                "const uint32 t = ATSCHEDULER_GETTIME(mpScheduler) + 1;\n\tmChangeQueue",
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
