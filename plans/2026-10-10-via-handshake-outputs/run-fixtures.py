from pathlib import Path
import os,subprocess,json
root=Path('/private/tmp/via-handshake-fix')
env=os.environ.copy()
env.update(EMU198X_STRICT_FIXTURES='1',EMU198X_C64_ROM_DIR='/private/tmp/c64-catalogue-mirror/catalogue-c64/roms/commodore-c64')
commands=[]
for package in ['machine-acorn-atom','machine-acorn-bbc-micro','machine-commodore-pet','machine-oric-atmos']:
 commands.append(['cargo','test','--release','-p',package,'--','--ignored','--nocapture'])
commands.extend([
 ['cargo','test','--release','-p','machine-commodore-1571','--test','boot_smoke','--','--ignored','--nocapture'],
 ['cargo','test','--release','-p','machine-commodore-vic-20','--test','joystick_probe','--test','keyboard_type','--test','rom_boot','--','--ignored','--nocapture'],
 ['cargo','test','--release','-p','machine-commodore-vic-20','--test','vici_vice_survey','vic_i_matches_the_vice_survey','--','--ignored','--nocapture'],
 ['cargo','test','--release','-p','machine-commodore-vic-20','--test','vici_vice_survey','the_comparator_rejects_a_deliberately_wrong_frame','--','--ignored','--nocapture'],
 ['cargo','test','--release','-p','runtime-commodore-c64','--test','disk_1571_load','--test','disk_save_roundtrip','--','--ignored','--nocapture']
])
results=[]
with (root/'fixtures.log').open('w') as log:
 for command in commands:
  log.write(json.dumps(command)+'\n');log.flush()
  result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
  results.append({'command':command,'exit_code':result.returncode})
  (root/'fixture-commands.json').write_text(json.dumps(results,indent=2)+'\n')
  print(json.dumps(results[-1]),flush=True)
  if result.returncode:raise SystemExit(result.returncode)
