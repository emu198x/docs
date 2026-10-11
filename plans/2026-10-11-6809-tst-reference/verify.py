"""Verify complete TST flag outputs and deliberately incorrect probe controls."""

import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
reference = (root / "reference-flags.bin").read_bytes()
actual = (root / "actual-flags.bin").read_bytes()
if len(reference) != 131072 or len(actual) != 393216:
    raise ValueError("incomplete outputs")
if actual != reference * 3:
    raise ValueError("full flag outputs differ")
for filename, digest in json.loads((root / "summary.json").read_text())[
    "hashes"
].items():
    if hashlib.sha256((root / filename).read_bytes()).hexdigest() != digest:
        raise ValueError(f"hash mismatch: {filename}")
for args, name in [(["3"], "wrong-cycles"), (["2", "4001"], "wrong-address")]:
    result = subprocess.run(
        [str(root / "probe"), *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 101:
        raise ValueError(f"negative control did not fail: {name}: {result.returncode}")
print("393216 complete flags match; both wrong timing/address controls fail")
