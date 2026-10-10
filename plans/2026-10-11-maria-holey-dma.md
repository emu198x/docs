# MARIA holey-object termination

Qualify holey DMA before connecting the native machine caller. The native
fetch path currently substitutes zero for each holey graphics byte and
continues the object. The qualified reference suppresses the line-RAM write
and clears the width counter. MAME's aggregate renderer continues bytes;
the software guide defines address holes but does not settle their native
shutdown timing. Preserve this distinction in the evidence.

1. Extend the own full-clock bus harness with hole-mask, graphics-address,
   direct/indirect width, zone height and Kangaroo cases. Include crossings
   into/out of a hole, the second byte of an indirect character, a prior
   overlapping object and a following visible object. Record reads, address
   setup, HALT/ownership, zone handoff and both line banks. Reference code
   stays untouched; use the existing qualified scratch adapters.
2. Reproduce the native mismatch, then correct the existing fetch stages.
   Suppress actual reads/writes and terminate at measured edges rather than
   charging a whole object's fake reads. Compare mid-stage save continuations
   within the already-approved unreleased snapshot layouts.
3. Run all previous native timing/playback/control gates, affected packages,
   Asteroids, Clippy and formatting. Use a deliberate holey timing/pixel fault
   to prove the gate rejects a wrong implementation. Commit evidence and the
   bounded correction; keep PR #1704 draft for WSYNC, native machine wiring,
   physical NMI and POKEY gates.

Sources: Atari 7800 Software Guide holey-DMA and DLL sections; qualified
Atari7800_MiSTer `29aaacbbed127c670972c8a0a950ca82dc87e5df`, with MAME as
contrasting implementation precedent. This extends the approved fetch
pipeline; no new dependencies, geometry changes or architectural pattern.

## Result

The existing fetch stages now suppress the actual graphics latch/write and
end the object after its current character. Two-byte indirect mode retains
both address slots; a hole on the first byte remains latched across the
second byte, including address wrap out of the masked window. HPOS and prior
overlapping pixels remain unchanged, even with Kangaroo enabled.

The first native regression reproduced the continued-width fault:

```text
assertion `left == right` failed: case 1 8 1 1 34816 1 0 0, event 41
  left: "15507 A 8801"
 right: "15507 A 1c08"
```

In that case the reference moves from the first suppressed graphics slot
to the next object's header. The previous implementation instead advanced
to another graphics byte, and its zero-byte blit could erase earlier pixels.
The shared fetch path fixes both native DMA and the compatibility renderer.
The existing saved `holey` flag retains suppression; no snapshot fields or
version changes are added to the approved unreleased layout.

The reference matrix contains 696 distinct cases. Address-boundary rows
cover all four fetch forms, all four masks, seven graphics addresses,
widths 2/8 and Kangaroo on/off. A separate timing set covers widths
1/2/8/31-or-32, heights 1/2/8/16, both CPU speeds and both regions. The
complete union is checked, rather than relying only on a row count.
The addresses include the lower-memory exception, entry into H8/H16 holes,
and `$FFFF` wrap. Prior overlapping and following visible objects make
suppressed writes and premature termination observable.

All 122,826 byte consumptions, 142,516 address transitions, 11,136 HALT
edges, 22,272 ownership transitions and 5,568 zone/two-bank observations
match the independent capture. Four cases retain full events; the matrix
retains per-stream counts and FNV-1a signatures. Pending direct, indirect
and second-byte holey stages resume for 256 native ticks and match live bus,
read and complete state continuations, including suppressed `$0000` slots.

Three deliberate faults fail the detailed regression: removing sticky
suppression, writing zero pixels over the prior object, and skipping the
second indirect slot. These independently exercise read suppression, pixel
preservation and timing.

## Reproduction

Use the existing qualified reference adapters documented in
[`2026-10-10-maria-clock-handoff.md`](2026-10-10-maria-clock-handoff.md).
From the docs repository:

```sh
python3 plans/2026-10-11-maria-holey-dma/capture_holey.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-holey-dma/full \
  /private/tmp/maria-holey-dma/full/vectors.txt
```

The script checks compilation before simulation and requires complete
HALT cycles, read counts and both valid line-RAM banks. It writes the raw
capture plus `holey-matrix.txt` and `holey-vectors.txt`. Committed SHA-256:

- Matrix: `081655a9f7781b7b5fda67a44e822905d205a162503144d108cec914caa46abc`
- Detailed: `fd1f0a4fe65576d1f5071021c2bb8272f6cccb00e7f0137580caceebaf97455b`

Source verification uses the affected-package, Asteroids, Clippy and format
commands in [the cutoff plan](2026-10-11-maria-dma-cutoff.md). Logs and
deliberate-fault outputs are in `/private/tmp/maria-holey-dma/`; the own
Python capture script passes Ruff. All 118 affected package tests and the
separate 200-frame Asteroids smoke pass, as do Clippy and workspace
formatting. Source commit: `ca21699a`.

The software guide establishes hole address decoding but does not specify
the native termination edges. MAME also skips holey pixel writes, but its
aggregate loop continues checking later bytes. The reference's measured
object termination is the implemented precedent; this is not presented as
independent physical-chip verification. No reference RTL is copied into
production. WSYNC release and the other native machine/NMI/POKEY gates
remain open on draft PR #1704.
