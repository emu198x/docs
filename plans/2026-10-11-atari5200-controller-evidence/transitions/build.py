"""Run original Altirra SKCTL/scan/matrix code with a one-event scheduler.

Audio, serial and analogue side paths are no-ops. Neither the SKCTL case nor
scan transitions are rewritten. Event times use the reference scheduling API.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/Users/stevehill/Projects/198x')
OUT = Path(__file__).resolve().parent
path = ROOT / 'emulators/atari/altirra/src/ATAudio/source/pokey.cpp'
raw = path.read_bytes()
src = raw.decode().replace('\r\n', '\n')

def between(start: str, end: str, offset: int = 0) -> str:
    first = src.index(start, offset)
    return src[first:src.index(end, first)]

blocks = {
    'scan': between('\t\tcase kATPokeyEventKeyboardScan:', '\t\tcase kATPokeyEventTimer1Borrow:'),
    'write': between('\t\tcase 0x0F:', '\t\tdefault:', src.index('void ATPokeyEmulator::WriteByte(')),
    'clock': between('uint32 ATPokeyEmulator::UpdateLast15KHzTime()', 'uint32 ATPokeyEmulator::UpdateLast64KHzTime()'),
    'schedule': between('void ATPokeyEmulator::UpdateKeyboardScanEvent()', 'void ATPokeyEmulator::QueueKeyboardIRQ()'),
    'break': between('void ATPokeyEmulator::AssertBreakIRQ()', 'void ATPokeyEmulator::AssertIrq('),
    'matrix': between('void ATPokeyEmulator::UpdateEffectiveKeyMatrix()', 'bool ATPokeyEmulator::CanPushKey('),
    'set_matrix': between('void ATPokeyEmulator::SetKeyMatrix(', 'template<uint8 activeChannel>'),
}
shim = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>
#include <vector>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using uint64=uint64_t;
constexpr unsigned kATPokeyEventKeyboardScan=1;
struct Scheduler {
  uint64 now=0, due=0; bool active=false; unsigned token=1;
  uint64 GetTick64() const { return now; }
  void* AddEvent(unsigned delay, void*, unsigned id) {
    assert(id==kATPokeyEventKeyboardScan && delay>0);
    due=now+delay; active=true; return &token;
  }
  void UnsetEvent(void*& event) { if(event) active=false; event=nullptr; }
  void SetEvent(unsigned delay, void* target, unsigned id, void*& event) {
    UnsetEvent(event); event=AddEvent(delay,target,id);
  }
};
#define ATSCHEDULER_GETTIME(p) uint32((p)->now)
#define VDASSERT(x) assert(x)
struct Renderer { void SetInitMode(bool) {} };
struct Cassette { void PokeyResetSerialInput() {} };
unsigned VDFindLowestSetBitFast(unsigned x) { assert(x); return __builtin_ctz(x); }
struct ATPokeyEmulator {
  Scheduler scheduler; Scheduler* mpScheduler=&scheduler;
  Renderer renderer; Renderer* mpRenderer=&renderer; Cassette* mpCassette=nullptr;
  void* mpKeyboardScanEvent=nullptr; void* mpKeyboardIRQEvent=nullptr;
  bool mb5200Mode=true, mbKeyboardScanEnabled=false;
  uint8 mSKCTL=0, mKeyScanCode=0, mKeyScanState=0, mKeyScanLatch=0;
  uint8 mKBCODE=0, mSKSTAT=255, mIRQEN=192, mIRQST=255;
  bool mbControlKeyLatchedState=false, mbShiftKeyLatchedState=false, mbBreakKeyLatchedState=false;
  bool mbControlKeyState=false, mbShiftKeyState=false;
  uint16 mKeyMatrix[8]{}, mEffectiveKeyMatrix[8]{};
  uint32 mLast15KHzTime=0, mLast64KHzTime=0, mLastPolyTime=0, mPotLastTimeSlow=0;
  uint32 mPoly9Counter=0, mPoly17Counter=0;
  uint64 mPolyShutOffTime=0;
  bool mbSerialWaitingForStartBit=false, mbSerialRateChanged=false, mbSerClockPhase=false;
  unsigned mCounter[4]{};
  unsigned mSerialInputShiftRegister=0,mSerialOutputShiftRegister=0,mSerialOutputCounter=0,mSerialInputCounter=0;
  bool mbSerOutValid=false,mbSerShiftValid=false,mbSerInBurstPendingData=false,mbSerInBurstPendingIRQ1=false,mbSerInBurstPendingIRQ2=false;
  unsigned mSerOutBurstDeadline=0, mSerialInputResetCounter=0;
  bool mbNotifyBiClockChange=false;
  void (*mpNotifyBiClockChangeFn)()=nullptr;
  template<unsigned N> void UpdateTimerCounter() {}
  template<unsigned N> unsigned GetAUDFP1() { return 1; }
  void UpdatePots(unsigned) {}
  void AssertIrq(bool) {}
  void NegateIrq(bool) {}
  void RecomputeAllowedDeferredTimers() {}
  void SetupTimers(unsigned) {}
  bool IsSerialOutputClockRunning() { return true; }
  void FlushSerialOutput() {}
  void NotifyForceBreak() {}
  void QueueKeyboardIRQ() { std::abort(); } // unreachable in physical 5200 mode
  void WriteByte(uint8 reg, uint8 value);
  void OnScheduledEvent(uint32 id);
  uint32 UpdateLast15KHzTime(); uint32 UpdateLast15KHzTime(uint32 t);
  void UpdateKeyboardScanEvent();
  void AssertBreakIRQ();
  void UpdateEffectiveKeyMatrix();
  void SetKeyMatrix(const bool matrix[64]);
  unsigned edges=0, key_irqs=0, break_irqs=0;
  uint64 first_edge=0, first_key=0, first_shift=0, first_break=0;
  bool acknowledge=false;
  void advance(uint64 target) {
    assert(target>=scheduler.now);
    while(scheduler.active && scheduler.due<=target) {
      scheduler.now=scheduler.due; scheduler.active=false;
      OnScheduledEvent(kATPokeyEventKeyboardScan);
      ++edges;
      if(edges==1) first_edge=scheduler.now;
      if(!(mSKSTAT&4) && !first_key) first_key=scheduler.now;
      if(!(mSKSTAT&8) && !first_shift) first_shift=scheduler.now;
      if(!(mIRQST&128) && !first_break) first_break=scheduler.now;
      if(!(mIRQST&64)) ++key_irqs;
      if(!(mIRQST&128)) ++break_irqs;
      if(acknowledge) mIRQST|=192;
    }
    scheduler.now=target;
  }
  void inputs(uint16 keys, bool top) {
    bool matrix[64]{};
    for(unsigned code=0;code<64;++code) matrix[code]=(keys&(1u<<((code>>1)&15)))!=0;
    SetKeyMatrix(matrix);
    for(unsigned row: {0u,2u,6u}) mKeyMatrix[row]=(mKeyMatrix[row]&255)|(top?256:0);
    UpdateEffectiveKeyMatrix();
  }
};
'''
assembled = shim + '\nvoid ATPokeyEmulator::WriteByte(uint8 reg,uint8 value) {switch(reg) {\n' + blocks['write'] + '\ndefault: std::abort(); }}\n'
assembled += '\nvoid ATPokeyEmulator::OnScheduledEvent(uint32 id) {switch(id) {\n' + blocks['scan'] + '\ndefault: std::abort(); }}\n'
assembled += ''.join(blocks[k] for k in ('clock','schedule','break','matrix','set_matrix'))
main = (OUT/'cases.cpp').read_text()
(OUT/'probe.cpp').write_text(assembled+main)
(OUT/'provenance.json').write_text(json.dumps({
 'source':str(path.relative_to(ROOT)), 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'blocks':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in blocks.items()},
 'scope':'Unchanged SKCTL case, keyboard event, divider scheduler and matrix methods; scheduler/board input shim; serial/audio/pot paths stubbed; no full machine.'
},indent=2)+'\n')
subprocess.run(['clang++','-std=c++17','-O2','-Wall','-Wextra',str(OUT/'probe.cpp'),'-o',str(OUT/'probe')],check=True)
with (OUT/'capture.csv').open('w') as out,(OUT/'stderr.txt').open('w') as err:
 subprocess.run([str(OUT/'probe')],stdout=out,stderr=err,check=True)
print((OUT/'stderr.txt').read_text())
