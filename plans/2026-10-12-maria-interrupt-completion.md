# Complete native MARIA interrupt delivery

Continue the already-approved native stages and unreleased v6 snapshot design.
The 12 October request is to finish the job, including guest validation and
integration. The source baseline is `52cba0da`; preserve its POKEY correction.

1. Implement the recovered interrupt controller's sampled input/output stages
   in `crates/atari-maria/src/interrupt.rs`, using its three reachable states,
   set/reset latch and descriptor request. Compare against the original
   retained circuit traces, including fast/slow clock changes. Capture and
   output remain distinct MARIA phases; CPU edge is sampled, never treated as
   a half-cycle level. Do not use a fixed-duration pulse timer.
2. Connect the stages to the existing divider and DMA descriptor delivery in
   `dma.rs` and `lib.rs`. Expose the NMI level continuously to Sally in
   `crates/machine-atari-7800/src/lib.rs`. Preserve diagnostic descriptor-event
   consumption separately from the pin. Continuing zones must not repeat an
   old descriptor's interrupt request.
3. Include all pending stages in `state.rs` and serde within the approved
   unreleased layouts. Test pending/asserted/released continuation and invalid
   state rejection before mutation.
4. Run the unchanged 192-case interrupt and 32-case raster acceptance probes.
   Promote the passing executed guests into permanent regressions. Retain
   their handler/palette suppression negatives and add timing-stage faults.
5. Adjudicate timing using the strongest available evidence, recording exact
   model boundaries. The original recovered controller and GCC specification
   agree on a one-CPU-cycle pulse; the FPGA's replacement uses two. Compare
   the production stage against the recovered circuit before deciding whether
   remaining physical uncertainties require a narrower shipping claim.
6. Run affected packages, Asteroids, formatting and Clippy. Commit the bounded
   passing correction, rebase the branch on main, run fresh CI, update the PR
   and merge only once the implementation and stated acceptance gates pass.

The original design evidence determines the state transitions. The scope is
native digital observation, not an analogue electrical simulation. Unknown
layout revision and sub-period electrical delays must remain explicit; passing
software tests cannot be presented as a physical measurement. This plan does
not waive the existing assertion-delay adjudication requirement.

## Results

The source stage matches all 32,832 circuit cases and 16,416 pulses, including
all modeled clock transitions and CPU-return delays. The export checks every
regenerated case against the retained matrix before compressing 300 distinct
input/output traces for permanent Rust tests. The [timing adjudication](2026-10-12-maria-interrupt-completion/adjudication.md)
records the selected digital sequence and remaining physical-validation limits.

The unchanged original probes now pass **192/192 CPU delivery cases** and
**32/32 raster cases**, including all 6,144 pixel samples. Suppressing the
handler fails 72 cases; redirecting its colour write fails 24 raster cases.
The tests are now permanent machine regressions. The native pulse test checks
both regions and fast/slow/WSYNC guests: each pulse spans one live CPU edge,
with widths of 8, 10 or 12 native periods where the clock permits them.

Save/restore continuation passes **640 direct-chip cases** and **960 machine
cases**, including pending, asserted and WSYNC-held interrupts. Corrupt phase,
command and Boolean encodings reject before replacing live chip state.

Three deliberately introduced faults each execute and fail their target test
with `0 passed; 1 failed`: early assertion, lost pending snapshot command and
restored line-boundary delivery. Source bytes are restored after each check.
Afterward the full affected Atari chip/machine/runtime/frontend run passes
**353 tests**, with **19 external-fixture tests ignored**. Asteroids separately
passes the executed 200-frame smoke. Clippy with all targets and warnings
denied, Rust formatting, Ruff and diff checks pass.

The first package run also caught an obsolete test fixture: it injected NMI
straight into Sally, which the newly connected MARIA pin correctly overwrote.
Its failure was `NMI edge must still reach the CPU detector`. The replacement
executes a WSYNC guest receiving actual DMA-triggered pulses. Its first draft
incorrectly expected nearly all pulses to arrive during WSYNC; the trace showed
122 held arrivals among 243 NTSC pulses. The final invariant checks both held
and running arrivals, unchanged CPU progress during held detection, and equality
of all detections, releases and executed handlers. It does not pin an invented
held-pulse count.

Evidence and the vector exporter are in the [adjacent folder](2026-10-12-maria-interrupt-completion/).
The source correction does not close #196's external timing-ROM requirement or
claim a physical production-revision measurement under #197.

## Integration

The correction is source commit `6ffc4e76b2ea1bd5fa69496f11e3ac1c015cd474`
after rebasing the complete branch on main
`9790f2437f6a1dd16d5f004233f51fe79d444740`. MARIA and Atari 7800 source/test
files are byte-identical across the rebase. Main's newer shared POKEY fixes are
included, and a fresh affected-package run passes **364 tests**, zero failures,
with 19 external-fixture tests ignored. The separate Asteroids smoke is rerun
on this head. Fresh remote CI is required before the source merge.
