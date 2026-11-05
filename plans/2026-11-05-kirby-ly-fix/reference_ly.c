#define GB_INTERNAL
#include <Core/gb.h>
#include <assert.h>
#include <stdio.h>

static uint32_t pixels[160 * 144];
static uint32_t rgb(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) {
    (void)gb; return ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}
int main(void) {
    GB_gameboy_t gb;
    GB_init(&gb, GB_MODEL_DMG_B);
    GB_set_rgb_encode_callback(&gb, rgb);
    GB_set_pixels_output(&gb, pixels);
    GB_write_memory(&gb, 0xFF40, 0x91);
    unsigned start = 0, end = 0, next = 0;
    unsigned previous = gb.io_registers[GB_IO_LY];
    for (unsigned dot = 1; dot < 80000; dot++) {
        // GB_display_run takes 8MHz units; two units are one LCD dot.
        GB_display_run(&gb, 2, true);
        unsigned ly = gb.io_registers[GB_IO_LY];
        unsigned mode = gb.io_registers[GB_IO_STAT] & 3;
        if (ly == 153 && previous != 153 && !start) {
            start = dot;
            printf("{\"event\":\"ly_153\",\"dot\":%u,\"mode\":%u}\n", dot, mode);
            assert(mode == 1);
        }
        if (start && !end && ly == 0) {
            end = dot;
            printf("{\"event\":\"ly_zero\",\"dot\":%u,\"mode\":%u,\"ly_153_duration\":%u}\n",dot,mode,end-start);
            assert(mode == 1 && end-start == 4);
        }
        if (end && mode == 2) {
            next = dot;
            printf("{\"event\":\"next_mode_2\",\"dot\":%u,\"mode\":%u,\"zero_during_vblank\":%u}\n",dot,mode,next-end);
            break;
        }
        previous = ly;
    }
    assert(start && end && next);
    GB_free(&gb);
    return 0;
}
