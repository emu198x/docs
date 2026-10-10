"""Run the populated MARIA reference fetch matrix with checked Icarus adapters."""

import argparse
import hashlib
import itertools
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run(command: list[str], log: Path, *, negative: bool = False) -> str:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    output = result.stdout + result.stderr
    log.write_text(output)
    if (result.returncode == 0) == negative:
        raise RuntimeError(f"unexpected status {result.returncode}: {log}")
    return output


def expand_array(source: str, pattern: str, name: str, width: int, count: int) -> str:
    def replace(match: re.Match[str]) -> str:
        values = [int(value) for value in re.findall(r"5'd(\d+)", match[1])]
        if len(values) != count:
            raise ValueError(f"unexpected {name} inventory")
        residue = re.sub(r"5'd\d+|[\s,]", "", match[1])
        if residue or any(value >= 1 << width for value in values):
            raise ValueError(f"unexpected {name} constant")
        prefix = f"wire [4:0] {name} [32];\n" if count == 32 else ""
        return prefix + "\n".join(
            f"assign {name}[{index}] = {width}'d{value};"
            for index, value in enumerate(values)
        )

    adapted, matches = re.subn(pattern, replace, source, flags=re.DOTALL)
    if matches != 1:
        raise ValueError(f"expected one {name} aggregate, got {matches}")
    return adapted


def playback_and_traces(reference: Path, output: Path) -> None:
    here = Path(__file__).resolve().parent
    for mode, slow in itertools.product(range(1, 5), range(2)):
        run(
            [
                "vvp",
                str(output / "fetch.vvp"),
                f"+object={mode}",
                "+width=2",
                f"+slow={slow}",
                "+trace_reads",
            ],
            output / f"trace-o{mode}-s{slow}.log",
        )
    binary = output / "playback.vvp"
    run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "playback_tb",
            "-o",
            str(binary),
            str(reference / "maria.sv"),
            str(reference / "video_sync.sv"),
            str(output / "DMA.masked.sv"),
            str(output / "control.sv"),
            str(output / "line_ram.sv"),
            str(here / "playback_tb.sv"),
        ],
        output / "playback-build.log",
    )
    for slow, pal in itertools.product(range(2), range(2)):
        command = ["vvp", str(binary), "+object=1", "+width=2", f"+slow={slow}"]
        if pal:
            command.append("+pal")
        result = run(command, output / f"playback-s{slow}-p{pal}.log")
        if "PLAYBACK_RESULT checked=7680 graphics=352" not in result:
            raise RuntimeError("missing playback inventory")
    negative = run(
        ["vvp", str(binary), "+object=1", "+width=2", "+drop_pixel"],
        output / "negative-playback.log",
        negative=True,
    )
    if "wrong playback" not in negative:
        raise RuntimeError("playback negative failed for an unexpected reason")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="vendored rtl/Maria directory")
    parser.add_argument(
        "output", type=Path, help="local scratch, outside the reference"
    )
    args = parser.parse_args()
    reference, output = args.reference.resolve(), args.output.resolve()
    if output.is_relative_to(reference.parent):
        parser.error("output must be outside the reference tree")
    output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent
    hashes = {
        name: hashlib.sha256((reference / name).read_bytes()).hexdigest()
        for name in ["DMA.sv", "control.sv", "line_ram.sv", "maria.sv", "video_sync.sv"]
    }
    if (
        hashes["DMA.sv"]
        != "d86608b30af23821ef252cdff61c93f8effdd0e25fab18f06111fa831df1c8fc"
    ):
        raise ValueError("unqualified DMA reference revision")
    run(
        [
            sys.executable,
            str(here.parent / "2026-10-10-maria-dli-oracle/prepare_rtl.py"),
            str(reference / "DMA.sv"),
            str(output),
        ],
        output / "prepare.log",
    )
    control = (reference / "control.sv").read_text()
    control = expand_array(
        control,
        r"wire \[4:0\] color_ram_index \[32\] = '\{(.*?)\};",
        "color_ram_index",
        5,
        32,
    )
    if (
        control.count("logic old_phase;") != 1
        or control.count("assign cram_select =") != 1
    ):
        raise ValueError("unexpected old_phase declaration or use")
    control = control.replace("\tlogic old_phase;\n", "")
    control = control.replace(
        "\tassign cram_select =", "\tlogic old_phase;\n\tassign cram_select ="
    )
    (output / "control.sv").write_text(control)
    line_ram = expand_array(
        (reference / "line_ram.sv").read_text(),
        r"assign pb_map_index = '\{(.*?)\};",
        "pb_map_index",
        6,
        8,
    )
    (output / "line_ram.sv").write_text(line_ram)
    # Value inventories and reference hashes make the adapter reproducible.
    # Widening each original five-bit constant to six bits is zero extension.
    manifest = [f"reference {name} {value}" for name, value in hashes.items()]
    for name in ["DMA.masked.sv", "control.sv", "line_ram.sv"]:
        manifest.append(
            f"generated {name} {hashlib.sha256((output / name).read_bytes()).hexdigest()}"
        )
    (output / "hashes.log").write_text("\n".join(manifest) + "\n")
    binary = output / "fetch.vvp"
    run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "fetch_tb",
            "-o",
            str(binary),
            str(reference / "maria.sv"),
            str(reference / "video_sync.sv"),
            str(output / "DMA.masked.sv"),
            str(output / "control.sv"),
            str(output / "line_ram.sv"),
            str(here / "fetch_tb.sv"),
        ],
        output / "build.log",
    )

    matrix = list(
        itertools.product(
            range(1, 5), range(4), [1, 2, 3, 16], range(3), range(2), range(2)
        )
    )

    def check(row: tuple[int, int, int, int, int, int]) -> str:
        mode, width_index, height, flag, slow, pal = row
        width = [1, 2, 8, 31 if mode == 1 else 32][width_index]
        name = f"o{mode}-w{width}-h{height}-f{flag}-s{slow}-p{pal}"
        command = [
            "vvp",
            str(binary),
            f"+object={mode}",
            f"+width={width}",
            f"+height={height}",
            f"+flag={flag}",
            f"+slow={slow}",
        ]
        if pal:
            command.append("+pal")
        result = run(command, output / f"{name}.log")
        if result.count("FETCH_RESULT ") != 1:
            raise RuntimeError(f"missing fetch result: {name}")
        return name + " PASS"

    # Validate failure controls before launching the expensive matrix. A failed
    # compile raises above, so an older binary can never supply a passing result.
    for option, expected in [
        ("+old_bus", "wrong descriptor low byte"),
        ("+unknown_clocks", "unknown clock selection"),
        ("+suppress_nmi", "wrong inventory"),
    ]:
        negative = run(
            ["vvp", str(binary), "+object=1", "+width=2", "+flag=2", option],
            output / f"negative-{option[1:]}.log",
            negative=True,
        )
        if expected not in negative:
            raise RuntimeError(f"negative failed for an unexpected reason: {option}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, matrix))
    playback_and_traces(reference, output)
    for name, digest in hashes.items():
        if hashlib.sha256((reference / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"reference changed: {name}")
    if len(rows) != 768:
        raise RuntimeError("incomplete matrix")
    summary = (
        "\n".join(rows)
        + "\nCASES=768 PASSED=768 FAILED=0 PLAYBACK=4/4 NEGATIVES=REJECTED\n"
    )
    (output / "summary.log").write_text(summary)
    print(summary, end="")


if __name__ == "__main__":
    main()
