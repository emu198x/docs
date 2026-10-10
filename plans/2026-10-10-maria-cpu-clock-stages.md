# MARIA variable CPU clock stages

Implement the clock portion of the approved native DMA design using the
108-case clock matrix and GCC1702B page 29. Keep source PR #1704 draft while
machine DMA, full peripheral timing, raster and physical NMI gates remain.

1. In `machine-atari-7800/src/lib.rs`, reproduce the fixed-divider fault with
   a real CPU loop that reads a slow peripheral and returns through ROM.
   Its seven CPU cycles take 60 native ticks (56 fast plus four for the slow
   access), not the current 56. Include fast RAM/MARIA/ROM controls and both
   TIA/RIOT slow addresses in both regions. Preserve failing output.
2. Add `atari-maria/src/clock.rs` with saved phase, remaining ticks, upcoming
   phase-2 divider choice and retained slow-access selection for the following
   phase 1. Expose address input and one-native-tick phase strobes on MARIA.
   `tick_clock` advances the clock portion only; final DMA integration will
   drive it from the complete native chip tick. No lookup schedule or second
   time counter is introduced.
3. Compare every strobe against all 108 independently captured vectors,
   including address changes at the selection/latch boundaries. Check exact
   case inventory and demonstrate a wrong-duration negative. Extend direct
   chip snapshots and the ongoing unreleased runtime v6 fields to preserve
   divider/phase/pins; compare resumed traces at every native phase.
4. Replace the machine CPU /8 test with MARIA's phase-1 strobe. Drive RIOT
   from phase 2, consistent with the reference wiring. Preserve CPU pin-based
   transactions. Full bus transaction phasing and DMA ownership follow in the
   next native-DMA slice; the current aggregate stalls remain temporary.
   TIA keeps its oscillator-derived clock. POKEY's fixed-rate tick currently
   also advances its host sampler; separating variable chip clocks from host
   sampling is a remaining integration gate, alongside tracked restore #1705.
   Do not silently slow its host sample stream by merely moving `tick()`.
5. Run machine/chip/runtime/frontend tests, real Asteroids, native-phase
   save/restore comparisons, Clippy, formatting and a deliberate timing
   mutation. Commit this stage only after the bounded checks pass; no merge
   or accuracy closure until the complete approved correction is validated.

This is an implementation slice of the already-approved MARIA clock/pipeline
and v6 boundary, not a new architecture or a separate release. The machine
still begins after BIOS with MARIA enabled; MEN transition/reset timing is not
claimed by these steady-clock probes.

## Implemented and verified

MARIA now exposes an address input and native-tick phase strobes. Its saved
divider retains both the upcoming phase-2 selection and the access latch that
extends the following phase 1. Every strobe matches all 108 captured vectors,
including asynchronous address changes at each of the twelve tested offsets.
The test compares the complete case inventory and every timestamp, not just
the set of observed cycle lengths. The initial phase is normalized to the
reference's preceding phase-1 edge; subsequent edges have no adjustment.

The CPU follows phase 1 and RIOT follows phase 2. The real CPU's seven-cycle
slow-access loop now takes 60 native ticks; TIA/RIOT cases failed at 56 before
the correction. Fast RAM, MARIA and ROM controls retain 56. Both regions pass.
A separate timer test observes each native tick with CPU RDY held low: RIOT
continues on phase 2 at the measured fast/slow rate while CPU execution remains
stopped. This isolates the clock wiring; WSYNC/DMA ownership still awaits the
complete native pipeline.

Direct saves preserve input/strobe pins and all divider fields. The runtime
keeps the ongoing, unreleased v6 layout. Direct continuation is checked at 48
successive native instants in both regions. Machine snapshots cover every
native tick in the 60-tick slow-access loop, then compare 600 ticks of CPU bus
activity, phase strobes, RIOT and TIA output against uninterrupted execution.
Every continuation executes ten loops (70 CPU cycles), so equal empty traces
cannot satisfy the test. Invalid direct-state countdowns leave the live chip
unchanged.

Validation: 85 package tests pass, plus the separate 200-frame Asteroids test.
Clippy with warnings denied and package formatting pass. A controlled change
from six to five ticks for stretched phases fails the independent vector gate;
the correct duration was restored before final checks. Original failure,
negative-control and passing outputs are in the adjacent evidence directory.

Remaining before merge: DMA ownership/startup/descriptor/shutdown wiring,
phase-2 bus transactions, variable-clock POKEY with independent host sampling,
raster/buffer handoff and physical NMI adjudication. TIA and the existing POKEY
host stream still use their prior oscillator-derived scheduling; this stage
does not claim that POKEY receives the newly variable PCLK. No issue is closed
by this intermediate commit.
