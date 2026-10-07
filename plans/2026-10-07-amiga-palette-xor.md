# AGA palette-XOR phase

Lane: best-in-class campaign. Continue the user's approved accuracy investigation.

1. Reproduce the three palette-XOR residuals with the current native build and
   unchanged guests/reference fields. Retain executable and input hashes.
2. Trace BPLCON4 delivery and BPLAM visibility through the existing Lisa stages.
   Compare the registered UAE implementation and independently measured raster
   origins; distinguish register propagation from output-coordinate errors.
3. Add a regression that fails for the demonstrated cause before correcting
   `crates/commodore-denise-aga/` or the responsible existing board stage.
   Preserve snapshot 54 unless concrete evidence requires an approved extension.
4. Rebuild and compare all three guests, then the affected mid-line corpus.
   Run chip, board, snapshot and video checks appropriate to the changed stage.
5. Record source-qualified observations in the primary reference library, retain
   replayable evidence in `test-data/commodore/amiga/`, and update the relevant
   existing decision and changelog. Software agreement is not silicon calibration.

No image alignment search, changed reference pixels, new dependencies or clocks.

## Reproduced cause and bounded correction

Current snapshot-54 native captures reproduce 128 differing samples per field
in all nine comparisons. Native counter trace accepts BPLCON4 at counter 260
and changes XOR at 262.5. The independently origin-qualified reference edge is
261.5. UAE's `expand_drga_early` accepts BPLAM at idx0; the second lores half's
unaligned renderer latches it at native sample 2. This is six native samples,
not the old ten. The former calibration included four padded reference-buffer
samples in the timing measurement.

Use tap 4 of the existing ten-sample history. Its encoding, clocking, and raw
register mirror stay intact; there is no new snapshot state. The revised
regression failed at native offset 6 before the correction (expected green,
observed old blue). A trace-only instrumented reference build is also being
checked against the untouched reference fields.

## Verified result

The trace-only reference confirms BPLAM input at counter 260 and visible XOR
at 261.5 in fields 9..11. Its constant-word fields are byte-identical to the
previous reference. All three variants now match their origin-qualified
reference rasters exactly. The replay archive retains nine pre-fix fields,
each with 128 mismatches, as negative controls.

The affected 24-guest mid-line corpus passes all 72 field comparisons (zero
RGB differences). This is a fresh run of that corpus, not a claimed rerun of
the full 128-guest sweep. Chip/board tests pass 247 checks; register replay
passes 10; snapshot replay passes 56. All six A1200 Test Kit patterns are exact.
Strict Clippy passes, the native release binary is rebuilt, and the archive
replay checks both corrected fields and negative controls. Snapshot 54 remains
compatible. No reference pixels, raster origins or crop contracts changed.

Evidence: `test-data/commodore/amiga/ecs-output-phase/palette-xor/validation.json`
and its README/replay script in the code repo. Primary observations and the
full-superhires decision record identify the superseded timing claim.

The AGA top-of-field line, OCS right edge, and programmable edges around the
counter reset remain separate investigations. The present guests do not
calibrate sprite-bank timing, arbitrary CPU-write phases, or silicon timing.
