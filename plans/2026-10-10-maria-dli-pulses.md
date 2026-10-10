# MARIA DLI pulse investigation

Investigate source issue #197 in the engineering-frontier accuracy lane. The
border correction is independently submitted in source PR #1703; do not mix
it with interrupt changes. First establish observed failures and the reference
schedule, then agree any new pipeline or snapshot design before implementation.

## Plan

1. Read the current MARIA scanline producer, machine CPU/DMA handoff and shared
   6502 NMI sampling. Consult Atari's software guide and the existing MiSTer
   DMA module before proposing timing behaviour.
2. Add a temporary diagnostic test to `crates/machine-atari-7800/src/lib.rs`
   using a synthetic cartridge with an NMI counter. Sweep PAL/NTSC and zone
   heights 1, 2, 3 and 16. Count pin edges and executed handlers separately.
   Include zones without DLI as a negative control. Retain the probe and logs
   in this plan's adjacent evidence directory; restore production source after
   measurement if a correction is not yet agreed.
3. Run the reference DMA RTL with controlled external clocks and memory if the
   available simulator supports it. Distinguish a whole-DMA trace from a pulse
   generator isolation test; neither substitutes for an original-hardware
   measurement. Record assertion/deassertion and shutdown relationship.
4. Write the smallest evidence-backed design that addresses the actual loss
   and timing. Identify any native-clock, public-API or snapshot change and
   request agreement where required. Do not replace missing timing with an
   arbitrary CPU-tick clear or close #197 on a narrower counter-only result.

## Confirmed emulator defect

The CPU probe ran against source `ca4cb986be193194305218a25a6f337ae4f98d5c`.
It counts MARIA's actual pending-DLI events in one chip run, then counts NMI pin
edges and executed NMI handlers in a machine run with the same display list.
This tests agreement between the producer and consumer without assuming an
absolute hardware raster origin. The synthetic cartridge sets DPP and CTRL,
then its NMI handler increments zero-page RAM. No third-party ROM is needed.

Twenty-four rows cover both regions, heights 1/2/3/16 and DLI disabled, enabled
on every entry, or enabled on alternating entries. Only the two consecutive
single-line rows fail:

| Configuration | Chip requests | NMI edges | Executed handlers |
| --- | ---: | ---: | ---: |
| NTSC, height 1, every entry flagged | 240 | 1 | 1 |
| PAL, height 1, every entry flagged | 240 | 1 | 1 |
| Either region, height 1, alternating flags | 120 | 120 | 120 |
| Either region, height 2, every entry flagged | 120 | 120 | 120 |
| Either region, height 3, every entry flagged | 80 | 80 | 80 |
| Either region, height 16, every entry flagged | 15 | 15 | 15 |
| All unflagged controls | 0 | 0 | 0 |

The machine assigns `cpu.nmi = maria.take_dli()` once per scanline and never
clears it between consecutive true results. The CPU correctly detects only the
first edge. The alternating single-line control proves an inactive intervening
line restores delivery. The diagnostic fails with `every chip DLI request must
reach the CPU`, two mismatched rows. Production source was restored byte for
byte after the run; `git diff --exit-code` is clean.

## A separate zone-handoff defect

The original Atari guide explicitly places a zone's DLI after DMA on the last
line of the **previous** zone. Source: the local extracted primary document,
`reference/by-system/atari-7800/atari-7800-software-guide.txt`, lines 247–270.
The PDF volume is not mounted in this session; the local original-document
text is available and was read directly.

Our `render_visible_line` loads the current descriptor at the beginning of its
zone, renders that zone, and requests DLI when that same zone ends. This binds
the interrupt to the wrong side of the descriptor transition. MAME's
`atari_maria_device::startdma` loads the next DLL header at the previous zone's
shutdown and tests the newly fetched flag. MAME revision:
`9391e1eff80eb04abd58d48218a1d3b9643c1ea8`.

