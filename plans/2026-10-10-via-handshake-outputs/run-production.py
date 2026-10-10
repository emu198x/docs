from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os, subprocess, json, hashlib
root=Path('/private/tmp/via-handshake-fix')
binary=root/'catalogue-production'
env=os.environ.copy()
env.update(EMU198X_CATALOGUE_MEDIA_ROOT='/private/tmp/c64-catalogue-mirror/catalogue-c64/media',EMU198X_CATALOGUE_FIRMWARE_ROOT='/private/tmp/c64-catalogue-mirror/catalogue-c64/roms',EMU198X_STRICT_FIXTURES='1')
def run(i):
 command=[str(binary),'run','--shard',f'{i}/3','--manifest','crates/emu198x-catalogue/manifest/c64.toml']
 with (root/f'production-shard-{i}.log').open('w') as log:
  result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
 record={'command':command,'exit_code':result.returncode}
 (root/f'production-shard-{i}.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record),flush=True)
 return result.returncode
(root/'production-binary.sha256').write_text(hashlib.sha256(binary.read_bytes()).hexdigest()+'\n')
with ThreadPoolExecutor(max_workers=3) as executor:
 results=list(executor.map(run,[1,2,3]))
raise SystemExit(1 if any(results) else 0)
