// Own bounded scheduler/observers. Reference bodies are inserted separately.
#include <algorithm>
#include <limits>
#define ATLOGPOKEYTI(...) ((void)0)
struct Event { uint32 time = 0, type = 0; bool active = false; };
struct Scheduler {
    uint32 now = 1000;
    Event events[4];
    operator uint32() const { return now; }
    uint32 GetTick() const { return now; }
    Event* AddEvent(uint32 delay, void*, uint32 type) {
        if (!delay || type < 3 || type > 6) unsupported();
        auto& e = events[type - 3];
        if (e.active) unsupported();
        e = {now + delay, type, true};
        return &e;
    }
    void UnsetEvent(Event*& e) { if (e) { e->active = false; e = nullptr; } }
    uint32 GetTicksToEvent(Event* e) const {
        if (!e || !e->active || e->time < now) unsupported();
        return e->time - now;
    }
    void SetEvent(uint32, void*, uint32, Event*&) { unsupported(); }
    Event* next() {
        Event* found = nullptr;
        for (auto& event : events)
            if (event.active && (!found || event.time < found->time)) found = &event;
        return found;
    }
};
struct TimerRenderer {
    ATPokeyRenderer output;
    std::vector<std::pair<uint32, int>> events;
    void AddChannelEvent(int channel) {
        events.emplace_back(output.scheduler, channel);
        output.AddChannelEvent(channel);
    }
    void ClearChannelDeferredEvents(int, uint32) { unsupported(); }
    void SetChannelDeferredEvents(int, uint32, uint32) { unsupported(); }
    void SetChannelDeferredEventsLinked(int, uint32, uint32, uint32, uint32, uint32) { unsupported(); }
};
struct ATPokeyEmulator {
    Scheduler scheduler;
    Scheduler* mpScheduler = &scheduler;
    TimerRenderer renderer;
    TimerRenderer* mpRenderer = &renderer;
    bool mbFastTimer1 = false, mbFastTimer3 = false, mbLinkedTimers12 = false, mbLinkedTimers34 = false;
    bool mbUse15KHzClock = false, mbSerialWaitingForStartBit = false;
    bool mbSerialOutputState = false, mbSerClockPhase = false, mbNotifyBiClockChange = false;
    bool mbAllowDeferredTimer[4] {}, mbDeferredTimerEvents[4] {};
    uint8 mSKCTL = 3, mIRQEN = 7, mIRQST = 0xff, mAUDF[4] {};
    int mCounter[4] {1, 1, 1, 1}, mCounterBorrow[4] {};
    uint32 mTimerPeriod[4] {}, mTimerFullPeriod[2] {}, mDeferredTimerStarts[4] {}, mDeferredTimerPeriods[4] {};
    int mAUDFP1A[4] {1, 1, 1, 1}, mAUDFP1B[4] {1, 1, 1, 1};
    uint32 mAUDFP1Time[4] {}, mLast15KHzTime = 1000, mLast64KHzTime = 1000;
    int mSerialOutputCounter = 0;
    Event* mpTimerBorrowEvents[4] {};
    Event *mpEventResetTwoTones1 = nullptr, *mpEventResetTwoTones2 = nullptr, *mpEventSerialOutput = nullptr;
    void (*mpNotifyBiClockChangeFn)() = unsupported;
    std::vector<std::pair<uint32, uint8>> irqs;
    void AssertIrq(bool) { irqs.emplace_back(scheduler.now, mIRQST); }
    void OnSerialInputTick() { unsupported(); }
    template<int channel> void RecomputeTimerPeriod();
    template<int channel> void UpdateTimerCounter();
    template<uint8 channel> void FireTimer();
    template<unsigned channel> int GetAUDFP1(uint32) const;
    template<unsigned channel> int GetAUDFP1() const;
    uint32 UpdateLast15KHzTime();
    uint32 UpdateLast15KHzTime(uint32);
    uint32 UpdateLast64KHzTime();
    uint32 UpdateLast64KHzTime(uint32);
    void SetupTimers(uint8);
    void FlushDeferredTimerEvents(int);
    void SetupDeferredTimerEvents(int, uint32, uint32);
    void SetupDeferredTimerEventsLinked(int, uint32, uint32, uint32, uint32, uint32);
    void dispatch(uint32 event) {
        switch (event) {
            // BORROW_CASES
            default: unsupported();
        }
    }
};

