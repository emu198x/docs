# Qualify and fix the final-line DMG LY read

[PR #2304](https://github.com/emu198x/emu198x/pull/2304) corrects the monochrome
CPU-visible LY read after the first four dots of the final VBlank line.
The user approved this narrow scope; CGB and LYC/STAT timing stay separate.

The prior diagnosis is in `../2026-11-05-kirby-first-divergence/`. The shared
reference observation is committed in umbrella `198x` at `588b4fe4`:
`reference/by-system/nintendo-gameboy/2026-final-scanline-ly-observations.md`.
This is pinned reference-emulator qualification, not a physical-device capture.

`reference_ly.c` directly drives the unmodified SameBoy 1.0.3 DMG-B PPU,
installs a valid RGB/pixel sink, enables LCDC and advances one LCD dot at a time.
It records a four-dot LY=153 interval, followed by zero while mode 1 continues.
`reference-ly.jsonl` contains the actual output. GateBoy independently models
the early zero; its phase convention is not used as an exact edge measurement.

Build the probe with `clang -O2 -D_GNU_SOURCE -DGB_INTERNAL
-DGB_VERSION='"1.0.3"' -DGB_COPYRIGHT_YEAR='"2026"' -I SAMEBOY_ROOT
reference_ly.c SAMEBOY_ROOT/Core/*.c -lm -lpthread -o reference_ly`.
The regular combined static library internalises this entry point, so compile
the original Core sources together with the probe. All build outputs belong
outside the vendored reference. The loop fails if any transition is absent,
the interval differs from four dots, or mode 1 ends at the LY reset.

Before the fix, the new synthetic boundary test fails at dot 4 (153 vs 0).
The new fixture-gated Kirby test fails at field 240 with the exact original
Emu198x hash. `ppu-red.log` and `kirby-red.log` retain both failures (exit 101).
After the fix, 29 PPU tests pass. The family run passes 183 tests, with 27
fixture-gated tests ignored. The explicit commercial run passes all three
cases with none ignored, including three Kirby hashes and exact save/replay.
Clippy with `-D warnings`, formatting and diff whitespace checks pass.

`verification.json` records the source head, 33 unchanged frozen specimen
hashes, unchanged original Tetris/Mario expected cases and checked pinned
reference identity. No dependencies, specimen bytes or save schemas change.
All original game/boot bytes stay local and are removed with the task cache.
