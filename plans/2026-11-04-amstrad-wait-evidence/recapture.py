"""Capture every unchanged Spectrum oracle using bounded native processes."""

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def hashes(output: str) -> tuple[str, str]:
    frame = re.search(r'boot\.frame_hash\s*=\s*"(xxh64:[0-9a-f]{16})"', output)
    audio = re.search(r'audio\.hash\s*=\s*"(xxh64:[0-9a-f]{16})"', output)
    if not frame or not audio:
        raise ValueError("capture omitted a complete frame/audio hash")
    return frame.group(1), audio.group(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("crates/emu198x-catalogue/manifest/spectrum.toml"),
    )
    args = parser.parse_args()
    if args.self_test:
        assert hashes(
            'boot.frame_hash = "xxh64:0123456789abcdef"\n'
            'audio.hash = "xxh64:fedcba9876543210"'
        ) == ("xxh64:0123456789abcdef", "xxh64:fedcba9876543210")
        for malformed in [
            "",
            'boot.frame_hash = "xxh64:0123456789abcdef"',
            'audio.hash = "xxh64:fedcba9876543210"',
        ]:
            try:
                hashes(malformed)
            except ValueError:
                pass
            else:
                raise AssertionError("incomplete capture accepted")
        print(
            "Complete capture accepted; empty/frame-only/audio-only captures rejected."
        )
        return
    if args.binary is None or args.output is None:
        parser.error("--binary and --output are required")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest_bytes = args.manifest.read_bytes()
    manifest = tomllib.loads(manifest_bytes.decode())
    entries = manifest["entry"]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)) == 103, "complete known manifest required"
    media_root = Path(
        os.environ.get(
            "EMU198X_CATALOGUE_MEDIA_ROOT", "/Volumes/Data/Library/ROMs/TOSEC"
        )
    )
    firmware_root = Path(
        os.environ.get(
            "EMU198X_CATALOGUE_FIRMWARE_ROOT", str(Path.home() / ".emu198x/roms")
        )
    )
    variants = {e["variant"] for e in entries}
    paths = {media_root / e["media"]["path"] for e in entries}
    paths.update(
        firmware_root / f["path"]
        for fw in manifest["system"]["firmware"]
        if fw["variant"] in variants
        for f in fw["files"]
    )
    inputs = {str(p): digest(p) for p in sorted(paths)}
    identity = {
        "binary_sha256": digest(args.binary),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "root_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "root_diff": subprocess.check_output(["git", "diff"], text=True),
        "input_sha256": inputs,
        "expected_entries": ids,
        "concurrency": 3,
        "timeout_seconds": 300,
        "temporary_path_overrides": False,
    }
    (args.output / "identity.json").write_text(json.dumps(identity, indent=2))
    start = time.monotonic()
    results = {}

    def capture(entry: dict[str, Any]) -> dict[str, Any]:
        directory = args.output / entry["id"]
        directory.mkdir()
        began = time.monotonic()
        record = {
            "id": entry["id"],
            "variant": entry["variant"],
            "expected_frame": entry["boot"]["frame_hash"],
            "expected_audio": entry["audio"]["hash"],
        }
        try:
            with (directory / "capture.log").open("w") as log:
                subprocess.run(
                    [
                        str(args.binary),
                        "capture",
                        "--entry",
                        entry["id"],
                        "--manifest",
                        str(args.manifest),
                        "--save-screenshot",
                        str(directory / "screen.png"),
                        "--save-audio",
                        str(directory / "audio.wav"),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=300,
                    check=True,
                )
            frame, audio = hashes((directory / "capture.log").read_text())
            assert (directory / "screen.png").stat().st_size > 100
            assert (directory / "audio.wav").stat().st_size > 44
            record.update(
                status="captured",
                frame_hash=frame,
                audio_hash=audio,
                frame_matches=frame == record["expected_frame"],
                audio_matches=audio == record["expected_audio"],
            )
        except (
            subprocess.SubprocessError,
            ValueError,
            OSError,
            AssertionError,
        ) as error:
            record.update(status="error", error=str(error))
        record["seconds"] = round(time.monotonic() - began, 2)
        (directory / "result.json").write_text(json.dumps(record, indent=2))
        return record

    def summary() -> dict[str, Any]:
        ordered = [results[id] for id in ids if id in results]
        report = {
            "elapsed_seconds": round(time.monotonic() - start, 2),
            "completed": len(ordered),
            "expected": len(ids),
            "results": ordered,
            "errors": [r for r in ordered if r["status"] != "captured"],
            "changed": [
                r
                for r in ordered
                if r["status"] == "captured"
                and not (r["frame_matches"] and r["audio_matches"])
            ],
        }
        temporary = args.output / "summary.tmp"
        temporary.write_text(json.dumps(report, indent=2))
        temporary.replace(args.output / "summary.json")
        return report

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(capture, e) for e in entries]
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            assert record["id"] not in results
            results[record["id"]] = record
            report = summary()
            print(
                f"{report['completed']}/103 {record['id']}: {record['status']} "
                f"({len(report['changed'])} changed, {len(report['errors'])} errors)",
                flush=True,
            )
    report = summary()
    assert set(results) == set(ids), "missing capture coverage"
    assert args.manifest.read_bytes() == manifest_bytes, (
        "manifest changed during capture"
    )
    assert digest(args.binary) == identity["binary_sha256"], (
        "binary changed during capture"
    )
    assert all(digest(Path(p)) == sha for p, sha in inputs.items()), (
        "input changed during capture"
    )
    assert not report["errors"], "capture errors are not hash disagreements"
    print(
        json.dumps(
            {
                "complete": report["completed"],
                "changed": len(report["changed"]),
                "seconds": report["elapsed_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
