# Verify DLI effects in the framebuffer

Continue the approved MARIA correction. The native interrupt probe counts
executed handlers but does not verify their visible effect. Add that missing
acceptance gate without selecting an unqualified physical NMI delay.

1. Add `2026-10-11-maria-dli-raster-outcome/probe.rs`: run CPU guests in both
   regions, with zone heights 1/2/3/16 and absent/all/alternating/single flags.
   Each handler toggles BACKGRND between two distinct palette colours.
2. Observe real descriptor fetches and CPU register writes. At a point well
   inside each displayed line, compare the framebuffer with the colour implied
   by the requested interrupts. Separately check writes against rendered colour
   so delivery and rendering failures remain distinguishable.
3. Execute through the native machine using a temporary test module, preserving
   pre-existing source edits byte for byte. Save bounded logs and hashes. A
   negative control redirects the handler's colour write to a palette register:
   handler execution alone must not pass the framebuffer check.
4. Validate the complete nonempty case inventory, guard failure handling, run
   formatting and lint, and record exact failures. This is a coarse visible
   outcome gate, not evidence for an exact interrupt assertion tick. PR 1704
   stays draft until the approved timing gate is resolved.

No production API, timing or schema change in this step. Use the Rust skill
for the diagnostic module. Existing native playback qualification supplies
the framebuffer coordinate mapping; the Atari software guide supplies
upcoming-zone DLI ownership. The probe will not infer physical timing from
the current implementation.

## Result

The native machine fails **16 of 32 cases**. Eight no-interrupt controls and
eight single-interrupt cases pass. The matrix covers both regions, four zone
heights and four flag patterns. Each case checks 192 displayed scanlines:
**6,144 framebuffer samples** in each capture.

Two failing cases are the known consecutive one-line interrupt loss: NTSC
requests 243 handlers and executes one; PAL requests 293 and executes one.
The other **14 cases execute every requested handler**, but their framebuffer
colours match the preceding line's requested state instead of the current
line's state. All 191 adjacent-line comparisons per case confirm that shift.
This reveals a visible one-scanline delay that an end-of-frame handler count
cannot detect. Across the baseline, 900 sampled pixels have the wrong colour.

All 6,144 samples match the most recent actual CPU BACKGRND write. The current
renderer carries the guest writes correctly; the line-boundary NMI assignment
delays their execution. The probe records actual descriptor-flag reads, not
a duplicate DMA scheduler. For repeating flags the closest sampled pixel is
570 native ticks after the latest flagged descriptor read. This generous
deadline distinguishes a full-line delay without selecting among the disputed
short assertion delays. It does not qualify an exact physical pulse edge.

The synthetic cartridge's handler counts in 16 bits, alternates two distinct
palette colours, writes BACKGRND and returns. Redirecting that store to a
palette register leaves handler execution intact but makes **24 cases fail**,
including 22 whose final handler count still agrees. It produces 3,072 wrong
samples while retaining zero disagreements with actual BACKGRND bus writes.
This confirms that the pixel check measures the visible outcome.

Both Cargo runs exit 101. The baseline reports:

```text
assertion `left == right` failed: requested DLIs must produce the guest's visible colour changes
  left: 16
 right: 0
```

Nine capture tests reject incomplete/duplicate cases, missing pixels or
requests, an insufficient deadline margin, compiler failure, missing executed
tests and a false completion summary; a complete synthetic green capture is
accepted. Ruff lint/format, Rust formatting and diff hygiene pass. The runner
restored the source byte for byte, preserving the existing POKEY work. Source
HEAD and exact source/probe hashes are recorded in the adjacent `summary.json`.

The [Atari Software Guide](https://7800.8bitdev.org/index.php/7800_Software_Guide)
places a zone's DLI after the preceding zone's DMA. The existing
[physical timing investigation](2026-10-11-maria-dynamic-raster-clock.md)
still leaves the exact external assertion edge unresolved. This new test
closes a validation-coverage gap; it does not fix production timing or settle
that disagreement. Source PR 1704 remains draft and issue 197 remains open.

## Reproduction

Run with exclusive access to the machine source file. Pre-existing edits are
preserved. Capturing the failing baseline exits **1**, not success.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-dli-raster-outcome/run_probe.py \
  ../emu198x /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-dli-raster-outcome -v
```
