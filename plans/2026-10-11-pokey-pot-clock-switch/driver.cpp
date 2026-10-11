int main() {
    for (uint8 old_mode : {0, 3, 4, 7})
    for (uint8 new_mode : {0, 3, 4, 7})
    for (uint32 phase : {0, 57, 110})
    for (uint32 change : {16, 64, 128}) {
        ATPokeyEmulator chip;
        chip.mSKCTL = old_mode;
        chip.mLast15KHzTime -= phase;
        chip.mPotLastTimeSlow -= phase;
        chip.StartPotScan();
        std::cout << "CASE " << unsigned(old_mode) << ' ' << unsigned(new_mode)
                  << ' ' << phase << ' ' << change;
        for (uint32 tick = 0; tick <= 27002; ++tick) {
            chip.scheduler.now = 1000 + tick;
            if (tick == change) chip.WriteByte(15, new_mode);
            const auto pot = chip.ReadByte(0);
            for (uint8 i = 1; i < 8; ++i)
                if (chip.ReadByte(i) != pot)
                    throw std::runtime_error("pot channel disagreement");
            std::cout << ' ' << unsigned(pot) << ':' << unsigned(chip.ReadByte(8))
                      << ':' << unsigned(chip.mPotMasterCounter) << ':' << chip.mbPotScanActive;
        }
        std::cout << '\n';
    }
}
