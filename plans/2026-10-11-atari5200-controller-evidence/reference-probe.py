"""Compile unchanged Altirra keyboard-event/Break logic in a bounded harness.

This executes scan transitions, not the scheduler's CPU-write phase. The harness
supplies the selected 5200 matrix and invokes one event per 114 CPU clocks.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/Users/stevehill/Projects/198x')
OUT = Path(__file__).resolve().parent
source_path = ROOT / 'emulators/atari/altirra/src/ATAudio/source/pokey.cpp'
raw = source_path.read_bytes()
source = raw.decode().replace('\r\n', '\n')
start = source.index('\t\tcase kATPokeyEventKeyboardScan:')
end = source.index('\t\tcase kATPokeyEventTimer1Borrow:', start)
scan = source[start:end]
start = source.index('void ATPokeyEmulator::AssertBreakIRQ()')
end = source.index('void ATPokeyEmulator::AssertIrq(', start)
brk = source[start:end]
shim = r'''
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
using uint8 = uint8_t;
using uint32 = uint32_t;
constexpr uint32 kATPokeyEventKeyboardScan = 1;
struct Scheduler {
  void* AddEvent(unsigned cycles, void*, unsigned) {
    if (cycles != 114) std::abort();
    return nullptr;
  }
};
struct ATPokeyEmulator {
  Scheduler scheduler;
  Scheduler* mpScheduler = &scheduler;
  void* mpKeyboardScanEvent = nullptr;
  bool mb5200Mode = true, mbKeyboardScanEnabled = false;
  uint8 mSKCTL = 2, mKeyScanCode = 0, mKeyScanState = 0, mKeyScanLatch = 0;
  uint8 mKBCODE = 0, mSKSTAT = 255, mIRQEN = 192, mIRQST = 255;
  bool mbControlKeyLatchedState = false, mbShiftKeyLatchedState = false;
  bool mbBreakKeyLatchedState = false;
  std::array<unsigned, 8> mEffectiveKeyMatrix{};
  void AssertIrq(bool) {}
  void AssertBreakIRQ();
  void OnScheduledEvent(uint32 id);
};
'''
main = r'''
int main() {
  unsigned failures = 0, cases = 0;
  puts("port,selected,skctl,key,top,seen_status,seen_irq,first_key_clock,first_shift_clock,first_break_clock,key_irqs");
  for (unsigned port=0; port<4; ++port)
  for (unsigned selected=0; selected<4; ++selected)
  for (unsigned skctl=0; skctl<4; ++skctl)
  for (unsigned key=0; key<16; ++key)
  for (unsigned top=0; top<2; ++top) {
    ATPokeyEmulator p;
    p.mSKCTL=skctl;
    if (port==selected) {
      if (key) for (unsigned code: {key*2,key*2+1,key*2+32,key*2+33})
        p.mEffectiveKeyMatrix[code>>3] |= 1u<<(code&7);
      if (top) for (unsigned row: {0u,2u,6u}) p.mEffectiveKeyMatrix[row] |= 0x100;
    }
    unsigned seen_status=0, seen_irq=0, first_key=0, first_shift=0, first_break=0, key_irqs=0;
    for (unsigned step=1; step<=192; ++step) {
      p.OnScheduledEvent(kATPokeyEventKeyboardScan);
      seen_status |= unsigned(~p.mSKSTAT)&12;
      seen_irq |= unsigned(~p.mIRQST)&192;
      if (!(p.mSKSTAT&4) && !first_key) first_key=step*114;
      if (!(p.mSKSTAT&8) && !first_shift) first_shift=step*114;
      if (!(p.mIRQST&128) && !first_break) first_break=step*114;
      if (!(p.mIRQST&64)) ++key_irqs;
      // Software acknowledges both sources after every event, so recurrence is visible.
      p.mIRQST |= 192;
    }
    bool expect_key=port==selected && key && skctl==2;
    bool expect_top=port==selected && top && (skctl&2);
    bool pass=bool(seen_status&4)==expect_key && bool(seen_status&8)==expect_top
        && bool(seen_irq&64)==expect_key && bool(seen_irq&128)==expect_top;
    if (expect_key) pass &= first_key==(key*2+2)*114 && key_irqs==6;
    if (expect_top) pass &= first_shift==17*114 && first_break==49*114;
    failures += !pass;
    ++cases;
    printf("%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",port+1,selected,skctl,key,top,
        seen_status,seen_irq,first_key,first_shift,first_break,key_irqs);
  }
  fprintf(stderr,"%u mismatches across %u original-reference scan cases\n",failures,cases);
  return failures ? 1:0;
}
'''
cpp = shim + '\nvoid ATPokeyEmulator::OnScheduledEvent(uint32 id) { switch(id) {\n' + scan + '\n}}\n' + brk + main
(OUT/'reference-probe.cpp').write_text(cpp)
(OUT/'reference-provenance.json').write_text(json.dumps({
 'source':str(source_path.relative_to(ROOT)), 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'scan_block_sha256':hashlib.sha256(scan.encode()).hexdigest(),
 'break_block_sha256':hashlib.sha256(brk.encode()).hexdigest(),
 'scope':'Unchanged keyboard event and AssertBreakIRQ; matrix/scheduler/IRQ-ack shim; no CPU-write phase or electrical validation.'
},indent=2)+'\n')
subprocess.run(['clang++','-std=c++17','-O2','-Wall','-Wextra',str(OUT/'reference-probe.cpp'),'-o',str(OUT/'reference-probe')],check=True)
with (OUT/'reference.csv').open('w') as out, (OUT/'reference.stderr').open('w') as err:
 subprocess.run([str(OUT/'reference-probe')],stdout=out,stderr=err,check=True)
print((OUT/'reference.stderr').read_text())
