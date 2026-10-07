# AGA top-of-field blanking

Lane: best-in-class Amiga campaign. The user approved investigating the
remaining raster boundaries, starting with the AGA top-of-field scanline.

1. Reproduce the ten retained AGA blanking guests on current main. Use the
   existing `ecs-output-phase/tools/compare_phase.py` counter-qualified raster
   contract; preserve reference pixels and retain input/executable hashes.
2. Trace the differing line through the existing A1200 board and Lisa blanking
   stages and the registered UAE source. Establish whether the disagreement is
   signal timing, initialization, or capture semantics before changing behaviour.
3. Add a failing regression for the demonstrated cause and make the smallest
   correction in the existing stage. Seek agreement if new pipeline state or a
   snapshot schema change proves necessary.
4. Recompare all ten guests, run relevant chip/board and snapshot checks, and
   retain the old failing captures as negative controls. Extend validation to
   the broader 128-guest corpus after the boundary corrections are settled.
5. Record reproducible evidence under
   `test-data/commodore/amiga/ecs-output-phase/`, source-qualified observations
   in the primary reference library, and the result in this plan.

No framebuffer resizing, image alignment search, new clocks or dependencies.
OCS right-edge and counter-reset residuals remain separate bounded changes.

## Reproduction and cause

At main `bed564d1981c2529cc75ac130e4aa03bac4d2104`, a fresh release
build reproduces 1,304 differing RGB samples in each of eighteen fields:
six guests times three retained reference fields. Four control guests are
exact across all twelve comparisons. Every comparison covers 1508×574
samples at the existing independently qualified horizontal origins.

The native image exposes COLOR00 in native x=[16,668), y=[2,4). The reference
keeps that segment black. Horizontal blanking already masks x=[668,924),
and both outputs become visible at x=924. Subsequent lines agree.

The native trace observes STRVBL at line 25, then STRHOR at line 26, through
the existing normal RGA/counter stage. This is not a missing Agnus strobe.
The board's `service_timing_strobe` currently feeds only the horizontal
counter; neither its final output mask nor Lisa retains vertical blanking.

Trace-only instrumentation of the registered FS-UAE producer records the
pending vertical release, retained programmed vertical-blank latch, and its
clear at counter 319 / reference x=912 (HBSTOP's next-counter comparison).
All three fresh reference buffers are byte-identical to the archived fields.
Reference `linear_vpos` is a queue/display label, not Agnus VPOS: it resets
at `vsync_startline`, and the queued raster spans the preceding beam line.
Do not equate that trace label with the native VPOS column or change the
registered crop to compensate.

The hardware manual's STRHOR/STRVBL/STREQU register descriptions establish
strobe delivery on the destination bus. Exact latch timing here is UAE-family
implementation evidence, not a new physical-hardware measurement. Current
vendored WinUAE also separates pending fixed and programmed vertical changes;
the older registered FS-UAE uses a shared pending change. The static controls
do not distinguish these implementations during selector changes.

## Approved bounded design

The user approved this extension and version 55 with “I'm happy with that”.

Extend the existing Lisa output stages, rather than infer vertical blanking
from viewport rows or Agnus VPOS:

- Retire the actual timing strobe through the existing normal RGA stage and
  notify Lisa at that stage. Preserve the horizontal-counter timing.
- Retain the preceding vertical/non-vertical strobe identity, pending vertical
  start/stop events, and fixed/programmed vertical-blank levels in Lisa.
  Keep fixed and programmed event histories separate as in current WinUAE.
- Consume pending events at the appropriate fixed/programmed horizontal
  comparator edges, including fine sample positions. Compose vertical and
  horizontal output levels after palette/HAM/sprite progression.
- Keep ECS and OCS behaviour outside this bounded correction. They require
  their own strobe/blanking evidence rather than inheriting Lisa's semantics.
- Persist new in-flight stages in Amiga snapshot version 55; reject version
  54. Do not hide new mutable state behind serde defaults or skipped fields.

Expected files: `crates/commodore-denise-aga/src/lib.rs`, the existing chip
trait in `crates/common-commodore-amiga/src/`, its `denise.rs`/`denise_counter.rs`
strobe delivery, `crates/machine-commodore-amiga-a1200/src/lib.rs`, and
`crates/runtime-commodore-amiga/src/snapshot.rs` plus the corresponding
snapshot/diagnostic assertions. Final names depend on the existing trait hook.

Verification must cover red-before/green-after latch tests; both blanking
edges; fixed/programmed selection; reset/wrapping/equal comparators; all
in-flight restore boundaries; the ten retained guests and strict A1200 Test
Kit gate. No claimed silicon calibration or completion of the full 128-guest
sweep. Broader validation follows the separate boundary corrections.

A crop/mask adjustment cannot represent this signal history and was rejected.

Evidence and replay live in the code repo at
`test-data/commodore/amiga/ecs-output-phase/top-field-blanking/`.

## Implementation

The existing horizontal counter exposes the strobe about to retire; the A1200
board delivers it to Lisa before computing that tick's blanking. Its normal
stage and counter commit are unchanged. Lisa retains separate pending fixed
and programmed events, their levels, and the preceding strobe identity. The
selected comparator consumes only its matching start/stop event. The output
mask is applied after palette/HAM/sprite advancement.

The board regression failed at native (16,2), observing `0xFF001111` instead
of black. It passes after correction. Fresh captures of all ten guests now
pass thirty whole-common-raster comparisons, with zero differing RGB samples.
The archive keeps the failing fields and exact controls and replays both.

Verification: 224 chip/board checks (including the separate normal-stage
delivery regression), 56 runtime library checks, ten register pipeline
checks and all 57 snapshot checks pass. The snapshot sweep reaches 24
half-CCK boundaries and observes pending starts, pending releases and retained
blank levels. All six strict A1200 Test Kit patterns remain exact. Strict
Clippy, formatting, Ruff, evidence replay and its tampered-capture negative
control pass. The full 128-guest sweep remains deferred until the separately
tracked raster-boundary work is closed.

The first new snapshot test incorrectly advanced the machine with a coloured
framebuffer while leaving runtime boot-count bookkeeping stale. Its immediate
round-trip differed only in recomputed runtime summary fields. The test now
keeps its reset palette, as the existing direct-machine replay tests do; it
checks every saved byte and explicitly requires live pending/latched vertical
states. The separate board regression and live images verify visible colour
output. No snapshot equality assertion or restore stage was removed.
