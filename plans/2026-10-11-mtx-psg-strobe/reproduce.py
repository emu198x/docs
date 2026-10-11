"""Run the exact reference handlers and temporary native-machine guest probe."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--expect', choices=['failure', 'success'], required=True)
args = parser.parse_args()
base = Path(__file__).resolve().parent
repo = Path(os.environ['EMU198X'])
with tempfile.TemporaryDirectory(prefix='198x-mtx-strobe-reference-') as tmp:
    work = Path(tmp)
    for name in ['reference.py', 'mame_probe.cpp']:
        shutil.copyfile(base / name, work / name)
    subprocess.run(['python3', 'reference.py'], cwd=work, check=True)
    for name in ['mame.csv', 'mame-handlers.inc', 'handler-sha256.txt']:
        assert (work / name).read_bytes() == (base / name).read_bytes(), name

source = repo / 'crates/machine-memotech-mtx/src/lib.rs'
original = source.read_bytes()
assert b'mod psg_strobe_probe' not in original
try:
    source.write_bytes(original + (base / 'guest_probe.rs').read_bytes())
    run = subprocess.run(
        ['cargo', 'test', '-p', 'machine-memotech-mtx', '--lib',
         'out6_latches_and_in3', '--', '--nocapture'],
        cwd=repo, capture_output=True, text=True)
    output = run.stdout + run.stderr
    print(output)
    rows = [line for line in output.splitlines() if line.startswith('STROBE,')]
    assert len(rows) == 16, 'both models must execute all eight operations'
    if args.expect == 'failure':
        assert run.returncode == 101 and 'left: 16' in output
        assert all(row.endswith(',false') for row in rows)
    else:
        assert run.returncode == 0
        assert all(row.endswith(',true') for row in rows)
finally:
    source.write_bytes(original)
assert source.read_bytes() == original
print('Production source restored:', hashlib.sha256(original).hexdigest())
