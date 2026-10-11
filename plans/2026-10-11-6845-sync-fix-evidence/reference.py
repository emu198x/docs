"""Compile unchanged MAME sync-width stages; generated vendor code stays local."""
from pathlib import Path
import argparse
import hashlib
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
source_bytes = args.source.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == "62523f73d0cf24bad50610d9f0aaa41ab46f0458a5c0601f824fc7e121977bb8"
source = source_bytes.decode()

def body(marker: str) -> str:
    start = source.index("{", source.index(marker))
    depth = 1
    end = start + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start + 1:end - 1]

horizontal = body("TIMER_CALLBACK_MEMBER(mc6845_device::hsync_on)")
vertical = body("if ( m_vsync_ff )")
args.output.mkdir(parents=True, exist_ok=True)
code = r"""
#include <cstdint>
#include <cstdio>
struct Timer { int remaining = 0; void adjust(int clocks) { remaining = clocks; } };
struct Probe {
 uint8_t m_sync_width = 0, m_hsync_width_counter = 0, m_vsync_width_counter = 0;
 bool m_supports_vert_sync_width = false, m_vsync_ff = false, high = false;
 Timer timer; Timer* m_hsync_off_timer = &timer;
 int cclks_to_attotime(int clocks) { return clocks; }
 void set_hsync(bool state) { high = state; }
 void horizontal() { HORIZONTAL }
 void vertical(bool& new_vsync) { if (m_vsync_ff) { VERTICAL } }
};
int main() {
 int cases=0, failures=0;
 puts("variant,signal,width,expected,observed");
 for (int variant=0;variant<2;++variant) {
  for(int width=1;width<=15;++width) {
   Probe p; p.m_sync_width=width; p.horizontal();
   int count=0;
   for(int tick=0;tick<32;++tick) {
    if(p.high) ++count;
    if(p.timer.remaining && --p.timer.remaining==0) p.set_hsync(false);
   }
   ++cases; failures += count!=width;
   printf("%d,h,%d,%d,%d\n",variant,width,width,count);
  }
  for(int width=0;width<=15;++width) {
   Probe p; p.m_supports_vert_sync_width=variant; p.m_sync_width=width<<4;
   // A new pulse starts with counter zero; later line boundaries run the
   // unchanged width stage before any new match_line assertion.
   p.m_vsync_ff=true; bool high=true; int count=0;
   for(int line=0;line<32;++line) {
    if(high) ++count;
    p.vertical(high);
   }
   int expected=variant && width ? width : 16;
   ++cases; failures += count!=expected;
   printf("%d,v,%d,%d,%d\n",variant,width,expected,count);
  }
 }
 fprintf(stderr,"%d stage cases, %d mismatches\n",cases,failures);
 return failures ? 1 : 0;
}
""".replace("HORIZONTAL", horizontal).replace("VERTICAL", vertical)
cpp = args.output / "reference.cpp"
cpp.write_text(code)
subprocess.run(["c++", "-std=c++17", "-O2", str(cpp), "-o", str(args.output / "reference")], check=True)
run = subprocess.run([str(args.output / "reference")], capture_output=True, text=True)
(args.output / "reference.csv").write_text(run.stdout)
(args.output / "reference.stderr").write_text(run.stderr)
print("MAME source SHA-256:", hashlib.sha256(args.source.read_bytes()).hexdigest())
print(run.stderr, end="")
raise SystemExit(run.returncode)
