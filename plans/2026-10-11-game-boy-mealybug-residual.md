# Investigate the remaining Mealybug DMG pixels

Issue #316's original 1/24 survey predates the current per-dot PPU. The current
source claims 23/24 exact against DMG-CPU B references, with four dark pixels
at x=0 on lines 19–22 of `m3_lcdc_bg_en_change`. Verify that claim and trace the
remaining physical mechanism before considering a change.

1. Run the existing complete Mealybug gate and per-ROM diagnostic from source
   `ba718712`, preserving logs and image differences. Verify all 24 cases
   execute their LD B,B completion marker and use the correct silicon-specific
   reference. Read the upstream source/provenance and current decision records.
2. Compare the residual guest against the existing SameBoy/GateBoy precedents
   and the hardware photo. Inspect original guest instructions and trace
   background enable, object stall, first-pixel output and register delivery.
3. Make a bounded correction only if an existing-stage bug is demonstrated.
   Do not whiten particular coordinates or relax the pixel baseline. Any new
   persisted stage or snapshot/API change requires a concrete approved design.
4. If corrected, require exact pixels for the full 24-ROM gate, unchanged
   dmg-acid2/mooneye results, affected crate tests, Clippy and formatting. Keep
   evidence and update #316's actual remaining scope before any closure.

Source paths: `crates/nintendo-game-boy-ppu/src/{lib.rs,mode3.rs,fifo.rs}`,
`crates/machine-nintendo-game-boy/src/{lib.rs,tests.rs}`. References are external
under `assets/test-suites/gameboy/mealybug-tearoom/`; no guest bytes are changed.

## Result

The first-pixel boundary is still unresolved. The live trace locates the
four mismatches, and an independent LCD-pin capture rules out GateBoy's
framebuffer capture as the cause of its different answer. No PPU behaviour,
expected image, regression threshold or snapshot schema changed.

Primary observations and source links are recorded in the umbrella reference
library at `reference/by-system/nintendo-gameboy/2026-mealybug-lcd-boundary-observations.md`,
commit `2bb31553`. The software survey and reproducer sources are in
[the evidence directory](2026-10-11-game-boy-mealybug-residual-evidence/README.md).

| Model / capture | Exact CPU-B-selected ROMs | BG_EN differing pixels |
| --- | ---: | ---: |
| Emu198x `ba718712` | 23/24 | 4 |
| SameBoy `208ba4af`, DMG-B, own boot ROM | 15/24 | 4 |
| GateBoy `36797ad4`, native framebuffer | 19/24 | 148 |
| Same GateBoy, separate LCD-pin observer | 19/24 | 148 |

All 24 ROMs reached LD B,B in every survey. The two GateBoy capture paths
agree on all 23,040 pixels of every ROM, not merely their differing-pixel
counts. The original corpus hashes and all measurement rows are preserved.
The existing Emu198x gate passing means its baseline is unchanged; it does
not mean the remaining four pixels pass an exact-image comparison.

### What the traces distinguish

On line 19, Emu198x emits x=0 at dot 102 using LCDC=93. The pending CPU write
is at staged dot 2. Only after emitting that pixel does LCDC become 92, so
x=1 at dot 103 is light. The sprite fetch has already finished, although
its earlier stall put this first pixel on the write boundary.

GateBoy's last captured line 19 puts BG_EN falling on the same phase as
HSYNC falling, while its internal pixel index remains zero. The following
phase raises LCD CLK. It therefore presents a light value to the independent
LCD sampler. Its other 148 mismatches remain, including mid-line background
disables that arrive early relative to the CPU-B expected image.

Spurden's published hardware captures suggested a concrete alternative
observer: shift 159 pixels from the data immediately before each rising CLK,
then latch them with the final data-pin value at CPL. We attached that
observer to unchanged GateBoy signals. Chip code and guest bytes remained
unchanged; only host audio output was discarded. Both reference trees remain
external to this repository.

The observer initially indexed CPL by the current LY, which had already
advanced to the next line. The final host tags each shift sequence with the
LY at the clock edges instead. That correction removes the row offset without
moving pixel data or changing chip timing. A simple clock-edge-only capture
also misses the final direct-data pixel; it is not the verified capture path.

The two clean reference models disagree with each other and with the
CPU-B expectations at this boundary. Neither establishes a justified
first-pixel exception in Emu198x. Issue #316 stays open.

### Next experiment

Use a controlled guest that moves BG_EN and palette writes across the first
visible pixel with several sprite X and fine-scroll positions, and capture
LCD clock, HSYNC and both data pins on identified DMG-CPU B hardware. This
would distinguish register delivery from LCD input sampling. A proposed
persisted output stage would need that evidence and explicit schema/design
approval; the present investigation authorizes no such extension.

The production source worktree was restored after its temporary trace, and
`git status --porcelain` is empty. No production tests were disabled or
rewritten to accommodate the residual.
