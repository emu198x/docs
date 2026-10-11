# Atari 7800 native MARIA machine integration

Connect the qualified MARIA pipeline to the production machine in the
engineering-frontier accuracy lane. This is the next approved v6 slice,
not closure of #196/#197. The machine still renders/fetches each line in one
callback, uses a flat DMA budget and a 912-period line. The qualified chip
uses 908 periods, timed reads, independent ownership and live playback.

1. Add failing machine regressions in `crates/machine-atari-7800/src/lib.rs`
   for native DMA activity, live reads/output and exact chip/machine frame
   boundaries. Run actual 6502 code to configure the display and change RAM.
   Keep the existing CPU read/write-phase, RMW, slow-access and timer tests.
2. Replace `process_scan_line`, `dma_budget` and `line_cycle` with the saved
   Sally HALT sample, bus-release stage and retained bus address. Inspect
   continuously visible CPU pins; route memory only at real consume phases.
   MARIA register writes reach native input pins rather than the immediate
   debug/compatibility helper. TIA keeps its native divide-by-four clock;
   RIOT follows phase 2. The existing POKEY sample/clock separation is still
   an open gate. No CPU callback or extra clock ticks in memory helpers.
3. Align cold MARIA raster phase with a complete first 908-period line and
   update the machine frame budget plus frontend clock assertions. Check both
   regions, complete frames and instruction stepping across frame boundaries.
   Save and resume bus ownership, retained-address and pending CPU transactions
   through complete DMA and pixel output, including live RAM changes.
4. Retain the existing line-sampled NMI delivery only as the explicitly open
   legacy integration seam until physical NMI phase is adjudicated. Do not
   invent a pulse delay or claim #197 fixed. Remove/collapse the public bulk
   chip helper in a subsequent bounded change before merging the branch.
5. Run affected packages, runtime/frontend contracts, Asteroids, Clippy and
   formatting; prove the new outcome gates fail with lost native DMA/retained
   address. Commit the bounded integration only after reading those results.
   Keep PR #1704 draft; do not close #196/#197 without the planned timing ROM
   and interrupt/raster evidence.

Reference: qualified native MARIA captures in the clock, ownership, playback,
cutoff, CTRL, holey and WSYNC plans. MiSTer `rtl/top.sv` M6502C wrapper samples
HALT at phase 1; CPU enable uses the previous sample and bus release follows
one native edge later. Its address mux retains an undriven address, and RW is
read when Sally releases the bus. These are implementation observations; the
T65 core's internal RDY staging is not assumed to map directly to our 6502
core. The earlier shared CPU pin decision still binds the implementation.

## Result

The machine now calls the native MARIA pipeline on every oscillator period.
It supplies live memory at actual DMA consume edges, retains the shared
address while neither chip drives it, and routes MARIA CPU writes through
input pins. Sally's saved HALT sample controls CPU advancement separately
from the saved bus-release stage. The aggregate renderer callback, flat DMA
budget and line-cycle counter are removed from the machine caller.

The first new regressions failed on the old machine:

```text
native DMA never ran
assertion `left == right` failed: frame budget must use qualified raster
  left: 239856
 right: 238804
```

Both regions now use the independently qualified 908-period raster. The
cold construction point is normalised to an already-entered row-zero edge
so its first line is complete; this is a model origin, not a claim to have
qualified MEN/reset startup on hardware. Existing warm reference captures
keep their explicitly measured initial raster and divider state.
Frame counts follow actual chip wrap even during instruction stepping;
`run_frame` still advances one complete frame's worth of native time from
any current phase. Runtime/frontend frame budgets share that value.

The live guest sets DPP, palettes and DMA through executed 6502 writes.
After the first graphics byte is consumed, the test changes the next RAM
byte before its fetch and checks the two resulting eight-pixel groups on
reference raster 18. That inter-byte graphics mutation is a test stimulus,
not a claim that the halted CPU can write during DMA. Separate fast/slow
CPU guests increment RAM through real read/modify/write cycles while ordinary
or overlong lists own the bus. Both regions preserve every dummy/final write
value and RIOT tick. Retained-address descriptor reads and repeated ownership
handoffs must occur; a zero-DMA or non-executing guest cannot pass.

Saves at more than 60 distinct ownership/read/CPU phases per region/speed
resume 2,048 native ticks, including a post-save RAM change. They compare
actual bus/pins, CPU progress, timer, READY, both rendered output and audio,
then the complete state. Removing retained address, using the new HALT
sample too early, and omitting the saved bus address each fail a regression.
The saved machine fields replace the obsolete aggregate budget/counter
within the approved unreleased v6 layout.

The old colour-bar assertion required every pixel of each line to share one
background value. Native playback exposes a CPU background change at the
right edge. Its replacement checks every active/border pixel against the
actual CPU write time plus the separately qualified register-delivery stage;
centre pixels still alternate every line.

The old audio test expected two TIA samples per MARIA line and advertised
nominal refresh times that count. TIA continues its independent 228-colour-
clock cadence while MARIA uses 227 TIA clocks per line. The sample stream is
unchanged for equal elapsed native time; the host rate now follows the
regional oscillator divided by 456, rounded to integer Hz. Six-frame checks
compare against a continuously running standalone sound core. A runtime
sink checks emitted packet timestamps, rates and real sample counts in both
regions, to within one partially accumulated sample.

## Verification and remaining gates

Logs and deliberate-fault outputs are under `/private/tmp/maria-machine-native/`.
All 126 affected package tests, the separate 200-frame Asteroids render
smoke through native DMA, Clippy and formatting pass. Source commit:
`25ba0e2e`. Three deliberate ownership/state faults fail the new regressions.
Use the affected-package, Asteroids, Clippy and format commands in the
[cutoff plan](2026-10-11-maria-dma-cutoff.md).

This slice does **not** settle physical NMI assertion/width. Its legacy event
to CPU level seam remains line-sampled and cannot deliver consecutive flagged
one-line zones correctly. The pulse stage, actual interrupt/raster test ROM,
POKEY chip-clock/host-sample separation and collapse/removal of the old public
chip scanline helper remain required before PR #1704 merges. The package and
Asteroids checks do not substitute for those acceptance gates. No issue is
closed by this intermediate integration.