Counting delivered interrupts alone would miss this fault. The existing
scanline-wide DMA budget also cannot establish an exact shutdown/pulse phase:
it asserts the CPU pin at the line boundary before its budget is consumed.

## Reference simulation: what passed and what did not

Reference: unmodified Atari7800_MiSTer `rtl/Maria/DMA.sv`, revision
`29aaacbbed127c670972c8a0a950ca82dc87e5df`. Simulator: Icarus Verilog 13.0.
No vendored source was edited or copied into this evidence directory.

`pulse_tb.sv` isolates the actual module's HALT-release-to-NMI logic by supplying
controlled HALT and DLI values. Sixteen rows cover DLI off/on and all eight
release phases of the supplied CPU clock. Every eligible shutdown produces a
separate pulse, lasting 16 supplied master ticks (two supplied CPU cycles).
DLI-clear rows produce no pulse. This is pulse-generator evidence, not a
full-DMA or physical-hardware timing measurement.

`dma_tb.sv` exercises the whole module with external clock phases, blanking
strobes and memory. It explicitly initialises LONGHDR, IND and sel5_cnt to zero
before reset because those controls have no reset assignments. This is a
harness initial-state assumption, not a claim about silicon power-up state.
Initial attempts without it propagated unknown values and are not validation.

The final 48-row sweep checks 40 DMA starts and 40 shutdowns in every row, as
well as NMI count, pulse width and the selected-entry boundary. Twelve
single-line rows pass: four CPU phases, each with no DLI, every entry flagged,
or only the second entry flagged. The every-entry cases produce 40 independent
interrupts. Suppressing NMI in the otherwise passing height-1 case correctly
fails with `edges=0 expected=40`.

**The other 36 rows fail.** Heights 2, 3 and 16 stall with one DMA start and no
shutdown. They are a harness/reference-integration problem, not evidence for
emulator timing, and cannot be called passes even when no interrupt was
requested. The shutdown-count check prevents that false green. The whole-DMA
harness therefore remains diagnostic and deliberately returns nonzero.

The next step is to reproduce the reference's own clock/reset and memory
interface for longer zones, starting from the working pulse isolation. Do not
keep adjusting a hand-made timing schedule until selected examples pass. The
absolute shutdown-to-NMI phase is not settled: the isolated/full-module traces
must be reconciled with the guide's one-7.16-MHz-cycle statement before a timing
implementation is approved. Issue #197 remains open.

## Reproduction and scope

The adjacent `probe.rs` is a temporary Rust test module to append to
`crates/machine-atari-7800/src/lib.rs` in an isolated checkout, then run:

```sh
cargo test -p machine-atari-7800 --lib dli_probe::consecutive_zone_interrupts_reach_the_cpu -- --exact --nocapture
```

It is expected to fail on the recorded source. Remove the temporary module
after measurement. The committed production source has no diagnostic edits.

For the RTL diagnostics, using paths appropriate to the checkout:

```sh
iverilog -g2012 -s pulse_tb -o /tmp/pulse.vvp pulse_tb.sv /path/to/Atari7800_MiSTer/rtl/Maria/DMA.sv
vvp /tmp/pulse.vvp
python3 run_rtl_sweep.py /path/to/Atari7800_MiSTer/rtl/Maria/DMA.sv /tmp/maria-dli-sweep
vvp /tmp/maria-dli-sweep/dma_tb.vvp +height=1 +flag=1 +phase=0 +suppress_nmi
```

The pulse isolation passes. The full sweep and suppression control fail for
the reasons above. The Python runner passes Ruff checks and formatting.
No new dependency, public API, snapshot format or production timing changes
are included. A future staged DMA/DLI correction will need an agreed design;
the current Atari 7800 runtime snapshot version is 5.

## Reference follow-up

The [comparator diagnosis](2026-10-10-maria-dli-oracle.md) resolves the 36
longer-zone simulation failures. All 48 rows pass after a checked simulation-only
comparison adaptation. The [approved staged design](2026-10-10-maria-timed-dma-design.md)
covers the production correction; the exact assertion delay remains a gate.
