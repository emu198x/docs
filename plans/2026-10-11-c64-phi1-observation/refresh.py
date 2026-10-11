"""Observe refresh address progression through CPU reads on five VIC-II models."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from capture import MODELS, layout


def derive(original: bytes, bank: int, irq: int) -> bytes:
    data = original
    changes = [
        (bytes.fromhex("a95599003f"), bytes.fromhex("98ea99003f"), 1),
        (bytes.fromhex("a9028d12d0"), bytes([0xA9, irq & 255, 0x8D, 0x12, 0xD0]), 2),
        (
            bytes.fromhex("a94b8d11d0"),
            bytes([0xA9, 0xCB if irq > 255 else 0x4B, 0x8D, 0x11, 0xD0]),
            2,
        ),
    ]
    for opcode, address in [
        (0x99, 0x3F00),
        (0x8D, 0x3FFF),
        (0x99, 0x07F8),
        (0x8D, 0x39FF),
    ]:
        target = address + bank * 0x4000
        changes.append(
            (
                bytes([opcode, address & 255, address >> 8]),
                bytes([opcode, target & 255, target >> 8]),
                1,
            )
        )
    for before, after, count in changes:
        assert data.count(before) == count, before.hex()
        data = data.replace(before, after)
    assert len(data) == len(original)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--testbench", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", type=Path, default=Path("/opt/homebrew/bin/x64sc"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    (output / "empty.cfg").write_text("")
    rows = []
    for model, name, cycles in MODELS:
        lines = 312 if cycles == 63 else 262 if cycles == 64 else 263
        original = (args.testbench / f"{name}.prg").read_bytes()
        _, _, measured = layout(original, cycles)
        for bank in range(4):
            for case, irq in [
                ("ordinary", 2),
                ("rollover", 37),
                ("frame-wrap", lines - 15),
            ]:
                stem = f"{model}-bank{bank}-{case}"
                program = output / f"{stem}.prg"
                program.write_bytes(derive(original, bank, irq))
                dump = output / f"{stem}.bin"
                page = output / f"{stem}-page.bin"
                monitor = output / f"{stem}.mon"
                page_start = bank * 0x4000 + 0x3F00
                end = 0x0801 + len(original) - 3
                monitor.write_text(
                    f'delete\nload "{program}" 0\n> $dd02 $03\n> $dd00 ${3 - bank:02x}\ntrace load $dead\nbreak store $d7ff\ng $080d\nr\nbsave "{dump}" 0 $0801 ${end:04x}\nbsave "{page}" 0 ${page_start:04x} ${page_start + 255:04x}\nquit\n'
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
                raw = dump.read_bytes()
                memory = page.read_bytes()
                assert len(raw) == len(original) - 2 and len(memory) == 256
                samples = raw[measured : measured + cycles]
                trace = re.findall(
                    r"Trace  load dead\)\s+(\d+)/\$[0-9a-f]+,\s+(\d+)/\$[0-9a-f]+\n\.C:[^\n]+ A:([0-9A-F]{2})",
                    log,
                )
                assert len(trace) == cycles
                assert [int(a, 16) for _, _, a in trace] == list(samples)
                refresh = []
                for index, (line_text, cycle_text, _) in enumerate(trace):
                    line, cycle = int(line_text), int(cycle_text)
                    if 11 <= cycle <= 15:
                        low = (255 - 5 * line - (cycle - 11)) & 255
                        refresh.append(
                            {
                                "sample": index,
                                "monitor_line": line,
                                "monitor_cycle": cycle,
                                "address": page_start + low,
                                "actual": samples[index],
                                "expected": memory[low],
                            }
                        )
                assert len(refresh) == 5
                differences = [r for r in refresh if r["actual"] != r["expected"]]
                rows.append(
                    {
                        "model": model,
                        "cycles": cycles,
                        "lines": lines,
                        "bank": bank,
                        "case": case,
                        "irq": irq,
                        "original_sha256": hashlib.sha256(original).hexdigest(),
                        "program_sha256": hashlib.sha256(
                            program.read_bytes()
                        ).hexdigest(),
                        "refresh_page": list(memory),
                        "refresh": refresh,
                        "differences": differences,
                        "trace_samples": len(trace),
                        "command": cmd,
                    }
                )
                print(stem, len(differences), "differences", refresh, flush=True)
    (output / "comparison.json").write_text(json.dumps({"rows": rows}, indent=2) + "\n")
    assert len(rows) == 60 and all(not r["differences"] for r in rows)


if __name__ == "__main__":
    main()
