from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess
root=Path(__file__).parent
obj=root/'gateboy-objects';obj.mkdir(exist_ok=True)
sources=list((root/'GateBoy/src/GateBoyLib').glob('*.cpp'))+list((root/'metrolib/metrolib/core').glob('*.cpp'))
sources += [root/'metrolib/metrolib/gameboy'/f for f in ['MetroBoyCPU.cpp','GBConstants.cpp','Assembler.cpp']]
sources += [root/'reference_gateboy.cpp']
def compile(p):
 out=obj/('_'.join(p.relative_to(root).parts)+'.o')
 cmd=['clang++','-std=c++20','-O3','-DCONFIG_RELEASE','-I'+str(root/'metrolib'),'-I'+str(root/'GateBoy/src'),'-c',str(p),'-o',str(out)]
 r=subprocess.run(cmd,capture_output=True,text=True)
 return p,r,out
with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(compile,sources))
for p,r,out in results:
 if r.returncode: print(p, r.stdout,r.stderr)
if any(r.returncode for _,r,_ in results): raise SystemExit(1)
r=subprocess.run(['clang++',*[str(out) for _,_,out in results],'-o',str(root/'reference_gateboy')],capture_output=True,text=True)
print(r.stdout,r.stderr);raise SystemExit(r.returncode)
