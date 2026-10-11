# Preserve POKEY's unfiltered channel polarity

Engineering-frontier correction related to source issue #192. Its proposed
replacement of the XOR filter is not supported by the reference: the filter
does use a sampled bit and XOR. A separate, bounded defect is visible with
the filters disabled: channels 1/2 must be inverted relative to channels 3/4.
The current mixer uses the same polarity for all four.

The Altirra Hardware Reference Manual, page 108, describes synchronized pure
tones on channels 1/2 adding and channels 1/3 cancelling. Volume-only mode
bypasses that inversion. The vendored renderer independently implements the
disabled filter bits as ones, then XORs those bits into the low two outputs.
This establishes a waveform relationship without choosing an analogue gain
curve or depending on an internal counter's initial phase.

## Bounded design and verification

1. Record source identity and the observation in the umbrella reference layer.
   Inspect the existing mixer, reference renderer and archive implementation.
2. Add public-API regressions in
   `crates/atari-pokey/tests/unfiltered_polarity.rs`. Drive synchronized pure
   tones through register writes and ticks; check all six channel pairs,
   multiple periods, both base clocks and regional oscillator rates. Require
   nonempty output and changing tone levels. Opposite-polarity taps must sum
   to a constant; same-polarity taps must agree. Volume-only controls must add.
   Confirm these tests fail on the existing source before changing it.
3. In `crates/atari-pokey/src/lib.rs`, invert the disabled-filter output of
   channels 1/2, inside the existing volume-only bypass. Add no fields, APIs,
   timing stages or dependencies. Existing snapshot layouts are unchanged.
4. Run the regressions, chip tests, affected Atari machine/runtime tests,
   Clippy and formatting. Review and commit only this correction on its own
   branch, keeping the MARIA branch and pending POKEY snapshot work separate.

This does not settle filter enable/disable transitions, noise sampling,
half-cycle filter pulses or analogue mixing. Issue #192 remains open with a
corrected description; replacing its XOR with arithmetic subtraction would
not fix those problems. MARIA PR #1704 retains its physical NMI timing gate.

## Results

The unmodified mixer fails the public-output regression at the first
opposite-polarity pair (channels 1/3):

```text
clock=1789772 AUDCTL=0 AUDF=0 AUDC=af pair=0,2 sample=0:
opposite outputs must cancel, got 0.28947368+0.28947368
```

The volume-only control passes before the fix. After changing the two
disabled-filter branches, all 144 tone cases and 48 volume-only cases pass.
Each capture verifies its exact sample count (439 NTSC / 443 PAL), equal tap
lengths and, for tones, changing signal levels. Opposite-polarity pairs also
produce exactly the same mixed, DC-blocked output as a single volume-only
channel at full volume. Same-polarity pairs retain a changing mixed signal.

All 34 existing chip tests and both new integration tests pass. The six Atari
machine/runtime library suites pass 136 tests, with no ignored or failed
tests. Clippy (`atari-pokey --all-targets`, warnings denied), formatting, diff
checks and the 12-case ignore-policy self-test pass.

The donor archive has the same omitted inversion; no donor implementation
was copied. The source correction adds no retained state. Primary evidence
and hashes are in `reference/by-system/atari-8bit/pokey-output-polarity.md`,
umbrella commit `1324014d`. The manual is available through
[Avery Lee's Altirra page](https://www.virtualdub.org/altirra.html).

```sh
cargo test -p atari-pokey
cargo test -p machine-atari-5200 -p machine-atari-800xl \
  -p machine-atari-7800 -p runtime-atari-5200 \
  -p runtime-atari-800xl -p runtime-atari-7800 --lib
cargo clippy -p atari-pokey --all-targets -- -D warnings
cargo fmt --package atari-pokey --check
python3 scripts/check-ignore-reasons.py --self-test
```
