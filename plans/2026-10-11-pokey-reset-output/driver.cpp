// Own supplied-event driver. A renderer reset at 1016 is not a CPU STIMER write.
int main() {
    for (int channel = 0; channel < 4; ++channel)
    for (int filter = 0; filter < (channel < 2 ? 3 : 1); ++filter)
    for (int previous = 0; previous < 2; ++previous)
    for (int volume = 0; volume < 2; ++volume)
    for (int offset : {-4, -3, -2, -1, 0, 1, 2, 3, 4, 99})
    for (int partition : {1, 7, 64}) {
        ATPokeyRenderer r;
        r.target = channel;
        r.mNoiseFlipFlops = uint8(previous << channel);
        const int latch = channel < 2 && filter != 1;
        r.mChannelOutputMask = r.mNoiseFlipFlops | 0x30;
        if (channel < 2 && !latch) r.mChannelOutputMask &= uint8(~(0x10 << channel));
        r.mRenderState.mAUDCTL = filter ? uint8(4 >> channel) : 0;
        r.mRenderState.mAUDC[channel] = volume ? 0xb1 : 0xa1;
        r.mVolumeOnlyMask = uint8(volume << channel);
        r.mNonZeroVolumeMask = uint8(1 << channel);
        r.mChannelVolume[channel] = 1;
        r.mChannelVolMixIndex[channel] = 1;
        r.UpdateOutput2(2000);
        int events = 0, resets = 0;
        for (uint32 t = 1000; t <= 1064; ++t) {
            if (t > 1000 && ((t - 1000) % partition == 0 || t == 1064)) r.Flush(t);
            r.scheduler = t;
            if (t == 1016) { r.ResetTimers(); ++resets; }
            if (offset != 99 && int(t) == 1016 + offset) { r.AddChannelEvent(channel); ++events; }
        }
        if (resets != 1 || events != int(offset != 99) || !r.mChangeQueue.empty() || r.mLastFlushTime != 1064) unsupported();
        for (int c = 0; c < 4; ++c)
            if (r.mChannelEdgeBases[c] != r.mChannelEdges[c].size()) unsupported();
        std::printf("CASE %d %d %d %d %d %d %d %d %d", channel, filter, previous, volume, offset, partition, events,
            int((r.mNoiseFlipFlops >> channel) & 1), channel < 2 ? int((r.mChannelOutputMask >> (channel + 4)) & 1) : 0);
        for (const auto& [time, level] : r.changes) std::printf(" %u:%u", time, unsigned(level));
        std::puts("");
    }
}
