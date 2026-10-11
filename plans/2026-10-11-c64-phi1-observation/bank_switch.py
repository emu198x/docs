"""Qualify settled VIC bank routing through an original CPU guest."""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import re
import subprocess
from pathlib import Path

from capture import MODELS, digest

PATTERNS = (0x16, 0x26, 0x46, 0x86)
ENDPOINTS = {"io1": 0xDEAD, "io2": 0xDFAD, "colour": 0xD800}
CONTROLS = {"pra": 0xDD00, "ddra": 0xDD02}
CASES = list(itertools.product(range(4), range(4), range(8)))


def guest(control: str, endpoint: str) -> bytes:
    code = bytearray([0x78])  # SEI; IRQs cannot rewrite the bank during capture.

    def absolute(opcode: int, address: int) -> None:
        code.extend([opcode, address & 255, address >> 8])

    def store(address: int, value: int) -> None:
        code.extend([0xA9, value])
        absolute(0x8D, address)

    for address, value in [
        (1, 0x37),
        (0xDC0D, 0x7F),
        (0xDD0D, 0x7F),
        (0xD011, 0),
        (0xD015, 0),
        (0xD018, 0x14),
        (0xD800, 0x0A),
    ]:
        store(address, value)
    absolute(0xAD, 0xDD0D)  # Acknowledge any pending CIA2 NMI.
    for bank, value in enumerate(PATTERNS):
        # Idle graphics and refresh use 3Fxx, disabled sprites use 07F8..FF.
        code.extend([0xA2, 0, 0xA9, value])
        absolute(0x9D, bank * 0x4000 + 0x3F00)
        absolute(0x9D, bank * 0x4000 + 0x0700)
        code.extend([0xE8, 0xD0, 0xF7])
    store(0xDD02 if control == "pra" else 0xDD00, 3 if control == "pra" else 0)
    for index, (old, new, nops) in enumerate(CASES):
        store(CONTROLS[control], 3 - old if control == "pra" else old)
        code.extend([0xEA] * 10)
        store(CONTROLS[control], 3 - new if control == "pra" else new)
        code.extend([0xEA] * nops)
        absolute(0xAD, ENDPOINTS[endpoint])
        absolute(0x8D, 0x6000 + index)
    store(0x6080, 0xA5)
    store(0xD7FF, 0xA5)
    absolute(0x4C, 0x0800 + len(code))
    assert 0x0800 + len(code) < 0x3F00
    return bytes([0, 8]) + code


def verify(rows: list[dict]) -> dict:
    expected_keys = set(itertools.product([m[0] for m in MODELS], CONTROLS, ENDPOINTS))
    keys = [(r["model"], r["control"], r["endpoint"]) for r in rows]
    assert len(keys) == len(expected_keys) and set(keys) == expected_keys
    differences = []
    stale_bank_rejections = 0
    for row in rows:
        actual = row["samples"]
        assert len(actual) == len(CASES) and row["sentinel"] == 0xA5
        assert row["trace_samples"] == len(CASES)
        assert len(row["trace"]) == len(CASES)
        assert [int(a, 16) for _, _, a in row["trace"]] == actual
        assert all(type(v) is int and 0 <= v <= 255 for v in actual)
        for index, ((old, new, _nops), value) in enumerate(
            zip(CASES, actual, strict=True)
        ):
            expected = PATTERNS[new]
            stale = PATTERNS[old]
            if row["endpoint"] == "colour":
                expected = (expected & 0xF0) | 0x0A
                stale = (stale & 0xF0) | 0x0A
            if value != expected:
                differences.append(
                    [
                        row["model"],
                        row["control"],
                        row["endpoint"],
                        index,
                        value,
                        expected,
                    ]
                )
            stale_bank_rejections += value != stale
        # Derive failures from actual data; never trust the recorded count.
    assert not differences, differences[:20]
    assert stale_bank_rejections == 2880, stale_bank_rejections
    return {
        "rows": len(rows),
        "samples": len(rows) * len(CASES),
        "differences": len(differences),
        "stale_bank_rejections": stale_bank_rejections,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roms", type=Path, required=True)
    parser.add_argument("--x64sc", type=Path, default=Path("/opt/homebrew/bin/x64sc"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    (output / "empty.cfg").write_text("")
    rows, logs = [], {}
    for model, _, _ in MODELS:
        for control, endpoint in itertools.product(CONTROLS, ENDPOINTS):
            stem = f"{model}-{control}-{endpoint}"
            program = output / f"{stem}.prg"
            program.write_bytes(guest(control, endpoint))
            dump, monitor = output / f"{stem}.bin", output / f"{stem}.mon"
            monitor.write_text(
                f'delete\nload "{program}" 0\ntrace load ${ENDPOINTS[endpoint]:04x}\n'
                f'break store $d7ff\ng $0800\nr\nbsave "{dump}" 0 $6000 $6080\nquit\n'
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
            logs[stem] = log
            assert "Stop on store d7ff" in log and "Unexpected token" not in log
            raw = dump.read_bytes()
            assert len(raw) == 129 and raw[-1] == 0xA5
            trace = re.findall(
                rf"Trace  load {ENDPOINTS[endpoint]:04x}\)\s+(\d+)/\$[0-9a-f]+,\s+(\d+)/\$[0-9a-f]+\n\.C:[^\n]+ A:([0-9A-F]{{2}})",
                log,
            )
            assert [int(a, 16) for _, _, a in trace] == list(raw[:-1])
            rows.append(
                {
                    "model": model,
                    "control": control,
                    "endpoint": endpoint,
                    "samples": list(raw[:-1]),
                    "sentinel": raw[-1],
                    "trace_samples": len(trace),
                    "trace": trace,
                    "program_sha256": digest(program),
                    "command": cmd,
                }
            )
            print(stem, len(trace), "completed reads", flush=True)
    identities = {
        p.name: digest(p)
        for p in [
            args.x64sc,
            *(args.roms / f"{r}.rom" for r in ["kernal", "basic", "chargen"]),
        ]
    }
    (output / "comparison.json").write_text(
        json.dumps({"identities": identities, "rows": rows}, indent=2) + "\n"
    )
    with gzip.open(output / "traces.json.gz", "wt") as stream:
        json.dump(logs, stream)
    print(json.dumps(verify(rows)), flush=True)


if __name__ == "__main__":
    main()
