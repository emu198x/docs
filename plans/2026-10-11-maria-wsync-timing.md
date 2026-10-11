# MARIA WSYNC assertion and release

Qualify WSYNC at native resolution before connecting the machine caller.
The current native path latches WSYNC but has no raster release; the
compatibility caller clears it at the aggregate line boundary.

1. Extend our existing full-clock register harness to capture WSYNC writes,
   READY edges, CPU clock strobes and DMA ownership. Exercise both regions,
   fast/slow CPU idle addresses, all four register mirrors, one/two consecutive
   writes and writes around line-RAM reset with DMA off, ordinary and busy.
   Preserve raw events and require complete writes and release observations.
2. Reproduce the discrepancy in `crates/atari-maria/src/dma.rs` tests. Extend
   existing register stages in `control.rs`, native raster delivery in
   `dma.rs`, and direct/serde state in `state.rs` as needed within the approved
   unreleased v6 design. The chip owns release; the machine later connects RDY.
3. Compare live pending-stage save continuations and deliberately break the
   release/strobe timing to prove the regression fails. Run affected package
   tests, Asteroids, Clippy and formatting. Record source/evidence commits and
   keep PR #1704 draft for native integration and remaining NMI/POKEY gates.

Sources: GCC1702B WSYNC/READY description; qualified Atari7800_MiSTer
`29aaacbbed127c670972c8a0a950ca82dc87e5df`, `maria.sv` READY path,
`control.sv` WSYNC strobe and `video_sync.sv` line-RAM reset. Reference RTL
is read-only and is not copied into production. Native edge measurements
are implementation precedent, not independent physical-chip measurements.

## Result

The native path now retains the WSYNC write selection, internal wait and
phase-held output separately. The write selection is updated during CPU
phase 2 and retained until a following access replaces it. Line-RAM reset
can release READY during phase 1 while that selection still keeps the
internal wait asserted; READY can fall again and remain low until the next
line. The output retains its value during phase 2.

The initial detailed regression failed before the correction:

```text
assertion `left == right` failed: case 14556 512 0 1 1 2, event 142
  left: "14563 Q 0"
 right: "14566 H 0"
```

The previous native path asserted the wait as soon as the register write
committed and never released it through the raster. The compatibility
machine still clears the old aggregate-line flag until native integration;
this correction qualifies the chip path ahead of that integration.

All 960 captured schedules match: ten target times around vertical-blank
exit, line-RAM reset and horizontal-blank start; all four register mirrors;
fast/slow idle addresses; both regions; DMA disabled, ordinary and overlong;
one or two consecutive writes. There are 1,440 write selections, 2,288
READY edges, 6,400 HALT edges, 12,800 ownership transitions and 1,064,784 CPU
phase strobes. 184 cases have a short release followed by reassertion; the
other 776 have one assertion/release pair. These are legal bus waveform
stimuli, not an executed 6502 guest or physical chip traces.

Four detailed cases preserve every event. The complete matrix preserves
per-stream counts and FNV-1a signatures, with an explicit Cartesian case
inventory. Direct save continuations cover distinct write/wait/output and
CPU phases for 1,024 native ticks, comparing live bus, READY, pending stages
and complete state. Three deliberate faults fail: removing the line-reset
bypass, replacing the held output with the internal wait, and losing the
saved wait latch. The three booleans join the already-approved unreleased
runtime v6/direct version-1 layout; neither intermediate layout may ship.

## Reproduction

Use the qualified adapters from [the clock handoff probe](2026-10-10-maria-clock-handoff.md).
From this repository:

```sh
python3 plans/2026-10-11-maria-wsync-timing/capture_wsync.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-wsync-timing/full \
  /private/tmp/maria-wsync-timing/full/wsync-matrix.txt
```

Compilation failure stops capture; each case must finish every write and
balanced READY transitions, with DMA activity present only in enabled cases.
The matrix and four detailed cases are generated together. SHA-256:

- Matrix: `daa3b7fc9aff317e8ed1ace7d9cb9a27dc4c381a1130558b369ac006cbab3e9e`
- Detailed: `3a3cbd258b7a81b31535e22b8ad52c28882930c4060d394433221e0acc129798`

Raw captures and deliberate-fault outputs are in
`/private/tmp/maria-wsync-timing/`. The own Python harness passes Ruff.
The [cutoff plan](2026-10-11-maria-dma-cutoff.md) lists the affected-package,
Asteroids, Clippy and format commands. All 121 affected package tests, the
separate 200-frame Asteroids smoke, Clippy and formatting pass. Source
commit: `15fb682e`. Native machine ownership, actual
CPU instruction/interrupt delivery, physical NMI phase and POKEY remain
open on draft PR #1704.
