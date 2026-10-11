// Read-only LCD observer. No GateBoy chip stages are changed.
#include "GateBoyLib/GateBoy.h"
#include <cstdio>
#include <fstream>
#include <iterator>
#include <memory>

// Only discard host audio; the reference's sound chip continues to run.
void audio_post(int, short, short) {}

static bool write_frame(const char* path, const uint8_t* pixels) {
  FILE* file = fopen(path, "wb");
  if (!file) return false;
  const bool complete = fwrite(pixels, 1, 160 * 144, file) == 160 * 144;
  const bool closed = fclose(file) == 0;
  return complete && closed;
}

int main(int argc, char** argv) {
  if (argc != 4) return 2;
  std::ifstream input(argv[1], std::ios::binary);
  blob cart((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
  if (cart.empty()) return 3;
  auto gb = std::make_unique<GateBoy>();
  gb->reset();
  FILE* trace = fopen(argv[3], "w");
  if (!trace) return 5;
  fprintf(trace, "phase,ly,x,bg_enable,clock,hsync,data,pc,op\n");

  // Shift 159 pixels on CLK rising edges using the data before the edge.
  // CPL latches those pixels plus the current data-pin value. Use the LY
  // observed when pixels were clocked: LY can advance before CPL rises.
  uint8_t shifted[159] = {};
  uint8_t latched[160 * 144];
  memset(latched, 255, sizeof(latched));
  int previous_clock = 0, previous_data = 0, previous_cpl = 0, shifted_y = -1;
  bool hit = false;
  int after = 0;
  for (int phase = 0; phase < 10000000; phase++) {
    gb->next_phase(cart);
    const auto& state = gb->get_state();
    const auto& pins = gb->get_pins();
    const int y = bit_pack(state.reg_ly);
    const int x = bit_pack(state.pix_count) - 8;
    const int clock = bit0(pins.lcd.PIN_53_LCD_CLOCK.qp_ext_old());
    const int hsync = bit0(pins.lcd.PIN_54_LCD_HSYNC.qp_ext_old());
    const int cpl = bit0(pins.lcd.PIN_55_LCD_LATCH.qp_ext_old());
    const int data = 3 - (bit0(pins.lcd.PIN_51_LCD_DATA0.qp_ext_old())
                       + 2 * bit0(pins.lcd.PIN_50_LCD_DATA1.qp_ext_old()));
    if (clock && !previous_clock) {
      shifted_y = y;
      memmove(shifted, shifted + 1, 158);
      shifted[158] = previous_data;
    }
    if (cpl && !previous_cpl && shifted_y >= 0 && shifted_y < 144) {
      memcpy(latched + shifted_y * 160, shifted, 159);
      latched[shifted_y * 160 + 159] = data;
    }
    previous_clock = clock;
    previous_data = data;
    previous_cpl = cpl;
    if (y == 19 && x >= -8 && x < 16) {
      fprintf(trace, "%llu,%d,%d,%d,%d,%d,%d,%04x,%02x\n",
        (unsigned long long)gb->get_sys().gb_phase_total_old, y, x,
        bit0(state.reg_lcdc.VYXE_LCDC_BGENp.qp_old()), clock, hsync, data,
        gb->get_cpu().core.get_op_addr(), gb->get_cpu().core.get_op());
    }
    if (!hit && gb->get_cpu().core.get_op() == 0x40) {
      hit = true;
      fprintf(stderr, "marker phase=%d pc=%04x\n", phase, gb->get_cpu().core.get_op_addr());
    }
    if (hit && ++after >= 140448) break;
  }
  if (fclose(trace)) return 6;
  if (!hit) return 4;
  for (unsigned i = 0; i < sizeof(latched); i++) if (latched[i] > 3) return 7;
  const std::string latch_path = std::string(argv[2]) + ".lcd";
  if (!write_frame(argv[2], gb->get_mem().framebuffer)
      || !write_frame(latch_path.c_str(), latched)) return 8;
  return 0;
}
