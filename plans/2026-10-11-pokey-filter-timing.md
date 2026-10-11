# Qualify POKEY high-pass output timing

Continue issue 192 in the engineering-frontier lane. The corrected waveform
transfer and disabled filter latch do not qualify the active filter's timing.
The hardware reference describes half-cycle pulses that the current whole-
cycle output path cannot represent.

1. Execute the pinned Altirra renderer's unchanged `AddChannelEvent`, `Flush2`,
   timer dispatch/transfer, edge merge and `ProcessOutputEdges` methods in a
   portable local C++ harness. Extract reference text only into scratch storage.
   Observe digital channel output before analogue mixing; fail on unsupported
   executed branches instead of silently substituting missing behaviour.
2. Supply known pure-tone timer events to both filter pairs. Sweep relative
   event phase, waveform/filter initial bits, enabled/disabled filtering and
   volume-only output. Compare whole-window and partitioned flushing. Preserve
   timer-event coordinates separately from physical counter-underflow timing.
3. Require complete nonempty case and event inventories, record half-cycle
   transitions/pulse widths and exercise mutations that remove or shift them.
   Compare the equivalent current chip stage where its granularity permits;
   do not claim full timer/noise/register-write phase equivalence from this
   supplied-event experiment.
4. Preserve primary observations before the derived summary; run capture
   guard tests, compile warnings and Python lint/format checks. Write a concrete
   implementation design only after the timed evidence is available. Additional
   retained stages, clock contracts or save schemas require agreement; this
   research slice changes none of those.

Exact files: probes, guards and bounded evidence in the adjacent
`2026-10-11-pokey-filter-timing/` directory. Reuse the extraction conventions in
`2026-10-11-pokey-noise-sampling/capture.py`. Primary observations belong in
`reference/by-system/atari-8bit/pokey-filter-timing.md` at the umbrella.

## Executed evidence

The unchanged renderer passes all **648 supplied-event cases**, consuming
**7,776 input events**. Both filter pairs produce the same result across
1/7/120-cycle flush partitions. The trace contains **1,188 half-cycle
transitions**, including **120 settled half-cycle pulses**. Volume-only
controls remain constant and disabled-filter tones retain their inversion.
Rounding the filter update down to a whole cycle in an extracted-code
mutation fails with `missing settled half-cycle pulses`.

The scaffold observes the digital mix index for one volume-1 channel, before
analogue conversion. It coalesces simultaneous intermediate values so a
zero-duration transition cannot be counted as a pulse. Polynomial updating,
deferred event generation and audio logging fail if unexpectedly executed.
Pure tones bypass polynomial reads; selecting the init-mode table branch
does not qualify physical initialization. Reference source, extracted-method
and harness hashes are in `summary.json`. Generated reference code stays in
local scratch storage.

The public chip probe runs against main `8a312132`, including the three merged
POKEY corrections. All **32 synchronized active-filter cases remain completely
silent** after warm-up. The other **64 controls pass**: unfiltered pure tones
vary and volume-only output stays at one. All 96 rows produce more than 1,700
host samples. Both regional clocks, both base clocks, both filter pairs and
AUDF 0/3/15/63 are covered. The diagnostic fails:

```text
assertion `left == right` failed: half-cycle filter offset cannot erase the entire waveform
  left: 32
 right: 0
```

The manual's p. 108 description rules out complete cancellation. The current
chip updates the waveform and immediately captures that same value into its
filter latch. Its mixer observes equality, and the sample accumulator receives
no pulse area. The failure is now established through the public audio output;
it is not inferred solely from source inspection.

Seven capture guards pass, including missing/duplicate inputs, erased pulses
and flush-partition disagreement. The C++ builds use `-Wall -Wextra -Werror`;
Python lint/formatting and Rust probe formatting pass. No production code,
clock API or save format changed. Issue 192 remains open.

## Timing boundary before implementation

The renderer schedules waveform transitions at input-event +2 cycles and
filter operations at paired-input-event +0.5 cycles. These supplied events
enter through the actual scheduler enqueue method. In the full chip, its
caller is the timer-borrow handler. Its timestamp must be reconciled with raw
counter underflow and timer IRQ timing before selecting production phases.
In particular, the renderer's positive relative input offset must not be
equated to the manual's wording about a high timer running two cycles ahead.

The next implementation design must preserve timed waveform/filter state and
its pulse area through sampling and save/restore. That still requires a
concrete clock/schema agreement. Changing latch assignment order alone would
not represent the observed half-cycle pulse. Register-write delivery and
polynomial phase are outside this supplied-pure-tone experiment.

Primary observations are recorded in the umbrella reference note named above.
The manual and implementation are both by Avery Lee, so they do not constitute
independent hardware measurements. Original distribution:
[Altirra](https://www.virtualdub.org/altirra.html).

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-filter-timing/capture.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-filter-timing -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-filter-timing/probe_chip.py \
  ../emu198x-pokey-polarity /path/to/local-output/chip-red.log \
  --target-dir ../emu198x/target
```

The reference capture and its negative-control verifier pass. The public chip
probe exits **101** while this defect remains; its temporary integration test
is removed after execution. The runner refuses to overwrite an existing file.
