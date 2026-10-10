# MARIA scanline border output

Address Atari 7800 issue #198: active pixels use live BACKGRND, but the machine
fills the entire border once at frame start. A later register write leaves the
border one frame behind. The border also ignores CTRL.BC and colour kill.

This is engineering-frontier accuracy work. Keep the existing scanline renderer,
framebuffer geometry, public API and snapshot fields. No new dependencies.

## Evidence and design

The shared Atari 7800 reference, section 9b, describes selectable background
extension versus a black horizontal border. Existing MiSTer `line_ram.sv`
selects black when the border is active and CTRL.BC is clear, otherwise the
current background register; `maria.sv` then applies colour kill to that output.
The reference has been consulted before changing rendering behaviour.

For every rendered scanline that maps into the existing framebuffer window,
paint that row's background and side borders from current BACKGRND/CTRL. Overlay
the active line buffer as before. Remove the machine's frame-start repaint, so
already-rendered rows retain the colour they had when produced. Retain the public
`fill_border()` method as an explicit image-clear operation for compatibility.

The existing PAL vertical placement is explicitly provisional in `border_top()`
and the framebuffer-window decision. This change preserves that mapping and its
vertical background policy. It does not claim new PAL placement, vertical
blanking, DMA/display alignment or within-scanline register timing accuracy.

## Tasks and verification

1. Add failing chip regressions in `crates/atari-maria/src/lib.rs` for successive
   background values, both regions, BC on/off and colour kill. Require existing
   rows to remain unchanged. Cover PAL rows outside the active band too.
2. Add a machine regression in `crates/machine-atari-7800/src/lib.rs` with a
   synthetic 6502 cartridge writing BACKGRND and WSYNC. Verify border/active
   agreement on distinct raster rows from CPU execution.
3. Implement row painting using the existing scanline counter and window
   mapping. Remove only the frame-start repaint. Verify the tests fail before
   the correction and pass afterwards; retain reference paths and logs.
4. Run both packages' tests, relevant strict fixture tests if staged, Clippy,
   formatting and hygiene checks. Inspect snapshot round-trip coverage and
   verify no schema/API changes. Update the public evidence record and local
   knowledge; commit, push and merge after CI. Close #198 only with the stated
   scanline-level scope verified.

## Results

Verified source commit `3c40da9e6e642d61f445fea195e805e482c5336d`, tree
`0caaad0007d2487b61471373cd20023eed547ca3`. The four affected files are
unchanged from the tested pre-rebase commit `2c37dcee`; the rebase adds only
the unrelated shared-6502 interrupt validation gate.

- Before the correction, all three new chip regressions fail. The CPU-driven
  colour-bar regression also fails: `border differs from background on row 0`.
- After the correction, 21 MARIA unit tests, 22 machine unit tests and both
  synthetic cartridge tests pass. This includes the existing snapshot
  round-trip, both regions, all 16 combinations of region/DMA/BC/colour kill,
  distinct colours on successive rows, preservation of past rows, and the
  existing PAL window across raster wrap.
- The first package run exposed an old synthetic boot assertion that required
  a uniform whole frame despite the cartridge leaving BC clear. Its corrected
  invariant checks every active pixel and both black borders. The cartridge
  that loops before writing BACKGRND still fails that boot predicate.
- Asteroids runs 200 frames and passes the render smoke check. That check now
  counts colours only within the active picture, so a black border cannot
  turn a solid background into a false game-render pass. Supplying the solid
  synthetic cartridge deliberately fails: `screen never rendered (1 colours,
  76800 non-background px)`.
- Focused all-target Clippy with warnings denied, workspace formatting, fixture
  guard hygiene, ignore-reason hygiene and doc-link checks pass. The latter
  checks run their own positive and negative self-tests. Existing tracked
  backlogs are unchanged.

The first attempt to run the machine regression used an unqualified exact
filter and selected zero tests. That output is not validation; the retained
`machine-red.log` uses the full `tests::` name and records an actual failure.
`first-green.log` records the stale synthetic assertion failure, not a passing
suite. `packages-green.log` is the complete corrected package run.

## Sources and reproduction

Primary reference: `reference/by-system/atari-7800/atari-7800-reference.md`,
section 9b, derived from Atari's software guide. Implementation precedent:
Atari7800_MiSTer revision `29aaacbbed127c670972c8a0a950ca82dc87e5df`,
`rtl/Maria/line_ram.sv` lines 50–66 (live background versus black border), and
`rtl/Maria/maria.sv` lines 126 and 242 (colour-kill mask and CTRL.BC wiring).
This is source inspection, not an executed RTL comparison. No reference
implementation code or cartridge payload is copied into the change.

Asteroids fixture: `Asteroids (1987)(Atari)(NTSC).a78`, SHA-256
`259c92f46ddbe143365369e66d1943a8a5654566ec3dc9355775adb28243bb35`.
The fixture is local and is not committed.

Run from the source repository:

```sh
cargo test -p atari-maria -p machine-atari-7800
EMU198X_ATARI_7800_CART='/path/to/Asteroids (1987)(Atari)(NTSC).a78' cargo test -p machine-atari-7800 --test cart_boot cart_boots_without_panic -- --exact --ignored --nocapture
cargo clippy -p atari-maria -p machine-atari-7800 --all-targets -- -D warnings
cargo fmt --all --check
python3 scripts/check-fixture-guards.py --self-test
python3 scripts/check-ignore-reasons.py --self-test
python3 scripts/check-doc-links.py --self-test
```

The original cart resolver can fall back if an explicit path is missing; the
recorded positive and negative runs both use existing files. The smoke check
proves rendered game output, not complete cartridge or DMA timing accuracy.
Logs are retained in the adjacent `2026-10-10-maria-live-border/` directory.
