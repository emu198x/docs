// Own linked-pair reset driver. Original reference methods remain unchanged.
int main() {
    checkScheduler();
    for (int pair = 0; pair < 2; ++pair)
    for (int mode = 0; mode < 3; ++mode)
    for (int low : {0, 1, 15, 255})
    for (int high : {0, 1, 2, 255})
    for (int anchor = 0; anchor < 2; ++anchor)
    for (int offset = -6; offset <= 2; ++offset)
    for (int action = 0; action < 4; ++action) {
        const int lo = pair * 2, hi = lo + 1, target = lo + anchor;
        ATPokeyEmulator p;
        p.mbUse15KHzClock = mode == 1;
        p.mbFastTimer1 = p.mbFastTimer3 = mode == 2;
        p.mbLinkedTimers12 = pair == 0;
        p.mbLinkedTimers34 = pair == 1;
        for (int c = 0; c < 4; ++c) {
            const int value = c == lo ? low : c == hi ? high : 255;
            p.mAUDF[c] = uint8(value);
            p.mCounter[c] = p.mAUDFP1A[c] = p.mAUDFP1B[c] = value + 1;
        }
        p.RecomputeTimerPeriod<0>(); p.RecomputeTimerPeriod<1>();
        p.RecomputeTimerPeriod<2>(); p.RecomputeTimerPeriod<3>();
        auto& r = p.renderer.output;
        r.target = target;
        r.mRenderState.mAUDC[target] = 0xa1;
        r.mNonZeroVolumeMask = uint8(1 << target);
        r.mChannelVolume[target] = 1;
        r.mChannelVolMixIndex[target] = 1;
        r.UpdateOutput2(2000);
        p.SetupTimers(uint8(3 << lo));
        const uint32 firstLow = p.mpTimerBorrowEvents[lo]->time;
        const uint32 firstHigh = p.mpTimerBorrowEvents[hi]->time;
        const uint32 period = p.mTimerPeriod[hi];
        const uint32 write = (anchor ? firstHigh : firstLow) + period + offset;
        const uint32 end = write + 20 + 4 * period;
        std::vector<uint32> writes;
        if (action) writes.push_back(write);
        if (action >= 2) writes.push_back(write + action - 1);
        size_t writeIndex = 0;
        uint32 dispatched = 0;
        while (true) {
            auto* event = p.scheduler.next();
            const uint32 nextWrite = writeIndex < writes.size() ? writes[writeIndex] : end + 1;
            if (event && event->time <= end && event->time <= nextWrite) {
                if (++dispatched > 200000 || event->time < p.scheduler.now) unsupported();
                p.scheduler.now = r.scheduler = event->time;
                const uint32 type = event->type;
                event->active = false;
                p.dispatch(type);
                p.mIRQST = 0xff;
            } else if (nextWrite <= end) {
                p.scheduler.now = r.scheduler = nextWrite;
                p.writeStimer();
                ++writeIndex;
            } else break;
        }
        if (writeIndex != writes.size()) unsupported();
        r.Flush(end + 3);
        if (!r.mChangeQueue.empty()) unsupported();
        std::printf("CASE %d %d %d %d %d %d %d %u %u %u %u %u", pair, mode, low, high, anchor, offset, action, firstLow, firstHigh, period, write, end);
        for (const auto& [time, channel] : p.renderer.events)
            if (channel == lo || channel == hi) std::printf(" E%u:%d", time, channel);
        for (const auto& [time, mask] : p.irqs)
            if ((pair == 0 && (mask == 254 || mask == 253)) || (pair == 1 && mask == 251)) std::printf(" I%u:%u", time, unsigned(mask));
        for (uint32 time : p.renderer.resets) std::printf(" R%u", time);
        for (const auto& [time, level] : r.changes) std::printf(" O%u:%u", time, unsigned(level));
        std::puts("");
    }
}
