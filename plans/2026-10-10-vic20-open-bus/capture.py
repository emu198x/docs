import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Capture the complete VIC-20 timing measurement in native VICE"
)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument(
    "--testbench", type=Path, default=Path.home() / ".emu198x/test-suites/vic20"
)
parser.add_argument(
    "--roms", type=Path, default=Path.home() / ".emu198x/roms/commodore-vic-20"
)
parser.add_argument("--xvic", default="/opt/homebrew/bin/xvic")
args = parser.parse_args()
OUT = args.output.resolve()
FIXTURES = args.testbench.resolve() / "vice-testprogs/split-tests/timing"
ROMS = args.roms.resolve()
OUT.mkdir(exist_ok=False)
for model, program, kernal in [
    ("pal", "timing.prg", "kernal.rom"),
    ("ntsc", "timing_ntsc.prg", "kernal-ntsc.rom"),
]:
    work = OUT / model
    work.mkdir()
    prg = FIXTURES / program
    data = prg.read_bytes()
    end = int.from_bytes(data[:2], "little") + len(data) - 2
    save = work / "save.mon"
    save.write_text(f'r\nbsave "{work / "measurement.bin"}" 0 $17c0 $1bff\nquit\n')
    inject = work / "inject.mon"
    inject.write_text(
        f'del 1\nload "{prg}" 0\n'
        f"> 002d {end & 255:02x} {end >> 8:02x} {end & 255:02x} {end >> 8:02x} {end & 255:02x} {end >> 8:02x}\n"
        "> 0277 52 55 4e 0d\n> 00c6 04\n"
        "break store $17e8 if A == $01\n"
        f'command 1 "playback \\"{save}\\""\nx\n'
    )
    start = work / "start.mon"
    start.write_text(f'break $e5ea\ncommand 1 "playback \\"{inject}\\""\nx\n')
    config = work / "vicerc"
    config.write_text("")
    command = [
        args.xvic,
        "-config",
        str(config),
        "-default",
        "-console",
        "-silent",
        "-sounddev",
        "dummy",
        "-warp",
        "+autostart-delay-random",
        "-model",
        f"vic20{model}",
        "-memory",
        "none",
        "-kernal",
        str(ROMS / kernal),
        "-basic",
        str(ROMS / "basic.rom"),
        "-chargen",
        str(ROMS / "char.rom"),
        "-limitcycles",
        "40000000",
        "-nativemonitor",
        "-moncommands",
        str(start),
    ]
    (work / "command.json").write_text(json.dumps(command, indent=2))
    result = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, timeout=100, check=False
    )
    (work / "native.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, f"{model}: native exit {result.returncode}"
    assert b"Stop on store 17e8" in result.stdout + result.stderr, (
        f"{model}: completion checkpoint missing"
    )
    binary = work / "measurement.bin"
    assert binary.is_file(), f"{model}: no capture; inspect native.log"
    measured = binary.read_bytes()
    assert len(measured) == 1088
    assert measured[40] == 1
    print(model, result.returncode, hashlib.sha256(measured).hexdigest(), flush=True)
