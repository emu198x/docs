int main() {
    unsigned case_index = 0;
    for (uint8 old_mode : {0, 3, 4, 7})
    for (uint8 new_mode : {0, 3, 4, 7})
    for (uint32 phase : {0, 57})
    for (uint32 change : {64, 128})
    for (unsigned action : {0, 1, 2})
    for (unsigned charged : {0, 1})
    for (unsigned order : {0, 1}) {
        const unsigned selected = case_index++ % 8;
        ATPokeyEmulator chip;
        chip.mSKCTL = old_mode;
        chip.mLast15KHzTime -= phase;
        chip.mPotLastTimeSlow -= phase;
        chip.mPotLatches.fill(42);
        chip.SetPotPosHires(selected, 64 << 16);
        chip.mPotChargeLevels[selected] = charged ? chip.kPotChargeThreshold + 100 : 0;
        chip.StartPotScan();
        auto input = [&]() {
            const int position = action == 0 ? 1 << 16 :
                action == 1 ? chip.kPotHiPosGrounded : chip.kPotHiPosUnconnected;
            chip.SetPotPosHires(selected, position);
        };
        auto observe = [&](uint32 tick, unsigned after) {
            const auto pot = chip.ReadByte(selected);
            const auto other = chip.ReadByte((selected + 1) % 8);
            for (unsigned i = 0; i < 8; ++i)
                if (i != selected && chip.ReadByte(i) != other)
                    throw std::runtime_error("untouched channel disagreement");
            std::cout << unsigned(old_mode) << ' ' << unsigned(new_mode) << ' ' << phase << ' '
                      << change << ' ' << action << ' ' << charged << ' ' << order << ' ' << selected << ' '
                      << tick << ' ' << after << ' ' << unsigned(pot) << ' ' << unsigned(other) << ' '
                      << unsigned(chip.ReadByte(8)) << ' ' << unsigned(chip.mPotMasterCounter) << ' '
                      << chip.mbPotScanActive << ' ' << chip.mPotChargeLevels[selected] << '\n';
        };
        for (uint32 tick = 0; tick <= change + 27000; ++tick) {
            chip.scheduler.now = 1000 + tick;
            chip.UpdatePots(0);
            if (tick == change) {
                observe(tick, 0);
                if (order == 0) {
                    input(); chip.WriteByte(15, new_mode);
                } else {
                    chip.WriteByte(15, new_mode); input();
                }
                observe(tick, 1);
            }
            if (tick == change + 1 || tick == change + 2 || tick == change + 3 ||
                tick == change + 114 || tick == change + 27000) observe(tick, 0);
        }
    }
}
