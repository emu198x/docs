# Clock POKEY noise at channel timer events

Engineering-frontier work following the disabled-filter polarity correction.
The current mixer ANDs a continuously changing polynomial bit with an
unconditionally toggled timer output. The hardware instead clocks a retained
output flip-flop: a timer event either toggles it, samples noise into it, or is
blocked by poly-5. Between events its state holds.

## Evidence and bounded design

The Altirra Hardware Reference Manual pages 106–107 describes the sampled
waveform and its frequency aliases: a channel sampling poly-4 every multiple
of 15 clocks becomes constant. The vendored renderer's `FireTimer` method
implements the same retained transition. Issue #192's noise/filter concern
depends on this earlier stage being correct.

1. Compile the unchanged, hash-pinned `FireTimer` method in a small temporary
   C++ driver. Capture all channel, distortion, polynomial-selection, input
   bit, previous-state and timer-event combinations. Reject incomplete or
   duplicated input inventories and check event/state consistency. Exercise
   failing mutations in the verifier. Keep reference source outside Git.
2. Add a chip-level regression against those observations and public-output
   regressions for held noise and period aliases. Run them red before edits.
3. Reuse `Channel::output` as its actual retained output flip-flop. Clock it
   once for each existing divider underflow, including linked low/high events;
   move noise selection from the mixer to that clocked update. Keep timer/IRQ
   schedules, polynomial tables/phase, volume-only override and existing
   high-pass scheduling intact. Add no fields or dependencies and change no
   snapshot representation. This corrects the behavior of the existing saved
   flip-flop rather than adding another pipeline.
4. Replace the old combinational-gate test with the compiled-reference test:
   the old assertion encodes the diagnosed fault. Verify volume-only still
   clocks hidden state, masked audio events do not suppress timer IRQs, and
   linked events reach both output stages. Run chip and Atari consumer suites,
   Clippy, formatting and test hygiene before committing.

Primary observations go first to
`reference/by-system/atari-8bit/pokey-noise-sampling.md`. Own capture code and
bounded results go beside this plan; observed vectors and Rust tests belong
in `crates/atari-pokey/`.

This isolates the output-stage transfer from divider timing and polynomial
phase. It does not establish either from the supplied inputs. Short-polynomial
sequence/reset phase, channel tap delays, active high-pass timing and its
half-cycle pulses remain explicit subsequent gates. No model agreement here
is described as a new physical measurement.

## Root cause and results

The reference capture executes 4,096 distinct inputs: 1,152 cause output
changes and 2,560 hold because the clock is absent or blocked. Four verifier
tests reject missing/repeated inputs, forced holding and suppressed events.
Rust exercises every captured input in both normal and volume-only mode,
giving 8,192 retained-state checks. Before the correction, 1,792 disagree.
Afterward, all agree. The fixture test checks complete, unique input coverage.

Both public-output regressions fail on the former implementation:

```text
noise changed without a timer event: clock=1789772 AUDCTL=0 channel=0 distortion=0
sampling a repeated noise bit must stay constant: clock=1789772 channel=0 AUDC=cf AUDF=14
```

After the correction, 128 held-output cases and 32 frequency-alias cases
pass across all channels and both regional oscillator rates. All 32 detuned
controls produce changing noise, so silence alone cannot pass the gate.
Volume-only still advances hidden waveform state. Five linked/unlinked clock
configurations preserve timer IRQs while poly-5 blocks audio updates; linked
low-byte borrows and complete underflows update the appropriate outputs.

The consumer suite exposed an old test that assumed poly-4 continuously
gated a square wave and therefore had to be quieter by an arbitrary ratio:

```text
P4 (0.10901736) should remain gated relative to pure tone (0.12288636)
```

That assertion encoded the diagnosed mechanism. It is replaced in
`crates/machine-atari-800xl/src/lib.rs` by four executed cartridge alias tests
and four detuned controls. The guest now explicitly releases SKCTL init.
The test observes the CPU, mapped register writes and mixed audio drain,
requires complete audio windows, and checks settled silence versus audible
noise. Reinstating the old chip source makes this new machine test fail:

```text
repeated noise bit must settle to silence: AUDC=cf AUDF=14 RMS=0.08874711
```

The corrected chip passes 36 unit and four public-output tests, including the
preceding polarity matrix. All 136 Atari machine/runtime library tests pass.
Clippy on both affected crates, formatting, diff checks and test hygiene pass.
The old chip-level combinational truth-table test is replaced by the compiled
reference transfer test; no test is ignored or disabled.

The primary evidence is umbrella commit `380acc41`. The original manual is
available through [Avery Lee's Altirra page](https://www.virtualdub.org/altirra.html).
`summary.json` pins the source, extracted function and observed-vector hashes.
The C++ driver uses supplied bits at every tap position and supplied timer
events; it qualifies the transfer only, not the upstream clock/tap phases.

## Reproduction

From this docs repository:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-noise-sampling/capture.py \
  ../../emulators/atari/altirra/src/ATAudio/source/pokeyrenderer.cpp \
  /path/to/scratch /path/to/noise-transfer.txt /path/to/summary.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-noise-sampling -v
```

From the source repository:

```sh
cargo test -p atari-pokey
cargo test -p machine-atari-5200 -p machine-atari-800xl \
  -p machine-atari-7800 -p runtime-atari-5200 \
  -p runtime-atari-800xl -p runtime-atari-7800 --lib
cargo clippy -p atari-pokey -p machine-atari-800xl --all-targets -- -D warnings
cargo fmt --package atari-pokey --package machine-atari-800xl --check
```
