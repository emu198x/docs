# Preserve Game Gear stereo routing through audio and snapshots

Status: proposed; implementation requires agreement for the shared chip-state
and runtime snapshot changes. Engineering-frontier correction for source issue
#149, following the [executed audit](2026-10-11-sn76489-stereo-audit.md).
The separate register-loader truncation fix is in source PR #1720.

## Evidence and required outcome

The current public-API probe fails 768 of 1,024 channel/mask cases. A synthetic
Game Gear cartridge completes its PSG/panning writes and halts at PC 17, but
all-enabled, muted and left-only configurations produce identical samples in
one-channel host packets. Neither the register byte nor the stereo API currently
changes output routing.

A correction must preserve routing at the time samples are generated, pass
left/right data through the live Game Gear runtime, and resume partial audio
windows exactly after a runtime snapshot. Mono systems remain mono consumers.
The primary SN76489 reference defines high-nibble left / low-nibble right.
Mesen2 and MAME corroborate the mapping; MAME's `stereo_w` flushes the previous
stream before changing its mask. These sources establish time-dependent routing,
not a newly measured physical write-latch phase or analogue filter response.

## Approaches

1. **Extend the current chip mixer and accumulator (recommended).** Integrate
   the current outputs on each existing input-clock tick, retain separate L/R
   partial sums and filter histories, and emit stereo at the shared sample
   boundary. All consumers use one audio timebase and chip implementation.
2. **Add a Game Gear-specific audio wrapper.** Preserve the shared mono sampler
   but maintain a second timeline and snapshot contract for Game Gear. This
   duplicates sampling and risks mono/stereo phase disagreement; it also adds
   an architectural pattern for a register already owned by the chip.

Applying the final mask when draining channel buffers cannot meet the temporal
requirement: it changes audio generated before a later register write.

## Proposed bounded design

In `crates/ti-sn76489/src/lib.rs`:

- Keep tone/noise transitions on the existing divide-by-16 clock. On each
  existing master-clock `tick`, accumulate the held channel levels and selected
  left/right sums. Register writes change subsequent contributions, never
  earlier ones. Do not run extra chip ticks inside a write or drain method.
- Use the original constructor's full input clock for the sample phase rather
  than the truncated `clock_hz / 16` rate. The current mono and diagnostic
  accumulators share this native-clock boundary with stereo. Their integration
  becomes finer; sample values can change where writes or transitions fall
  inside the old 16-clock buckets. This is an explicit part of the correction,
  not a promise of bit-identical old mono waveforms.
- Add L/R partial sums, L/R high-pass input/output histories and interleaved
  output storage to the existing serialized chip. Preserve the existing filter
  coefficient; analogue filter calibration is separate work.
- Treat mono and stereo drains as alternative views of the same generated
  interval. Either drain clears its counterpart, as the current stereo drain
  already consumes mono. Repeated drains produce no duplicate samples; unused
  stereo storage cannot grow while a mono consumer runs. Keep diagnostic
  per-channel draining independent, matching the existing public API.
- Keep the 30-byte manual register-image layout unchanged. It already omits
  resampling/filter history and is not used by the six live-machine snapshot
  modules. Document that limit precisely; it cannot serve as the stereo
  continuation test. Full runtime snapshots use the derived serde chip state.

In `crates/machine-sega-master-system/src/lib.rs`, expose an explicit stereo
buffer drain while retaining the existing mono drain. In
`crates/runtime-sega-master-system-class/src/runtime.rs`, use it only for
Game Gear and set the resulting `AudioPacket.channels` to 2. SMS uses the mono
path and declares one channel. No host mixer or catalogue rewrite is required.

## Snapshot changes requiring approval

Retain all partial sums, sample/divider phase, panning mask and separate filter
histories through serde. Changing the shared chip layout requires versioning
all six snapshot modules, affecting seven machine catalogues:

| File under `crates/` | Version change |
| --- | --- |
| `runtime-sega-master-system-class/src/snapshot.rs` (SMS and Game Gear) | 8 → 9 |
| `runtime-acorn-bbc-micro/src/snapshot.rs` | 8 → 9 |
| `runtime-coleco-colecovision/src/snapshot.rs` | 5 → 6 |
| `runtime-memotech-mtx/src/snapshot.rs` | 5 → 6 |
| `runtime-sega-sg-1000/src/snapshot.rs` | 5 → 6 |
| `runtime-sord-m5/src/snapshot.rs` | 5 → 6 |

Reject prior versions before payload decode or live-state mutation, following
the existing envelope checks. Recheck version numbers against main immediately
before implementation. No dependencies are required.

## Bite-sized work and verification

1. Add red regressions in `ti-sn76489/src/lib.rs`: all masks/channels; writes
   before/after generated samples; short enabled pulses at each divider phase;
   left/right isolation and filter histories; alternating mono/stereo drains.
   Keep nonempty/nonzero controls. Compare pulse contributions with explicit
   native-clock interval weights, and distinguish that model from physical
   subclock measurements.
2. Extend the existing accumulation path and retain its new state. Check output
   count over full input-clock seconds for NTSC/PAL and 4 MHz callers, additive
   L/R routing, all-enabled agreement with mono, unchanged oscillator/LFSR
   transitions, and muted-channel controls. Measure frame cost before/after so
   the finer integration has a known performance cost.
3. Wire the machine and runtime stereo path. Promote the executed synthetic
   cartridge into `runtime-sega-game-gear/tests/audio.rs` (new file). Capture
   actual host packets for both-enabled, muted, left-only, right-only and timed
   pan changes; assert the guest completes. Add the corresponding mono control
   to `runtime-sega-master-system/tests/audio.rs` (new file).
4. Update the six snapshot modules and their existing rejection tests. Extend
   `machine-sega-master-system/src/lib.rs`'s postcard tests to compare resumed
   samples at partial-window and panning boundaries. Add runtime continuation
   coverage in `runtime-sega-game-gear/tests/audio.rs`; run the six existing
   runtime snapshot suites. A serialization round trip alone is insufficient:
   compare the subsequent samples and timestamps after restore.
5. Run affected chip, machine and runtime tests, Clippy and formatting. Retain
   failures and corrected outputs with hashes. Submit a scoped source PR and
   merge only after exact-head CI passes; then verify #149's chip, timing,
   snapshot and host-output requirements before resolving it.

The native-clock integration and six snapshot version changes are one coherent
pipeline correction. Do not partially ship a drain-time approximation merely
to make the static panning cases pass.
