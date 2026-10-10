# Atari 7800 CPU bus phases before DMA handoff

Move CPU memory transactions to their bus phase before replacing MARIA's
aggregate DMA stalls. The approved native-DMA design already covers saved
pending transactions, CPU pin wiring and WSYNC-independent interrupt sampling.
This stage keeps the same unmerged runtime v6 boundary.

1. Reproduce four faults in `machine-atari-7800/src/lib.rs`: writes take effect
   on phase 1, reads sample before phase 2, WSYNC prevents NMI edge detection,
   and WSYNC stalls the second write of an NMOS read-modify-write instruction.
   Preserve failing real-CPU regressions with fast/slow clock controls.
2. CPU phase 1 advances the existing pin-based CPU state. Store whether that
   bus cycle is active; phase 2 samples memory or commits the pending write.
   Preserve this flag through serde in the ongoing v6 layout. RIOT remains
   phase-2 clocked. Reference wiring uses phase 1 for Sally execution and
   phase 2 for peripheral/cart writes; GCC1702B page 29 gives the address/data
   windows. No CPU callback or second time loop is introduced.
3. Wire WSYNC to CPU RDY during CPU-owned slots. RDY holds reads, leaves NMOS
   writes running, and keeps the existing CPU NMI detector clocked. Leave the
   current line-release point until native raster/ownership wiring replaces
   it; this stage does not claim correct horizontal WSYNC release timing.
4. Snapshot between address presentation and the phase-2 access. Prove restored
   writes occur at the same phase and reads see the same subsequent memory
   changes. Compare actual CPU/RAM/RIOT/TIA continuation, not state bytes alone.
5. Run the focused red/green tests, affected packages, Asteroids, Clippy and
   formatting; retain reference clock/fetch gates. Commit before moving on to
   timed DMA ownership. PR #1704 remains draft and issue #197 stays open.

The aggregate-DMA path remains a known limitation: it still renders the list
in bulk at a line boundary. Native startup/descriptor/shutdown stages must
replace it before the complete correction can merge. POKEY host sampling and
physical NMI phase/width remain the previously recorded gates.

## Implemented and verified

CPU phase 1 now advances the CPU and presents its pins; phase 2 performs the
pending memory transaction. The machine saves whether that bus cycle is
active, including the initial reset read. This separates a CPU clock edge from
the read/write effect that the upcoming DMA ownership stages must arbitrate.

WSYNC drives CPU RDY during CPU-owned slots. Read cycles stop advancing while
the existing CPU NMI edge detector continues to sample assertion and release.
NMOS writes continue, including the dummy and final writes of `INC WSYNC`.
The existing aggregate DMA slots still stop CPU execution separately; the
native HALT/Sally-release path remains to be implemented.

All four regressions failed before implementation:

- A RAM write had already stored 90 (`0x5a`) during phase 1, when RAM should
  still contain zero until phase 2.
- A read followed by a store retained 17 (`0x11`) instead of a live update to
  119 (`0x77`) made after address presentation.
- WSYNC prevented the CPU from observing an NMI edge.
- The two `INC WSYNC` writes were separated by 832 native ticks instead of 8.

All four pass afterward. Snapshot tests cover every native tick between
address presentation and the phase-2 transaction, with RAM and RIOT targets
in both regions. Restored writes occur at the same tick; restored reads sample
the same subsequent RAM/port-input update and carry it through a real CPU
store. Existing slow-clock, timer and TIA continuation checks remain green.

Validation: 91 package tests, including the 108 clock vectors and 64 fetch
vectors; the separate 200-frame Asteroids smoke; Clippy with warnings denied;
package formatting and diff checks. Original failing output and final checks
are in the adjacent evidence directory. Runtime v6 remains unreleased and
source PR #1704 remains draft; this stage does not close #197.
