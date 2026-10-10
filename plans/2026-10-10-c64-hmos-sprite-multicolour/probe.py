"""Extract VICE's unchanged sprite functions for the directed dot oracle.

Run from the emulator source checkout; compile the emitted C and compare its
stdout to sprite-mc-dots.txt. The extraction retains the reference semantics;
only the surrounding chip/memory state and inert DMA flags are supplied here.
"""

import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--reference", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
source = args.reference.read_text()
functions = source[
    source.index("static DRAW_INLINE uint8_t get_trigger_candidates") : source.index(
        "/**************************************************************************",
        source.index("static DRAW_INLINE void draw_sprites8"),
    )
]
header = """#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define DRAW_INLINE
#define COL_D025 1
#define COL_D026 3
#define COL_D027 2
struct { uint8_t regs[64], sprite_display_bits, sprite_background_collisions, sprite_sprite_collisions; int color_latency; struct { uint32_t data; int x; } sprite[8]; } vicii;
static uint8_t sprite_pri_bits, sprite_expx_bits, sprite_mc_bits, sprite_pending_bits, sprite_active_bits, sprite_halt_bits, sbuf_expx_flops, sbuf_mc_flops;
static uint32_t sbuf_reg[8];
static uint8_t sbuf_pixel_reg[8], render_buffer[8], pri_buffer[8];
static int sprite_x_pipe[8];
#define cycle_is_sprite_dma1_dma2(f) 0
#define cycle_is_sprite_ptr_dma0(f) 0
#define cycle_is_check_spr_disp(f) 0
#define cycle_get_sprite_num(f) 0
#define cycle_get_xpos(f) ((int)(f))
"""
main = """int main(void) {
for (int hmos=0;hmos<2;hmos++) for (int expand=0;expand<2;expand++) for (int mc=0;mc<2;mc++) for (int phase=0;phase<8;phase++) {
 memset(&vicii,0,sizeof(vicii)); memset(sbuf_reg,0,sizeof(sbuf_reg)); memset(sbuf_pixel_reg,0,sizeof(sbuf_pixel_reg));
 sprite_pri_bits=sprite_active_bits=sprite_halt_bits=sbuf_expx_flops=sbuf_mc_flops=0;
 sprite_pending_bits=1; sprite_expx_bits=expand; sprite_mc_bits=mc;
 vicii.color_latency=!hmos; vicii.regs[0x1c]=mc; vicii.regs[0x1d]=expand;
 sbuf_reg[0]=0x69ad96; for(int s=0;s<8;s++) sprite_x_pipe[s]=vicii.sprite[s].x=80+phase;
 printf("%d %d %d %d ",hmos,expand,mc,phase);
 for(int cycle=0;cycle<4;cycle++) {
  if(cycle==1) vicii.regs[0x1c]=!mc;
  memset(render_buffer,0,8); draw_sprites8(80+cycle*8);
  for(int dot=0;dot<8;dot++) printf("%d",render_buffer[dot]);
 }
 puts("");
}
}
"""
args.output.write_text(header + functions + main)
