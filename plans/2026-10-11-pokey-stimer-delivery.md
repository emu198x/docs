# Qualify POKEY STIMER cancellation and reload stages

Engineering-frontier continuation of issue 192. Keep the proposed production
stages and snapshot changes pending their separate approval. This experiment
changes only reference validation.

1. Extend the bounded connected timer harness with the original STIMER write
   case and both scheduled reset cases. Supply stable event slots and FIFO tie
   ordering, as inspected in Altirra's scheduler. Check replacing/cancelling
   events explicitly. Observe renderer reset calls without claiming their
   waveform effect is executed.
2. Start an unlinked channel from a declared loaded count of 32. Exercise all
   four channels at both base clocks and both direct-clock-capable channels,
   four AUDF boundaries, reset writes from six clocks before through two after
   the first borrow, and no reset/single reset/retrigger after one or two clocks.
   Verify all 1,440 rows, exact borrow/IRQ delivery and reset observer timing.
3. Require mutations that suppress cancellation or move either reset stage to
   fail. Inspect coincident ordering against the original scheduler before
   treating it as an oracle. Retain source hashes and full observations; source
   extraction remains in scratch. Qualify no linked, control-write or analogue
   behavior from this bounded experiment.
4. Reproduce any confirmed public-chip fault, retaining failing evidence and
   restoring production files. Write primary observations first, then results
   here. Run verifier/scheduler guards, C++ warnings-as-errors, Ruff and Rust
   formatting. Keep issue 192 open until the full correction is implemented.

Files: adjacent `2026-10-11-pokey-stimer-delivery/` driver, scheduler, capture,
verifier guards and observations; primary note in the umbrella Atari-8bit
reference folder. Reuse the connected-borrow capture as the prerequisite.

## Results

All **1,440 reference cases** pass, with **7,560 selected-channel borrow
events**, **5,172 IRQ assertion calls** and **1,080 renderer-reset calls**.
The original STIMER write schedules its first event three clocks later. That
event cancels a borrow due one clock afterward, then schedules the second
reset event for the next clock. Coincident first-stage borrows remain visible.
Repeated writes one/two clocks apart replace the pending first-stage event.

The reference counter assignment at write+4 is an implementation coordinate,
not a claim that the hardware reload occurs at that phase. The *Altirra
Hardware Reference Manual*, printed pp108–110, describes physical reload at
write+3, four-clock IRQ preemption, unchanged base-clock phase, and the first
AUDF0 direct-clock IRQ at write+8. The executed IRQ trace agrees with the
preemption and initial-period boundaries. The manual and implementation have
the same author; this is not independent hardware measurement.

The public current-chip probe fails **72 of 96 cases**; all **24 no-reset
controls pass**. It warms up through two IRQs, then writes STIMER one/two/three
clocks before the next predicted IRQ, with single and repeated writes, four
divider values and both regional frequencies. The actual failure is:

```text
assertion `left == right` failed: STIMER must preserve pending IRQs until its reset stages arrive
  left: 72
 right: 0
```

The register accessor reloads the counters immediately. This drops the pending
IRQ and advances the reset period four clocks relative to the reference.
The test checks actual IRQ status and clears/re-enables it through register
writes after each observation. Source was `91bb2ffe`, whose period correction
merged as `03372dda`. The diagnostic exits101 and is removed after capture;
the source worktree remains clean with chip source hash
`89287a23e8c5fc8b71e37029ef053eeef3fbf3561928ff4652443185788ae6f4`.

Three timing mutations fail: no cancellation, early first stage and late second
stage. Reversed FIFO ordering fails the scheduler's guard. Nine verifier tests
reject incomplete/duplicate inventories, shifted inputs/reset/borrow times,
missing IRQs and uncoalesced repeated writes. All five executables compile with
warnings denied. Ruff, Rust formatting and diff checks pass. The earlier
connected-borrow matrix is rebuilt and checked as a prerequisite.

The own scheduler follows the inspected original equal-time insertion order;
its implementation is bounded to four borrows and two resets. Source hashes
are in `summary.json`. Supplied writes follow events already scheduled for the
same timestamp; no physical CPU bus phase is inferred. The renderer reset
entry is an observer only, so this does not qualify its waveform change.
Other channels are started by reset, but each row checks only its selected
channel's complete sequence through the declared horizon. Linked counters,
two-tone mode, STIMER/AUDF combinations, other control writes and power-up
remain open. No production or save-format change is made here.

Primary observations are in
`reference/by-system/atari-8bit/pokey-stimer-delivery.md`. The original sources
are distributed through [Altirra's author](https://www.virtualdub.org/altirra.html).
Issue192 remains open; the separate staged design is still proposed.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-stimer-delivery/capture.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-stimer-delivery -v
```

The full observed matrix is `baseline.txt`, with no reference source. Generated
C++ stays in local-output. To reproduce the public-chip failure, copy `probe.rs`
to an absent `crates/atari-pokey/tests/stimer_delivery_probe.rs` in an isolated
checkout and run:

```sh
cargo test -p atari-pokey --test stimer_delivery_probe -- --nocapture
```

This acceptance check currently **fails**, Cargo exit101. Remove only that
newly installed file afterward. `chip-red.log` retains all observations and
the failed assertion.
