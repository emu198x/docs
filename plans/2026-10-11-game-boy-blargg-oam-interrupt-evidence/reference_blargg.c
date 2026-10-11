#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "SameBoy/Core/gb.h"
static uint32_t rgb(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) {
    (void)gb; return 0xff000000u | ((uint32_t)r<<16) | ((uint32_t)g<<8) | b;
}
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    GB_gameboy_t *gb = GB_init(GB_alloc(), strcmp(argv[1], "cgb") == 0 ? GB_MODEL_CGB_E : GB_MODEL_DMG_B);
    if (!gb || GB_load_boot_rom(gb, argv[2]) || GB_load_rom(gb, argv[3])) return 3;
    uint32_t pixels[256*224];
    GB_set_rgb_encode_callback(gb, rgb);
    GB_set_pixels_output(gb, pixels);
    GB_set_turbo_mode(gb, true, true);
    GB_debugger_set_disabled(gb, true);
    int done = 0;
    for (unsigned frame=1; frame<=3600; frame++) {
        GB_run_frame(gb);
        size_t size=0;
        const uint8_t *ram=GB_get_direct_access(gb, GB_DIRECT_ACCESS_CART_RAM, &size, NULL);
        if (size>=4 && ram[1]==0xde && ram[2]==0xb0 && ram[3]==0x61 && ram[0]<0x80) {
            printf("RAM status=%u frame=%u\n",ram[0],frame);
            for (size_t i=4; i<size && ram[i];i++) putchar(ram[i]);
            done=1; break;
        }
        if (strstr(argv[3],"interrupt_time")) {
            const uint8_t *tiles=GB_get_direct_access(gb, GB_DIRECT_ACCESS_VRAM,NULL,NULL);
            for (int row=0; row<32;row++) {
                if (!memcmp(tiles+0x1800+row*32,"Passed",6) || !memcmp(tiles+0x1800+row*32,"Failed",6)) {done=1; printf("CONSOLE frame=%u\n",frame); break;}
            }
            if (done) break;
        }
    }
    const uint8_t *vram=GB_get_direct_access(gb, GB_DIRECT_ACCESS_VRAM,NULL,NULL);
    puts("\nCONSOLE");
    for (int row=0;row<32;row++) {
        for (int col=0;col<20;col++) {
            unsigned char c=vram[0x1800+row*32+col]&0x7f;
            putchar(c>=32 && c<127 ? c : '?');
        }
        putchar('\n');
    }
    GB_free(gb); GB_dealloc(gb);
    return done ? 0 : 4;
}
