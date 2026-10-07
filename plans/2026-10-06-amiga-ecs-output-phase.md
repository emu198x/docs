# ECS absolute output phase

Continue the accuracy campaign from the completed version-53 window correction.
Seven lores and four hires A500+ guests disagree with the retained UAE-family
reference by one lores position. The hires data edge is early as well as DIW.
The user requested tracing and fixing this next.

## Bounded investigation

1. Reproduce the stored comparison and retain the version-53 source/binary
   identities. Use `horizontal-window/` guests, raw reference fields and the
   unchanged source-derived crop. Check complete fields and guest identities.
2. Trace native and reference counter positions, window equality, bitplane
   copy/output and any post-composition delay. Extend the existing read-only
   `runtime-commodore-amiga/examples/horizontal_window_trace.rs` if needed;
   instrument only a separate writable reference-source copy under `/tmp`.
   Include OCS controls to distinguish chip behaviour from reference-family
   or capture-origin differences. Record source-supported observations in
   `reference/by-system/commodore-amiga/2026-ecs-output-phase-observations.md`.
3. Identify the first divergent stage before choosing a correction. Preserve
   counter ownership, oscillator timing, sprite coordinates and raster crop.
   Existing binding phase decisions explicitly leave ECS calibration open.
   Any additional saved stage or architectural extension needs a concrete
   design and the user's agreement before implementation.
4. For a bounded correction within the existing stages, first add a failing
   invariant that observes real output, then make the smallest change in the
   implicated chip/board code. Rerun all eleven ECS window guests, relevant
   OCS/AGA controls, restore tests and affected crate tests/Clippy. Record
   exact matches and remaining disagreements without changing reference images.

No framebuffer translation or empirical crop adjustment is an acceptable fix.
The software reference remains implementation evidence, not hardware proof.

## Completed evidence

The baseline reproduces all 33 ECS failures. Instrumented reference captures
reproduce all 33 original raw fields byte for byte. In all 6,600 active line
observations, counter 100 maps to reference buffer x=36, not x=32: the reported
origin 368 omits four samples of retained line-output padding. Both the start
match and hires data drain agree with the native counter trace. An OCS hires
control has the same source offset and agrees after counter-domain mapping.

The separate `ecs-output-phase/tools/compare_phase.py` requires complete origin
evidence, preserving the original failing comparison alongside it. All eleven
ECS guests now match all 33 fields in the shared counter domain; the OCS control
matches three fields. This corrects the diagnostic mapping, not chip timing.
It does not change the admitted video gate or claim physical-beam calibration.

Negative controls detect one injected pixel error in each of three fields and
reject an empty origin trace. Three unit tests additionally reject incomplete,
duplicate and inconsistent observations. The native trace example builds and
passes strict release Clippy. Production and snapshot 53 are unchanged.

## Confirmed AGA consequence and proposed correction

Two fresh AGA controls (legacy and timed-start rewrite) each establish the same
counter origin over all 600 active observations. The old mapping matches all
six fields; counter mapping fails all six (3,200 / 3,088 samples per field).
Native opens at counter 130 instead of the reference's 129, and its legacy
data end is counter 438 instead of 437. The earlier Lisa phase calibration
mistook output-buffer padding for a chip delay.

Recommended next bounded change:

1. Update `knowledge/decisions/amiga-lisa-bitplane-diw-output-phase.md` from
   the superseded absolute-image argument to the observed comparator/copy
   ordering. Preserve version-53 timed DIW delivery and fine-bit decoding.
2. Recalibrate the existing Lisa window and serial-output stages in
   `common-commodore-amiga/src/denise_chip.rs`,
   `commodore-denise-aga/src/lib.rs` and `commodore-denise-ocs/src/chip.rs`.
   First pin counter-domain start/data-end failures with native traces. Keep
   the existing serialized layout where possible; do not delete saved stages
   merely because a history tap changes. Any new schema extension needs its
   own demonstrated design.
3. Trace sprite and COLOR controls independently before changing their phase:
   the shared source origin weakens old absolute-image arguments but does not
   prove that every output delay is wrong. Requalify affected contracts from
   measured source origins, retaining all former failures and producer hashes.
4. Recheck all seventeen AGA window guests plus textured scroll, sprite/priority
   and colour controls, snapshot replay, strict Test Kit and boot regressions.
   Never compensate by translating native output or fitting a crop to pixels.

Alternative: retain the current Lisa delay and label the absolute phase as
known incorrect. Adding the same delay to ECS would encode the comparison
error in another chip and contradict the counter traces.

This changes a binding phase decision and production behaviour, beyond the
original ECS assumption. The project's “Design before code” rule requires
agreement on this concrete correction before implementation.

## Approval and execution

The user approved the bounded Lisa recalibration on 2026-10-06: “Please fix
that, I approve”. Keep snapshot 53 layout, correct the proven window and
bitplane taps, and trace sprite/COLOR independently before changing them.

The first correction matches all 51 AGA window fields. Independent controls
then confirm sprite output and Copper colour edges one lores tick late. The
coloured-border controls additionally expose fixed HBLANK ending at native
counter 93 instead of reference 92. `checkhorizontal1_aga` compares `cnt_next`
with the fixed $10/$5D values; the native method used the current counter.
Correct this existing comparator input along with the approved sprite/COLOR
taps. Retain programmable blanking timing and all saved layouts. The strict
control comparison includes the border, so leaving this error would fail it.

A separate hires producer run records counter 100 at buffer x18 with retained
padding 2 on all 600 active observations: raw origin is counter 91. Requalify
the A1200 Test Kit consumer transform to `runtime_x = producer_raw_x + 6`,
preserving all independently captured PNGs and their exact assertions. The
old manifest/assertions are retained under the diagnostic correction record.

## Completed correction

All 24 guests now match all 72 fields in the independently traced counter
domain (62,322,624 RGB pixels). The final executable rechecked all seventeen
window guests after the sprite, colour and blanking changes. All 600 hires
origin observations agree with the full-resolution origin. The complete
sources, controls, previous failures and producer hashes are recorded in
`test-data/commodore/amiga/ecs-output-phase/lisa-correction/`.

Validation covers 511 focused Rust tests across the common pipeline, all
three Denise variants, runtime graphics and 54 snapshot checks. Tests that
pinned the disproven output tick now assert the counter-backed phase while
retaining exact payloads, collision conditions and restore comparisons. Their
initial failures and final reruns are retained. Both strict Test Kit lanes pass
all six cases, including both alternating phases. Seven original boot-matrix
checks pass unchanged; the A1200 Workbench image is requalified from the exact
predetermined two-hires-sample phase change, inspected in full and passes a
fresh replay. All eight matrix checks are green across these runs.

Release Clippy passes all targets of seven affected packages; the final test
edits pass their recheck. Rustfmt, Ruff, three origin-validator tests and a
byte-identical colour-guest rebuild pass. Snapshot version/layout stays 53.
The complete independent producer images and exact Test Kit assertions remain
unchanged. No native framebuffer translation or geometry change was made.

This closes the demonstrated Lisa phase discrepancy. It does not claim
physical-hardware consensus, recalibrate ECS Copper colour timing, or replace
the outstanding wider graphics-combination campaign.
