# Programmable blanking at the Denise counter reset

Lane: best-in-class Amiga campaign. Continue the approved blanking work.

The earlier plan identifies a coverage gap, not a reproduced fault: UAE
passes the pending next counter on the second output tick, whereas the
current Lisa comparator adds one to the current counter. Existing retained
traces show current 455 / next 2 at the reset. Probe that distinction before
changing behaviour.

1. Reuse the SPHX blanking guest and builder. Vary HBSTRT and HBSTOP across
   all eight fine positions at CCK 1; retain CCK 0 and 2 controls. Capture
   three reference fields and fresh version-56 native images for every case.
   Keep input/producer hashes and the existing counter-qualified comparator.
2. Confirm the failing samples and the current/next-counter trace. Add a
   board regression that fails before correction. Record primary observations.
3. If confirmed, expose the existing counter's committed-next comparison
   through `common-commodore-amiga/src/{denise_counter,denise}.rs`, and supply
   it from `machine-commodore-amiga-a1200/src/lib.rs` to the existing Lisa
   comparator in `commodore-denise-aga/src/lib.rs`. Preserve old entry points
   for standalone callers. No new state, clock or schema is anticipated.
4. Verify all fine edges, both sides of reset and snapshot replay. Repeat
   the new corpus, retained ordinary controls, relevant chip/board/runtime
   tests and strict A1200 Test Kit. Preserve failing captures as controls.
5. Retain build/capture/replay evidence under `ecs-output-phase/counter-reset`,
   update the primary observations and binding counter decision, then commit
   and push this bounded correction. Do not claim the full campaign complete.

ECS receives a delayed Agnus CSYNC signal rather than Lisa's local comparator;
do not apply Lisa-specific counter semantics to it without separate evidence.
New saved state or architectural changes require separate approval. Fixed
host raster coordinates, reference pixels and clocks remain unchanged.

## Confirmed cause and bounded implementation

The twenty-case probe reproduces eight failures (the first four fine bits of
CCK 1 for each edge) and twelve exact controls. Each has three complete
reference fields. HBSTRT=$0001 differs at 551,408 samples per field;
HBSTOP=$0001 differs at 404,976. The retained current=455 / next=2 trace
explains why reconstructing current+1 entirely misses those comparisons.

The board regression fails at native x1468..1471, writing COLOR00 instead
of black while the preceding four samples are correctly coloured. It passes
after exposing `DeniseHorizontalCounter::next_comparison_position` through
the existing shared wrapper and passing it to Lisa's new additive entry
point. The old standalone entry point keeps its ordinary increment semantics.
No state, clock, snapshot schema or framebuffer coordinate changes.

Counter tests verify reset policy for all strobes, both chipset policies,
half-CCK restoration and nine-bit wrap. Lisa tests verify all eight fine
positions for both edges. Runtime replay covers 32 live pre/post-reset
boundaries for aligned and fine start/stop cases, positively observing the
pending reset and both blank levels.

## Verified result

All sixty new reference fields match after correction. All thirty retained
ordinary AGA blanking fields remain exact: ninety fields and 77,903,280 RGB
samples. Replay reproduces the twenty-four old failures and thirty-six exact
baseline controls before requiring the corrected result. Every new guest
rebuilds byte-identically from the retained seed and existing SPHX builder.

All 227 affected library tests and 59 snapshot tests pass. The strict A1200
Test Kit gate matches all six patterns. Release build, strict Clippy, Rust
formatting, Ruff and artifact replay pass. An altered PNG fails the hash
check; updating its hash still fails the reference comparison. No failing
reference field or crop boundary was removed.

The replay trace parser initially matched the suffix of `lastpix` as `x`;
its strict trace check rejected the result. A word boundary now selects the
actual `x` key, and the retained positive reset traces and complete replay
pass. This was an evidence-parser fault; the chip correction was unchanged.

Snapshot 56 remains compatible with the preceding OCS correction. The
separate full 128-guest campaign and unrelated blanking paths were not rerun
or declared complete by this bounded investigation.
