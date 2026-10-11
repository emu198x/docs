#include <set>
int main() {
    for (uint8 mode : {0, 3, 4, 7})
    for (uint32 phase : {0, 57, 110})
    for (uint32 duration : {8, 128, 1024, 25992})
    for (uint32 initial : {0, 1})
    for (uint32 restart : {64, 512, 27000}) {
        ATPokeyEmulator chip;
        chip.mSKCTL = mode;
        chip.mLast15KHzTime -= phase;
        chip.mPotLastTimeSlow -= phase;
        chip.mPotGroundedMask = 0;
        chip.mPotChargeRates.fill(chip.kPotChargeThreshold / duration);
        chip.mPotChargeLevels.fill(initial ? chip.kPotChargeThreshold + 100 : 0);
        chip.mPotLatches.fill(42);
        chip.StartPotScan();
        std::set<uint32> samples{restart - 1, restart, restart + 1};
        for (uint32 offset : {0, 1, 2, 3, 4, 7, 8, 9, 15, 63, 64, 65,
                              127, 128, 129, 230, 231, 232, 511, 512, 513,
                              1023, 1024, 1025, 25991, 25992, 25993, 26002, 27000, 27002}) {
            samples.insert(offset);
            samples.insert(restart + offset);
        }
        auto observe = [&](uint32 tick, unsigned after) {
            const auto pot = chip.ReadByte(0);
            for (uint8 i = 1; i < 8; ++i)
                if (chip.ReadByte(i) != pot || chip.mPotChargeLevels[i] != chip.mPotChargeLevels[0])
                    throw std::runtime_error("pot channel disagreement");
            std::cout << unsigned(mode) << ' ' << phase << ' ' << duration << ' '
                      << initial << ' ' << restart << ' ' << tick << ' ' << after << ' '
                      << unsigned(pot) << ' ' << unsigned(chip.ReadByte(8)) << ' '
                      << unsigned(chip.mPotMasterCounter) << ' ' << chip.mbPotScanActive << ' '
                      << chip.mPotChargeLevels[0] << '\n';
        };
        for (uint32 tick = 0; tick <= restart + 27002; ++tick) {
            chip.scheduler.now = 1000 + tick;
            chip.UpdatePots(0);
            if (samples.contains(tick)) observe(tick, 0);
            if (tick == restart) {
                chip.StartPotScan();
                observe(tick, 1);
            }
        }
    }
}
