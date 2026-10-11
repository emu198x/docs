"""Execute Altirra's unchanged matrix closure against a 4x4 switch graph."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/Users/stevehill/Projects/198x')
OUT = Path(__file__).resolve().parent
source_path = ROOT / 'emulators/atari/altirra/src/ATAudio/source/pokey.cpp'
raw = source_path.read_bytes()
source = raw.decode().replace('\r\n', '\n')
start = source.index('void ATPokeyEmulator::UpdateEffectiveKeyMatrix()')
end = source.index('bool ATPokeyEmulator::CanPushKey(', start)
method = source[start:end]
shim = r'''
#include <cstdint>
#include <initializer_list>
#include <cstring>
#include <cstdio>
using uint16 = uint16_t;
struct ATPokeyEmulator {
  uint16 mKeyMatrix[8]{}, mEffectiveKeyMatrix[8]{};
  bool mb5200Mode = true;
  void UpdateEffectiveKeyMatrix();
};
'''
main = r'''
int main() {
  unsigned errors=0, ghost_cases=0;
  puts("held_mask,top,ghost_positions,reference_matrix");
  for (unsigned held=0; held<32768; ++held)
  for (unsigned top=0; top<2; ++top) {
    ATPokeyEmulator p;
    bool edge[8][8]{};
    for (unsigned key=1; key<16; ++key) {
      if (!(held & (1u<<(key-1)))) continue;
      for (unsigned duplicate=0; duplicate<4; ++duplicate) {
        unsigned code=key*2+(duplicate&1)+(duplicate&2)*16;
        p.mKeyMatrix[code>>3] |= 1u<<(code&7);
      }
      unsigned row=key>>2, col=4+(key&3);
      edge[row][col]=edge[col][row]=true;
    }
    if (top) p.mKeyMatrix[0]=p.mKeyMatrix[0]|0x100,
             p.mKeyMatrix[2]=p.mKeyMatrix[2]|0x100,
             p.mKeyMatrix[6]=p.mKeyMatrix[6]|0x100;
    p.UpdateEffectiveKeyMatrix();
    unsigned effective=0, ghosts=0;
    for (unsigned row=0; row<4; ++row) {
      bool visited[8]{}; visited[row]=true;
      // A conductive path in the physical row/column switch network is enough
      // to pull down that column. Eight passes cover every simple path.
      for (unsigned pass=0; pass<8; ++pass)
        for (unsigned a=0; a<8; ++a)
          if (visited[a]) for (unsigned b=0; b<8; ++b) if (edge[a][b]) visited[b]=true;
      for (unsigned col=0; col<4; ++col)
        if (visited[col+4]) effective |= 1u<<(row*4+col);
    }
    ghosts=effective & ~(held<<1);
    ghost_cases += ghosts!=0;
    for (unsigned code=0; code<64; ++code) {
      bool actual=p.mEffectiveKeyMatrix[code>>3]&(1u<<(code&7));
      bool expected=effective&(1u<<((code>>1)&15));
      errors += actual!=expected;
    }
    // Only these rows sample KR2; unused effective-matrix bits are not pins.
    for (unsigned row: {0u,2u,6u}) {
      bool expected=top;
      errors += bool(p.mEffectiveKeyMatrix[row]&0x100)!=expected;
    }
    printf("%u,%u,%u,",held,top,ghosts);
    for (unsigned row=0; row<8; ++row) printf("%03x%s",p.mEffectiveKeyMatrix[row],row==7?"\n":":");
  }
  fprintf(stderr,"%u mismatches across 65536 matrix cases; %u cases contain phantom keys\n",errors,ghost_cases);
  return errors ? 1:0;
}
'''
cpp = shim+method+main
(OUT/'matrix-reference.cpp').write_text(cpp)
(OUT/'matrix-provenance.json').write_text(json.dumps({
 'source':str(source_path.relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),
 'method_sha256':hashlib.sha256(method.encode()).hexdigest(),
 'scope':'Unchanged 5200 effective matrix method versus independent row/column graph reachability; electrical delays excluded.'
},indent=2)+'\n')
subprocess.run(['clang++','-std=c++17','-O2','-Wall','-Wextra',str(OUT/'matrix-reference.cpp'),'-o',str(OUT/'matrix-reference')],check=True)
with (OUT/'matrix-reference.csv').open('w') as out, (OUT/'matrix-reference.stderr').open('w') as err:
 subprocess.run([str(OUT/'matrix-reference')],stdout=out,stderr=err,check=True)
print((OUT/'matrix-reference.stderr').read_text())
