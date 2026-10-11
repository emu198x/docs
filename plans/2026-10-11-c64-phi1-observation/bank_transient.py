"""Compare visible bank-switch consequences with discrete/custom VICE glue."""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
from pathlib import Path

from capture import MODELS, digest
from PIL import Image

PAIRS = [(0, 1), (1, 2), (1, 3), (2, 3)]
SCENARIOS = [
    (pair, marker)
    for pair in PAIRS
    for marker in ((0, 0x55, 0xAA, 0xFF) if pair == (1, 2) else (0xAA,))
]


def guest(pair: tuple[int, int], marker: int = 0xAA) -> bytes:
    code = bytearray([0x78])

    def absolute(op: int, address: int) -> None:
        code.extend([op, address & 255, address >> 8])

    def store(address: int, value: int) -> None:
        code.extend([0xA9, value])
        absolute(0x8D, address)

    for address, value in [
        (1, 0x37),
        (0xDC0D, 0x7F),
        (0xDD0D, 0x7F),
        (0xD011, 0),
        (0xD015, 0),
        (0xDD02, 3),
        (0xDD00, 3),
        (0xD016, 8),
        (0xD018, 0x18),
        (0xD020, 2),
        (0xD021, 0),
    ]:
        store(address, value)
    absolute(0xAD, 0xDD0D)
    # Identical code-zero screen matrices; bank-specific RAM character zero.
    for bank, pattern in enumerate([0, 0, 0xFF, marker]):
        code.extend([0xA2, 0, 0xA9, 0])
        for page in range(4):
            absolute(0x9D, bank * 0x4000 + 0x0400 + 256 * page)
        code.extend([0xE8, 0xD0, 0xF1])
        for row in range(8):
            store(bank * 0x4000 + 0x2000 + row, pattern)
    code.extend([0xA2, 0, 0xA9, 1])
    for page in range(4):
        absolute(0x9D, 0xD800 + 256 * page)
    code.extend([0xE8, 0xD0, 0xF1])
    store(0xD011, 0x1B)
    store(0x02, 16)
    code.extend([0xA0, 0])  # 16 * 256 iterations, two bank stores each.
    loop = len(code)
    store(0xDD00, 3 - pair[0])
    store(0xDD00, 3 - pair[1])
    code.append(0x88)  # DEY
    code.extend([0xD0, (loop - len(code) - 2) & 255])
    code.extend([0xC6, 2])  # DEC $02
    code.extend([0xD0, (loop - len(code) - 2) & 255])
    store(0x6000, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    assert len(code) < 0x1800
    return bytes([0, 8]) + code


def pixels(path: Path) -> tuple[tuple[int, int], bytes]:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return rgb.size, rgb.tobytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", type=Path, default=Path("/opt/homebrew/bin/x64sc"))
    parser.add_argument("--models", nargs="+", default=[m[0] for m in MODELS])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    (output / "empty.cfg").write_text("")
    captures, comparisons = [], []
    for model, (pair, marker) in itertools.product(args.models, SCENARIOS):
        for glue in (0, 1):
            stem = f"{model}-{pair[0]}-{pair[1]}-marker{marker:02x}-glue{glue}"
            program = output / f"{stem}.prg"
            program.write_bytes(guest(pair, marker))
            monitor, dump = output / f"{stem}.mon", output / f"{stem}.bin"
            screenshot = output / f"{stem}.png"
            monitor.write_text(
                f'delete\nload "{program}" 0\nbreak store $d7ff\ng $0800\nr\n'
                f'bsave "{dump}" 0 $6000 $6000\nscreenshot "{screenshot}" 2\nquit\n'
            )
            cmd = [
                str(args.x64sc),
                "-config",
                str(output / "empty.cfg"),
                "-default",
                "-console",
                "-silent",
                "-sounddev",
                "dummy",
                "-warp",
                "-model",
                model,
                "-gluelogictype",
                str(glue),
                "-VICIIfilter",
                "0",
            ]
            for rom in ["kernal", "basic", "chargen"]:
                cmd += [f"-{rom}", str(args.roms.resolve() / f"{rom}.rom")]
            cmd += [
                "-initbreak",
                "ready",
                "-limitcycles",
                "30000000",
                "-nativemonitor",
                "-moncommands",
                str(monitor),
            ]
            run = subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            log = (run.stdout + run.stderr).decode(errors="replace")
            (output / f"{stem}.log").write_text(log)
            assert "Stop on store d7ff" in log and "Unexpected token" not in log
            assert dump.read_bytes() == bytes([0xA5])
            captures.append(
                {
                    "stem": stem,
                    "program_sha256": digest(program),
                    "image_sha256": digest(screenshot),
                    "command": cmd,
                }
            )
        paths = [
            output / f"{model}-{pair[0]}-{pair[1]}-marker{marker:02x}-glue{g}.png"
            for g in (0, 1)
        ]
        size, discrete = pixels(paths[0])
        other_size, custom = pixels(paths[1])
        assert size == other_size and min(size) > 200
        differences = [
            i // 3
            for i in range(0, len(discrete), 3)
            if discrete[i : i + 3] != custom[i : i + 3]
        ]
        comparisons.append(
            {
                "model": model,
                "pair": pair,
                "marker": marker,
                "size": size,
                "differences": len(differences),
                "pixel_indices": differences,
            }
        )
        print(model, pair, marker, size, len(differences), "pixels differ", flush=True)
    identities = {
        p.name: digest(p)
        for p in [
            args.x64sc,
            *(args.roms / f"{r}.rom" for r in ["kernal", "basic", "chargen"]),
        ]
    }
    (output / "comparison.json").write_text(
        json.dumps(
            {
                "identities": identities,
                "captures": captures,
                "comparisons": comparisons,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
