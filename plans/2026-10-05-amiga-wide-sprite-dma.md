# Correct wide sprite DMA and validate complete native rasters

1. Add address-sensitive sprite data and control-fetch regressions in
   `crates/commodore-agnus-ocs/src/agnus.rs`. Cover four sprite FMODE encodings
   and all even offsets in an eight-byte block. Verify the tests fail before
   the fix; inspect FS-UAE `fetch32_spr`, `fetch64` and control pointer updates.
2. Correct selected word lanes and control pointer stride in that same service
   method. Preserve control latch timing, request lifecycle and bus ownership.
   Run OCS/AGA Agnus and A1200 tests, including snapshot regressions.
3. Build reproducible, padded wide-sprite guest inputs from the existing neutral
   guest under `test-data/commodore/amiga/wide-sprite-dma/`. Use distinct lanes,
   controlled alignment, sufficient row data and the unchanged SPHX ready record.
4. Capture three adjacent FS-UAE fields at its full native sample clock, and
   capture the rebuilt Emu198x app. Compare every RGB sample in the complete
   common raster at fixed recorded origins; fail on any unmatched pixel and
   verify the comparator rejects pre-fix output. Record non-overlapping edges
   explicitly; do not search alignment or conceal timing residuals.
5. Update primary observations and codebase knowledge. Run strict Clippy, Ruff,
   runtime snapshot/serial regressions and available boot goldens. Search current
   assets for the missing A1000 boot disk; report missing media explicitly.

No API/schema changes or dependencies are required. Historical hires captures
remain useful for their stated coverage; this new native capture adds a full
sample-rate diagnostic gate rather than changing their reference pixels.

Full-raster investigation additionally reproduced missing fixed Lisa HBLANK: selectors off returned no blanking. The new chip edge regression fails before the fix. Restore the existing fixed comparator window in the current selector path, then rerun every full-raster case without masking the edge.


Completed: address-sensitive red/green regressions, padded reproducible guests,
explicit fixed HBLANK correction, 72 full-common-raster comparisons with zero
mismatches, preserved pre-fix failures, and separate recorded upstream reference
producer correction. 378 distinct Rust tests pass; strict Clippy/Ruff and patch
application checks pass. All boot golden assets are required and present. The
recovered private A1000 disk passes through the current media lookup without
an environment override. Primary observations, codebase knowledge and golden
rebaseline provenance are recorded. Evidence and limits are in
`/private/tmp/emu198x-wide-sprite-validation/verification.json`.
