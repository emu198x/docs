"""Join the verified STIMER counter capture to the original renderer reset path."""

import argparse
import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

from capture import replace_one

HERE = Path(__file__).parent
VERIFY_TIMERS = runpy.run_path(
    str(HERE.parent / "2026-10-11-pokey-stimer-delivery/capture.py")
)["verify"]


def verify(text: str) -> dict[str, object]:
    timer_lines = []
    transitions = 0
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 11 or fields[0] != "CASE":
            raise ValueError("malformed connected reset output")
        channel = int(fields[1])
        timer_lines.append(
            " ".join(field for field in fields if not field.startswith("O"))
        )
        operations = []
        observed = []
        for field in fields[9:]:
            if field.startswith("E"):
                time, _ = map(int, field[1:].split(":"))
                operations.append((time * 2 + 4, 1))
            elif field.startswith("R"):
                operations.append((int(field[1:]) * 2, 0))
            elif field.startswith("O"):
                observed.append(tuple(map(int, field[1:].split(":"))))
        state = 0
        latch = int(channel < 2)
        expected = [(2000, latch)]
        for time, toggle in sorted(operations):
            state = state ^ 1 if toggle else 1
            level = state ^ latch
            if expected[-1][0] == time:
                expected[-1] = (time, level)
                if len(expected) > 1 and expected[-2][1] == level:
                    expected.pop()
            elif expected[-1][1] != level:
                expected.append((time, level))
        if observed != expected:
            raise ValueError(f"connected reset waveform mismatch: {fields[1:6]}")
        transitions += len(observed) - 1
    # Delegate the complete timer inventory and its independent timing formulas;
    # matching output alone must never conceal missing or wrong input events.
    result = VERIFY_TIMERS("\n".join(timer_lines) + ("\n" if timer_lines else ""))
    result["output_transitions"] = transitions
    result["combined_capture_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    for folder, script in (
        ("timer", HERE.parent / "2026-10-11-pokey-stimer-delivery/capture.py"),
        ("renderer", HERE / "capture.py"),
    ):
        subprocess.run(
            [
                sys.executable,
                str(script),
                str(args.reference),
                str(args.scratch / folder),
            ],
            check=True,
        )
    renderer = (args.scratch / "renderer/baseline.cpp").read_text()
    timer = (args.scratch / "timer/baseline.cpp").read_text()
    # The renderer assembly already retains the reference event enum from the
    # prerequisite. Start after that shared definition when attaching the chip.
    start = "// Own bounded scheduler/observers."
    driver_start = "// Own driver. Initial loaded count"
    if (
        renderer.count("// Own supplied-event driver.") != 1
        or timer.count(start) != 1
        or timer.count(driver_start) != 1
    ):
        raise ValueError("ambiguous connected boundary")
    renderer = renderer.split("// Own supplied-event driver.")[0]
    timer_core = timer[timer.index(start) : timer.index(driver_start)]
    timer_core = replace_one(
        timer_core,
        "void ResetTimers() { resets.push_back(output.scheduler); }",
        "void ResetTimers() { resets.push_back(output.scheduler); output.ResetTimers(); }",
    )
    driver = timer[timer.index(driver_start) :]
    driver = replace_one(
        driver,
        "            ATPokeyEmulator p;",
        """            ATPokeyEmulator p;
            auto& r = p.renderer.output;
            r.target = channel;
            r.mRenderState.mAUDC[channel] = 0xa1;
            r.mNonZeroVolumeMask = uint8(1 << channel);
            r.mChannelVolume[channel] = 1;
            r.mChannelVolMixIndex[channel] = 1;
            r.UpdateOutput2(2000);""",
    )
    driver = replace_one(
        driver,
        "            if (writeIndex != writes.size()) unsupported();",
        "            if (writeIndex != writes.size()) unsupported();\n            r.Flush(end + 3);\n            if (!r.mChangeQueue.empty()) unsupported();",
    )
    driver = replace_one(
        driver,
        '            std::puts("");',
        '            for (const auto& [time, level] : r.changes) std::printf(" O%u:%u", time, unsigned(level));\n            std::puts("");',
    )
    source = renderer + timer_core + driver
    summary: dict[str, object] = {
        "assembled_source_sha256": hashlib.sha256(source.encode()).hexdigest()
    }
    for name, content in (
        ("connected", source),
        (
            "disconnected-reset",
            replace_one(
                source,
                "resets.push_back(output.scheduler); output.ResetTimers();",
                "resets.push_back(output.scheduler);",
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
        if name == "connected":
            summary[name] = verify(output)
        else:
            try:
                verify(output)
            except ValueError as error:
                summary[name] = {"rejected": str(error)}
            else:
                raise ValueError("disconnected reset escaped verifier")
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
