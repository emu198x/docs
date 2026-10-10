# Proposed MARIA DMA and DLI stages

**Status: approved by the user on 10 October 2026.**

Approval covers the staged correction, native clock contract and version-6
snapshot change described below. The assertion-delay adjudication remains a
required implementation gate.

Fix issue #197 by giving MARIA's DMA completion, next-zone descriptor and NMI
pulse their own clocked stages. The current whole-line renderer cannot express
the interrupt boundary described by Atari or the separate pulses observed in
the reference. The evidence is in `2026-10-10-maria-dli-pulses.md` and
`2026-10-10-maria-dli-oracle.md`.

This is a larger correction than clearing NMI after one CPU tick. That change
would repair event counts while preserving the wrong descriptor boundary and
unscheduled DMA. It would not meet the issue's timing acceptance criteria.

## Existing failure modes to carry into the new gates

- Consecutive flagged one-line zones collapse 240 chip events into one CPU
  interrupt, in PAL and NTSC. Alternating flagged zones do not lose events.
- The current descriptor's flag fires after its own zone, whereas the next
  descriptor controls the interrupt after the preceding zone's DMA.
- The machine asserts NMI at the line boundary before consuming the line's
  aggregate DMA budget; it has no separate shutdown or pulse phase.
- Display-list and graphics reads happen in bulk at the boundary. CPU writes
  during the real fetch interval cannot affect those already-completed reads.
- There is no partial DMA transaction or NMI pulse stage to save and restore.

The first two are confirmed functional defects. The latter three are limits
visible in the current code and need dedicated red/green timing and snapshot
probes during implementation. Do not treat this list as already-run coverage.

## Recommended design

1. Extend MARIA's existing descriptor, header and graphics processing into
   explicit idle/startup, descriptor fetch, header fetch, direct/indirect
   graphics, shutdown and NMI stages. Keep the existing palette and pixel
   decoding helpers. Avoid an alternative renderer or a precomputed event list.
2. Expose MARIA's current DMA read address/strobe, returned byte, CPU-halt and
   NMI levels to the machine. Advance reads at their actual stage boundaries.
   The machine continues to inspect CPU pins; no CPU bus trait or callback.
3. Drive the stages from a single native master counter with the phase
   resolution needed by the reference's MARIA and CPU clocks. The proposed
   base is four ticks per current colour-clock tick (nominal 14.32 MHz NTSC).
   Derive MARIA phases, colour/audio ticks and CPU slots from that counter.
   Region rates remain explicit; investigate existing PAL clock metadata while
   updating the clock contract rather than copying NTSC's rate into both.
4. Fetch the upcoming descriptor during the prior zone's shutdown. Its DLI
   flag arms a distinct NMI pulse. Preserve the initial vertical-blank fetch
   and line-buffer ownership explicitly so descriptor prefetch does not move
   graphics or lose a line. Keep the framebuffer dimensions; validate its
   mapping against the measured fetch/output relationship.
5. Clock the NMI stage independently of whether the CPU executes an instruction
   or is waiting for WSYNC. Preserve both assertion and release state. The
   exact shutdown-to-assertion phase is still a research gate: the primary guide
   states one 7.16-MHz cycle. The isolated DMA reference yielded 17 supplied
   native ticks after HALT release; the full-clock reference yields 18 on fast
   accesses and 20 on slow accesses in the measured matrix. Its two-CPU-cycle
   pulse also differs from the acceptance specification's one-cycle width.
   See `2026-10-10-maria-native-clock.md`. Do not choose an arbitrary compromise.
   Record the adjudication before locking a production timing expectation.
6. Preserve the current public scanline helper only if it can drive this same
   pipeline without a second implementation. If that contract cannot be kept,
   document the API break explicitly as part of the agreed pipeline change.

## State and API impact

Advance the Atari 7800 runtime snapshot envelope from **5 to 6**, rejecting
version 5 before machine decoding. Save all pending descriptor/fetch/shutdown
state, line-buffer ownership, native clock phase and NMI assertion/release
state. Update MARIA's direct chip-state encoding as well and reject the old
encoding explicitly, rather than decoding old bytes into new fields.

