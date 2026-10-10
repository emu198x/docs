# NTSC greydot CPU timing — issue 1629

Lane: engineering-frontier accuracy. Compare the existing NTSC discrepancy
with native VICE x64sc before choosing a production correction. The separate
VIA timer 2 change remains on its own source branch and draft PR 1689.

1. Reproduce greydot on both NTSC chip models using the locally staged C64
   ROMs and VIC-II testbench. Retain input identities, native VICE store
   traces and matching Emu198x traces. Extend the existing diagnostic in
   `crates/runtime-commodore-c64/tests/vicii_testbench.rs` for model selection
   and bounded CPU tracing as needed; no production timing changes yet.
2. Locate the first diverging CPU cycle around the raster IRQ stabilisation
   and subsequent loop. Compare the current VIC-II/CPU stages with vendored
   VICE, then cite primary hardware sources for the mechanism. Do not infer
   the cause from the issue's badline/sprite-DMA suggestion alone.
3. Record the concrete failing evidence and bounded design. Apply a small
   correction to existing stages if the evidence supports it; obtain
   approval before new architecture or breaking snapshot changes.
4. Require a red/green regression, exact 8562 greydot output, unchanged PAL
   colour-pipeline lanes and NTSC gfxfetch, affected chip/machine/runtime
   suites, Clippy and formatting. Any catalogue output movement needs cause
   classification before recapture. Retain evidence and close 1629 only
   after its scope is proved.

Initial source baseline: `ae399c87ecf649cf19d4753c9fd024945f22251c`.
No dependencies or snapshot changes are proposed at this stage. Reference
implementation: `emulators/c64/vice-3.10/src/viciisc/` and its CPU core.


## Finding: the reported mismatch is between two native launch phases

Native VICE reproduces **exactly 521 differing 8562 pixels** merely by
changing the launch phase. At `$0848` (the first CLI), the native monitor
redirects to a trampoline with 0–5 NOPs followed by `JMP $0848`. This produces
two steady patterns on both NTSC chips. In one, the first `$D021` store is at
raster 110/cycle 15; in the other, cycle 16. Later bands alternate between
those phases.

The trace explains why. The second raster IRQ enters the handler at line
109, monitor execution cycle 9 or 10. Its stabiliser's `LDA $D012` and
`EOR $D012` read at cycles 59/63 or 60/64. Both pairs still read line 109 on
a 65-cycle NTSC line, so both produce zero and take the same BEQ. The
one-cycle difference survives. This PAL test's stabilisation does not
establish a unique NTSC store phase. No CPU/VIC-II production correction is
justified by this evidence.

The reference's opcode trace reports the cycle before the opcode fetch;
its store trace reports the store's engine cycle. Keeping those conventions
separate avoids inventing another one-cycle difference from trace labels.

## Verification

Twelve native runs (six launch delays on each of the 6567R8/8562) retain two
stable 408-store traces. Each full frame in a capture agrees, and all
captures in the same phase agree byte for byte, including screenshots.
The final capture explicitly supplies the same KERNAL/BASIC/character ROMs
as Emu198x. `native-identity.json` records program/ROM/tool hashes, commands,
log identities and all six generated fixture hashes. The capture script's
`--check-fixtures` pass regenerated and matched every committed byte.

Twelve Emu198x runs vary the ordinary BASIC launch time from 150 to 155 boot
frames on each NTSC chip. Both native phases occur. Every run matches all
408 stores and all 94,848 pixels of its corresponding VICE window: 4,896
store observations and 1,138,176 pixel comparisons total. `comparison.json`
and the twelve logs retain the observations. These are digital output
comparisons, not analogue or physical-hardware validation.

The 384×247 reference starts at raster 28 and wraps after 262; the horizontal
crop is 16 within the 416-pixel framebuffer. Native screenshots use our
indexed palette and all VICE colour controls at neutral (1000), avoiding
NTSC display colour adjustments being mistaken for palette-index changes.

The source regression requires both phases, checks every store and pixel,
and cross-compares the other native phase. That negative control gives 521
mismatches on the 8562 and 49 on the 6567R8. Deliberately corrupting the first
reference store from cycle 15 to 14 also makes the test fail (exit 101).
The fixture was restored and all six hashes rechecked before the final
passing run.

Nine fixture-backed VIC-II checks and the row diagnostic pass, including both PAL colour-register
models, all five colour-fetch cases, CPU store phases, sequencer phases and
pixels, sprite DMA, PAL graphics fetch and the NTSC graphics-fetch gate.
The direct greydot regression passes again after the negative control.
Clippy initially requested `as_chunks` for the two fixed-size array views;
those were corrected, and the final warnings-denied check passes. Formatting,
doc-link, fixture-guard and ignore-reason checks pass. No production code,
framebuffer geometry, catalogue hash or snapshot layout changed.

Reproduce native captures from the docs repository (new output directory):

```sh
python3 plans/2026-10-10-c64-ntsc-greydot/capture.py --output /path/to/new-capture --source ../emu198x --testbench ~/.emu198x/test-suites/c64-vicii --roms ~/.emu198x/roms/commodore-c64 --check-fixtures ../emu198x/test-data/commodore/c64/ntsc-greydot
```

Run the regression from the source repository:

```sh
EMU198X_STRICT_FIXTURES=1 cargo test -p runtime-commodore-c64 --release --test vicii_testbench ntsc_greydot_matches_both_native_launch_phases -- --ignored
```

The temporary `diagnostic.patch.gz` added bounded CPU tracing and model/frame
selection to the existing diagnostic; it is retained for audit, not part of
the production or final test-helper changes. The committed regression makes
those ad-hoc environment controls unnecessary.
