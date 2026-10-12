# Complete MARIA PR 1704

Engineering-frontier correction requested on 12 October. The native pipeline
and Atari 7800 v5-to-v6 change are already approved. Preserve the existing
uncommitted POKEY clock separation and PET investigation.

1. Reproduce the native DLI producer/pin/vector/handler and framebuffer probes
   against `edc96b5a` plus the preserved clock work. Record all failing cases.
   Use `2026-10-11-maria-native-dli-probe/run_probe.py` and
   `2026-10-11-maria-dli-raster-outcome/run_probe.py` sequentially because they
   temporarily install a module in the same machine source.
2. Adjudicate the missing interrupt-controller stage against the primary GCC
   specification/layout and unchanged reference implementations. Trace the
   real clock inputs before choosing assertion/release boundaries. Retain the
   existing timing gate; a count-only pulse patch cannot close it.
3. Complete the existing POKEY clock/sample correction in
   `crates/atari-pokey/src/lib.rs` and `crates/machine-atari-7800/src/lib.rs`.
   Proposed bounded shared-state extension: serialize the six partial-audio
   fields already owned by POKEY, leave delivered queues excluded, and bump
   Atari 5200/800XL runtime snapshots 18 to 19. The unreleased MARIA payload
   remains within approved Atari 7800 v6. This changes no synthesis stage or
   direct-chip codec. It needs approval for the additional shared envelopes;
   the broader timed-POKEY proposal remains separate and will rebase/version
   against whichever layouts have actually shipped.
4. After that approval, update `crates/runtime-atari-5200/src/snapshot.rs` and
   `crates/runtime-atari-800xl/src/snapshot.rs` with rejection-before-mutation
   tests. Validate mixed/channel audio continuation at partial sample phases,
   actual chip-clock edges during DMA/slow accesses and host sample deadlines.
5. Implement the qualified MARIA interrupt stage in the existing chip pipeline,
   state codec and machine pin wiring. Save during pending/asserted/released
   stages and compare future bus, interrupt and framebuffer outcomes. Promote
   the complete guest matrices into permanent regressions once green.
6. Run chip/machine/runtime/frontend tests, physical/reference timing probes,
   timing cartridges, Asteroids smoke, Clippy, formatting and negative controls.
   Commit bounded passing changes. Rebase against main once local work is
   committed, run fresh CI, and merge only after all stated gates pass.

The source of the extra approval requirement is AGENTS.md: “Breaking changes
to APIs or data schemas”. The proposed audio persistence fields and failing
80-case regression are already recorded in
`2026-10-11-pokey-clock-sampling.md`. The TIA/POKEY host mixer is a separate
issue and is not introduced here.

## Baseline reproduced on 12 October

Both temporary guest probes restored the machine source byte for byte.
The interrupt matrix reproduced all 192 cases: 6 baseline failures, versus
72 when the handler was suppressed (66 detectable only at handler outcome).
The raster matrix reproduced 16 failures out of 32, versus 24 when the
handler's colour write was redirected. These are still failing acceptance
checks, not passing corrections.

The audio continuation test executed and failed all 80 phase/frequency cases:
`test result: FAILED. 0 passed; 1 failed; 0 ignored`. The failure is
`audio restore mismatches`. An initial build encountered stale shared-cache
POKEY metadata (`no method named tick_chip`); rebuilding the unchanged POKEY
source removed that build error before recording the actual regression.

The local external 7800 cartridge inventory contains Asteroids, but no supplied
DMA timing cartridge. The existing CPU-driven synthetic matrices are available.
The GCC p.14 scan was checked again: it specifies one CPU-cycle pulse, one
cycle after HALT release. The FPGA's active two-cycle pulse and the conditional
layout schedule remain distinct evidence. No production NMI schedule has been
selected from those conflicting timing claims.

The bounded shared persistence approval was requested. Its implementation and
5200/800XL snapshot changes remain pending that answer. No prior source work
was discarded and no snapshot layout was changed in this baseline step.

## Approval

The user approved proceeding with the bounded shared persistence correction
on 12 October (“Fix it, please”), in response to the explicit v18-to-v19
request. Implement the six retained fields and both runtime envelopes without
asking again. The broader timed POKEY redesign remains separate.

## POKEY correction verified

The approved clock and persistence correction is implemented. The six retained
fields preserve the partial mixed/channel sums, sample count, fractional phase
and DC-filter history. Output queues remain excluded. The 5200 and 800XL reject
v18 before decoding or changing live state; their current version is v19.
The 7800 retains its approved, unreleased v6 envelope.

The affected chip, machine, runtime and frontend release suites pass **346
tests**, with **19 external-fixture tests ignored**. The separate Asteroids
smoke executes 200 frames and passes. Clippy with `--all-targets` and
`-D warnings`, `cargo fmt --all --check`, and `git diff --check` pass.

The original 80 partial-sample restore cases now pass. A further 1,280 saves
cover both regions, fast/slow accesses, live DMA ownership, partial sampling
windows and drained/undrained output queues. Each compares the next 640 native
ticks of mixed and four-channel audio, then CPU progress, framebuffer and the
complete serialized state. All pass. The clock checks retain the 720 held-CPU
observations and four executed guest runs through a full regional frame.

Negative controls were executed, then source files restored byte for byte:

- Omitting the saved fractional sample phase fails the native continuation
  test (`0 passed; 1 failed`).
- Reverting the 5200 version to 18 fails its old-layout rejection test
  (`0 passed; 1 failed`).
- Reverting the 800XL version to 18 fails its old-layout rejection test
  (`0 passed; 1 failed`).

After restoration, all 61 machine/runtime library tests in those three
packages pass again. Logs are in
[`2026-10-12-maria-completion/`](2026-10-12-maria-completion/).

This closes the bounded POKEY implementation gap on the branch. It does not
resolve the 6/192 DLI and 16/32 raster failures reproduced above, establish a
physical NMI schedule, or qualify a hardware DMA timing cartridge. PR #1704
must remain draft until those gates pass. The direct-chip legacy codec and
broader timed-POKEY redesign remain separate.
