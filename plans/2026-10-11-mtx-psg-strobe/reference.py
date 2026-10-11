"""Compile exact MAME sound handlers with a recording write sink."""
from pathlib import Path
import hashlib
import os
import subprocess

source = Path(os.environ['MAME']) / 'src/mame/memotech/mtx_m.cpp'
text = source.read_text()
bodies = []
for signature in ['uint8_t mtx_state::mtx_sound_strobe_r()',
                  'void mtx_state::mtx_sound_latch_w(uint8_t data)']:
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    bodies.append(text[start:end])
extracted = '\n\n'.join(bodies) + '\n'
Path('mame-handlers.inc').write_text('// license:BSD-3-Clause\n// copyright-holders:Lee Ward, Dirk Best, Curt Coder\n' + extracted)
Path('handler-sha256.txt').write_text(hashlib.sha256(extracted.encode()).hexdigest()+'\n')
subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','mame_probe.cpp','-o','mame_probe'],check=True)
with Path('mame.csv').open('w') as output:
    subprocess.run(['./mame_probe'],stdout=output,check=True)
