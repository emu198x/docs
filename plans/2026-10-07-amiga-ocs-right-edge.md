# OCS fixed-blank right edge

Lane: best-in-class Amiga campaign. The user approved investigating and
correcting the remaining OCS right-edge discrepancy after the Lisa fix.

1. Reproduce the retained OCS colour guest with the current release build.
   Preserve executable/input hashes and use the existing counter-qualified
   `ecs-output-phase/tools/compare_phase.py` raster contract.
2. Trace the differing samples through the OCS output, retained line context,
   and registered UAE producer. Consult vAmiga for independent implementation
   precedent and distinguish chip blanking from host buffer padding.
3. Demonstrate the responsible invariant with a failing regression before a
   bounded correction in the existing OCS/common Denise stage. Preserve
   snapshot 55 unless evidence calls for an explicitly approved extension.
4. Repeat the full retained comparison, the strict A500 Test Kit gate and
   relevant chip/board/snapshot checks. Retain the old failure as a negative
   control and preserve unrelated AGA/ECS output.
5. Record primary observations, executable evidence and the final verification.

No extra emulated clock ticks, crop adjustment, image alignment search or
reference-pixel changes. Counter-reset programmable cases remain separate.

## Reproduction and cause

The current version-55 binary reproduces 2,288 differing RGB samples in each
of three fields. All differences occupy the last four 35 ns samples in the
fixed 1508-by-574 common raster, across 572 rows. The guest, reference bytes,
counter origins and comparison algorithm are unchanged.

An instrumented run of the registered UAE producer retains byte-identical
raw fields. Across all 600 active line observations, counter 13 writes the
last coloured samples at buffer x=1504..1507. Counter 14 matches next-counter
$0F and writes black at x=1508..1511. The following tick positively observes
those four writes and the asserted horizontal-blank level. This is chip
blanking, not host padding. The retained trace has 3,000 checked observations.

OCS currently passes `DeniseOutputSignals::unblanked` to the output stage.
The board regression fails with coloured `0xFF113355` instead of black at
native columns 760..761; columns 758..759 remain correctly coloured.

## Approved bounded correction

Add one retained fixed-horizontal-blank level to the existing OCS Denise
core. Compare its existing independent nine-bit counter's next position:
set at $0F, clear at $5D, retain otherwise. Feed that level to the existing
final output mask from the OCS board on each existing output tick. Do not
alter host projection, clocks, DMA or the ECS/AGA board paths.

The reference's `handle_strobes` can reset the horizontal counter without
clearing `denise_hblank`. A stateless interval test would lose that history;
a framebuffer-column mask would not follow the chip counter. Retain the
latch in snapshots rather than reconstructing it on restore.

Files: `crates/commodore-denise-ocs/src/{chip,debug}.rs` and its tests;
`crates/machine-commodore-amiga-ocs/src/lib.rs`;
`crates/runtime-commodore-amiga/src/snapshot.rs` and relevant snapshot tests;
the existing diagnostic register mapping if needed for the new field.
Advance Amiga snapshots to version 56 and explicitly reject version 55.
The user approved this additional saved field and compatibility break on
2026-10-07 after reviewing the live trace and failing regression.

Verify both comparator edges, a reset that skips a stop edge, free-running
nine-bit wrap, and saves before/after each transition. Re-run all three
unchanged reference fields, strict A500 Test Kit, affected chip/board/runtime
tests, formatting and Clippy. Keep the original red result as a negative
control. The independent vAmiga implementation masks a coarser fixed Agnus
interval; it corroborates blanking as an output operation, not the precise
UAE comparator phase. Original-hardware calibration remains unclaimed.

Evidence: `test-data/commodore/amiga/ecs-output-phase/ocs-right-edge/` in the
code repo. Reference scratch source and executable were restored after the
instrumented capture.

## Result

The correction uses one saved OCS latch and the existing final mask. All
three fresh OCS fields are exact; the ECS and AGA programmed-central controls
are also exact. Nine fields cover 7,790,328 RGB samples with unchanged
reference bytes, comparison origins and extents. The retained baseline still
reproduces 2,288 differences per OCS field.

All 620 distinct selected tests pass: 373 library checks, 128 additional OCS
chip integration checks, 58 snapshot checks and 61 display-register/lifecycle
checks. Snapshot replay covers seven reset/edge boundaries with both real
blank levels. The strict A500+A501 Test Kit gate passes all six patterns.
The release build, strict Clippy, formatting, Ruff and evidence replay pass.
An altered-capture negative control is rejected by the evidence hash check.

The old publication test failed at (760,572), expecting red where the new
chip blank level correctly produces black. It now requires the coloured
carry through column 759 and black through 767, retaining the publication
timing assertions. Its original failure log is archived. The complete
128-guest campaign and separately tracked programmable reset cases have not
been rerun or closed by this bounded correction.
