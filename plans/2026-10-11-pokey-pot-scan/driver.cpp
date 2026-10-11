int main() {
    for (uint8 mode : {0, 3, 4, 7}) {
        for (uint32 phase : {0, 16, 57, 110}) {
            ATPokeyEmulator chip;
            chip.mSKCTL = mode;
            chip.mLast15KHzTime -= phase;
            chip.mPotLastTimeSlow -= phase;
            chip.StartPotScan();
            std::cout << "CASE " << unsigned(mode) << ' ' << phase;
            for (uint32 tick = 0; tick <= 26002; ++tick) {
                chip.scheduler.now = 1000 + tick;
                const auto pot = chip.ReadByte(0);
                for (uint8 i = 1; i < 8; ++i)
                    if (chip.ReadByte(i) != pot)
                        throw std::runtime_error("pot channel disagreement");
                std::cout << ' ' << unsigned(pot) << ':' << unsigned(chip.ReadByte(8));
            }
            std::cout << '\n';
        }
    }
}
