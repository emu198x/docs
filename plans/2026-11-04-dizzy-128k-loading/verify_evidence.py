"""Check the retained, independently captured Dizzy loading evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TITLE_SHA256 = "e452aefb327773df0365da1184e5b4a05aefe04722145dfd320f54e91db28f1b"


def verify(directory: Path) -> None:
    screens = [
        (directory / name).read_bytes()
        for name in (
            "48k-title.scr",
            "128k-48basic-title.scr",
            "fuse128-48basic-raw.scr",
        )
    ]
    if any(len(screen) != 6912 for screen in screens):
        raise ValueError("every title capture must contain all 6912 screen bytes")
    if not screens[0] == screens[1] == screens[2]:
        raise ValueError("48K, 128K/48 BASIC and Fuse title screens disagree")
    if hashlib.sha256(screens[0]).hexdigest() != TITLE_SHA256:
        raise ValueError("captures do not show the qualified Dizzy title screen")
    failed = (directory / "fuse128-menu-raw.scr").read_bytes()
    if len(failed) != 6912 or failed == screens[0]:
        raise ValueError(
            "the Tape Loader negative control is missing or reached the title"
        )

    report = json.loads((directory / "128k.report.json").read_text())
    cpus = [o["registers"] for o in report["observations"] if o["kind"] == "query_cpu"]
    progress = [
        o["result"]["value"]
        for o in report["observations"]
        if o["kind"] == "query" and o["result"]["path"] == "tape.progress"
    ]
    if len(cpus) != 3 or len(progress) != 3 or progress != [1.0] * 3:
        raise ValueError(
            "the 16000/20000/40000-frame failed-load observations are incomplete"
        )
    if any(not 0x0556 <= int(cpu["pc"][1:], 16) <= 0x0605 for cpu in cpus):
        raise ValueError("the failed run did not stay in the ROM tape-reading routines")
    trace = json.loads((directory / "trace.report.json").read_text())
    reads = [o["bytes"] for o in trace["observations"] if o["kind"] == "memory_read"]
    reference = bytes.fromhex((directory / "fuse128-menu-raw-loader.hex").read_text())
    if bytes(reads[-1][:60]) != reference:
        raise ValueError("Emu198x and Fuse do not have the same damaged loader")
    if reference[:18] != bytes(18) or reference[18] != 0x55:
        raise ValueError("the recorded loader self-overwrite is absent")
    watches = [o for o in trace["observations"] if o["kind"] == "watch_memory_log"]
    if len(watches) != 1 or not any(
        entry["pc"] == 0x5B13 and entry["addr"] == 0x5B00
        for entry in watches[0]["entries"]
    ):
        raise ValueError("the guest's write over its own loader was not captured")
    print("PASS: three complete title screens agree; both negative controls agree")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", type=Path, default=Path(__file__).parent
    )
    args = parser.parse_args()
    try:
        verify(args.directory)
    except (OSError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
