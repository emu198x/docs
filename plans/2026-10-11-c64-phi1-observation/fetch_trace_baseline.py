"""Validate an isolated headless VICE build before using fetch instrumentation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from bank_transient import guest, pixels
from capture import MODELS, digest, layout
from verify_fetch_trace import verify


def compare(actual: bytes, expected: bytes) -> None:
    assert expected and len(actual) == len(expected), "missing/short payload"
    assert actual == expected, "payload differs from retained native evidence"


def reject_mutation(actual: bytes, expected: bytes) -> None:
    changed = bytes([actual[0] ^ 1]) + actual[1:]
    try:
        compare(changed, expected)
    except AssertionError:
        return
    raise AssertionError("changed payload passed")


def execute(
    args: argparse.Namespace,
    model: str,
    stem: str,
    commands: str,
    *,
    arm_in_monitor: bool = True,
) -> str:
    env = os.environ.copy()
    env.pop("EMU198X_VIC_TRACE", None)
    if args.trace:
        env["EMU198X_VIC_TRACE"] = str(args.output / f"{stem}.csv")
        if arm_in_monitor:
            assert commands.count("\ng $") == 1
            commands = commands.replace("\ng $", "\n> $02ff $a5\ng $", 1)
    monitor = args.output / f"{stem}.mon"
    monitor.write_text(commands)
    cmd = [
        str(args.binary.resolve()),
        "-config",
        str(args.output / "empty.cfg"),
        "-default",
        "-console",
        "-sounddev",
        "dummy",
        "-warp",
        "-model",
        model,
        "-gluelogictype",
        "1",
        "-VICIIfilter",
        "0",
        "-directory",
        str(args.data.resolve()),
        "-logfile",
        str(args.output / f"{stem}-vice.log"),
    ]
    for rom in ("kernal", "basic", "chargen"):
        cmd.extend([f"-{rom}", str(args.roms.resolve() / f"{rom}.rom")])
    cmd.extend(
        [
            "-initbreak",
            "ready",
            "-limitcycles",
            "30000000",
            "-moncommands",
            str(monitor),
        ]
    )
    # Headless uses the logger for monitor output. -silent would hide the
    # completion witness; -nativemonitor belongs to the GTK frontend.
    run = subprocess.run(cmd, capture_output=True, timeout=60, check=True, env=env)
    log = (run.stdout + run.stderr).decode(errors="replace")
    (args.output / f"{stem}.log").write_text(log)
    assert log.count("Stop on store d7ff") == 1, "missing/duplicate completion"
    assert "Unexpected token" not in log
    (args.output / f"{stem}-command.json").write_text(json.dumps(cmd, indent=2))
    return log


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--testbench", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    (args.output / "empty.cfg").write_text("")
    evidence = Path(__file__).resolve().parent
    native = json.loads((evidence / "native/comparison.json").read_text())["rows"]
    rows = []
    for model, program_name, cycles in MODELS:
        stem = f"{model}-bank"
        program = args.output / f"{stem}.prg"
        program.write_bytes(guest((1, 2), 0xFF))
        sentinel = args.output / f"{stem}.bin"
        picture = args.output / f"{stem}.png"
        execute(
            args,
            model,
            stem,
            f'delete\nload "{program}" 0\nbreak store $d7ff\ng $0800\nr\n'
            f'bsave "{sentinel}" 0 $6000 $6000\nscreenshot "{picture}" 2\nquit\n',
        )
        assert sentinel.read_bytes() == bytes([0xA5])
        reference = evidence / "transient-native" / f"{model}-1-2-markerff-glue1.png"
        size, actual = pixels(picture)
        expected_size, expected = pixels(reference)
        assert size == expected_size and min(size) > 200
        compare(actual, expected)
        reject_mutation(actual, expected)
        rows.append(
            {
                "model": model,
                "case": "bank",
                "dimensions": size,
                "pixels": len(actual) // 3,
                "different_pixels": 0,
                "program_sha256": digest(program),
                "png_sha256": digest(picture),
                "reference_sha256": digest(reference),
            }
        )
        print(stem, len(actual) // 3, "pixels exact", flush=True)

        original = (args.testbench / f"{program_name}.prg").read_bytes()
        _, _, measured = layout(original, cycles)
        for endpoint in ("io1", "colour"):
            source = next(
                r for r in native if r["model"] == model and r["endpoint"] == endpoint
            )
            assert hashlib.sha256(original).hexdigest() == source["source_sha256"]
            assert original.count(bytes.fromhex("ad ad de")) == 1
            derived = (
                original
                if endpoint == "io1"
                else original.replace(
                    bytes.fromhex("ad ad de"), bytes.fromhex("ad 00 d8")
                )
            )
            stem = f"{model}-{endpoint}"
            program = args.output / f"{stem}.prg"
            program.write_bytes(derived)
            dump = args.output / f"{stem}.bin"
            end = 0x0801 + len(original) - 3
            execute(
                args,
                model,
                stem,
                f'delete\nload "{program}" 0\nbreak store $d7ff\ng $080d\nr\n'
                f'bsave "{dump}" 0 $0801 ${end:04x}\nquit\n',
            )
            raw = dump.read_bytes()
            assert len(raw) == len(original) - 2
            actual = raw[measured : measured + cycles]
            expected = (evidence / "native" / f"{stem}-samples.bin").read_bytes()
            assert len(expected) == cycles
            compare(actual, expected)
            reject_mutation(actual, expected)
            rows.append(
                {
                    "model": model,
                    "case": endpoint,
                    "samples": list(actual),
                    "program_sha256": digest(program),
                    "differences": 0,
                }
            )
            print(stem, len(actual), "samples exact", flush=True)
    assert len(rows) == 15
    assert {(r["model"], r["case"]) for r in rows} == {
        (m, c) for m, _, _ in MODELS for c in ("bank", "io1", "colour")
    }
    traces = {}
    if args.trace:
        for model, _, cycles in MODELS:
            for case in ("bank", "io1", "colour"):
                name = f"{model}-{case}"
                traces[name] = verify(args.output / f"{name}.csv", cycles)
    summary = {
        "binary_sha256": digest(args.binary),
        "rows": rows,
        "mutation_controls_rejected": len(rows),
        "traces": traces,
    }
    (args.output / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
