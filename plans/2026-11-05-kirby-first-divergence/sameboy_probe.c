#define GB_INTERNAL
#include <Core/gb.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static uint32_t pixels[160 * 144];
static unsigned frames;
static unsigned callbacks;
static int anchored;
static const char *out;
static uint8_t read_observer(GB_gameboy_t *gb, uint16_t addr, uint8_t value) {
    if (addr == 0xFF44 && gb->boot_rom_finished && getenv("KIRBY_LY_TRACE")) {
        static unsigned n;
        if (n < 32) fprintf(stderr, "LY %u pc=%04x value=%02x internal=%u\n", n++,gb->pc,value,gb->current_line);
    }
    if (addr == 0xFF04 && getenv("KIRBY_BUS_TRACE")) {
        fprintf(stderr, "DIV pc=%04x value=%02x counter=%04x ly=%02x boot=%d\n", gb->pc, value, gb->div_counter, gb->io_registers[GB_IO_LY], gb->boot_rom_finished);
    }
    return value;
}
static void cpu_observer(GB_gameboy_t *gb, uint16_t addr, uint8_t op) {
    static unsigned n;
    if (!gb->boot_rom_finished || !getenv("KIRBY_CPU_TRACE") || n >= 150000) return;
    fprintf(stderr, "CPU %u %04x %02x %04x %04x %04x %04x %04x ly=%02x div=%04x\n", n++,addr,op,gb->af,gb->bc,gb->de,gb->hl,gb->sp,gb->io_registers[GB_IO_LY],gb->div_counter);
}
static uint32_t gray(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) {
    (void)gb; (void)g; (void)b;
    if (r % 85) { fprintf(stderr, "unexpected gray %u\n", r); exit(2); }
    return (255-r)/85;
}
static void vblank(GB_gameboy_t *gb, GB_vblank_type_t type) {
    callbacks++;
    if (type != GB_VBLANK_TYPE_NORMAL_FRAME || !gb->boot_rom_finished) return;
    if (!anchored) { anchored = 1; frames = 0; return; }
    frames++;
    if (getenv("KIRBY_ALL_FIELDS") || frames == 240 || frames == 480 || frames == 720) {
        char path[1024];
        if (snprintf(path, sizeof(path), "%s-%u.gray", out, frames) >= (int)sizeof(path)) exit(2);
        FILE *file = fopen(path, "wb");
        if (!file) { perror(path); exit(2); }
        for (unsigned i = 0; i < 160*144; i++) {
            if (pixels[i] > 3 || fputc((int)pixels[i], file) == EOF) exit(2);
        }
        if (fclose(file)) exit(2);
        if (getenv("KIRBY_ALL_FIELDS")) {
            snprintf(path, sizeof(path), "%s-%u.mem", out, frames);
            file = fopen(path, "wb"); if (!file) exit(2);
            for (unsigned a = 0x8000; a < 0xA000; a++) if (fputc(gb->vram[a-0x8000],file)==EOF) exit(2);
            for (unsigned a = 0xC000; a < 0xE000; a++) if (fputc(gb->ram[a-0xC000],file)==EOF) exit(2);
            for (unsigned a = 0xFE00; a < 0xFEA0; a++) if (fputc(gb->oam[a-0xFE00],file)==EOF) exit(2);
            if (fclose(file)) exit(2);
        }
        printf("frame=%u callbacks=%u pc=%04x div=%02x\n", frames, callbacks, gb->pc, GB_safe_read_memory(gb, 0xFF04));
        fflush(stdout);
    }
}
int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "ROM BOOT OUTPUT_PREFIX\n"); return 2; }
    out = argv[3];
    GB_gameboy_t gb;
    GB_init(&gb, GB_MODEL_DMG_B);
    GB_set_rgb_encode_callback(&gb, gray);
    GB_set_palette(&gb, &GB_PALETTE_GREY);
    GB_set_pixels_output(&gb, pixels);
    GB_set_vblank_callback(&gb, vblank);
    GB_set_read_memory_callback(&gb, read_observer);
    GB_set_execution_callback(&gb, cpu_observer);
    if (GB_load_boot_rom(&gb, argv[2]) || GB_load_rom(&gb, argv[1])) return 2;
    uint64_t ticks = 0;
    while (frames < 720 && ticks < 8ULL * 1000 * 1000 * 120) ticks += GB_run(&gb);
    int result = frames == 720 ? 0 : 1;
    printf("frames=%u ticks_8mhz=%llu booted=%d\n", frames, (unsigned long long)ticks, gb.boot_rom_finished);
    GB_free(&gb);
    return result;
}
