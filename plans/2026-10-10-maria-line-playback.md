# MARIA line RAM and native playback

This implements the framebuffer portion of the approved native DMA design.
The existing renderer resolves palette colours while fetching and interprets
write mode as display resolution. Atari's software guide instead specifies
two line RAMs, separate write/read modes and palette lookup during playback.
MAME and the qualified FPGA reference both implement that separation.

1. Add an own `line_ram` reference bench beside this plan. Capture output
   across every graphics byte, palette, write mode, read mode and Kangaroo
   setting, including overlap. Probe horizontal-position units, clipping and
   wrap separately. Record the measured output, not copied reference code.
2. Add failing output regressions in `atari-maria`, then replace the existing
   colour-resolving blitter with 160 encoded cells and a second playback
   buffer. Reuse one decoder for the native path and compatibility helper.
   Preserve short-header write-mode retention and live read-mode/palette
   sampling. Keep all pending data inside the unreleased snapshot layouts.
3. Drive playback and line transfer from `tick_dma` at their observed native
   edges. Extend the full-clock playback bench to capture exact output and
   transfer timing with varied graphics, positions and live register changes.
   Keep framebuffer dimensions and the existing viewport origin; do not hide
   the initial buffer latency by moving the picture window.
4. Validate snapshot continuation before/after transfer and during displayed
   pixels. Verify both regions, background/border, transparency and live
   palette/read-mode changes. Run the existing DMA/fetch/clock vectors,
   affected packages, Asteroids, Clippy and formatting. Include deliberate
   failing controls for the reference capture and pixel timing gate.

This stage does not settle NMI phase/width, DMA cutoff/restart or replace the
machine's aggregate bus ownership. Source PR #1704 remains draft until those
gates and POKEY clock/sampling separation are complete. No new dependency or
framebuffer geometry change is needed.

Primary source: `reference/by-system/atari-7800/atari-7800-software-guide.txt`,
sections Display, CTRL and graphics modes. Implementation precedents:
`mame/src/mame/atari/maria.cpp` and qualified Atari7800_MiSTer revision
`29aaacbbed127c670972c8a0a950ca82dc87e5df`, `line_ram.sv` and `video_sync.sv`.
The FPGA's deliberately disabled colour-RAM write collision is not evidence
that production silicon lacks that effect; retain it as a qualification limit.

## Implemented and verified

Source commit: `9a82da3c224664b5bb37b3ce9753df815627ef39` on draft PR #1704.

The renderer now stores 160 five-bit palette/colour cells and keeps a separate
playback bank. Write mode selects four or two cells per byte. Read mode selects
the output interpretation, including all six documented graphics modes and
the RM=01 alias. Horizontal positions count cells in every mode, wrap at 256,
and discard writes outside the 160-cell line. Palette lookup happens when the
pixel is displayed, so later register changes affect future pixels only.

The native entry emits a pixel on MARIA phase 0 and transfers the completed
input bank at column 412, after sampling the old bank's last active pixel.
The cleared input bank then accepts subsequent DMA writes. First populated
output appears on raster 18 in the qualified capture; the viewport origin is
still raster 16, preserving the observed initial two-line latency. Framebuffer
sizes remain 374×240 NTSC and 368×288 PAL, with the existing PAL origin still
qualified as provisional in the source. The compatibility helper uses the
same cell decoder; it still runs the old aggregate machine schedule.

Four output regressions failed before implementation: early palette lookup,
incorrect 320A decoding/colour entry, single-pixel HPOS units, and eight-pixel
extended-mode byte width. All now pass. The reference gates cover:

- All 32,768 byte/write-mode/read-mode/palette/Kangaroo combinations over an
  existing object, plus 48 horizontal boundary/wrap cases: 277,504 exact
  colour-code comparisons.
- 160 full-clock captures, 960 lines and 356,160 framebuffer pixels, with both
  regions, CPU access rates, write/read modes and edge positions. Half-cycle
  checks reject pixels emitted early, not just pixels missing at the next edge.
- Ninety-six observed register changes during display, covering palette,
  background and read mode. These changes are injected at their observed
  register-commit edge to qualify playback itself. CPU-write-to-register
  propagation is a distinct integration gate; this test does not validate it.
- Exact line-transfer edges, live changes without repainting earlier pixels,
  and 1,024 resumed native ticks across both buffers and transfer/output edges.
  Direct snapshots reject invalid five-bit cells transactionally.

The reference capture rejects forced black output. The initial full-clock
capture also correctly rejected `incomplete output`: it had counted the
32 reset ticks inside its raster budget and stopped before the last NTSC
border pixels. The corrected runner counts 22 complete post-reset rasters;
no fixture was accepted from the truncated run. A deliberate one-tick-early
Rust output and a save containing the wrong playback bank both fail the
respective gates. Source restored afterward; positive video checks pass.

Validation: 107 affected package tests, the separate 200-frame Asteroids
smoke, Clippy with warnings denied, Rust formatting and Python Ruff. Evidence
logs are adjacent. The existing 768 DMA, 64 fetch and 108 clock vectors remain
green. Asteroids validates the changed shared decoder through the current
machine path; the native timing path is validated by the separate captures.

This satisfies the decode requirements of source issue #194, including its
per-mode tests. Its description's shorthand for 160B is inaccurate: the
software guide specifies up to twelve nontransparent colours and two cells
per byte, which the measured matrix confirms. DMA scheduling and abort costs
remain separate work under #196. The line comparator also advances #431,
without claiming a complete guest-frame comparator against MAME/ProSystem.
Keep #194 open until the source PR merges; PR #1704 remains draft for machine
ownership wiring, cutoff/restart, register propagation, physical NMI timing
and POKEY clock/sampling separation.

Fixture SHA-256 values:

- `line-ram-vectors.txt`: `49cc3d565e48c541d0aa7609cd2d88a73aba9a9caeb72e0bba426d0a3c5d03f2`
- `raster-vectors.txt`: `5782a071e9d403d971839a6d1318f07a9bf35be254482db4e8ac8471fa64b8dd`

## Reproduction

From this docs repository, using the existing checked reference adapters:

```sh
python3 plans/2026-10-10-maria-line-playback/capture_line_ram.py \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-line-playback \
  ../emu198x/crates/atari-maria/tests/data/line-ram-vectors.txt
python3 plans/2026-10-10-maria-line-playback/capture_raster.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-line-playback/raster \
  ../emu198x/crates/atari-maria/tests/data/raster-vectors.txt
```

Both scripts check compilation before execution and require complete, unique
case inventories. Only own harnesses and observed output vectors are retained
in Git; reference RTL remains unmodified outside these repositories.
