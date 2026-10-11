// Own driver. Initial loaded count, observation horizon and CPU write ordering
// are supplied explicitly; the original reference performs both reset stages.
int main() {
    checkScheduler();
    for (int channel = 0; channel < 4; ++channel)
    for (int mode = 0; mode < 3; ++mode) {
        if (mode == 2 && (channel & 1)) continue;
        for (int audf : {0, 1, 15, 255})
        for (int offset = -6; offset <= 2; ++offset)
        for (int action = 0; action < 4; ++action) {
            ATPokeyEmulator p;
            p.mbUse15KHzClock = mode == 1;
            p.mbFastTimer1 = p.mbFastTimer3 = mode == 2;
            for (int c = 0; c < 4; ++c) {
                p.mAUDF[c] = 255;
                p.mCounter[c] = p.mAUDFP1A[c] = p.mAUDFP1B[c] = 256;
            }
            p.mAUDF[channel] = uint8(audf);
            p.mAUDFP1A[channel] = p.mAUDFP1B[channel] = audf + 1;
            p.mCounter[channel] = 32;
            p.RecomputeTimerPeriod<0>(); p.RecomputeTimerPeriod<1>();
            p.RecomputeTimerPeriod<2>(); p.RecomputeTimerPeriod<3>();
            p.SetupTimers(uint8(1 << channel));
            const uint32 first = p.mpTimerBorrowEvents[channel]->time;
            const uint32 write = first + offset;
            const uint32 end = first + 20 + 4 * p.mTimerPeriod[channel];
            std::vector<uint32> writes;
            if (action) writes.push_back(write);
            if (action >= 2) writes.push_back(write + action - 1);
            size_t writeIndex = 0;
            uint32 dispatched = 0;
            while (true) {
                auto* event = p.scheduler.next();
                const uint32 nextWrite = writeIndex < writes.size() ? writes[writeIndex] : end + 1;
                // Drain previously scheduled events before a supplied write at
                // that timestamp. No physical CPU bus phase is inferred.
                if (event && event->time <= end && event->time <= nextWrite) {
                    if (++dispatched > 200000 || event->time < p.scheduler.now) unsupported();
                    p.scheduler.now = p.renderer.output.scheduler = event->time;
                    const uint32 type = event->type;
                    event->active = false;
                    p.dispatch(type);
                    p.mIRQST = 0xff;
                } else if (nextWrite <= end) {
                    p.scheduler.now = p.renderer.output.scheduler = nextWrite;
                    p.writeStimer();
                    ++writeIndex;
                } else break;
            }
            if (writeIndex != writes.size()) unsupported();
            std::printf("CASE %d %d %d %d %d %u %u %u", channel, mode, audf, offset, action, first, write, end);
            for (const auto& [time, ch] : p.renderer.events)
                if (ch == channel) std::printf(" E%u:%d", time, ch);
            const uint8 mask = channel == 0 ? 254 : channel == 1 ? 253 : channel == 3 ? 251 : 0;
            for (const auto& [time, irq] : p.irqs)
                if (irq == mask) std::printf(" I%u:%u", time, unsigned(irq));
            for (uint32 time : p.renderer.resets) std::printf(" R%u", time);
            std::puts("");
        }
    }
}
