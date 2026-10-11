#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "SameBoy/Core/gb.h"
static bool done;
static unsigned markers;
static uint16_t marker_pc;
static uint32_t rgb(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) {
    (void)gb; return 0xff000000u | ((uint32_t)r<<16) | ((uint32_t)g<<8) | b;
}
static void executed(GB_gameboy_t *gb, uint16_t address, uint8_t opcode) {
    if (opcode == 0x40 && GB_safe_read_memory(gb, 0xff50) != 0) {
        done = true; markers++; marker_pc = address;
    }
}
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    GB_gameboy_t *gb = GB_init(GB_alloc(), GB_MODEL_DMG_B);
    if (!gb || GB_load_boot_rom(gb, argv[1]) || GB_load_rom(gb, argv[2])) return 3;
    uint32_t pixels[160*144] = {0};
    GB_set_rgb_encode_callback(gb, rgb);
    GB_set_palette(gb, &GB_PALETTE_GREY);
    GB_set_pixels_output(gb, pixels);
    GB_set_turbo_mode(gb, true, true);
    GB_debugger_set_disabled(gb, true);
    GB_set_execution_callback(gb, executed);
    unsigned steps = 0;
    for (; steps < 10000000 && !done; steps++) GB_run(gb);
    fprintf(stderr,"marker=%u pc=%04x steps=%u\n",markers,marker_pc,steps);
    if (!done) return 4;
    FILE *out = fopen(argv[3], "wb");
    if (!out) return 5;
    for (unsigned i=0; i<160*144; i++) {
        unsigned r = (pixels[i]>>16)&255, g=(pixels[i]>>8)&255, b=pixels[i]&255;
        if (r != g || g != b || r%85) { fprintf(stderr,"non-shade pixel %u: %08x\n",i,pixels[i]); return 6; }
        if (fputc(3-r/85,out)==EOF) return 7;
    }
    if (fclose(out)) return 8;
    GB_free(gb); GB_dealloc(gb);
    return 0;
}
