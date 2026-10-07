# Amiga mid-line display-register fixes

Lane: engineering-frontier. User approved extending the existing timed chip
stages and rejecting older Amiga save states on 2026-10-05.

The existing 24 guests reproduce four BPLCON0 transitions, FMODE 1→3, and a
BPLCON4 XOR edge ten native samples early. Preserve their original captures.

1. Preserve the baseline executable and images in `/private/tmp/emu198x-midline-display/`.
2. Add a failing native-sample XOR regression in `crates/commodore-denise-aga/`.
   Extend Lisa's existing output stages in `src/lib.rs`, retaining raw register
   mirrors and serializing in-flight state. Compare all three XOR guests with
   the unchanged full-resolution reference fields.
3. Investigate Alice BPLCON0 propagation and Lisa's serial-mode transition in
   `crates/commodore-agnus-ocs/src/agnus.rs`,
   `crates/common-commodore-amiga/src/denise.rs`,
   `crates/common-commodore-amiga/src/denise_chip.rs`,
   `crates/commodore-denise-aga/src/lib.rs`, and
   `crates/machine-commodore-amiga-a1200/src/lib.rs`. Separate raw and active
   copies in the existing stages. Add grant/serial regressions before fixing.
4. Isolate FMODE 1→3 against the distinct-word and pointer-reset cases. Verify
   the reference's grant-time fetch width and serializer load width before
   changing either stage. Add a regression that detects the observed failure.
5. Bump `crates/runtime-commodore-amiga/src/snapshot.rs` to v43 and update
   `tests/snapshot_roundtrip.rs`; verify pending writes resume identically and
   old-version input is rejected explicitly.
6. Rebuild and compare all 24 guests (72 unchanged reference fields) over the
   entire recorded common raster. Re-run static wide-DMA probes and relevant
   chip/board/snapshot tests, strict-asset golden matrix, formatting and Clippy.
7. Record actual evidence and remaining limits in the primary observations,
   chip changelogs, and `knowledge/decisions/amiga-full-superhires-framebuffer.md`.

No dependencies, reference-image changes, alignment searches, or broad
refactors. Each correction must explain its cause and pass before the next.

## Completed verification

All seven steps are complete. Alice DMA copies, Lisa output selectors,
continuous serial phase, FMODE data-width latching, complete holding-group
replacement and the ten-native-period XOR output stage are covered by
regressions. Snapshot v43 preserves their pending state and rejects v42.

The wider copy boundary exposed a Workbench regression: the comparator had
used a DDF-relative origin. It now uses the physical Denise counter. The
existing Workbench golden remains unchanged; all eight strict-asset boot
checks pass. The new counter test was verified failing under the old input
and passing with the correction. Diagnostic queries now expose the retained
serial history, cursor, phase and held sample consistently.

All 144 whole-common-raster reference comparisons pass with zero differences:
72 mid-line and 72 static sprite/playfield fields, 124,975,872 RGB pixels.
The release regression run passes 799 tests across 66 targets. The broad run
leaves 31 explicit fixture/campaign tests ignored; both Test Kit video gates
were invoked separately and pass all six patterns exactly. Release build,
formatting, strict Clippy and Ruff pass. The optional trace patch applies
cleanly and recreates both logged source files exactly; its nine fields
remain byte-identical to the original reference captures.

Original failures, unchanged references, corrected captures and SHA-256
evidence are retained in `/private/tmp/emu198x-midline-display/fix-verification.json`.
This establishes agreement with the registered software-reference probes,
not independent silicon calibration or accuracy for untested combinations.
