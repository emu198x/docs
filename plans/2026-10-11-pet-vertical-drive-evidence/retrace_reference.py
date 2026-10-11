"""Compile unchanged VICE PET signal and VIA read stages in an original driver."""
from pathlib import Path
import hashlib
import subprocess
import sys

root, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=True)
expected = {
    'pet.c': 'e0dd49d56dc4379ad1c356c1013c1a92f87fc91f40c9a23141412ab1670f0e47',
    'petvia.c': '963b8c312eff89806ca8d00f0e936a77a5a3d0c42d69e199f7abd2a748979ef2',
}
texts = {}
for name, digest in expected.items():
    data = (root / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, name
    texts[name] = data.decode()

def function(text: str, marker: str) -> str:
    start = text.index(marker)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

macros = '\n'.join(line for line in texts['pet.c'].splitlines()
                   if line.startswith('#define SIGNAL_VERT_BLANK_'))
assert len(macros.splitlines()) == 2
source = '''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
typedef unsigned long CLOCK;
typedef struct { uint8_t via[16]; } via_context_t;
#define VIA_PRB 0
#define VIA_DDRB 2
#define PIA_SIG_CB1 1
#define PIA_SIG_RISE 1
#define PIA_SIG_FALL 0
static unsigned int external_high, offscreen;
static unsigned int parallel_nrfd, parallel_ndac, parallel_dav;
static CLOCK maincpu_clk;
static void drive_catch_up_hook(CLOCK t) { (void)t; }
static unsigned int crtc_offscreen(void) { return offscreen; }
static void pia1_signal(int pin, int edge, CLOCK offset) {
    (void)pin; (void)offset; external_high = edge;
}
''' + macros + '\n' + function(texts['pet.c'], 'static void pet_crtc_signal(') + '\n' + function(texts['petvia.c'], 'static uint8_t read_prb(') + '''
int main(void) {
    unsigned int cases = 0, failures = 0;
    for (unsigned int signal = 0; signal < 2; signal++) {
        offscreen = signal;
        pet_crtc_signal(signal, 0);
        if (external_high != !signal) failures++;
        for (unsigned int ddr = 0; ddr < 256; ddr++) {
            for (unsigned int latch = 0; latch < 256; latch++) {
                via_context_t ctx = {0};
                ctx.via[VIA_DDRB] = ddr;
                ctx.via[VIA_PRB] = latch;
                unsigned int pins = signal ? 0xdf : 0xff;
                unsigned int expected = (pins & ~ddr) | (latch & ddr);
                if (read_prb(&ctx, false) != expected) failures++;
                cases++;
            }
        }
    }
    printf("%u VIA direction/latch cases; two PIA levels; %u failures\\n", cases, failures);
    return failures != 0;
}
'''
(output / 'reference.c').write_text(source)
subprocess.run(['cc', '-std=c11', '-O2', str(output/'reference.c'), '-o', str(output/'reference')], check=True)
subprocess.run([str(output/'reference')], check=True)
