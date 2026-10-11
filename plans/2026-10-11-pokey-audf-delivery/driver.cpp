// Own driver; original AUDF write cases and timer methods are inserted separately.
int main() {
    for (int channel = 0; channel < 4; ++channel)
    for (int mode = 0; mode < 3; ++mode) {
        if (mode == 2 && (channel & 1)) continue;
        for (int oldValue : {0, 1, 15, 255})
        for (int newValue : {0, 1, 15, 255})
        for (int offset : {-3, -2, -1}) {
            ATPokeyEmulator p;
            p.mbUse15KHzClock = mode == 1;
            p.mbFastTimer1 = p.mbFastTimer3 = mode == 2;
            p.mAUDF[channel] = uint8(oldValue);
            p.mCounter[channel] = p.mAUDFP1A[channel] = p.mAUDFP1B[channel] = oldValue + 1;
            p.RecomputeTimerPeriod<0>(); p.RecomputeTimerPeriod<1>();
            p.RecomputeTimerPeriod<2>(); p.RecomputeTimerPeriod<3>();
            auto& r = p.renderer.output;
            r.target = channel;
            r.mRenderState.mAUDC[channel] = 0xa1;
            r.mChannelVolume[channel] = 1;
            r.mChannelVolMixIndex[channel] = 1;
            r.mNonZeroVolumeMask = uint8(1 << channel);
            r.UpdateOutput2(2000);
            p.SetupTimers(uint8(1 << channel));
            const uint32 first = p.mpTimerBorrowEvents[channel]->time;
            const uint32 writeTime = first + offset;
            r.Flush2(writeTime);
            p.scheduler.now = r.scheduler = writeTime;
            p.writeAudf(uint8(channel * 2), uint8(newValue));
            for (int n = 0; n < 4; ++n) {
                auto* event = p.scheduler.next();
                if (!event || event->time < p.scheduler.now) unsupported();
                const uint32 time = event->time, type = event->type;
                r.Flush2(time);
                p.scheduler.now = r.scheduler = time;
                event->active = false;
                p.dispatch(type);
                p.mIRQST = 0xff;
            }
            r.Flush2(p.scheduler.now + 3);
            std::printf("CASE %d %d %d %d %d %u", channel, mode, oldValue, newValue, offset, writeTime);
            for (const auto& [time, ch] : p.renderer.events) std::printf(" E%u:%d", time, ch);
            for (const auto& [time, mask] : p.irqs) std::printf(" I%u:%u", time, unsigned(mask));
            for (const auto& [time, level] : r.changes) std::printf(" O%u:%u", time, unsigned(level));
            std::puts("");
        }
    }
}
