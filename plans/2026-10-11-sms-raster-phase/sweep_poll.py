import csv
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "poll-sweep"
OUT.mkdir(exist_ok=True)


def run(case):
    region, reload, delay = case
    name = f"{region}-r{reload}-d{delay}"
    rom = OUT / (name + ".sms")
    subprocess.run(
        [
            "python3",
            str(ROOT / "make_poll_guest.py"),
            str(reload),
            str(rom),
            str(delay),
        ],
        check=True,
        capture_output=True,
    )
    rings = {}
    for core, exe in [("reference", "reference_host"), ("emu", "emu_probe")]:
        prefix = OUT / (name + "-" + core)
        result = subprocess.run(
            [str(ROOT / exe), str(rom), region, str(prefix), "60"],
            cwd=ROOT / "genesis-plus-gx",
            check=True,
            capture_output=True,
            text=True,
        )
        prefix.with_suffix(".log").write_text(result.stdout + result.stderr)
        ram = prefix.with_suffix(".ram").read_bytes()
        assert len(ram) == 8192
        idx = ram[0]
        ring = [
            {
                "v": ram[0x100 + (idx - 24 + j) % 256],
                "h": ram[0x300 + (idx - 24 + j) % 256],
                "status": ram[0x200 + (idx - 24 + j) % 256],
            }
            for j in range(24)
        ]
        assert any(x["v"] for x in ring), (name, core, "empty IRQ observations")
        rings[core] = ring
    return {"region": region, "reload": reload, "delay": delay, "rings": rings}


cases = [
    (region, reload, delay)
    for region in ["ntsc-u", "pal"]
    for reload in [31]
    for delay in [0, 1, 4, 16]
]
with ThreadPoolExecutor(max_workers=2) as pool:
    rows = list(pool.map(run, cases))
(OUT / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
with (OUT / "summary.csv").open("w") as out:
    w = csv.writer(out, lineterminator="\n")
    w.writerow(
        ["region", "reload", "delay_nops", "reference_h", "emu_h", "v_sequences_equal"]
    )
    for row in rows:
        a, b = row["rings"]["reference"], row["rings"]["emu"]
        w.writerow(
            [
                row["region"],
                row["reload"],
                row["delay"],
                sorted({x["h"] for x in a}),
                sorted({x["h"] for x in b}),
                [x["v"] for x in a] == [x["v"] for x in b],
            ]
        )
print((OUT / "summary.csv").read_text())
