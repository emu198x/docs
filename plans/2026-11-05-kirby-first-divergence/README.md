# Kirby: final-scanline LY read changes startup

Current main reproduces #2182 exactly. The first game-visible disagreement
is its first LY read at `$0150` (`LDH A,[$44]`): Emu198x returns `$99`,
SameBoy returns `$00`. At the following instruction (`$0152`), A therefore
already differs. The CPU observers sample different fetch phases, so their
four-dot DIV offset is not evidence of a timer bug. After `CP $90`, the conditional branch at `$0154` falls
through in Emu198x and loops to `$0150` in SameBoy. This precedes the later
sprite-coordinate differences; replacing the framebuffer golden would hide it.

## Evidence and limits

Source commit: `9d9f756a681c9a04a64f44fbd18ad05f52e82895`. SameBoy 1.0.3,
DMG-B, source hashes in `sameboy-sources.json`. Game and original boot ROM
identities are unchanged from the October 28 qualification. No input is sent.
Field zero is the first real LCD completion after BOOT unmaps; LCD-off
callbacks are excluded. No commercial ROM, boot, screenshot, or memory dump
bytes are retained here.

| Checkpoint | Original differing pixels | Diagnostic run differing pixels |
|---|---:|---:|
| 240 | 201 | 0 |
| 480 | 135 | 0 |
| 720 | 177 | 0 |

The diagnostic changes only the returned CPU bus value for LY when BOOT is
already unmapped, the internal scanline is 153, and dot is at least 16. It
returns zero instead of 153, without moving a clock, scanline, interrupt or
frame boundary. The first affected read is at internal line 153, dot 424.
All three resulting screen hashes exactly match the unchanged reference.
**Dot 16 is a deliberately late experimental guard, not a proposed hardware
reset edge.** This establishes the causal read for these checkpoints; it
does not qualify the exact early reset edge or LYC/STAT interrupt behaviour.

All nine original game/checkpoint hashes reproduce, including Tetris and
Mario's six exact matches. Passive consecutive-field, CPU, LY and DIV
observers preserve all six Kirby baseline hashes. The DIV observer finds
no guest DIV reads; the three reference DIV reads are the probe's checkpoint
printouts. DIV-based random seeding does not explain this run.

`report.json` retains 720 consecutive field comparisons, separate VRAM/WRAM/
OAM hashes and mismatch counts, the first seven post-boot instruction
observations, the causal LY read and the three diagnostic results. VRAM agrees
from field 2 onward. Initial screen differences occur at fields 1, 6, 11 and
16; persistent title differences begin at field 62. At field 240, all six OAM
mismatches are sprite X coordinates, one pixel apart. These observations do
not make the earlier LCD-off transitions into independent rendering bugs.

## Mechanism and sources

Emu198x `crates/emu198x-nintendo-game-boy-ppu/src/lib.rs::read_ly` returns
its internal scanline throughout VBlank. Its only special case is an early
next-line read on visible lines. It has no final-scanline early zero case.

Pinned SameBoy `Core/display.c`, block `/* Lines 153 */`, sets the readable
LY to zero early while retaining the final line's timing and mode 1. GateBoy
`src/GateBoyLib/LogicBoy.cpp` independently separates readable LY from its
internal frame/line phase, resetting the readable value during that line.
The two implementations use different phase conventions; neither has been
used here to claim an exact Emu198x dot threshold. The gate model is read-only
precedent, not copied code or a physical-machine measurement.

The held Nintendo Programming Manual v1.1 and its system-reference
summarisation describe 154 lines but do not settle this early read edge.
[Pan Docs issue #646](https://github.com/gbdev/pandocs/issues/646) records the
same documentation gap and the early LY reset before VBlank finishes.
A proper fix needs source-backed edge tests, including LYC/STAT effects,
rather than the diagnostic's arbitrary late guard. No production fix or
new hardware timing decision is included in this investigation.

## Reproduce

Create an isolated checkout at the source commit above. Apply `observer.patch`
and place `emu_probe.rs` at
`crates/runtime-nintendo-game-boy/examples/kirby_probe.rs`. The three archive
paths and members are listed in `rom-identities.json`; extract read-only local
copies named `kirby.gb`, `tetris.gb` and `mario.gb`. Identify the original
256-byte DMG boot by the SHA-256 in `identity.json`.

Build the Rust example with `cargo build --locked --release -p
runtime-nintendo-game-boy --example kirby_probe`. Build the pinned SameBoy
static library with all OBJ/LIBDIR outputs outside its vendored source; compile
`sameboy_probe.c` using `clang -O2 -I SAMEBOY_ROOT sameboy_probe.c
libsameboy.a -lm -lpthread -o sameboy_probe`.

Both probes take `ROM BOOT OUTPUT_PREFIX`. Run each without extra environment
variables for checkpoints 240/480/720. Set `KIRBY_ALL_FIELDS=1` for all 720
fields plus `.mem` observations, `KIRBY_CPU_TRACE=1` for at most 150,000
post-boot instruction observations, or `KIRBY_LY_TRACE=1` for at most 32 LY
reads. `KIRBY_BUS_TRACE=1` observes DIV reads. On the Rust probe only,
`KIRBY_FORCE_FINAL_LY_ZERO=1` enables the diagnostic counterfactual.
All execution loops have fixed bounds. SameBoy memory observations copy raw
arrays directly: calling memory read helpers for VRAM/OAM from a display
callback can resynchronise the display and is unsuitable for a passive probe.

`python3 capture.py CAPTURE_DIRECTORY > report.json` rebuilds the report from
the local-only outputs. `python3 verify.py` checks the retained comparison and probe hashes.
The negative control changes a diagnostic hash and must exit nonzero.

## Next action

Agree a production design for CPU-visible early LY reset with model-specific
edge evidence, independent boundary regressions and the qualified Kirby
checkpoints. Keep the internal scanline/frame clock intact. Qualify any
LYC/STAT behaviour separately instead of silently reusing the CPU-read rule.

After restoring unmodified source, the existing explicitly enabled Tetris and
Mario screenshot/save-replay regressions pass (2 passed, none ignored).
`qualified-tests.log` retains the output. This is diagnostic evidence, not a
new passing Kirby regression or a released fix.
