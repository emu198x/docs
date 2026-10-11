# VIC-II unused-register readback

Lane: engineering-frontier accuracy. Source baseline: `6779586a`.

The HMOS-II issue audit found that `$D02F–$D03F` return the retained DMA
byte in both `read` and `peek`. The primary register reference says these
addresses read `$FF`; VICE 3.10's `viciisc/vicii-mem.c` agrees. Existing tests
only compare unused addresses to each other, so cannot detect this error.

1. Generate an original 6502 guest that reads every unused register in all
   sixteen mirrors before and after writes. Capture its 544 results on native
   VICE for all five chip profiles, with a completion sentinel and exact input
   identities. Keep the original generator and retained capture evidence here.
2. Add a hermetic machine regression using that guest and a chip regression
   across all five models and all possible retained-bus values. Run them red
   on the current implementation; require actual CPU completion before judging
   the output. Source files: `crates/mos-vic-ii/src/lib.rs`,
   `crates/machine-commodore-c64/src/machine.rs` and its `test-data/`.
3. Return `$FF` from the existing unused-register branches. Preserve register
   masking, write handling and colour-RAM bus behaviour. No new state, API,
   timing or snapshot schema. Run chip, machine and runtime tests, Clippy and
   formatting. Commit the bounded correction and merge only after CI passes.
4. Correct issue 1630's completed mode/fetch/light-pen items and record the
   separate unresolved colour-RAM bus problem with source-backed boundaries.

Provenance: `reference/by-topic/vic-ii/vic-ii-registers.md`, register map;
Christian Bauer, *The MOS 6567/6569 video controller (VIC-II) and its
application in the Commodore 64*, register reference; VICE 3.10
`viciisc/vicii-mem.c`, unused cases in `vicii_read`. Native VICE is implementation
precedent, not a physical-hardware capture.

## Observed result

Native VICE returns all 544 expected bytes on each of five profiles (2,720
CPU reads). Each capture includes the `$A5` completion sentinel. The guest's
byte identity is recorded in `comparison.json`; the production regression
embeds those exact bytes. Emu198x has four shipping C64 board profiles, all
covered by the CPU regression; the fifth VIC-II model is covered directly.

Both regressions failed on the old implementation with `left: 0, right: 255`.
The fix changes only the unused cases in `read` and `peek`. The existing bank
selection test now observes the retained DMA diagnostic directly instead of
expecting an unused hardware register to expose it. No fetch behaviour changes.

The ordinary chip/machine/runtime run passes 399 tests, with 74 external-input
or diagnostic tests ignored. Native VICE needs execution outside the macOS
sandbox: the initial sandboxed process died with SIGSEGV before producing a
capture. The successful run was repeated from a fresh output directory.

## Separate follow-up

The source audit also found that `last_bus_data` is updated by matrix/sprite
fetches but not graphics or idle fetches, while colour RAM reads use its high
nibble. `render_pixels` suppresses graphics reads behind the vertical border
and outside the captured region. VICE's `cycle_phi1_fetch` and `last_read_phi1`
operate independently of drawing. The CPU colour-RAM capture below confirms the observable fault; it is not
fixed by returning `$FF` from unused registers.

Issue 1630's `$D011` mode pipeline and delayed idle fetch were already implemented
with the graphics-sequencer work in PR 1675 (issue 1660). Light-pen timing was corrected in
the October 10 work. The unresolved HMOS sprite multicolour stage remains
coupled to issue 1681; its two rejected prototypes and proposed pipeline
extension remain in `2026-10-10-c64-hmos-sprite-multicolour.md`.

### CPU colour-RAM reproduction

The `--colour-bus` guest disables display and sprites, selects bank zero,
writes `$96` to every refresh/idle source (`$3F00–$3FFF`) and sprite-pointer
source (`$0700–$07FF`), and sets colour RAM `$D800` to `$0A`. It then records
544 CPU reads. Uniform source bytes remove raster-phase uncertainty from this
probe; it does not qualify individual fetch cycles.

Native VICE produces `$9A` for all 2,720 reads across five chip profiles.
Emu198x produces `$0A` for all 2,176 reads across four shipping board profiles.
All CPU guests reach the completion sentinel. The retained runner exits 1
for the mismatch, checks the four nonempty result rows, and restores the source
byte for byte. This proves a real CPU-visible difference independently of
any debugger peek or framebuffer observation.

Reproduce with a fresh output directory for each command:

```sh
python3 capture.py --colour-bus --output /tmp/c64-colour-native --roms "$HOME/.emu198x/roms/commodore-c64"
python3 run_colour_probe.py --repo /path/to/emu198x --guest /tmp/c64-colour-native/unused-registers.prg --output /tmp/c64-colour-emulated
```

The second command intentionally fails until the fetch/bus correction lands.
The probe is retained here rather than adding a failing default source test.
A correction must qualify Phi1 data independently of visible rendering,
refresh and sprite ownership, and CPU Phi2 accesses. Merely replacing the
colour-RAM high nibble or reusing the most recent matrix access would pin the
wrong mechanism in place.

Final verification: all seven separately enabled VIC-II `matches` fixture
checks pass, including PAL/NTSC graphics, the colour pipeline, sequencer,
NTSC grey-dot phases and the light-pen reference/normalization comparisons.
The full external-media catalogue was not run; its Data volume is absent.

The native colour-RAM negative control fills the same sources with `$26`
while retaining the `$9A` expectation. All five models return `$2A` for all
544 samples; the capture rejects all 2,720 samples and exits 1. This verifies
that the native comparison does not pass merely because execution completes.
Source production fix: PR 1712, `9ea41c93892b0c5ad2fded06e24996e1d186eca7`.

The independently reproduced colour-RAM fault is tracked as source issue 1713.
