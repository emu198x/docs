# MARIA populated DMA trace qualification

Continue the approved staged DMA correction in
`2026-10-10-maria-timed-dma-design.md`. The native-clock source slice remains
unmerged. Before implementing fetch stages, qualify the full-clock harness
against populated lists and distinct data values.

## Tasks and verification

1. Extend the own `2026-10-10-maria-native-clock/raster_tb.sv` harness into
   `2026-10-10-maria-fetch-traces/fetch_tb.sv`, adding direct short/long headers,
   indirect one/two-byte characters, widths and fetch-latch observations.
2. Correct harness bus ownership against the vendored reference's `top.sv`
   Sally release stages and retained address, including registered memory
   outputs. The initial populated probe reads the CPU's `$55` as the last
   descriptor byte, selects `$1c55` instead of `$1c00` and produces no graphics.
   Preserve that failure as a negative control. Empty zero-filled memory hid
   this defect in the prior harness; do not promote its delays to hardware facts.
3. Run fast/slow, PAL/NTSC, zone height, flag, header and width cases. Verify
   completed pulse counts, exact graphics quantities, graphics addresses/data,
   descriptor ownership and absence of bus collisions. Record actual fetch
   latch times; distinguish a driven bus address from a sampled byte.
4. Publish own harness/scripts and compact traces, without copied reference
   implementation code. Record the remaining primary/reference NMI disagreement.
5. Use the qualified schedules to extend existing MARIA fetch stages and
   snapshot state. Production gates remain the approved live-write, restore,
   CPU-handler and raster-split regressions; reference-only evidence cannot
   close #197.

## Qualified result

The corrected harness passes **768 populated cases**: four header/character
modes, four widths, heights 1/2/3/16, no/all/second-entry flags, fast/slow CPU
accesses and PAL/NTSC. Short headers use widths 1/2/8/31; long headers also
exercise the zero width field meaning 32. Each case validates every graphics
address and returned byte, the exact number of graphics latches and complete
interrupt pulses, descriptor handoff, line periods and no CPU/MARIA bus collision.

A byte latch is observed before the reference clock edge that consumes it.
The harness retains the bus address while both masters have released it, delays
Sally's release/resume using the reference wrapper's clocked handoff, and models
a registered memory result. The old combinational mux is an explicit negative:
it fails on `address=8000 data=55` while consuming the descriptor low byte.
Suppressing NMI also fails. No reference RTL is changed or published.

Eight detailed traces cover all four fetch modes with fast and slow accesses.
The observed intervals in those traces are:

| Operation | Native oscillator ticks |
|---|---:|
| Consecutive descriptor/header bytes | 4 |
| Direct graphics bytes | 6 |
| Consecutive indirect characters, one graphics byte | 12 |
| Consecutive indirect characters, two graphics bytes | 18 |

These are intervals between consumed bytes, not a claim that each address is
first driven at that edge. `HPOS` observations identify the fourth/fifth header
byte separately from DMA register loads. End markers still lead to a following
high-byte read in this reference's pipeline. The final descriptor byte may be
consumed after external HALT rises, before Sally retakes the bus. Both details
must remain representable in the new stages.

The 3,200 observed interrupt pulses have these assertion delays from HALT rise:
fast accesses **15, 17 or 18** native ticks; slow accesses **17, 19 or 20**.
Widths remain 16/24 respectively. These values qualify this implementation's
behaviour, not the standalone hardware's unresolved NMI specification.

## Playback gate

Four PAL/NTSC × fast/slow cases each check all **7,680 active pixel samples**
on rasters 16–39. With a two-byte direct object, rasters 16 and 17 show only
background. The first graphics appear at raster 18, column 93, and occupy 16
pixels; 352 graphics samples are checked over the 22 subsequent rasters.
The data fetches occur earlier, across the preceding HBlank boundary. A forced
wrong pixel fails the gate. The FPGA's output window and line-buffer latency
are now measured together; this does not establish an absolute hardware raster
origin independently of that implementation.

## Reproduction

```sh
python3 plans/2026-10-10-maria-fetch-traces/run_fetch.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-fetch-reproduction
```

The runner checks compilation status before simulation and executes the old-bus
and NMI negatives before the large matrix. An injected compiler exit status 42
was also tested with a stale binary present: the runner rejected it without
invoking the simulator. An earlier exploratory sweep accidentally used a stale
binary after an Icarus declaration-order error and was discarded. Its counts
are not part of the 768 qualified cases.

The recorded 768-case matrix ran first; the final runner's eight detailed traces
and four playback cases were then run through `playback_and_traces` against the
same qualified build. `summary.log` records the matrix; each playback log ends
with its independently checked inventory. Ruff check/format passes. Source PR
#1704 remains draft; this trace work does not close #197.

## Implementation consequences

Use a saved live fetch stage, address/data state and line-buffer ownership.
Keep descriptor-low consumption distinct from HALT release; keep CPU bus return
clocked. Preserve header mode across short headers and deliver graphics to the
buffer that will be played back later. A fixed aggregate cycle budget cannot
express these observations. Exact NMI phase and DMA cutoff remain gates before
shipping the full correction.
