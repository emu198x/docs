#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint8 = uint8_t;
using uint32 = uint32_t;
using uint64 = uint64_t;
using sint32 = int32_t;
struct Scheduler {
    uint32 now = 1000;
    uint64 GetTick64() const { return now; }
};
#define ATSCHEDULER_GETTIME(p) ((p)->now)
// Original wrap-time struct and chip methods are inserted only in scratch.
/* WRAP */
class ATPokeyEmulator {
public:
    Scheduler scheduler;
    Scheduler *mpScheduler = &scheduler;
    uint8 mSKCTL = 0, mAddressMask = 15, mALLPOT = 0;
    uint8 mPotMasterCounter = 0, mPotGroundedMask = 255;
    bool mbPotScanActive = false;
    uint32 mPotLastTimeFast = 1000, mPotLastTimeSlow = 1000;
    uint32 mLast15KHzTime = 1000;
    uint64 mPotLastScanTime = 0;
    std::array<uint32, 8> mPotChargeLevels{}, mPotChargeRates{};
    std::array<uint8, 8> mPotLatches{};
    static constexpr uint32 kPotChargeThreshold = 0x40000000;
    static constexpr uint32 kPotChargeLimit = 0x96666666;
    static constexpr uint32 kPotDischargeRate = 0x03936c71;
    uint32 UpdateLast15KHzTime();
    uint32 UpdateLast15KHzTime(uint32);
    void StartPotScan();
    void UpdatePots(uint32);
    uint8 ReadByte(uint8);
};
