from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,os
p=Path(__file__).parent;root=Path(os.environ['EMU198X_GB_MEALYBUG_ROOT'])
def run(ref):
 name=ref.name.removesuffix('_dmg_blob.png'); path=p/(name+'-gateboy.shades')
 r=subprocess.run([str(p/'reference_gateboy'),str(root/(name+'.gb')),str(path),str(p/(name+'-gateboy-pins.csv'))],capture_output=True,text=True)
 assert r.returncode==0,(name,r.stderr)
 assert r.stderr.count('marker phase=')==1,(name,r.stderr)
 row=dict(rom=name,marker=r.stderr.splitlines()[0])
 a=path.read_bytes(); c=Path(str(path)+'.lcd').read_bytes();assert len(a)==len(c)==23040
 assert max(a)<=3 and max(c)<=3,(name,'unwritten/invalid pixels')
 row['capture_vs_framebuffer']=sum(x!=y for x,y in zip(a,c,strict=True))
 for suffix in ('dmg_blob','dmg_cpu_b'):
  f=root/f'{name}_{suffix}.png'
  if not f.exists():continue
  im=Image.open(f).convert('L');assert im.size==(160,144)
  b=bytes(3-(v*3+127)//255 for v in im.tobytes())
  row[suffix]=sum(x!=y for x,y in zip(a,b,strict=True))
  row['lcd_'+suffix]=sum(x!=y for x,y in zip(c,b,strict=True))
 return row
with ThreadPoolExecutor(max_workers=4) as pool:
 rows=[]
 for row in pool.map(run,sorted(root.glob('*_dmg_blob.png'))):
  rows.append(row);print(json.dumps(row),flush=True)
assert len(rows)==24
(p/'gateboy-survey.json').write_text(json.dumps(rows,indent=2)+'\n')
