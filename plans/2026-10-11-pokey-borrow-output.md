# Connect POKEY borrow scheduling to timed output

Engineering-frontier continuation of issue 192. The renderer's supplied-event
trace establishes half-cycle output behaviour, but the input event is a timer
borrow rather than a raw countdown edge. Qualify that connection before
designing new saved stages.

1. Extend the portable reference experiment with the unchanged timer-period,
   timer scheduling, counter reconstruction, AUDF selection and `FireTimer`
   methods. Execute the four original borrow-dispatch cases in a bounded
   switch wrapper; reject other event types and unsupported serial/deferred
   paths. Preserve original source in scratch only.
2. Drive both channel pairs through linked/unlinked, fast/base clocks, divider
   boundary values and slow-clock phases. Begin at explicitly supplied loaded
   counters, not an assumed power-up or CPU STIMER-write boundary. Observe
   actual scheduled borrow events, IRQ calls and renderer output transitions.
3. Check complete case inventory, first-event distance, settled high periods,
   linked low/high ordering and output delay relative to the actual enqueued
   event. Require negative controls which remove borrow delay or bypass event
   delivery. Treat unsupported executed branches as failures.
4. Preserve observations in the umbrella reference library, then reproducible
   scripts and summaries here. Use the resulting boundaries to write the
   pending-stage design, including machine clock routing, sample integration
   and save-schema impact. Do not change those contracts before agreement.

Exact files: the adjacent `2026-10-11-pokey-borrow-output/` directory, reusing
the scaffold and extraction conventions in `2026-10-11-pokey-filter-timing/`.
Primary note: `reference/by-system/atari-8bit/pokey-borrow-output.md`.
No production correction in this reference experiment.

## Result

All **576 connected cases** pass, comprising **210,884 timer events**,
**118,601 IRQ assertion calls** and **26,318 selected-channel output
transitions**. Reversing simultaneous dispatch order preserves those results.
Both deliberate mutations fail: removing borrow propagation changes the first
deadline; bypassing `FireTimer`'s renderer delivery loses the event inventory.

The reference schedules an unlinked borrow three clocks after the loaded
counter interval. Linked high events follow their final low event by another
three clocks. The selected waveform reaches the renderer output two clocks
after the corresponding borrow event. These coordinates connect the earlier
supplied-event capture to the original chip path; they do not establish CPU
write or power-up phase.

Both original channel pairs run at /28, /114 and direct clock, with low byte
0/1/15/255, high byte 0/1/2/255 and base-clock phases 0/1/divisor-minus-one.
All initial counters and AUDF latches are explicit. Serial/deferred event
paths fail if entered. The observer clears IRQ status after each dispatch to
identify assertion calls; it does not emulate CPU acknowledgement timing.
Only the selected high channel is audible, using ungated pure tone at volume 1.
The earlier renderer scaffold supplies the digital output observer and retains
its stated noise/init-mode/analogue limitations.

The first run failed `borrow delivery/order mismatch` because the driver ended
after the first of two events at the final timestamp. Draining that entire
timestamp resolves the missing observation. The reverse-priority run ensures
the successful result does not depend on that simultaneous dispatch ordering.

The current chip still fails all **16 linked-event cases**, despite correct
high-channel periods. Its low and high waveforms change together: interval
zero instead of three clocks. Both pairs and low bytes 0/1/15/255 with high
bytes 0/1 are covered, measuring the second high event. The diagnostic fails:

```text
assertion `left == right` failed: linked high event must follow the final low event by three clocks
  left: 16
 right: 0
```

Source was `91bb2ffe` (fast-period correction, now merged as `03372dda`). The
temporary probe left the source byte-identical, SHA-256
`89287a23e8c5fc8b71e37029ef053eeef3fbf3561928ff4652443185788ae6f4`.
This is retained evidence for the next stage correction, not a failing test
installed in the production suite. Issue 192 remains open.

Seven capture guards pass, rejecting absent/duplicate cases, shifted borrow or
output timestamps and lost IRQ delivery. All four C++ variants build with
warnings denied. Python lint/formatting and Rust probe formatting pass.
Primary observations precede this record in the umbrella note named above.
The manual and Altirra are both by Avery Lee; no independent hardware timing
claim is made. Original distribution: [Altirra](https://www.virtualdub.org/altirra.html).

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-borrow-output/capture.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-borrow-output -v
```

The complete observed baseline is retained as `baseline.txt.gz` (ordinary
gzip text, no source code); `samples.txt` gives three readable cases. Summary
hashes identify the full uncompressed captures. All extracted reference
methods stay in local scratch. `probe.rs` can be temporarily appended to
`crates/atari-pokey/src/lib.rs` in an isolated checkout and run with:

```sh
cargo test -p atari-pokey --lib \
  borrow_probe::linked_high_event_follows_low_event_by_three_clocks \
  -- --exact --nocapture
```

That diagnostic currently exits 101. Restore the original source after the
run. Register-delivery/reset collisions remain the next input-validation gate
for the proposed saved stages.
