# MARIA CPU clock and DMA handoff qualification

Continue the approved native-clock DMA correction from the committed fetch
stages. Source PR #1704 stays draft. This step qualifies startup/shutdown clock
boundaries before changing the machine's aggregate DMA stalls.

1. Observe CPU phase strobes with DMA disabled in an own `clock_tb.sv`, using
   the same checked reference adapters as the populated fetch harness. Cover
   fast ROM, slow RIOT, both transition directions at every native offset and
   repeated transitions. Reject unknown clock controls. Compare phase lengths
   with GCC1702B page 29: slow phase 2 and the following phase 1 are extended.
2. Extend `2026-10-10-maria-fetch-traces/fetch_tb.sv` and `playback_tb.sv` to
   initialize the reference's omitted `noslow` reset and reject unknown slow
   selectors after setup. Re-run the entire populated matrix and negative
   controls in a new scratch directory. Re-capture the 64 source vectors and
   compare them byte for byte. Record changed startup/NMI observations without
   presenting reference reset assumptions as measured hardware.
3. Add optional phase/bus-ownership tracing to the own populated harness. Trace
   HALT, Sally release, MARIA address drive, phase strobes, descriptor/header
   consumption and DMA release across fast/slow entry and exit. Preserve a
   compact trace matrix and exact accounting boundaries for the next production
   startup, descriptor and shutdown stages.
4. Check each stage's proposed timing against primary source accounting. Keep
   the NMI assertion/width disagreement open until adjudicated; no constant
   inferred from this FPGA alone becomes an exact physical expectation.

No reference RTL is modified or copied into production. Generated adapters and
binaries stay in scratch. Scripts fail on compilation failure before invoking
the simulator. No new dependency or snapshot-version change beyond approved v6
is introduced by this evidence step.

## Results

The standalone clock matrix passes 108 cases. Fast phase intervals are four
native ticks; slow intervals are six. Transitions can yield ten-tick CPU
periods, depending on the address-change phase. Repeated changes at the CPU
phase-1 boundary exercise all three periods (8/10/12). The matrix covers both
regions, both TIA and RIOT addresses, constant fast/slow selection, both
transition directions at twelve native offsets, and repeated transitions.
Unknown clock selection and a forced-fast slow access are rejected by separate
negative controls. These are observations of this reference implementation;
arbitrary asynchronous address changes are probe inputs, not CPU behaviour.

The first exploratory no-DMA clock probe found `noslow` unknown: the reference
clears that register on DMA release but omits it from reset. A fast ROM address
masks the unknown; a slow peripheral address exposes it. The revised benches
start it at zero and reject unknown selection after setup. This is an explicit
simulation initialization assumption, not a claim about physical power-on state.

The revised full-clock matrix passes 768/768, with four playback checks and all
negative controls rejected. The original old-bus and suppressed-NMI negatives
remain, and an unknown-clock negative is added. Its 3,200 complete NMI pulses
still have widths of 16 ticks (fast) or 24 (slow). Fast assertion-delay counts
remain `{15: 736, 17: 184, 18: 680}`; slow counts become
`{17: 312, 19: 736, 20: 552}`. The earlier slow counts were
`{17: 184, 19: 736, 20: 680}` because of the uninitialized startup selection.
The range is unchanged; use this revision for startup accounting.

All 64 header/graphics source vectors reproduce byte for byte after the reset
correction, with SHA-256
`eb99134dc8eafc5afeed501fe65f6753fde39fee4eb8cec948893da37ee5c996`.
The committed Rust fetch-stage timing therefore needs no correction from this
probe. This does not validate the machine's still-unreplaced aggregate stalls.

Eight additional ownership traces cover PAL/NTSC, fast/slow CPU addresses, and
one-/two-line zones. `PHASE` and `READ` lines describe inputs consumed at the
named tick's edge; `BUS`, `HALT` and `NMI` lines describe outputs after that
edge. This distinction is required when comparing events with the same label.

For the first populated one-line zone, the NTSC examples are:

| Event | Fast CPU address | Slow CPU address |
|---|---:|---:|
| HALT falls | 15441 | 15444 |
| Phase 1 samples HALT | 15446 | 15456 |
| CPU releases bus | 15447 | 15457 |
| MARIA enables address drive | 15453 | 15463 |
| First header byte consumed | 15460 | 15470 |
| Terminating header high byte consumed | 15496 | 15506 |
| Upcoming descriptor flag consumed | 15506 | 15516 |
| HALT rises / MARIA releases address drive | 15513 | 15523 |
| Upcoming descriptor low byte consumed | 15514 | 15524 |
| CPU retakes bus | 15519 | 15531 |

The startup portion in both examples is measured from the CPU phase that
samples HALT: bus release at +1, MARIA drive at +7, first byte consumption at
+14. The descriptor flag follows the terminator's high byte by ten ticks;
descriptor bytes are four ticks apart. These are bounded examples, not proof
that every possible phase/abort/live-register case follows these offsets.
The initial VBlank-end descriptor and a continuing zone have different work
inventories; preserve those paths separately in the production stages.

The low-byte read after HALT rises is valid because Sally has not yet retaken
the bus. The machine must retain the last address during that undriven window,
then resume CPU ownership at its sampled phase. Combining HALT release,
descriptor completion and CPU resume into one transition would corrupt it.

## Reproduction

```sh
python3 plans/2026-10-10-maria-fetch-traces/run_fetch.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria /tmp/maria-qualified
python3 plans/2026-10-10-maria-clock-handoff/run_clocks.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria /tmp/maria-qualified /tmp/maria-clocks
python3 plans/2026-10-10-maria-clock-handoff/run_handoff.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria /tmp/maria-qualified /tmp/maria-handoff
```

The adjacent directory contains the own scripts, compact clock vectors, DMA
inventory/hashes, negative controls and ownership traces. No reference RTL is
included. The earlier fetch-trace plan retains its historical counts; this
record supersedes its slow-startup distribution. Exact physical NMI phase and
width remain unresolved.
