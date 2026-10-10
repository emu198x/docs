# MARIA DMA enable/restart at CPU bus boundaries

Continue the approved native DMA design after scanline cutoff. The current
native path gates a raster request directly on CTRL; the reference has a
CPU-written holding register, clocked register delivery and separate pending
HALT/start signals. Those boundaries need measurement before machine wiring.

1. Add an own full-clock reference harness under
   `plans/2026-10-11-maria-dma-restart/`. Change CPU address/data/RW only at
   eligible CPU phase-1 edges, finish the selected write in phase 2, and retain
   Sally's existing sampled-HALT ownership model. Sweep enable and
   disable/re-enable around VBlank end and HBlank start, fast/slow accesses,
   both regions and multiple zone heights. Record actual CPU writes, CTRL
   holding/commit edges, reads, HALT, address ownership and descriptor state.
   Assert no CPU write is invented while MARIA owns the bus.
2. Compare native MARIA against both internal commit-edge stimuli (to isolate
   DMA control) and the legal CPU bus sequence (to qualify register delivery).
   Reproduce each discrepancy before changing production. Extend only the
   existing native control/DMA stages and their approved unreleased v6/direct
   snapshot state. No aggregate delays or clock advancement in memory methods.
3. Compare save/resume across any new pending edges. Run the prior clock,
   fetch, ownership, playback and cutoff gates; affected packages, Asteroids,
   Clippy and formatting. Prove timing/state tests reject a deliberate fault.
4. Commit the bounded correction and evidence. Keep source PR #1704 draft
   until machine ownership, physical NMI and POKEY gates also pass. Any
   unresolved primary/reference disagreement stays explicit.

Primary sources: Atari 7800 Software Guide register and DMA timing sections,
GCC1702B acceptance specification. Implementation precedent is the qualified
Atari7800_MiSTer revision `29aaacbbed127c670972c8a0a950ca82dc87e5df`, with
MAME as a separate control-semantics check. Reference RTL stays untouched.
Use the existing own bus harness and adapters; no new dependencies, geometry
changes or architectural pattern are needed.

## Findings and correction

Implemented in source commit `5b189b4e`, on the unmerged staged DMA branch.

The legal-write capture separates the CPU's write selection, the CTRL holding
register and the active register. A fast write selected at native tick 15422
enters the holding register at 15427 and becomes active at 15432. The previous
machine-style immediate delivery changed CTRL at 15426 instead:

```text
assertion `left == right` failed: tick 15426
  left: 96
 right: 64
```

Consecutive CTRL writes can replace the held value before either change
reaches the active register. The capture contains 864 CPU writes and holding
changes but only 800 active changes: 32 pairs coalesce. Requiring one active
change per write would incorrectly reject that behaviour. The gate requires
complete CPU/holding streams and compares the independently observed active
stream, including those zero-change cases.

DMA mode also crosses a sampling/reset pipeline. A pending request can
produce a short HALT pulse and then cancel before any reads. Once startup has
reached address ownership, DMA finishes even if CTRL disables further
requests. The initial Rust path failed to cancel the VBlank request:

```text
assertion `left == right` failed: case 14557 0 1 0 0 1, event 6
  left: "14575 B 0 1"
 right: "14574 H 1"
```

Native MARIA now samples CPU write pins, retains pending CTRL, and delivers
registers on their measured edges. DMA retains sampled mode and pending
request cancellation. These stages, input pins and write strobe are saved in
the existing approved, unreleased runtime-v6/direct-v1 layouts. The direct
`write` helper remains an immediate commit for the compatibility caller and
commit-edge playback fixtures; machine integration must use the new pins.

The compatibility scanline path also incorrectly accepted `DM=11` as enabled.
The software guide's CTRL table explicitly calls this “No DMA”; MAME and the
qualified reference agree. Its regression previously failed with reads still
occurring under CTRL `$60`. It now checks both mode bits and passes an
enable/disable/re-enable sequence in both regions. The diagnostic comment
claiming both `10` and `11` enabled DMA was corrected too. Test modes `00` and
`01` remain unimplemented and are not presented as normal DMA.

## Evidence

The full-clock restart matrix contains 576 cases: two raster boundaries,
nine requested write times, enable or disable/re-enable, heights 1/2,
fast/slow idle addresses, both regions and short/overrunning display lists.
CPU writes wait until an eligible phase-1 edge; none is inserted while MARIA
drives the bus. Four complete traces accompany per-stream counts and FNV-1a
signatures for the full matrix. It matches 176,930 reads, 190,142 address
transitions, 8,336 HALT edges, 16,560 ownership transitions and 4,608 zone/bank
observations, as well as all register events.

Warm fixture state is measured and asserted at tick 256, including the
reference's retained `ZONE_PTR=3`. Late enabling does not silently restart
the descriptor list. This fixture value is not a new physical-reset constant.
The own harness waits for combinational bus settling after changing CPU pins;
the earlier immediate post-assignment address trace was discarded.

An independent 64-case register capture checks 1,856 CPU writes and commits
across all four register mirrors, both regions and fast/slow CPU accesses.
It covers palette, background, display-list pointer, character base and CTRL.
WSYNC/RDY release remains separate, as does the colour-RAM collision delay
disabled in the reference implementation.

The four detailed restart cases save distinct pending register/DMA/clock
states, restore the input pins and continue for 256 native ticks after each
save. Comparisons include bus ownership, reads and the entire resulting
state, including both line banks. Removing CTRL's selection guard, dropping
the saved holding value, and suppressing request cancellation each fail the
regression. The single isolated write cannot detect the consecutive-write
guard fault; the complete restart trace does.

## Reproduction and validation

Use the checked scratch adapters from
[`2026-10-10-maria-clock-handoff.md`](2026-10-10-maria-clock-handoff.md).
From this docs repository:

```sh
python3 plans/2026-10-11-maria-dma-restart/capture_restart.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-dma-restart/settled \
  /private/tmp/maria-dma-restart/settled/vectors.txt
python3 plans/2026-10-11-maria-dma-restart/capture_registers.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-dma-restart/registers \
  ../emu198x/crates/atari-maria/tests/data/register-vectors.txt
```

The first script also writes `restart-matrix.txt` and `restart-vectors.txt`
beside its full capture. Both check compilation, complete case inventories,
actual event counts and valid register/bank data before producing fixtures.
Committed fixture SHA-256:

- Restart matrix: `99b68e5711a38ab7888bc63a1e9be76bb2f46bae75fe9f2fb45852710b95156e`
- Detailed restart: `87175f97a1b19fec0fa405ea34d773aba5b19cb10de8103b1df91a60f28f2dda`
- Register commits: `f5448933059a407a63df9c649ce43b808bac8fdb12560c195e3b525aa3611c00`

Source verification uses the affected-package, Asteroids, Clippy and format
commands in [the cutoff plan](2026-10-11-maria-dma-cutoff.md): all 115 package
tests, the separate 200-frame Asteroids smoke, Clippy and formatting pass.
The prior DMA, cutoff, fetch, clock and playback gates remain green. Logs and the
three deliberate-fault results are in `/private/tmp/maria-dma-restart/`.
Own Python scripts also pass Ruff. No reference RTL is copied into production.

## Remaining gates

Qualify holey-object termination and WSYNC release before replacing the
machine's aggregate renderer and DMA budget. Physical NMI timing, POKEY's
chip/sample clock separation and full native machine guest/save continuations
remain mandatory before PR #1704 merges. The physical colour-RAM collision
effect and power-on state are not settled by these reference captures.
