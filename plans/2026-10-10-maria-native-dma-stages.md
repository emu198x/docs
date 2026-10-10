# Native MARIA DMA ownership, descriptors and raster wiring

Replace the aggregate machine DMA path with the approved saved native-clock
pipeline. This is the next implementation stage after CPU bus phasing; source
PR #1704 stays draft until all timing and physical NMI gates are satisfied.

1. Extend the own reference handoff trace to record address changes as well as
   HALT, address-drive enable, Sally release, CPU phases and byte consumption.
   Confirm address setup intervals and both continuing-zone and next-descriptor
   shutdown. Preserve exact clock/accounting boundaries and keep this distinct
   from the unresolved NMI output pulse.
2. Add `atari-maria/src/dma.rs`: saved request, startup, descriptor-flag/high/low,
   display-list, short-shutdown and release stages. Reuse `fetch.rs` for all
   headers and graphics. Feed reads through address/data pins; keep address
   setup, read consumption, address-drive release and HALT release separate.
   The upcoming descriptor owns the next zone's offset/holey/DLI flags.
3. Add the native raster entry point in MARIA. Generate VBlank-end, HBlank,
   line-buffer handoff and cutoff from the measured 908-tick line. Integrate
   CPU-clock slow inhibition during DMA and keep its sampler state saved.
   Stage framebuffer/buffer changes together so the first fetched line is not
   displayed before the measured buffer handoff. Preserve framebuffer geometry.
4. In `machine-atari-7800/src/lib.rs`, replace `dma_budget`/`line_cycle` and the
   bulk rendering callback with native MARIA pins. Save Sally's sampled HALT
   and released-bus phases; retain the undriven address until one owner drives
   it. Perform CPU phase-2 transactions only while it owns the bus. Update
   frame budgets through the existing shared regional contract.
5. Extend direct chip and ongoing runtime-v6 snapshots with all pending stages,
   bus addresses/inputs, raster and buffers. Keep the public scanline helper
   only as a driver of the same completed native engine; remove duplicate
   descriptor/render walks when its machine caller is replaced.
6. Compare native read/address/ownership traces across modes, widths, zone
   heights, flags, CPU fast/slow phases and regions. Exercise live memory and
   DMA control changes, cutoff and restart. Save at every pending transition
   and compare continuation. Run affected packages, Asteroids, negatives,
   Clippy, formatting and CI before committing/merging the complete stage.

NMI production timing remains the explicit primary/reference adjudication
gate. Do not introduce a guessed fixed delay or claim issue #197 closed from
descriptor events alone. POKEY's variable chip clock and independent host
sampling also remain a pre-merge gate. No dependencies or reference RTL are
added to production.

## Implemented stage: native ownership and descriptor fetch

Source commit: `7b66da98cf9aba8cb9887ddd6f5ec3281fbc4c74` on draft PR #1704.

The native chip entry now clocks requests, startup, descriptor bytes, the
existing header/graphics engine and both shutdown paths. CPU slow-clock
inhibition follows the sampled HALT state. Address-drive release, HALT release
and Sally bus return remain distinct transitions. The last descriptor byte is
consumed after address drive falls, while Sally still leaves the retained
address on the bus. The upcoming descriptor owns the next zone's offset,
address and DLI event. This event is not yet a physical NMI output pulse.

Direct snapshots preserve native raster position, DMA phase/countdowns,
request/sample latches, clock inhibition and DMA address/data/control pins.
Invalid countdowns and raster positions are rejected before replacing live
state. Runtime serde saves the same fields inside the ongoing v6 envelope.
Both snapshot layouts remain unreleased on draft source PR #1704.

The chip path matches all 7,662 events in eight detailed handoff traces. The
broader 768-case matrix covers four fetch modes, widths 1/2/8/31-or-32, zone
heights 1/2/3/16, no/all/only-second DLI flags, fast/slow CPU addresses and both
regions. It compares every read and HALT transition through 40 raster lines,
plus all CPU phase, address and ownership events in the detailed window.
Stream totals are 494,592 byte reads, 36,864 HALT transitions, 656,928 CPU phase
events, 74,688 address changes and 18,432 ownership/inhibition changes.

The full matrix stores per-stream counts and FNV-1a signatures to keep the
fixture small; the eight detailed vectors retain exact individual events.
Fixtures derive exclusively from the checked reference capture, not the Rust
implementation. The tests require the full Cartesian inventory and non-empty
streams. Fixture SHA-256 values:

- `dma-vectors.txt`: `4995712e0a1c6a8fa87d6ec371be028468b47da3e68cdbebe25925c0c10ac191`
- `dma-matrix.txt`: `d8805ee21f96e96d14de208d2bb8e40eb89fb3b2a99e97f73e4e6ecb27ac4019`

Additional tests mutate descriptor memory between byte latches, including the
last byte after drive release. They verify upcoming-zone event ownership and
inventory across all flag/height/region combinations. Mid-DMA snapshots cover
all eight stages and pending clock/fetch transitions; restored bus activity is
compared with the original live chip's continuation.

Both deliberate faults fail the gates: extending startup by one native tick
changes the first driven address event from tick 14,581 to 14,582; omitting the
saved clock-inhibition latch fails the restore check. Validation passes 97
affected package tests, the separate 200-frame Asteroids smoke, Clippy with
warnings denied, package formatting and Python Ruff. Logs are adjacent.

This completes steps 1–2 and the associated snapshot portion of step 5. The
raster currently schedules native DMA only. The machine still calls the
aggregate scanline renderer; native framebuffer playback, buffer handoff,
cutoff, live DMA-disable/restart and Sally ownership wiring remain next. The
existing Asteroids check therefore protects the current machine path, not the
new native path. Physical NMI timing and POKEY chip/host clock separation also
remain pre-merge gates. Do not merge this stage or close #197 by itself.

## Reproduction

Use the qualified scratch tree produced by
`2026-10-10-maria-fetch-traces/run_fetch.py`, including the documented slow-clock
initialization. `2026-10-10-maria-clock-handoff/run_handoff.py` compiles the
updated own harness with checked return codes and emits the eight raw traces
plus `handoff.vvp`. From this docs repository:

```sh
python3 plans/2026-10-10-maria-native-dma-stages/capture_vectors.py \
  /private/tmp/maria-native-dma-stages/traces \
  ../emu198x/crates/atari-maria/tests/data/dma-vectors.txt
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-10-maria-native-dma-stages/capture_matrix.py \
  /private/tmp/maria-native-dma-stages/traces/handoff.vvp \
  /private/tmp/maria-native-dma-stages/matrix \
  ../emu198x/crates/atari-maria/tests/data/dma-matrix.txt
```

The matrix raw logs remain scratch evidence; only own harnesses and measured
vectors are committed. Reference RTL remains unmodified and is not copied
into the production repository.
