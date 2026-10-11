    // Non-pot subsystems are observers in this isolated register-path harness.
    // Their callbacks neither advance time nor modify the pot/base-clock state.
    struct Renderer { void SetInitMode(bool) {} } renderer;
    Renderer *mpRenderer = &renderer;
    struct Cassette { void PokeyResetSerialInput() { throw std::runtime_error("cassette callback"); } };
    Cassette *mpCassette = nullptr;
    bool mbSerialWaitingForStartBit = false, mbSerialRateChanged = false;
    bool mbSerClockPhase = false, mbSerOutValid = false, mbSerShiftValid = false;
    bool mbSerInBurstPendingData = false, mbSerInBurstPendingIRQ1 = false, mbSerInBurstPendingIRQ2 = false;
    bool mbNotifyBiClockChange = false, mb5200Mode = true, mbKeyboardScanEnabled = false;
    bool mbShiftKeyState = false, mbControlKeyState = false;
    uint32 mCounter[4]{}, mKeyMatrix[8]{};
    uint32 mLast64KHzTime = 1000, mLastPolyTime = 1000;
    uint32 mPoly9Counter = 0, mPoly17Counter = 0;
    uint64 mPolyShutOffTime = 0;
    uint32 mSerialInputShiftRegister = 0, mSerialOutputShiftRegister = 0;
    uint32 mSerialOutputCounter = 0, mSerialInputCounter = 0;
    uint32 mSerOutBurstDeadline = 0, mSerialInputResetCounter = 0;
    uint8 mSKSTAT = 255, mIRQST = 255, mIRQEN = 0;
    uint8 mKeyScanState = 0, mKeyScanCode = 0, mKBCODE = 0;
    int mpKeyboardScanEvent = 0, mpKeyboardIRQEvent = 0;
    template<unsigned I> void UpdateTimerCounter() { static_assert(I < 4); }
    template<unsigned I> uint32 GetAUDFP1() { throw std::runtime_error("serial counter reload"); }
    void NegateIrq(bool) {}
    void AssertIrq(bool) { throw std::runtime_error("unexpected IRQ"); }
    void mpNotifyBiClockChangeFn() { throw std::runtime_error("bidirectional callback"); }
    void QueueKeyboardIRQ() { throw std::runtime_error("keyboard IRQ"); }
    void UpdateKeyboardScanEvent() {}
    void RecomputeAllowedDeferredTimers() {}
    void SetupTimers(unsigned) {}
    bool IsSerialOutputClockRunning() { return true; }
    void FlushSerialOutput() { throw std::runtime_error("serial output"); }
    void NotifyForceBreak() { throw std::runtime_error("break callback"); }
    void WriteByte(uint8 reg, uint8 value);