// TIMER_METHODS

int main() {
    for (int pair = 0; pair < 2; ++pair)
    for (int linked = 0; linked < 2; ++linked)
    for (int mode = 0; mode < 3; ++mode)
    for (int low : {0, 1, 15, 255})
    for (int high : {0, 1, 2, 255})
    for (int phase_choice = 0; phase_choice < 3; ++phase_choice) {
        const int divisor = mode == 1 ? 114 : 28;
        const int phase = phase_choice == 0 ? 0 : phase_choice == 1 ? 1 : divisor - 1;
        const int lo = pair * 2, hi = lo + 1;
        ATPokeyEmulator p;
        p.scheduler.now += phase;
        const uint32 start = p.scheduler.now;
        p.mbUse15KHzClock = mode == 1;
        p.mbFastTimer1 = p.mbFastTimer3 = mode == 2;
        p.mbLinkedTimers12 = linked && pair == 0;
        p.mbLinkedTimers34 = linked && pair == 1;
        p.mAUDF[lo] = uint8(low); p.mAUDF[hi] = uint8(high);
        p.mCounter[lo] = p.mAUDFP1A[lo] = p.mAUDFP1B[lo] = low + 1;
        p.mCounter[hi] = p.mAUDFP1A[hi] = p.mAUDFP1B[hi] = high + 1;
        p.RecomputeTimerPeriod<0>(); p.RecomputeTimerPeriod<1>();
        p.RecomputeTimerPeriod<2>(); p.RecomputeTimerPeriod<3>();
        auto& r = p.renderer.output;
        r.scheduler = r.mLastFlushTime = start;
        r.target = hi;
        r.mRenderState.mAUDC[hi] = 0xa1;
        r.mChannelVolume[hi] = 1;
        r.mChannelVolMixIndex[hi] = 1;
        r.mNonZeroVolumeMask = uint8(1 << hi);
        r.UpdateOutput2(start * 2);
        p.SetupTimers(uint8(3 << lo));
        const uint32 firstLow = p.mpTimerBorrowEvents[lo]->time;
        const uint32 firstHigh = p.mpTimerBorrowEvents[hi]->time;
        int lowEvents = 0, highEvents = 0, dispatched = 0;
        // Complete the final timestamp, including another timer due on the
        // same clock; stopping after the first dispatch would truncate it.
        while (lowEvents < 4 || highEvents < 4 ||
               (p.scheduler.next() && p.scheduler.next()->time == p.scheduler.now)) {
            auto* event = p.scheduler.next();
            if (!event || ++dispatched > 200000) unsupported();
            const uint32 t = event->time, type = event->type;
            if (t < p.scheduler.now) unsupported();
            if (t > r.mLastFlushTime) r.Flush2(t);
            p.scheduler.now = r.scheduler = t;
            event->active = false;
            p.dispatch(type);
            p.mIRQST = 0xff;
            if (int(type) - 3 == lo) ++lowEvents;
            if (int(type) - 3 == hi) ++highEvents;
        }
        r.Flush2(p.scheduler.now + 3);
        std::printf("CASE %d %d %d %d %d %d %u %u %u %u %u", pair, linked, mode, low, high, phase, start, firstLow, firstHigh, p.mTimerPeriod[lo], p.mTimerPeriod[hi]);
        for (const auto& [time, channel] : p.renderer.events) std::printf(" E%u:%d", time, channel);
        for (const auto& [time, mask] : p.irqs) std::printf(" I%u:%u", time, unsigned(mask));
        for (const auto& [time, level] : r.changes) std::printf(" O%u:%u", time, unsigned(level));
        std::puts("");
    }
}
