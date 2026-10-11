#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "/private/tmp/198x-gb-blargg-evidence/SameBoy/Core/gb.h"
static uint32_t rgb(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) {
    (void)gb; return 0xff000000u | ((uint32_t)r<<16) | ((uint32_t)g<<8) | b;
}
static unsigned trace_frame;
static unsigned logged;
static bool guard_report;
static unsigned guarded_writes;
static bool trace_write(GB_gameboy_t *gb, uint16_t address, uint8_t data) {
    if ((address >= 0xa000 && address <= 0xa003) || (address >= 0xbff0 && address < 0xc010)) {
        if (logged++ < 128) fprintf(stderr,"WRITE frame=%u pc=%04x sp=%04x addr=%04x data=%02x\n",trace_frame,GB_get_registers(gb)->pc,GB_get_registers(gb)->sp,address,data);
    }
    uint16_t pc=GB_get_registers(gb)->pc;
    // Controlled fixture experiment only: suppress out-of-range stores from
    // the pinned standalone-7 reporting routine, never from the OAM test.
    if (guard_report && (pc==0xc3f4 || pc==0xc3ff) && (address<0xa004 || address>0xbfff)) {
        guarded_writes++;
        return false;
    }
    return true;
}
int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) return 2;
    guard_report=argc==5 && strcmp(argv[4],"guard-report")==0;
    GB_gameboy_t *gb = GB_init(GB_alloc(), strcmp(argv[1], "cgb") == 0 ? GB_MODEL_CGB_E : GB_MODEL_DMG_B);
    if (!gb || GB_load_boot_rom(gb, argv[2]) || GB_load_rom(gb, argv[3])) return 3;
    uint32_t pixels[256*224];
    GB_set_rgb_encode_callback(gb, rgb);
    GB_set_pixels_output(gb, pixels);
    GB_set_turbo_mode(gb, true, true);
    GB_debugger_set_disabled(gb, true);
    GB_set_write_memory_callback(gb, trace_write);
    int done = 0;
    unsigned previous = 0;
    for (unsigned frame=1; frame<=3600; frame++) {
        trace_frame=frame;
        GB_run_frame(gb);
        size_t size=0;
        const uint8_t *ram=GB_get_direct_access(gb, GB_DIRECT_ACCESS_CART_RAM, &size, NULL);
        if (size>=4) {
            unsigned signature=ram[0] | ram[1]<<8 | ram[2]<<16 | ram[3]<<24;
            if (signature!=previous || frame%500==0) fprintf(stderr,"STATE frame=%u pc=%04x sp=%04x ram=%08x\n",frame,GB_get_registers(gb)->pc,GB_get_registers(gb)->sp,signature);
            previous=signature;
        }
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
    fprintf(stderr,"guard_report=%d suppressed_report_writes=%u\n",guard_report,guarded_writes);
    GB_free(gb); GB_dealloc(gb);
    return done ? 0 : 4;
}
