"""Build and execute the observation ROM, including deliberately broken controls."""

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
from pathlib import Path


def run(args: list[str], **kwargs: object) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{args!r}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(text: str) -> list[dict[str, int]]:
    parsed = [
        {k: int(v) for k, v in row.items()} for row in csv.DictReader(io.StringIO(text))
    ]
    if [(r["mode"], r["input"]) for r in parsed] != [
        (mode, value) for mode in range(4) for value in range(8)
    ]:
        raise ValueError("CSV must contain every mode/value pair exactly once")
    for row in parsed:
        if (
            row["retained_page"] != row["repeat"]
            or (row["retained_page"] ^ row["complement"]) != 255
        ):
            raise ValueError("CSV read controls failed")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="clean Emu198x source checkout")
    parser.add_argument("mesen", type=Path, help="Mesen2 source snapshot")
    parser.add_argument("core", type=Path, help="prebuilt MesenCore.dylib")
    parser.add_argument("output", type=Path, help="separate generated-output directory")
    args = parser.parse_args()
    source, mesen, core, output = (
        path.resolve() for path in (args.source, args.mesen, args.core, args.output)
    )
    here = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=True)
    for path in (output, output / "rebuild"):
        run(["python3", str(here / "build.py"), str(path)])
    rom = output / "mmc5-chr-observe.nes"
    if rom.read_bytes() != (output / "rebuild/mmc5-chr-observe.nes").read_bytes():
        raise ValueError("Cartridge build is not deterministic")

    target = output / "target"
    env = dict(os.environ, CARGO_TARGET_DIR=str(target))
    run(
        [
            "cargo",
            "build",
            "-p",
            "machine-nintendo-nes",
            "-p",
            "format-nintendo-nes-ines",
        ],
        cwd=source,
        env=env,
    )
    deps = target / "debug/deps"
    command = [
        "rustc",
        "--edition=2024",
        "-D",
        "warnings",
        str(here / "run.rs"),
        "-L",
        f"dependency={deps}",
        "-o",
        str(output / "run"),
    ]
    for name in ("machine_nintendo_nes", "format_nintendo_nes_ines"):
        libraries = list(deps.glob(f"lib{name}-*.rlib"))
        if len(libraries) != 1:
            raise ValueError(f"Ambiguous build artifacts: {libraries}")
        command += ["--extern", f"{name}={libraries[0]}"]
    run(command, cwd=source)
    emu_command = [str(output / "run"), str(rom), str(output / "emu198x")]
    print(run(emu_command), end="")
    observed = rows((output / "emu198x/observations.csv").read_text())

    local_core = output / "MesenCore.dylib"
    shutil.copy2(core, local_core)
    run(
        [
            "clang++",
            "-std=c++20",
            "-O1",
            "-I",
            str(mesen),
            "-I",
            str(mesen / "Core"),
            "-I",
            str(mesen / "Utilities"),
            str(here / "reference_run.cpp"),
            str(local_core),
            "-o",
            str(output / "reference_run"),
        ]
    )
    home = output / "mesen-home"
    home.mkdir(exist_ok=True)
    reference_command = [str(output / "reference_run"), str(home), str(rom)]
    reference = run(reference_command, cwd=output)
    if reference != run(reference_command, cwd=output):
        raise ValueError("Mesen observations are not deterministic")
    expected = rows(reference)
    (output / "mesen.csv").write_text(reference)

    broken = bytearray(rom.read_bytes())
    broken[16 + 32768 + 1] = 0  # page 0's complement must be $FF
    bad = output / "bad-complement.nes"
    bad.write_bytes(broken)
    negative = {}
    for name, command, error in [
        (
            "emu198x",
            [str(output / "run"), str(bad), str(output / "negative")],
            "guest read controls failed",
        ),
        (
            "mesen",
            [str(output / "reference_run"), str(home), str(bad)],
            "reference completion, static-page or read control failed",
        ),
    ]:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=output)
        if result.returncode != 1 or error not in result.stderr:
            raise ValueError(f"{name} failed to detect deliberately corrupted CHR data")
        negative[name] = {"exit_code": result.returncode, "stderr": result.stderr}

    summary = {
        "source_head": run(["git", "rev-parse", "HEAD"], cwd=source).strip(),
        "mesen_source_head": run(["git", "rev-parse", "HEAD"], cwd=mesen).strip(),
        "mesen_core_sha256": digest(local_core),
        "mesen_core_provenance": "Prebuilt local core; not rebuilt for this probe.",
        "rom_sha256": digest(rom),
        "rows": len(observed),
        "static_mismatches_by_mode": [
            sum(
                row["same_mode_page"] != ref["same_mode_page"]
                for row, ref in zip(observed, expected, strict=True)
                if row["mode"] == mode
            )
            for mode in range(4)
        ],
        "mesen_repeated_run_identical": True,
        "cartridge_rebuild_identical": True,
        "negative_controls": negative,
        "scope": "Host and full-emulator observations; unresolved low bits need real hardware.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
