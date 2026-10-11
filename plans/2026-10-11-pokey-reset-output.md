# Qualify POKEY reset delivery through the audio renderer

Engineering-frontier continuation of issue 192. The STIMER capture currently
observes the renderer reset entry point only. Execute its actual change queue,
reset dispatcher and flush boundaries before designing the saved output stages.

1. Extend the existing portable renderer scaffold with the original ResetTimers,
   QueueChangeEvent, ProcessChangeEvents, Flush and UpdateOutput methods. Retain
   the digital mix-index observer before analogue filtering. All extracted
   source stays in scratch; unrelated register and polynomial paths stay outside
   qualification.
2. Exercise all four channels, both initial flip-flop values, normal/volume-only
   modes, both eligible filter latches and disabled filters, no pending event or
   nine event offsets around reset, and three flush partitions. Check all 960
   cases, complete timed output and final hidden state. A supplied renderer reset
   is not a new CPU-write timing measurement.
3. Require missing reset, incorrect preset and wrong delivery-time mutations to
   fail. Preserve complete observations and add malformed/incomplete/shifted
   capture guards. Reproduce any confirmed current-chip fault through public
   channel samples, with controls, without installing permanent failing tests.
4. Connect the qualified STIMER write/counter stages directly to this renderer
   and rerun all 1,440 timer-reset cases through final waveform changes. Verify
   borrow/IRQ/reset observations unchanged and assert their complete digital
   output timeline. Reject a deliberately disconnected renderer reset.
5. Record primary observations, then results here; run C++ warnings-as-errors,
   Ruff, Rust formatting and hygiene. No production API or snapshot changes;
   the separate POKEY staged proposal remains pending approval.

Exact files: adjacent `2026-10-11-pokey-reset-output/` harness additions, driver,
capture, guards and evidence; umbrella `reference/by-system/atari-8bit/` note.
Reuse `2026-10-11-pokey-filter-timing/` reference extraction/scaffolding and the
verified connected-borrow capture for source assembly.

## Results

All **960 supplied renderer cases** pass, with **624 visible transitions** and
complete hidden-state checks. Reset presets the waveform flip-flops, preserves
the filter latch and changes hidden waveform state even under volume-only
output. Pending pure-tone events toggle the state at their delivered boundary;
reset precedes a coincident delivered toggle. All three flush partitions agree.
Missing reset, wrong preset and one-clock-late delivery mutations all fail.

The full STIMER-to-output connection also passes **all 1,440 cases**, producing
**7,808 output transitions**. Its timer/IRQ/reset capture is byte-identical to
the preceding counter experiment: 7,560 borrow events, 5,172 IRQ assertion calls
and 1,080 reset calls. The renderer receives actual reset calls from the original
second reset stage; the output observer sees the waveform change at write+4 in
reference scheduler coordinates. Disconnection leaves the timer capture intact
but fails `connected reset waveform mismatch`. This checks the end of the path,
not merely that the reset method was called.

The initial combined build failed on duplicate event-enum definitions. Its two
components both retained the shared enum; the assembler now attaches the timer
component after that definition. No reference method or expected timing changed.
All combined and supplied-event executables compile with warnings denied.

The public current-chip diagnostic fails **16 of 64 cases**, covering all four
channels and both regional frequencies when reset must change an unpreset
waveform. Normal and volume-only modes both fail; releasing volume-only exposes
the stale hidden state. All32 no-reset controls and 16 already-preset cases pass.
Initial states are established through observed public channel samples, not an
assumed power-up phase. The actual failure is:

```text
assertion `left == right` failed: STIMER must preset the retained audio flip-flops
  left: 16
 right: 0
```

The STIMER accessor reloads counters but never presets waveform output. This is
separate from its previously reproduced premature counter reset. The diagnostic
checks settled public samples; it does not measure the exact four-clock output
boundary. Source was `91bb2ffe`; the temporary test is removed after capture and
the source checkout remains unchanged. Cargo exits101. No permanent failing
test or production timing change is installed.

All **13 verifier tests** pass: 8 renderer guards and 5 connected-path guards.
Ruff, Rust formatting and diff checks pass. The prerequisite counter and borrow
captures rebuild with their existing mutations on full reproduction. Complete
data is in `baseline.txt` and `connected.txt`; method and capture hashes are in
their summaries. Extracted implementation stays in scratch.

Primary observations are in `reference/by-system/atari-8bit/pokey-reset-output.md`.
The *Altirra Hardware Reference Manual*, pp. 108 and 442, and source distribution
are available through [the author](https://www.virtualdub.org/altirra.html).
The same-author agreement is not an independent physical capture. Analogue
output, polynomial phase, linked/control-write interactions and physical CPU
write timing remain open. Issue 192 and the additional stage proposal remain
open.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-reset-output/connected.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-reset-output -v
```

The connected runner rebuilds and validates both component experiments before
joining them. `capture.py` runs the supplied renderer cases independently.
To reproduce the current-chip failure, copy `probe.rs` to an otherwise absent
`crates/atari-pokey/tests/reset_output_probe.rs` in an isolated checkout and run:

```sh
cargo test -p atari-pokey --test reset_output_probe -- --nocapture
```

Acceptance currently **fails**, Cargo exit 101. Remove only that newly installed
test afterward. `chip-red.log` retains all 64 observations and the assertion.
