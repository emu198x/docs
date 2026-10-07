# Amiga display-register phase sweep

Lane: engineering-frontier. The user approved sweeping resolution and fetch
width changes across fetch boundaries, including wide-to-narrow transitions.

1. Extend `emu198x/test-data/commodore/amiga/midline-display-registers/tools/build.py`
   with an optional phase sweep. Preserve the original eight-case guest bytes.
   Use distinct words, per-line pointer resets, 32 even Copper waits from
   $60 to $9E on lines 128..159, and DDF starts $30/$38. Cover six resolution
   directions, four fetch-width directions and three resolution controls.
2. Build both 13-case datasets twice and require identical ADF bytes. Record
   source, firmware, binary, configuration, guest and capture identities in
   `/private/tmp/emu198x-display-phase-sweep/`. Preserve the native baseline.
3. Capture three adjacent ready fields using the existing documented
   full-resolution FS-UAE diagnostic producer, and native output at frame 180.
   Require all 78 comparisons over the entire recorded common raster. Keep
   unmatched producer edges explicit; do not fit alignment or mask failures.
4. If differences exist, isolate their scanline/phase and trace the actual
   register and DMA deliveries against the registered reference source before
   changing production code. Add a regression that fails under the old path.
   Extend existing stages only where demonstrated. Seek approval for any new
   architecture or additional snapshot compatibility break.
5. Re-run the sweep after corrections and appropriate chip, DMA, snapshot,
   boot and strict Test Kit checks. Run formatting/Clippy if Rust changes.
   Record actual outcomes and remaining limits in the probe README, primary
   observations and `knowledge/decisions/amiga-full-superhires-framebuffer.md`.

No new dependencies, reference rebaselines, vendored edits or unrelated work.

## Discovery

The full baseline sweep completes: 72 of 78 reference-field comparisons pass.
Only FMODE 0→1 fails, at sixteen alternate phases per DDF origin: 240/248
RGB pixel differences per field. The reference repeats the last narrow word
while native output goes black. Registered FS-UAE retains a 32-bit shifter
with bit15/bit31 output taps; the native 16-bit shifter loses its upper half.
`runtime-commodore-amiga/tests/superhires_dma.rs` now has the failing
word37 replay regression. The native trace example accepts an optional line
number; temporary detailed tracing is restored. The exploratory reference
source and executable are restored after logging; its three traced fields
remain byte-identical to the original producer.

The user approved retaining the full serializer register and snapshot v44,
which makes v43 Amiga saves incompatible. The shared Denise core now retains
Lisa’s 32-bit register, reads its selected tap and clocks it even after the
narrow sixteen-bit window has drained. Parallel copy replaces the register.
The existing 64-bit FIFO path remains separate. A dedicated restore test
checks that upper-half bits survive and reappear after widening. No reference pixels have been changed.

## Completed verification

All five steps are complete. The phase sweep passes all 78 unchanged
reference-field comparisons after the retained-register correction. The
preceding 144 comparisons also remain exact: 222 whole-common-raster fields,
192,671,136 RGB pixels, zero differences. All 26 sweep guests rebuild
byte-identically; all 24 original guest ADFs remain unchanged.

The release regression suite passes 801 tests across 66 targets; all eight
strict-asset boot checks pass. Both explicit Test Kit video gates pass six
patterns exactly. Build, formatting, Ruff and strict Clippy pass. The broad
suite retains 31 explicit ignored fixture/campaign tests; only the two video
gates were invoked separately. The isolated HBLANK tail fixture now settles
and latches the wide selector before its direct inner-chip copy, retaining
its original tail-preservation assertion.

Original failures, baseline/final executables, unchanged reference captures,
corrected screenshots, trace logs and SHA-256 records live in
`/private/tmp/emu198x-display-phase-sweep/verification.json`. The logged
producer’s three fields match the original reference bytes exactly; its
unlogged source and executable have been restored. Snapshot v44 is verified
with retained upper-half restoration and explicit v43 rejection.

The scope covers the stated even WAIT positions, resolutions, two origins
and four width directions. Other legal delivery phases, FMODE=2 changes,
plane counts, scrolling/priority/HAM combinations and silicon calibration
remain unmeasured.
