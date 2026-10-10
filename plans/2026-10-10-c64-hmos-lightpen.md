# HMOS-II light-pen coordinate — issue 1630 item 4

Lane: engineering-frontier accuracy. This is independent of the sprite stage
extension awaiting approval. The current light-pen latch adds two X units for
all models; VICE uses one on HMOS-II. No additional pipeline state is proposed.

1. Reproduce the difference using the testbench's lightpen measurement program
   and physical-chip dumps for 6569, 6567R8, 8565 and 8562R4. Cross-check native
   VICE with the same guest before asserting physical dump parity.
2. Add a failing model-specific coordinate regression that checks the NMOS /
   HMOS relationship over the entire line, including the X wrap, final-line
   suppression and held-low frame retrigger. Reuse the existing chip axis to
   select the offset; leave retrigger constants and NMOS behaviour unchanged.
3. Validate guest RAM results against the native and hardware observations,
   run the chip/package tests, strict image lanes and snapshot replay. Record
   any pre-existing discrepancies rather than changing expected hardware data.
4. Commit one bounded correction. Update issue 1630 without closing its pending
   sprite item. Keep required catalogue validation explicit while the Data
   volume remains unavailable. No new dependency or snapshot layout is needed.

## Reproduction

The physical 6569/8565 and 6567/8562R4 dump pairs each differ only in 247 LPX
bytes, with HMOS one unit lower. The remaining nine LPX entries and all four
other result pages are equal within each pair. Comparing native VICE directly with the raw `.prg` files leaves two LPX
samples, offsets 766/767, four X units apart. The [normalization follow-up](2026-10-10-c64-lightpen-reference-normalization.md)
resolves this: the Makefile applies `makeref.c`'s pre-R03 correction before
embedding the references in the R04 guest. All prepared bytes match native
VICE and Emu198x; the raw files remain unchanged.

The shipping engine has 27 disagreements on each NMOS model and 272 on each
HMOS model. Of these, 25 per model are an independent held-low frame-retrigger
fault: the reset/retrigger currently runs at engine frame wrap, before the CPU
raster counter advances to line zero. `counter_line` reports the previous
frame's last line and the last-line suppression rejects the latch while still
setting `lp_triggered`. VICE resets/retriggers in `vicii_cycle_start_of_frame`,
at the actual line-zero counter transition. Move this existing event there;
keep the retrigger X constants and retained state unchanged. Directed tests
must go red for both families before the correction.

## Correction and validation

The offset now selects the existing chip revision. The once-per-frame reset
and held-low retrigger run at the line-zero raster-counter transition, after
engine cycle 2. No field was added, and snapshot version 18 remains unchanged.

| Model | Native disagreements before | After | Raw pre-R03 differences |
|---|---:|---:|---:|
| PAL 6569 | 25 | 0 | 2 |
| PAL 8565 | 272 | 0 | 2 |
| NTSC 6567R8 | 25 | 0 | 2 |
| NTSC 8562R4 | 272 | 0 | 2 |

All 5,120 native measurement bytes match. The measurement requires the guest's
completion-port write and checks all five pages. Its native fixtures reproduce
byte-for-byte in a second run. The retained raw comparison identifies both pre-R03 samples. Applying the
unchanged upstream converter makes all 5,120 physical-reference bytes match,
without excluding samples. The converter output also matches the references
embedded in the guest and passes through unchanged on a second conversion.

Both new directed regressions failed on the old implementation: HMOS X was one
unit too high, and the held-low frame retrigger left LPY at the old value. The
corrected tests sweep all 128 PAL/NTSC positions for the model difference,
exercise frame retrigger and last-line suppression on all five chip variants,
and preserve once-per-frame behaviour. The early NTSC variant's existing
retrigger constant is preserved; this is not new physical calibration of it.

All ten strict VIC-II fixture tests pass, including the 12-run NTSC greydot
phase test. All 15 runtime snapshot tests pass; the new one exercises 20
model/boundary combinations around frame wrap and the raster-counter edge.
The three-package suite passed 397 tests with 72 fixture/diagnostic skips; the
later directed suppression test also passes. All-target Clippy, formatting,
documentation links and fixture/ignore-reason self-tests pass.

The initial snapshot-test failure (`left: 255, right: 0`) was a test read-path
error: `machine.peek` deliberately reads RAM/ROM beneath I/O. It was corrected
to use `vic_register`, the existing side-effect-free live-chip accessor; no
production workaround was introduced.

The source PR remains draft until the required 13-entry C64 catalogue and
fresh-runtime replay can run with `/Volumes/Data/Library/ROMs/TOSEC` available.
This correction does not approve or implement the pending sprite extension.
