# MARIA resumable display-list fetch stages

Implement the header/graphics portion of the approved timed-DMA design on
`fix/maria-timed-dma`. Source PR #1704 stays draft until raster, descriptor,
shutdown, CPU handoff and NMI gates are complete. The preceding fetch traces
qualify byte consumption and playback separately; they do not settle physical
NMI timing.

1. In `crates/atari-maria/src/lib.rs`, reproduce the missing high-byte prefetch
   after a terminating header and the direct save format's missing buffers.
   Preserve red output before changing the implementation.
2. Add `crates/atari-maria/src/fetch.rs`: saved header-low/mode/high/width/position,
   direct, character-map and indirect-byte stages. Expose the current read
   address and sample input internally; advance one native tick at a time.
   Use measured byte-consumption intervals (4-tick headers, 6-tick direct
   graphics, 12/18-tick indirect characters), with independent pin/address
   expectations from the reference traces. Keep the existing pixel decoder.
3. Route the existing scanline helper through those stages and remove the old
   bulk header/direct/indirect loops. The helper remains a compatibility driver
   of the same pipeline, not a second renderer. Its aggregate stall estimate
   remains temporary until the machine consumes native DMA pins.
4. Add `crates/atari-maria/src/state.rs` for the approved direct-state version
   boundary: reject legacy bytes, save pending fetch/input state and buffers,
   and reject truncation transactionally. Runtime serde includes the added
   stages in the ongoing, unreleased v6 layout. No dependency is added.
5. Validate exact relative byte-latch traces against all four reference fetch
   modes, live memory/register changes between fetches, continuation from every
   pending phase, truncation/old-state rejection, existing pixel tests, runtime
   and frontend tests, Asteroids, Clippy and formatting. Demonstrate timing
   checks can fail by a controlled wrong-duration mutation.

The remaining descriptor/startup/shutdown and line-buffer/raster changes are
still required. Holey DMA/cutoff and complete graphics-mode coverage are not
claimed by the non-holey trace matrix. This slice must not be released alone.

## Implemented and verified

The scanline helper now drives saved header and graphics stages. The terminating
header consumes its high byte, and short headers retain the last extended
header's write mode. The direct state format has a `MARIA`/version-1 prefix,
includes both pixel buffers and pending inputs, and rejects malformed or legacy
states before changing the live chip. Runtime v6 remains unreleased.

The production tests consume 64 independently captured reference vectors:
four fetch modes, widths 1/2/8/31 (short) or 1/2/8/32 (extended), and offsets
0/1/2/15. Every byte-latch timestamp and address matches. Inventory equality
rejects missing or duplicate cases. A controlled change from six to five native
ticks for direct graphics fails the vector test; the original code was restored
before the final checks. Additional tests resume from every pending native
phase and input latch, compare subsequent timed reads and pixels, and exercise
memory/CHBASE writes between reads.

Results: 79 package tests pass, plus the separately run 200-frame Asteroids
smoke test. Clippy with warnings denied and package formatting pass. The
initial two regressions, deliberate timing failure and final outputs are in
[`2026-10-10-maria-fetch-stages/`](2026-10-10-maria-fetch-stages/).

To reproduce the measured fixture, first build the qualified full-clock harness
with [`run_fetch.py`](2026-10-10-maria-fetch-traces/run_fetch.py), then run:

```sh
python3 plans/2026-10-10-maria-fetch-stages/capture_vectors.py \
  /path/to/qualified/fetch.vvp /tmp/maria-vector-logs /tmp/fetch-traces.txt
```

The runner requires a successful process and one complete harness result for
each case before writing the fixture. It excludes the upcoming descriptor's
shutdown reads by their descriptor-latch strobe, then checks the full expected
fetch inventory. The initial capture incorrectly included those extra reads
for height-one zones and failed its count check; no fixture from that attempt
was used. A second complete capture reproduced the committed fixture byte for
byte. SHA-256: `eb99134dc8eafc5afeed501fe65f6753fde39fee4eb8cec948893da37ee5c996`.

This evidence qualifies relative header/graphics timing only. Machine DMA still
uses the compatibility helper's aggregate stall count, the old raster and
resolved-colour line buffer. Source PR #1704 stays draft; issue #197 stays open.
