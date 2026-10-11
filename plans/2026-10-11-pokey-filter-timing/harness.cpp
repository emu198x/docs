// Portable scaffolding only. Reference methods are extracted at run time.
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <utility>
#include <vector>
using uint8 = uint8_t;
using uint16 = uint16_t;
using uint32 = uint32_t;
using sint32 = int32_t;
using uintptr = uintptr_t;
#define VDRESTRICT
#define VDASSERT(x) assert(x)
#define VDFromLE32(x) (x)
#define ATSCHEDULER_GETTIME(p) (*(p))
static_assert(std::endian::native == std::endian::little);
[[noreturn]] void unsupported() { throw std::runtime_error("unsupported reference path"); }
struct DisabledLog {
    bool IsEnabled() const { return false; }
    template<typename... T> void operator()(const char*, T...) const {}
} g_ATLCPokeyTEv;
struct ATPokeyRenderer {
    using ChannelEdges = std::vector<uint32>;
    using FireTimerRoutine = std::pair<uint32*, const uint32*>
        (ATPokeyRenderer::*)(uint32*, const uint32*, uint32, uint32);
    template<int channel, bool poly9> static const FireTimerRoutine kFireRoutines[2][16];
    template<int channel, uint8 mode, bool affects, bool poly9>
    std::pair<uint32*, const uint32*> FireTimer(uint32*, const uint32*, uint32, uint32);
    template<int channel> FireTimerRoutine GetFireTimerRoutine() const;
    FireTimerRoutine GetFireTimerRoutine(int) const;
    void AddChannelEvent(int);
    void Flush2(uint32);
    static void MergeOutputEvents(const uint32*, const uint32*, uint32*);
    void ProcessOutputEdges(uint32, const uint32*, uint32);
    void FlushDeferredEvents(int, uint32) { unsupported(); }
    void LogOutputChange(uint32) { unsupported(); }
    void LogOutputEdges(uint32, const uint32*, uint32) { unsupported(); }
    struct { bool mbEnabled = false; } mDeferredEvents[4];
    struct {
        uintptr mPoly4Offset = 0, mPoly5Offset = 0, mPoly9Offset = 0, mPoly17Offset = 0;
        uint32 mPoly4Counter = 0, mPoly5Counter = 0, mPoly9Counter = 0, mPoly17Counter = 0;
        void UpdatePoly4Counter(uint32) { unsupported(); }
        void UpdatePoly5Counter(uint32) { unsupported(); }
        void UpdatePoly9Counter(uint32) { unsupported(); }
        void UpdatePoly17Counter(uint32) { unsupported(); }
    } mPolyState;
    struct Tables { uint8 mInitModeBuffer[256] {}, mPolyBuffer[256] {}; } tables;
    Tables* mpTables = &tables;
    bool mbInitMode = true;
    uint32 scheduler = 1000;
    uint32* mpScheduler = &scheduler;
    void* mpAudioLog = nullptr;
    struct { uint8 mAUDCTL = 0, mAUDC[4] {0xa0, 0xa0, 0xa0, 0xa0}; } mRenderState;
    uint8 mNoiseFlipFlops = 0, mChannelOutputMask = 0x30;
    uint8 mVolumeOnlyMask = 0, mNonZeroVolumeMask = 0;
    uint8 mChannelVolume[4] {};
    uint32 mChannelVolMixIndex[4] {};
    uint32 mLastFlushTime = 1000;
    uint32 mChannelEdgeBases[4] {};
    ChannelEdges mChannelEdges[4], mSortedEdgesTemp[4], mSortedEdgesTemp2[2];
    ChannelEdges mSortedEdgesHpTemp1, mSortedEdgesHpTemp2, mSortedEdges;
    int target = 0;
    uint32 calls = 0;
    std::vector<std::pair<uint32, uint16>> changes;
    void UpdateOutput2(uint32 time, uint16 level) {
        if (level > 1 || (!changes.empty() && time < changes.back().first)) unsupported();
        ++calls;
        // Keep the settled level at a timestamp; a zero-width intermediate
        // transition contributes no digital pulse area.
        if (!changes.empty() && time == changes.back().first) {
            changes.back().second = level;
            if (changes.size() > 1 && changes[changes.size() - 2].second == level) changes.pop_back();
            return;
        }
        if (changes.empty() || changes.back().second != level) changes.emplace_back(time, level);
    }
    void UpdateOutput2(uint32 time) {
        const uint8 bit = uint8(1 << target);
        const bool level = (mVolumeOnlyMask & bit) ||
            (((mChannelOutputMask ^ (mChannelOutputMask >> 4)) & bit) != 0);
        UpdateOutput2(time, uint16(level));
    }
};

// REFERENCE_METHODS

int main() {
    for (int pair = 0; pair < 2; ++pair)
    for (int phase = -4; phase <= 4; ++phase)
    for (int previous = 0; previous < 2; ++previous)
    for (int filter = 0; filter < 3; ++filter)
    for (int volume = 0; volume < 2; ++volume)
    for (int partition : {1, 7, 120}) {
        ATPokeyRenderer r;
        r.target = pair;
        r.mNoiseFlipFlops = uint8(previous << pair);
        const int latch = filter == 1 ? 0 : 1;
        r.mChannelOutputMask = r.mNoiseFlipFlops | uint8((0x30 & ~(0x10 << pair)) | (latch << (4 + pair)));
        r.mRenderState.mAUDCTL = filter ? uint8(4 >> pair) : 0;
        r.mRenderState.mAUDC[pair] = volume ? 0xb1 : 0xa1;
        r.mVolumeOnlyMask = uint8(volume << pair);
        r.mNonZeroVolumeMask = uint8(1 << pair);
        r.mChannelVolume[pair] = 1;
        r.mChannelVolMixIndex[pair] = 1; // Actual volume-1 mix index, other channels muted.
        r.UpdateOutput2(2000);
        uint32 events = 0;
        for (uint32 t = 1000; t <= 1120; ++t) {
            // Flush first: events at t belong to the next half-open interval.
            if (t > 1000 && ((t - 1000) % partition == 0 || t == 1120)) r.Flush2(t);
            for (int j = 0; j < 6; ++j) {
                const int low = 1010 + j * 16;
                if (int(t) == low || int(t) == low + phase) {
                    r.scheduler = t;
                    if (int(t) == low) { r.AddChannelEvent(pair); ++events; }
                    if (int(t) == low + phase) { r.AddChannelEvent(pair + 2); ++events; }
                }
            }
        }
        if (events != 12 || r.mLastFlushTime != 1120) unsupported();
        for (int channel = 0; channel < 4; ++channel)
            if (r.mChannelEdges[channel].size() != r.mChannelEdgeBases[channel]) unsupported();
        std::printf("CASE %d %d %d %d %d %d %u %u", pair, phase, previous, filter, volume, partition, events, r.calls);
        for (const auto& [time, level] : r.changes) std::printf(" %u:%u", time, unsigned(level));
        std::puts("");
    }
}
