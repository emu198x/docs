"""Capture greydot's two NTSC launch phases in native VICE, issue 1629."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_stores(text: str) -> list[tuple[int, int, int]]:
    pattern = (
        r"Trace store d021\)\s+(\d+)/\$[0-9a-f]+,\s+(\d+)/[^\n]+\n"
        r"[^\n]+ A:([0-9a-fA-F]+)"
    )
    rows = [(int(line), int(cycle), int(value, 16))
            for line, cycle, value in re.findall(pattern, text)]
    assert len(rows) == 1001, len(rows)
    frames: list[list[tuple[int, int, int]]] = [[]]
    for row in rows:
        if frames[-1] and row[0] < frames[-1][-1][0]:
            frames.append([])
        frames[-1].append(row)
    complete = [frame for frame in frames
                if len(frame) == 408 and frame[0][0] == 110 and frame[-1][0] == 231]
    assert complete and all(frame == complete[0] for frame in complete)
    return complete[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--testbench", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", default="x64sc")
    parser.add_argument("--check-fixtures", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    executable = shutil.which(args.x64sc)
    assert executable is not None
    prg = (args.testbench / "greydot/greydot.prg").resolve(strict=True)
    palette_source = args.source / "crates/mos-vic-ii/src/palette.rs"
    colours = [int(value.replace("_", ""), 16) & 0xFFFFFF
               for value in re.findall(r"0x(FF[0-9A-F_]+)", palette_source.read_text())]
    assert len(colours) == 16
    palette = out / "indexed.vpl"
    palette.write_text("# Digital C64 colour-index comparison\n" + "\n".join(
        f"{value >> 16:02X} {(value >> 8) & 255:02X} {value & 255:02X}"
        for value in colours) + "\n")
    config = out / "empty.cfg"
    config.write_text("")
    roms = {name: (args.roms / f"{name}.rom").resolve(strict=True)
            for name in ["kernal", "basic", "chargen"]}
    records = []
    phases: dict[int, list[tuple[int, int, int]]] = {}
    outputs: dict[str, str] = {}
    for model, chip in [("ntsc", "6567r8"), ("c64cntsc", "8562")]:
        seen = set()
        for delay in range(6):
            name = f"{chip}-delay{delay}"
            monitor, screenshot = out / f"{name}.mon", out / f"{name}.png"
            monitor.write_text(
                f'radix d\ndelete\nload "{prg}" 0\nbreak exec $0848\ng $0815\n'
                'delete\n> $0b00 ' + 'ea ' * delay + '4c 48 08\n'
                'break store $d7ff\ng $0b00\ndelete\ntrace store $d021\n'
                'trace exec $0850 $08d0\ntrace load $d012\nbreak store $d021\n'
                f'ignore 4 1000\ng\nscreenshot "{screenshot}" 2\nquit\n'
            )
            command = [executable, "-config", str(config), "-default", "-console",
                       "-silent", "-sounddev", "dummy", "-warp", "-model", model,
                       "-VICIIfilter", "0", "-VICIIextpal", "-VICIIpalette", str(palette)]
            for setting in ["saturation", "contrast", "brightness", "gamma", "tint"]:
                command += [f"-VICII{setting}", "1000"]
            for kind, path in roms.items():
                command += [f"-{kind}", str(path)]
            command += ["-initbreak", "ready", "-limitcycles", "12000000",
                        "-nativemonitor", "-moncommands", str(monitor)]
            process = subprocess.run(command, capture_output=True, check=True, timeout=30)
            text = (process.stdout + process.stderr).decode()
            (out / f"{name}.log").write_text(text)
            assert "Unexpected token" not in text and "Stop on store d021" in text
            stores = frame_stores(text)
            cycle = stores[0][1]
            assert stores[0] in [(110, 15, 0), (110, 16, 0)]
            assert cycle not in phases or stores == phases[cycle]
            phases[cycle] = stores
            for filename, data in [
                (f"cycle{cycle}-stores.bin", b"".join(
                    line.to_bytes(2, "little") + bytes([at, value])
                    for line, at, value in stores)),
                (f"{chip}-cycle{cycle}.png", screenshot.read_bytes()),
            ]:
                sha = hashlib.sha256(data).hexdigest()
                assert filename not in outputs or outputs[filename] == sha
                outputs[filename] = sha
                (out / filename).write_bytes(data)
                if args.check_fixtures:
                    assert (args.check_fixtures / filename).read_bytes() == data, filename
            seen.add(cycle)
            records.append({"model": model, "nop_count": delay, "cycle": cycle,
                            "command": command, "log_sha256": digest(out / f"{name}.log")})
            print(f"{chip}, {delay} NOPs: first store {cycle}, 408 stable stores", flush=True)
        assert seen == {15, 16}
    (out / "identity.json").write_text(json.dumps({
        "generator_sha256": digest(Path(__file__)), "x64sc_sha256": digest(Path(executable)),
        "program_sha256": digest(prg), "rom_sha256": {k: digest(p) for k, p in roms.items()},
        "output_sha256": outputs, "runs": records,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
