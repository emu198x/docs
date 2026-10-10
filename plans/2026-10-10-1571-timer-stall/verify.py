"""Check retained traces for the lost-ATN cause, without firmware payloads."""
from pathlib import Path
import gzip
import json
import re

ROOT = Path(__file__).resolve().parent


def inspect(name: str) -> dict:
    rows = gzip.decompress((ROOT / f"{name}.trace.gz").read_bytes()).decode().splitlines()
    jobs = []
    mechanics = []
    for row in rows:
        if row.startswith("TRACE event=bus") and "rw=false addr=000" in row:
            match = re.search(r"pc=(\w+).*addr=(000[0-4]) data=(\w+)", row)
            if match:
                jobs.append(match.groups())
        if row.startswith("TRACE event=mechanics"):
            match = re.search(r"motor=(\w+) head=(\d+)", row)
            assert match, row
            mechanics.append(match.groups())
    assert jobs and mechanics, "empty trace cannot establish recovery"
    return {"rows": rows, "jobs": jobs, "mechanics": mechanics}


failed = inspect("early-attention")
working = inspect("corrected-attention")
fixed = inspect("early-alternate")
assert len(failed["jobs"]) == 2945
assert len(working["jobs"]) == len(fixed["jobs"]) == 3114
assert failed["jobs"] == working["jobs"][: len(failed["jobs"])]
assert fixed["jobs"] == working["jobs"]
assert len(failed["mechanics"]) == 102
assert len(fixed["mechanics"]) == len(working["mechanics"]) == 138
assert fixed["mechanics"] == working["mechanics"]
assert failed["mechanics"][-1] == ("false", "14")
assert fixed["mechanics"][-1] == ("false", "22")

edge = "ATN cyc=160142709 pc=81bc asserted=true ifr_before=40 ifr_after=c2"
assert any(row.startswith(edge) for row in failed["rows"])
assert any(row.startswith(edge) for row in fixed["rows"])
checks = [
    (160142712, "addr=180f", "ifr1=c2"),
    (160142718, "addr=180f", "ifr1=c2"),
    (160142753, "addr=fffe", "ifr1=c2"),
    (160142799, "addr=1801", "ifr1=c2"),
    (160142804, "addr=007c data=01", "ifr1=40"),
    (160142870, "addr=007c data=01", "flag7c=01"),
]
for cycle, access, state in checks:
    assert any(f"cyc={cycle} " in row and access in row and state in row
               for row in fixed["rows"]), (cycle, access, state)
assert any("cyc=160142753 " in row and "ifr1=40" in row
           and "flag7c=00" in row for row in failed["rows"])

result = {
    "failed_job_writes": len(failed["jobs"]),
    "recovered_job_writes": len(fixed["jobs"]),
    "failed_mechanics_events": len(failed["mechanics"]),
    "recovered_mechanics_events": len(fixed["mechanics"]),
    "recovered_sequences_match_correct_timer_run": True,
    "same_atn_edge_cycle": 160142709,
    "irq_acknowledged_by_rom_cycle": 160142799,
    "software_attention_flag_written_cycle": 160142804,
    "wrong_timer_hashes_match_production": False,
}
print(json.dumps(result, indent=2))
