"""The transition checker must reject three plausible implementation faults."""
from pathlib import Path
import json
import subprocess

HERE = Path(__file__).resolve().parent
source = (HERE/'probe.cpp').read_text()
mutations = {
 'late-start': ('+ 81 - 114', '+ 82 - 114', 1),
 'reset-enable-phase': ('114 - (t - UpdateLast15KHzTime())', '81', 1),
 'clear-retained-shift': ('mSKSTAT |= 0x04;', 'mSKSTAT |= 0x0C;', 3),
}
results = {}
for name, (old,new,count) in mutations.items():
 actual = source.count(old)
 if actual != count:
  raise AssertionError(f'{name}: expected {count} targets, found {actual}')
 path = HERE/f'{name}.cpp'
 path.write_text(source.replace(old,new))
 subprocess.run(['clang++','-std=c++17','-O2',str(path),'-o',str(HERE/name)],check=True)
 with (HERE/f'{name}.csv').open('w') as out,(HERE/f'{name}.stderr').open('w') as err:
  run = subprocess.run([str(HERE/name)],stdout=out,stderr=err)
 if run.returncode != 1:
  raise AssertionError(f'{name}: expected checker failure, got {run.returncode}')
 results[name]={'exit':run.returncode,'result':(HERE/f'{name}.stderr').read_text().strip(),'replace':old,'with':new,'count':count}
(HERE/'negative-controls.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
