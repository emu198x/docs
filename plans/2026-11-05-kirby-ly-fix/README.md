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
reference identity. The published PPU receives patch version 0.1.1, a changelog entry and an
updated consumer requirement. No new dependencies, specimen bytes or save
schemas change.
All original game/boot bytes stay local and are removed with the task cache.

The first hosted run correctly rejected editing published 0.1.0 without a
new version (`published-version-red.log`). Follow-up commit raises the PPU
to 0.1.1; registry API confirms that version is new. The final explicit
commercial run (3 tests) and PPU run (29 tests) pass again at the updated
version. Hosted checks rerun on that final head.

Additional reference scope check: `reference_mono.c` repeats the same bounded
probe for DMG-B, MGB, SGB and SGB2. Invoke it with zero, one, two or three dummy
arguments respectively. SGB uses the documented NO_SFC model to isolate its
Game Boy PPU, with border disabled and a valid pixel sink. All four runs
report the identical four-dot readable-153 interval and continued mode 1;
the separate `reference-{dmg,mgb,sgb,sgb2}.jsonl` files retain the outputs.
This checks the shared monochrome path without expanding the production fix.

Standalone delivery check: `cargo publish --locked --dry-run` for PPU 0.1.1
packages and verifies successfully. Inspected the generated `.crate` archive:
its manifest says 0.1.1 and its `src/lib.rs` exactly matches the tested source.
`package-verification.json` retains both hashes. This was a dry run; no crate
was uploaded and no suite release was cut as part of this fix.

PR #2304 merged at `161a6ce00b9f830640fef75101a29d71561ea75f`; #2182 is closed.
All hosted checks passed on tested head `f3d10a7d95d4d5ba19d6a735ea2453ecf0274ab3`
([CI run](https://github.com/emu198x/emu198x/actions/runs/42026477721)).
The merged and tested Git trees are identical:
`d343cc7a9fa9aaf597e6cae382b26683bd882e5d`.
