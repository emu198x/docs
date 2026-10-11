# Qualify reset collisions in linked POKEY timer pairs

Engineering-frontier continuation of issue 192. Extend the connected reference
counter/reset/output path to linked timers before implementing the proposed
retained stages. Production architecture/schema approval remains pending.

1. Reuse the unchanged connected reference methods and FIFO scheduler. Supply
   both linked pairs at /28, /114 and direct clock, the specified low/high divider
   boundaries, and reset around the second low or
   high event group. Observe both channels, their IRQs and selected waveform.
2. Cover low bytes 0/1/15/255, high bytes0/1/2/255, both anchors, nine reset
   offsets and no/single/repeated writes: 6,912 cases. Verify the complete
   pre-reset sequence, cancellation boundary, independently derived loaded
   counters after reset, settled periods and digital waveform through a bounded
   horizon. Distinguish supplied CPU-write ordering from physical bus phase.
3. Reject suppression of either high-channel delivery and omission of reset
   cancellation. Preserve complete observations compressed, source hashes and
   synthetic verifier guards. Reproduce relevant public IRQ failures using both
   linked pairs and controls, without permanent failing production tests.
4. Write primary observations and results, run capture guards and lint/build
   checks, commit bounded evidence and update issue 192. Linked AUDF/control
   transitions, polynomial phases and physical CPU-write phase remain separate.

Files: adjacent `2026-10-11-pokey-linked-reset/` driver, capture, probe, guards
and evidence; umbrella Atari-8bit reference note. No dependencies, production
API changes or save-format changes in this validation slice.

## Results

All **6,912 connected reference cases** pass. The complete capture contains
**2,532,866 borrow events**, **1,285,651 IRQ assertion calls**, **5,184 reset
calls** and **1,158,200 selected-channel output transitions**. Both members'
events and IRQs are checked on every row. Low-anchor rows make the low member
audible; high-anchor rows make the high member audible. Reset also starts the
other pair, as the original method requires, but those events are not included
in the selected-pair observations.

The checker independently derives the surviving pre-reset events and each
post-reset group's low/high deadlines from loaded values and base-clock phase.
It verifies intermediate low events, the three-clock separation of the final
low and high event, subsequent periods and all delivered waveform transitions.
The anchor is in the second group so every supplied write is after initial
setup, even for the shortest direct-clock divider. No/single/repeated-write
rows cover the same timing positions.

Suppressing either pair's high-channel delivery fails its borrow sequence;
removing one-clock-away cancellation fails a reset collision. Eight verifier
guards check complete inventory, duplicate rows, lost high IRQs, missing output
and altered borrow/reset phases. All four new variants compile with warnings
denied; prerequisite captures and their mutations pass during reproduction.
Ruff, Rust formatting and diff checks pass.

The public current-chip probe fails **288 of 384 cases**. All **96 no-reset
controls pass**. Both linked pairs and regional frequencies are covered, with
low bytes 0/1/15/255, high bytes 0/1, three lead times and single/repeated
writes. The actual failure is:

```text
assertion `left == right` failed: STIMER must preserve pending linked high IRQs
  left: 288
 right: 0
```

Immediate counter reload discards a high IRQ that should remain observable
and restarts four clocks early. The diagnostic warms up through two real IRQs
and verifies their period before supplying the write. It uses public IRQ status
and acknowledgement; this is not a private-field-only observation. Source is
`91bb2ffe`, merged as `03372dda`. The temporary integration test exits 101 and
is removed afterward, leaving production unchanged.

`baseline.txt.gz` retains the complete 54-MiB text capture, compressed to about
13 MB; `samples.txt` holds three readable rows. No original reference source is
committed. Source/driver/capture hashes and deliberate-fault results are in
`summary.json`. The observed values come from the same original methods used
by the preceding captures; only the supplied driver and verifier are extended.

Primary observations are in `reference/by-system/atari-8bit/pokey-linked-reset.md`.
Source and hardware account: [Altirra's author](https://www.virtualdub.org/altirra.html),
*Hardware Reference Manual*, pp. 105–110. Same-author agreement is not independent
hardware measurement. Coincident write ordering is supplied, not measured from
a physical CPU. Linked AUDF/control transitions, polynomial phase and analogue
behavior remain open; the production stage/schema proposal is still pending.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-linked-reset/capture.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-linked-reset -v
```

The runner rebuilds the pinned connected-reset prerequisites, then streams the
larger linked captures to disk and checks every row. Generated implementation
and uncompressed captures remain in local-output. To reproduce the public-chip
failure, copy `probe.rs` to an absent
`crates/atari-pokey/tests/linked_reset_probe.rs` in an isolated checkout and run:

```sh
cargo test -p atari-pokey --test linked_reset_probe -- --nocapture
```

The acceptance result currently **fails**, Cargo exit 101. Remove only the newly
installed test afterward. `chip-red.log` retains all 384 observations.
