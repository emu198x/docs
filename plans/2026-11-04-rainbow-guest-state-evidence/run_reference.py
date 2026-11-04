"""Run a bounded read-only MAME probe on the preserved geometry control."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--backend", choices=["none", "soft"], default="none")
    args = parser.parse_args()
    assert args.script.is_file()
    reference = json.loads((ROOT / "reference-input-identity.json").read_text())
    archive = Path(
        "/Volumes/Data/Library/ROMs/TOSEC/Sinclair/ZX Spectrum/Games/[DSK]/Rainbow Islands - The Story of Bubble Bobble 2 (1990)(Ocean)(+3).zip"
    )
    original_zip = archive.read_bytes()
    assert sha(original_zip) == reference["media_archive_sha256"]
    with zipfile.ZipFile(archive) as z:
        original = z.read(reference["member"])
    assert sha(original) == reference["disk_sha256"]
    assert original.startswith(b"EXTENDED CPC DSK File")
    assert original[48:50] == bytes([45, 1])
    assert original[52 + 39 : 52 + 45] == bytes(6)
    assert 256 + sum(size * 256 for size in original[52 : 52 + 45]) == len(original)
    derived = original[:48] + bytes([42]) + original[49:]
    assert [
        i for i, (a, b) in enumerate(zip(original, derived, strict=True)) if a != b
    ] == [48]
    binary = Path("/opt/homebrew/bin/mame")
    assert sha(binary.read_bytes()) == reference["binary_sha256"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    script = output / "probe.lua"
    script.write_bytes(args.script.read_bytes())
    romroot = Path.home() / ".emu198x/roms/amstrad-zx-spectrum-plus3"
    with tempfile.TemporaryDirectory(prefix="native-run-", dir=output) as temporary:
        temp = Path(temporary)
        roms = temp / "specpls3"
        roms.mkdir()
        for name, indices in [("40092.ic7", [0, 1]), ("40093.ic8", [2, 3])]:
            data = b"".join((romroot / f"plus3-{i}.rom").read_bytes() for i in indices)
            assert hashlib.sha1(data).hexdigest() == reference["firmware_sha1"][name]
            (roms / name).write_bytes(data)
        disk = temp / "rainbow-declared-42-diagnostic-only.dsk"
        disk.write_bytes(derived)
        argv = [
            str(binary),
            "specpls3",
            "-bios",
            "en",
            "-rompath",
            str(temp),
            "-flop1",
            str(disk),
            "-video",
            args.backend,
            "-sound",
            "none",
            "-nothrottle",
            "-skip_gameinfo",
            "-noreadconfig",
            "-nowriteconfig",
            "-autoboot_delay",
            "0",
            "-autoboot_script",
            str(script),
            "-seconds_to_run",
            "140",
        ]
        if args.backend == "soft":
            argv.append("-window")
        record = {
            "scope": "Read-only guest-state observer; derived geometry diagnostic",
            "archive_sha256": sha(original_zip),
            "original_disk_sha256": sha(original),
            "derived_disk_sha256": sha(derived),
            "track_payload_sha256": sha(original[256:]),
            "changed_offsets": [48],
            "mame_sha256": reference["binary_sha256"],
            "firmware_sha1": reference["firmware_sha1"],
            "script_sha256": sha(script.read_bytes()),
            "argv": argv,
            "timeout_seconds": 90,
        }
        identity = output / "identity.json"
        identity.write_text(json.dumps(record, indent=2) + "\n")
        start = time.monotonic()
        try:
            with (output / "run.log").open("w") as log:
                run = subprocess.run(
                    argv,
                    check=False,
                    cwd=temp,
                    env=os.environ
                    | {
                        "PROBE_OUTPUT": str(output),
                        "SDL_VIDEODRIVER": "dummy",
                        "SDL_AUDIODRIVER": "dummy",
                    },
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=90,
                )
            record["exit_code"] = run.returncode
            assert run.returncode == 0
            assert "PROBE_COMPLETE" in (output / "run.log").read_text(), (
                "probe did not complete"
            )
        finally:
            record["seconds"] = round(time.monotonic() - start, 3)
            record["source_unchanged"] = archive.read_bytes() == original_zip
            record["diagnostic_input_unchanged"] = disk.read_bytes() == derived
            identity.write_text(json.dumps(record, indent=2) + "\n")
            assert record["source_unchanged"] and record["diagnostic_input_unchanged"]
    assert not temp.exists()
    print(
        json.dumps(
            {
                "output": str(output),
                "seconds": record["seconds"],
                "exit_code": record["exit_code"],
            }
        )
    )


if __name__ == "__main__":
    main()
