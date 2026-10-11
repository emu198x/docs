#include <set>
int main() {
    for (uint8 mode : {0, 3, 4, 7})
    for (uint32 phase : {0, 57})
    for (uint32 position : {64, 200})
    for (uint32 action : {0, 1, 2, 3, 4})
    for (uint32 change : {64, 8192, 27000})
    for (unsigned selected = 0; selected < 8; ++selected) {
        ATPokeyEmulator chip;
        chip.mSKCTL = mode;
        chip.mLast15KHzTime -= phase;
        chip.mPotLastTimeSlow -= phase;
        chip.mPotLatches.fill(42);
        for (unsigned i = 0; i < 8; ++i) chip.SetPotPosHires(i, position << 16);
        chip.StartPotScan();
        std::set<uint32> samples{change - 1, change, change + 1, change + 63, change + 64, change + 65};
        for (uint32 offset : {0, 1, 2, 3, 64, 114, 230, 231, 232, 1024, 8192, 25992, 26002, 27002}) {
            samples.insert(offset);
            samples.insert(change + offset);
        }
        auto observe = [&](uint32 tick, unsigned after) {
            unsigned other = (selected + 1) % 8;
            auto value = chip.ReadByte(selected);
            auto control = chip.ReadByte(other);
            for (unsigned i = 0; i < 8; ++i)
                if (i != selected && (chip.ReadByte(i) != control || chip.mPotChargeLevels[i] != chip.mPotChargeLevels[other]))
                    throw std::runtime_error("untouched channel disagreement");
            std::cout << unsigned(mode) << ' ' << phase << ' ' << position << ' '
                      << action << ' ' << change << ' ' << selected << ' ' << tick << ' ' << after << ' '
                      << unsigned(value) << ' ' << unsigned(control) << ' ' << unsigned(chip.ReadByte(8)) << ' '
                      << unsigned(chip.mPotMasterCounter) << ' ' << chip.mbPotScanActive << ' '
                      << chip.mPotChargeLevels[selected] << ' ' << chip.mPotChargeLevels[other] << '\n';
        };
        for (uint32 tick = 0; tick <= change + 27002; ++tick) {
            chip.scheduler.now = 1000 + tick;
            chip.UpdatePots(0);
            if (samples.contains(tick)) observe(tick, 0);
            if (tick == change) {
                int next = position << 16;
                if (action == 1) next = 1 << 16;
                if (action == 2) next = 200 << 16;
                if (action == 3) next = chip.kPotHiPosGrounded;
                if (action == 4) next = chip.kPotHiPosUnconnected;
                chip.SetPotPosHires(selected, next);
                observe(tick, 1);
            }
            if (tick == change + 64 && action >= 3) {
                chip.SetPotPosHires(selected, position << 16);
                observe(tick, 1);
            }
        }
    }
}