The proposed native counter also changes the units reported by machine clock
accessors, `run_frame()` and runtime `MachineTime`. Update the runtime clock
metadata and all consumers together. Emulated frame duration, CPU rate and
audio pitch must remain correct. This is an intentional clock-contract change,
not an accidental fourfold speedup.

No new dependency. No redesign of cartridge mapping, input, audio synthesis or
framebuffer geometry. Slow CPU access/HALT interactions are a validation gate
where they affect DMA startup; do not claim complete timing from fast empty
lists alone.

## Implementation sequence and verification

1. `crates/atari-maria/src/lib.rs` and a focused stage module if needed: express
   existing fetch/decode operations as saved stages. Add tests for descriptor
   handoff and live memory writes between fetches. Verify the old failure modes
   against the stage path before replacing its machine caller.
2. `crates/machine-atari-7800/src/lib.rs`: wire native clocks, DMA requests and
   HALT/NMI levels. Derive TIA/RIOT/POKEY ticks at their correct rates. Promote
   the CPU interrupt probe into a permanent regression with both regions,
   zone heights 1/2/3/16, all/alternating/single-entry flags, WSYNC waits, DMA
   disabled and restart cases. Count producer events, pin edges, vector reads
   and executed handlers; also check the actual raster split produced by a
   synthetic cartridge.
3. `crates/runtime-atari-7800/src/profiles.rs`, `runtime.rs`, and `snapshot.rs`:
   update the native clock contract and version 6 envelope. Test rejection of
   version 5 before mutation. Save/restore during descriptor fetch, graphics
   fetch, shutdown, asserted NMI and pulse release; compare resumed bus/pixel/
   interrupt traces with uninterrupted execution, not only equal state bytes.
4. Compare startup, descriptor boundaries, bus requests, shutdown and NMI
   across the reference phase matrix, populated direct/indirect lists, fast/
   slow CPU accesses and DMA cut-off. State any unresolved reference/primary
   disagreement. Run package/runtime tests, affected frontend checks, Asteroids
   and synthetic cartridge negatives, Clippy, formatting and hygiene.
5. Commit in reviewable pieces on one branch. Merge only after the complete
   timing correction and CI pass. Close #197 only when its raster timing and
   consecutive-pulse acceptance criteria are both demonstrated.

## Alternatives

- **Recommended: staged correction above.** Repairs the missing timing model
  and preserves enough state to validate and resume it. Requires API/clock and
  snapshot agreement.
- **Continue reference research before implementation.** Keep production
  unchanged while resolving the assertion-delay discrepancy and broader DMA
  traces. This remains useful work if the proposed scope is not yet agreed.

A counter-only pulse patch is not proposed as closure: it leaves a confirmed
wrong-zone interrupt and cannot prove the requested timing behaviour.

## First implementation slice: clock contract

Implemented and validated in source commit `7ffb356b`, intentionally unmerged
until the full correction is ready. Results and the separate POKEY restore
finding are in `2026-10-10-maria-native-clock.md`.

Establish native oscillator units before wiring pending DMA stages. In
`machine-atari-7800/src/lib.rs`, derive existing CPU, RIOT, POKEY, TIA and line
slots from the single native counter. Preserve this slice's existing raster
length and fetch behaviour; the staged DMA change will replace those next.
Expose the regional clock rate and frame budget for runtime metadata to use.
Correct the runtime's 262/312 budget disagreement with the actual 263/313-line
machine. Update stepping units and retain its existing wall-time safety cap.

In `runtime-atari-7800/src/profiles.rs`, use the machine's regional oscillator
rate and frame budget; in `snapshot.rs`, reject v5 and start the approved v6
branch layout. This branch stays unmerged until the full staged correction is
validated, so v6 is not released with an intermediate pipeline layout.

Tests: instruction native ticks versus actual CPU cycle advancement; runtime
host budget versus actual machine frame advancement for both regions; unchanged
TIA sample stream against a standalone sound core; resumed execution at every
native phase; v5 rejection before mutation. Run package tests, frontend tests,
Clippy and formatting. Record red controls before production edits.
