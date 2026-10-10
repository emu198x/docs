# Sprite mode timing evidence

The issue 1630 sprite correction is not complete. Two bounded prototypes were
rejected and rolled back. The [plan](../2026-10-10-c64-hmos-sprite-multicolour.md)
records their results and the proposed stage extension awaiting approval.

## Retained observations

- `before.json.gz`, `after.json.gz`, `delayed.json.gz`: all 17 sprite split
  programs on both PAL chip families, with image hashes and every mismatch
  coordinate. `after` is the dot-only prototype; `delayed` adds one engine
  tick of delay. Model `""` means 6569, `"-8565"` means 8565.
- `restored.log.gz`: the rollback sweep. Its complete JSON was compared with
  `before.json` and was identical, including all 34 hashes and coordinate lists.
- Eight PNGs and `comparison.json`: native VICE 3.10 captures. All eight
  regenerate byte-for-byte with the retained capture script. Six match the
  staged images exactly; the two `ss-mc-hires*` 8565 references differ by 44
  pixels each. Those historical images are not current-native goldens.
- `ss-*.log.gz`: native checkpoint traces after the first completed test frame.
  These are **instruction-end checkpoint observations**, not bus-tick traces.
  The capture runs through the next `$D7FF` completion (256 frames later).
- `stores.log.gz`, `store-comparison.json.gz`: 177 Emu198x store observations
  equal the first complete frame in the native checkpoint trace. Normalize
  the engine/reference cycle conventions before drawing bus-phase conclusions.
- `boundary.log.gz`: native register and chip dump at the first mode switch.
- `sprite-mc-dots.txt`: 64 sequences from the compiled VICE draw functions,
  covering both mode edges, both expansion states and all eight X phases.
  The chip regression in the rejected patch applies them to all five chip
  revisions (160 cases / 5,120 dots). All 160 fail before the dot correction
  and pass after it; full-machine images still fail.
- `dots-before.log.gz`, `chip-after.log.gz`, `packages.log.gz`: red/green
  directed and package results for the rejected prototypes. Green unit tests
  did not override the failing full-machine image evidence.
- `delayed-prototype.patch.gz`, `dot-only-lib.rs.gz`: rejected experimental
  source, retained only to reproduce the measurements. They are not shipping
  changes. The patch expects `sprite-mc-dots.txt` in the chip test fixtures.
- `reference-source-sha256.json`, `native-identity.json`, `sha256.json`: reference
  source, emulator/ROM and artifact identities. No ROM bytes are retained.

The generated pixel expectations establish VICE implementation parity. They
are not new direct measurements of physical silicon. The external testbench's
`spritesplit/8565.txt` separately describes comparisons with a real C64C.

## Reproduce

Run from `Emu198x/emu198x`, with the existing local VICE, C64 ROMs, testbench,
C compiler and Python/Pillow installation. Use a new output directory.

```sh
python3 ../docs/plans/2026-10-10-c64-hmos-sprite-multicolour/capture.py \
  --output /tmp/sprite-mode-native \
  --source . \
  --testbench "$HOME/.emu198x/test-suites/c64-vicii" \
  --roms "$HOME/.emu198x/roms/commodore-c64"

python3 ../docs/plans/2026-10-10-c64-hmos-sprite-multicolour/probe.py \
  --reference ../../emulators/c64/vice-3.10/src/viciisc/vicii-draw-cycle.c \
  --output /tmp/sprite-mode-probe.c
cc -O2 -o /tmp/sprite-mode-probe /tmp/sprite-mode-probe.c
/tmp/sprite-mode-probe > /tmp/sprite-mode-dots.txt
cmp /tmp/sprite-mode-dots.txt \
  ../docs/plans/2026-10-10-c64-hmos-sprite-multicolour/sprite-mc-dots.txt

EMU198X_STRICT_FIXTURES=1 SPRITE_SURVEY_OUTPUT=/tmp/sprite-mode-survey.json \
  cargo test -p runtime-commodore-c64 --release --test vicii_testbench \
  survey_sprite_multicolour_models -- --ignored --nocapture
```

The survey is deliberately a diagnostic, not an image-accuracy gate. Missing
ROMs, references or an incomplete reference set fail the run. The original
indexed-PNG decoder failure was reproduced before enabling PNG expansion;
all 34 comparisons then ran without exclusions.
