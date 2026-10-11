# Master System raster interrupt validation

Engineering-frontier investigation for source issue #212. Capture a reference
trace before changing timing. No production behaviour or snapshot changes are
approved by this investigation alone; propose the bounded correction once the
failure and its cause are demonstrated.

1. Pin Genesis Plus GX (`c7ecd07f0a08db1cdd6871d788476bfac55be638`) and inspect
   MAME's independent 315-5124 timing. Reconcile coordinate origins before
   comparing dots or scanline numbers. Consult the primary/reference SMS VDP
   material and existing tests; no donor CPU/timing code is ported.
2. Build the vendored reference in a temporary copy and run an original,
   deterministic SMS cartridge. The cartridge programs R10, services IRQs
   through a real Z80 ISR, reads status to acknowledge, and changes backdrop
   colour to expose the split. Retain RAM observations and rendered frames.
3. Run the identical cartridge against `machine-sega-master-system`; compare
   first split, repeated splits and near-vblank boundaries, with PAL/NTSC and
   counter reload controls. Source targets are `crates/sega-vdp/src/lib.rs`
   and `crates/machine-sega-master-system/tests/`; add permanent regressions
   only after the oracle differences are explained.
4. If a correction needs a new latch or saved stage, record the concrete design
   and request schema approval. Do not replace CPU pin timing with callbacks
   or a scanline shortcut to make the reference match.
5. Run available real cartridges and compare to the reference. Issue #212 also
   requires Sonic and Out Run captures; missing inputs remain explicit, and a
   passing synthetic test alone cannot close that acceptance item.
6. Run focused tests/Clippy, preserve a failing baseline, update the issue and
   publish evidence. Merge any implementation only after exact-head CI passes.

Initial source inspection suggests a phase mismatch: Emu198x updates the line
counter after rendering a line, while Genesis Plus GX processes it before the
active line's CPU work. MAME schedules its SMS HINT at horizontal position 26
with active drawing at position 63. These use different coordinate systems;
this is a hypothesis until a common guest trace demonstrates the effect.


## First live finding: background colour zero

The same R10=31 cartridge runs in the compiled Genesis Plus GX core and Emu198x.
Its ISR records repeating V counts 31,63,95,127,159,191 in both. However, the
active picture is black in Genesis Plus GX and shows alternating border-colour
bands in Emu198x. This is a colour-selection fault that contaminates the raster
probe: all background tile pixels are zero, CRAM[0] is black and R7 alternates
between red and green entries in the sprite palette.

The Sega Mark III software manual's colour, background and sprite/background
priority sections distinguish tile palette selection from zero's sprite-priority
behaviour. MAME's `draw_scanline_mode4` writes the selected palette entry even
for zero, and its compositor uses zero only for sprite priority. Our
`render_pixel` wrongly substitutes R7 for a zero pixel when priority is clear.

Bounded correction: retain existing sprite priority and left-column masking,
but when no sprite wins, always draw the selected background palette entry.
No new state, APIs, architecture or snapshot format. Add a matrix regression
for SMS1, SMS2 and Game Gear, both palettes and priority settings, with sprite,
nonzero background, blanking and left-column controls. Preserve the original
live failure and compare the same guest again after the correction. Correct
the erroneous zero/backdrop wording in the shared VDP reference as part of
recording the primary-source evidence. Then resume the timing investigation.


## Colour correction validation

Source head `8ff772b205f88b1b13f1e51d360877ea3e8a1cbe`:
173 focused tests pass, one commercial-ROM test is ignored by default; that
Alex Kidd test was also run explicitly and passes. Clippy, formatting and the
synthetic-image regeneration check pass. The 24-row colour matrix fails in
six rows before the fix and passes afterwards. The same unmodified guest's
49,152 active pixels all mismatch before and all match Genesis Plus GX after.

The broader inventory exposed five test targets whose fixture setup relied
on the colour-zero bug. The fixes retain the assertions: initialise the
background colour actually exposed by a missing sprite; select palette zero
for the CRAM output-level tests; blank the display for the R7 test and R7
latency cartridge. Boot cartridges now initialise background colour zero as
well as their border colour. Their display remains enabled. Genesis Plus GX
runs the regenerated SMS/GG boot cartridges as wholly green 256×192/160×144
pictures and the blanked raster cartridge as a two-colour frame.

The blanked raster test retains its CPU-latency bounds. It is explicitly a
consistency test and does not satisfy #212's active-display reference gate.
No test was disabled or removed, and no timing implementation was changed.

The primary observation and corrected hardware reference are committed in
umbrella `0eddb4ae` (not pushed):
`reference/by-topic/vdp-sms/2026-background-zero-observations.md`.

## Reproduction and evidence

[Evidence folder](2026-10-11-sms-raster-timing/) contains the original cartridge,
its generator, both headless runners, before/after pictures, RAM observations,
logs and hashes. The cartridge is original project-authored Z80 code; no
commercial ROM is bundled. Alex Kidd is identified by SHA-256 in metadata.

1. Export the pinned Genesis Plus GX revision to a temporary directory and run
   `make -f Makefile.libretro platform=osx CC=clang -j4` there. The original
   vendored checkout remains read-only.
2. Compile `reference_host.c` against its
   `libretro/libretro-common/include/libretro.h` and resulting dylib. Run from
   the dylib directory (its install name is relative). The host's empty BIOS/save
   directory is `/private/tmp/198x-sms-raster-evidence/empty`.
3. `python3 make_guest.py 31 split31.sms` produces the unchanged comparison ROM.
   Run `reference_host <absolute-ROM> ntsc-u <output-prefix> 30`.
4. `cargo build -p machine-sega-master-system`; compile `emu_probe.rs` with the
   matching Rust toolchain, `--edition=2024`, `-L dependency=<target>/debug/deps`
   and `--extern machine_sega_master_system=<matching rlib>`. Run it with the
   same four arguments. The runners emit a PPM and RAM dump and fail on missing
   output/setup, rather than returning a passing comparison.
5. Compare the reference 256×192 image to Emu198x's active rectangle
   `(12,25)-(268,217)`. Before the colour fix, 49,152 pixels differ. Afterwards
   zero differ. That active rectangle is the declared NTSC crop, not a fitted
   offset chosen to minimise differences.
6. Run the focused source checks:

```sh
cargo test -p sega-vdp -p machine-sega-master-system -p runtime-sega-master-system --no-fail-fast
cargo clippy -p sega-vdp -p machine-sega-master-system -p runtime-sega-master-system --all-targets -- -D warnings
cargo fmt --package sega-vdp --package machine-sega-master-system --check
python3 test-data/sega/synthetic-cart/build-synthetic-cart.py --check
```

The commercial-game run uses `EMU198X_SMS_CART` and
`cargo test -p machine-sega-master-system --test cart_boot -- --ignored`.
The test is a boot smoke check, not a pixel comparison against Alex Kidd.

Next: change the timing guest to write a tile-palette entry or scroll register,
then trace phase and compare split coordinates. The initial ISR V-count rings
agree on the repeating values 31,63,95,127,159,191; this alone cannot establish
horizontal phase. Sonic and Out Run captures remain unfulfilled acceptance work.

Source [PR #1726](https://github.com/emu198x/emu198x/pull/1726) has head
`205bfd85db9cf91bd7489e1d4dec7d7a32b8ef40` after formatting the generator. Ruff lint/format and the
regeneration check pass; formatting changes no cartridge bytes. The functional
test logs above are from its parent `8ff772b2`.
