"""Compile unchanged MAME write cases R0–R17; generated source stays local."""
from pathlib import Path
import argparse
import hashlib
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
raw = args.source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "62523f73d0cf24bad50610d9f0aaa41ab46f0458a5c0601f824fc7e121977bb8"
source = raw.decode()
start = source.index("switch (m_register_address_latch)", source.index("void mc6845_device::register_w("))
end = source.index("\t\tcase 0x12:", start)
switch = source[start:end] + "\t}\n"
HARNESS = r"""#include <cstdint>
#include <cstdio>
#include <initializer_list>
struct Probe {
 uint8_t m_register_address_latch=0,m_horiz_char_total=0,m_horiz_disp=0,m_horiz_sync_pos=0,m_sync_width=0,m_vert_char_total=0,m_vert_total_adj=0,m_vert_disp=0,m_vert_sync_pos=0,m_mode_control=0,m_max_ras_addr=0,m_cursor_start_ras=0,m_cursor_end_ras=0;
 uint16_t m_disp_start_addr=0,m_cursor_addr=0,m_light_pen_addr=0x2a59;
 void write(uint8_t data) { EXTRACTED_SWITCH }
};
int main(){
 int cases=0,failures=0;
 puts("register,value,expected,observed");
 for(int reg: {6,12,14,15,16,17}) {
  for(int value=0;value<256;++value) {
   Probe p;p.m_register_address_latch=reg;p.write(value);
   int observed=0,expected=0;
   switch(reg){case 6:observed=p.m_vert_disp;expected=value&0x7f;break;case 12:observed=p.m_disp_start_addr>>8;expected=value&0x3f;break;case 14:observed=p.m_cursor_addr>>8;expected=value&0x3f;break;case 15:observed=p.m_cursor_addr&0xff;expected=value;break;case 16:observed=p.m_light_pen_addr>>8;expected=0x2a;break;case 17:observed=p.m_light_pen_addr&0xff;expected=0x59;break;}
   ++cases;failures+=observed!=expected;printf("%d,%d,%d,%d\n",reg,value,expected,observed);
  }
 }
 fprintf(stderr,"%d reference register cases, %d mismatches\n",cases,failures);return failures?1:0;
}
"""

args.output.mkdir(parents=True, exist_ok=True)
cpp = args.output / "reference.cpp"
cpp.write_text(HARNESS.replace("EXTRACTED_SWITCH", switch))
subprocess.run(["c++", "-std=c++17", "-O2", str(cpp), "-o", str(args.output / "reference")], check=True)
run = subprocess.run([str(args.output / "reference")], capture_output=True, text=True)
(args.output / "reference.csv").write_text(run.stdout)
(args.output / "reference.stderr").write_text(run.stderr)
print(run.stderr, end="")
raise SystemExit(run.returncode)
