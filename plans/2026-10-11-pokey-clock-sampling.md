# Separate POKEY clocks from host sampling and retain partial audio

Engineering-frontier follow-up to MARIA's approved native pipeline and
issue #1705. The 7800 currently ticks POKEY every eight oscillator periods,
coupling timer advancement and sample production. MiSTer's `rtl/cart.sv`
connects both POKEYs' `ENABLE_179` to `pclk0`; `top.sv` routes the actual
MARIA-generated CPU phase-2 strobe there, independently of Sally's HALT.
The Atari software guide identifies the cartridge clock as CPU phase 2
(`reference/by-system/atari-7800/atari-7800-software-guide.md`, cartridge
connector description).
The qualified MARIA clock vectors already cover fast and stretched accesses.

The shared POKEY serde layout drops partial mixed/channel sums, sample count,
fractional sample phase and both DC-filter history values. These affect future
samples; only delivered output queues should be omitted. All serde consumers
are `machine-atari-5200`, `machine-atari-7800` and `machine-atari-800xl`.

## Proposed bounded correction

1. Split `Pokey::tick` in `crates/atari-pokey/src/lib.rs` into chip advancement
   and audio sampling methods. Keep `tick` calling both for existing fixed-
   clock consumers. Sampling uses its configured timebase; the 7800 sets that
   timebase to its native oscillator and samples each native tick. No extra
   timer ticks or catch-up in reads/writes. Existing synthesis stays intact.
2. In `crates/machine-atari-7800/src/lib.rs`, advance POKEY on MARIA phase 2,
   before CPU register writes, whether Sally is running or halted. Sample the
   resulting output once per oscillator tick. Slow accesses change chip
   progress, while host output remains 48 kHz in both regions.
3. Preserve the six partial-audio fields (including the four-channel array)
   in serde. Keep mixed/channel output queues skipped so restored audio does
   not replay delivered samples. Advance 5200 and 800XL runtime envelopes from
   **18 to 19**, rejecting 18 before machine decoding. 7800 stays within its
   already-approved, unreleased **v6** layout. No dependency addition.
4. Reproduce clock mismatch with fast/slow WSYNC-held accesses and compare
   actual RANDOM progression against a standalone chip driven by the measured
   phase-2 edges. Extend to executed guests and DMA ownership. Reproduce
   snapshot loss across partial sampling phases and both regions, with nonzero
   filter state and drained/undrained queues. Compare future timestamps,
   mixed/channel values, register/timer state and machine continuation.
5. Verify legacy `tick` and split calls agree under a uniform clock, while
   stretched intervals retain their proper time weight. Verify actual output
   counts over elapsed native time, not only advertised rates. Add runtime
   v18 rejection-before-mutation tests for 5200/800XL and resumed-audio checks.
   Run the shared chip and affected machine/runtime/frontend packages, Clippy,
   formatting and the existing Asteroids smoke. Deliberate state/clock faults
   must make the relevant checks fail.

The 5200/800XL envelope changes extend beyond the earlier 7800-only schema
approval and require agreement before implementation. The recommended design
fixes the shared state owner. A 7800-only wrapper would leave #1705's other
consumers broken and duplicate private sampling state; it is not recommended.

The compact `Pokey::save_state`/`load_state` API is a separate legacy register
format, unused by these runtime snapshots. Its omitted serial/pot pipeline
state needs a separate audit; this correction does not claim it is a complete
continuation snapshot. Physical MARIA NMI timing remains a separate gate.

## Reproduced on edc96b5a

All six region/address combinations disagree on RANDOM progression while
WSYNC holds CPU execution. Fast accesses first differ at oscillator tick 12
(actual `$ff`, phase-2-driven `$7f`); slow TIA/RIOT accesses first differ at
tick 24 (actual `$3f`, phase-2-driven `$7f`). The sweep checks 720 native
observations and verifies the CPU executed no cycles.

All 80 restore cases (40 sample offsets at each regional CPU frequency) lose
future mixed or per-channel audio after serialization. The test drains all
pre-save output, establishes nonzero audio/filter history and compares the
next 96 chip ticks. The first differences span offsets 0–36 after restoration;
it is not confined to a single sampling boundary.

The [evidence directory](2026-10-11-pokey-clock-sampling/) retains the exact
failing log and regression patch against `edc96b5a`. Run with
`cargo test -p machine-atari-7800 pokey_ -- --nocapture`. The existing POKEY
cartridge-routing check passes; both new outcome checks fail.

## Clock separation implemented locally

The already-approved 7800 clock portion is implemented in the source worktree:
`tick_chip` advances hardware and `sample_tick` accumulates elapsed output.
The existing `tick` API still calls both for fixed-clock systems. The 7800
clocks POKEY at MARIA phase 2 even during DMA, before CPU writes, and samples
on every native period. No snapshot field selection has changed yet; the
additional 5200/800XL schema approval is pending.

All 36 shared POKEY tests pass, including uniform-call equivalence and a
sampler-only check where a two-period pulse in a ten-period window contributes
exactly one fifth of full channel level. Sampling leaves chip state unchanged;
chip advancement leaves the output queue unchanged.

The six WSYNC-held clock cases now pass. Four live guest runs (both regions,
fast/slow accesses) verify RANDOM every native tick, real DMA ownership,
continued CPU progress and each individual 48 kHz host-output deadline.
Deliberately sampling only on phase 2 fails at native tick 299: zero samples
instead of one. These checks validate clock wiring and elapsed-time sampling;
they do not establish complete POKEY synthesis accuracy.

The 80-case audio restore regression is intentionally still failing until the
shared serialized fields and consumer versions are approved. The source work
is uncommitted and PR #1704 remains at `edc96b5a`. Do not merge an intermediate
layout or describe the save-state defect as fixed.

The broader run passes 62 MARIA, 36 POKEY, 11 frontend and 40 machine tests;
only the new restore regression fails. A separate run passes 166 tests
across the 5200/800XL machines and all three runtimes. External-firmware tests
remain ignored in that ordinary run. Clippy and formatting pass. The evidence
folder includes the logs and `clock-prototype.patch` against `edc96b5a`, so the
uncommitted clock work and pending regression are preserved for review.

The patches use zero context to keep embedded patch whitespace unambiguous.
Apply with `git apply --unidiff-zero` to an isolated checkout of `edc96b5a`.
Both were applied to temporary copies of that revision and their resulting
files compared with the recorded reproducer/current source respectively.
