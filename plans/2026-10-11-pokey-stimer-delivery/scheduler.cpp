// Bounded scheduler scaffolding. FIFO equal-time insertion follows the pinned
// Altirra scheduler; stable slots cover only timer borrows and the two resets.
struct Event { uint32 time = 0, type = 0, sequence = 0; bool active = false; };
struct Scheduler {
    uint32 now = 1000, serial = 0;
    Event events[11];
    operator uint32() const { return now; }
    uint32 GetTick() const { return now; }
    Event* AddEvent(uint32 delay, void*, uint32 type) {
        if (!delay || delay >= 100000000 || delay > std::numeric_limits<uint32>::max() - now ||
            !((type >= 3 && type <= 6) || type == 9 || type == 10)) unsupported();
        auto& e = events[type];
        if (e.active) unsupported();
        e = {now + delay, type, ++serial, true};
        return &e;
    }
    void RemoveEvent(Event* e) {
        if (!e || !e->active) unsupported();
        e->active = false;
    }
    void UnsetEvent(Event*& e) { if (e) { RemoveEvent(e); e = nullptr; } }
    uint32 GetTicksToEvent(Event* e) const {
        if (!e || !e->active || e->time < now) unsupported();
        return e->time - now;
    }
    void SetEvent(uint32 delay, void* target, uint32 type, Event*& e) {
        UnsetEvent(e);
        e = AddEvent(delay, target, type);
    }
    Event* next() {
        Event* found = nullptr;
        for (auto& e : events)
            if (e.active && (!found || e.time < found->time ||
                (e.time == found->time && e.sequence < found->sequence))) found = &e;
        return found;
    }
};

void checkScheduler() {
    Scheduler s;
    auto* a = s.AddEvent(10, nullptr, 3);
    auto* b = s.AddEvent(10, nullptr, 9);
    if (s.next() != a || s.GetTicksToEvent(a) != 10)
        throw std::runtime_error("scheduler FIFO order mismatch");
    s.SetEvent(10, nullptr, 3, a);
    if (s.next() != b) throw std::runtime_error("scheduler replacement order mismatch");
    s.RemoveEvent(b);
    if (s.next() != a) unsupported();
    s.UnsetEvent(a);
    if (a || s.next()) unsupported();
    bool rejected = false;
    try { s.AddEvent(0, nullptr, 3); } catch (const std::runtime_error&) { rejected = true; }
    if (!rejected) unsupported();
}
