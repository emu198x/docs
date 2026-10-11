# Count SMS sprites while the display is disabled

Engineering-frontier correction. FluBBa's unmodified SMS VDP Test 1.31
reproduces a missing overflow flag with display disabled (test 54), in PAL
and NTSC. Genesis Plus GX passes this check; MAME's SMS sprite selector also
runs independently of display enable. Both references suppress sprite pixel
output separately. The cartridge source describes the observed SMS1 result.

The existing `prepare_line_sprites()` requires display enable before scanning
the attribute table, conflating the sprite-count gate with pixel output.

## Bounded correction

1. In `crates/sega-vdp/tests/blanked_sprite_overflow.rs`, reproduce missing
   overflow via public ports and clock ticks. Cover SMS1/SMS2 PAL/NTSC and
   Game Gear, eight/nine sprites, list termination, off-line sprites,
   transparent patterns, overlap/collision and the blanked framebuffer.
   Confirm the overflow regression fails before editing production code.
2. In `crates/sega-vdp/src/lib.rs`, count Mode 4 sprites regardless of display
   enable, but stop before pattern rendering and collision detection when
   blanked. Preserve existing event timing and the save-state schema.
3. Re-run all twenty cartridge sprite checks in both regions from current
   main plus this correction, preserving original failures and raw RAM.
   Compare unchanged reference runs and inspect completed-page captures.
4. Run focused VDP, SMS/GG machine and runtime tests, formatting and Clippy.
   Publish the bounded source PR with exact-head checks before merging.

No timing-stage or snapshot approval is needed for this gate correction.
The pending native-clock proposal remains separate. The six new collision/
overflow line and H-count failures are not claimed fixed here. Test 46's
vertical-border collision fails in both current implementations and needs
chip-specific investigation. Keep issue #212 open.

The initial probe used unmerged colour-branch head `205bfd85`; production
work starts at main `1cb565cf` and contains none of that closed PR's changes.

## Validation outcome

Source commit `323b2e93ff8a6b2e5cd7e997129c92c37658597d` passes the
previously failing public-port regression. Before the change it reports
`left: 0, right: 64`; both control tests already pass. The corrected suite
covers five chip/region configurations and transparent/opaque patterns.

The full cartridge result changes only test 54 from $FF to zero in both
regions. All other nineteen bytes match the main baseline. Both regions
complete and display all twenty rows in all three runs (main, correction,
reference). [Evidence](2026-10-11-sms-blanked-sprite-overflow/) contains 120
result rows, raw 8 KiB RAM dumps, six inspected PNGs, runners, provenance and
validation logs. No external cartridge or third-party source is bundled.

The 189 focused VDP/machine/runtime tests pass. The one normally ignored
commercial test was separately run with the explicit Alex Kidd input and
passes its 600-frame framebuffer-diversity checks. This is a boot smoke,
not a gameplay or Sonic/Out Run raster comparison. Clippy and formatting
pass. The separate full ZEXDOC process is still in progress.

Main's grey test-page background is the known independent colour fault
from closed PR #1726. The new source branch does not include that fix.

## Reproduction

Build each pinned Emu198x revision with `cargo build -p
machine-sega-master-system --message-format=json`. Select that build's
`machine_sega_master_system` rlib from its compiler-artifact records, then
compile the retained Rust runner using Rust 1.99.0, edition 2024, that exact
`--extern` and its target's `-L dependency=.../debug/deps` directory.

Build the unmodified reference revision with `make -f Makefile.libretro
platform=osx CC=clang -j4`. Compile the retained C runner with clang, the
reference's `libretro/libretro-common/include` include directory and its
`genesis_plus_gx_libretro.dylib`. Run from the dylib's directory so its relative
install name resolves. The configured empty system directory supplies no BIOS.

Both runners take `ROM REGION OUTPUT_PREFIX FRAMES`: the hash-pinned
external `VDPTEST.sms`, `ntsc-u` or `pal`, a fresh prefix, and `1800`.
They output PPM, RAM and stdout metadata; PNGs are lossless conversions of the
PPMs. Each input pulse is in the retained runner, not injected into guest RAM.
Verify the completed sprite page before interpreting zero result bytes.

Primary observation record:
`reference/by-topic/vdp-sms/2026-vdptest-sprite-observations.md` in the umbrella.
