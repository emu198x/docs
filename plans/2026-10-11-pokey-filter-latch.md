# Preserve POKEY's disabled-filter latch through re-enable

Engineering-frontier follow-up to source issue #192. Disabling a filter forces
its retained bit high. The output XOR remains active. The existing mixer now
has the correct disabled polarity, but AUDCTL writes leave `hp_flipflop`
untouched, so enabling the filter can expose a stale bit.

The Altirra Hardware Reference Manual p108 states the forced-high latch rule.
The pinned `pokeyrenderer.cpp` AUDCTL handler sets bits `$10`/`$20` when their
filters are disabled; enabling preserves them. Its reset state also has both
filter bits high. Source identities and provenance are in the umbrella note
`reference/by-system/atari-8bit/pokey-output-polarity.md`.

## Bounded correction

1. Add public-output regressions in `crates/atari-pokey/tests/filter_latch.rs`.
   With channel timers held away from underflow, first enable must preserve
   disabled output. After a real paired-timer event captures a low bit,
   disable/re-enable must preserve the disabled output until the next event.
   Exercise both filter pairs, both base clocks, both regions, the other filter
   enabled/disabled, volume-only hiding and direct-state restore. Verify that
   changing only the other filter preserves the target's captured low bit.
2. Run those tests red. In `crates/atari-pokey/src/lib.rs`, initialise the two
   existing latches high because initial AUDCTL disables both filters. On an
   AUDCTL write, force each latch high if its old or new filter enable is clear;
   otherwise retain it. Checking the old enable also repairs an older snapshot
   whose disabled latch incorrectly contains zero before it is re-enabled.
3. Preserve the existing fields and snapshot layout. Add a focused saved-state
   compatibility regression for that older disabled latch. Do not change
   clock-to-register delivery or active-filter sampling/pulse stages.
4. Run chip/public-output tests, all affected Atari machine/runtime library
   suites, Clippy, formatting and hygiene. Record observed failures and results,
   commit separately and merge after CI. Keep issue #192 open for its remaining
   phase and active-filter timing gates.

No new dependency, API, schema or architectural pattern. This repairs the
retained state behind existing register/mixer behavior; it does not establish
the native phase at which a CPU write reaches that register.

## Results

Both new public-output regressions fail on the original source. First enable
and disable/re-enable each produce `left: 0.0`, `right: 1.0` despite no paired
timer event in the observation interval. The corrected existing latches pass
all 96 cases: 16 first-enable, 64 disable/re-enable and 16 older-state cases.

The matrix covers both regions, both base clocks, both filter pairs, the other
filter enabled/disabled, volume-only hiding and direct-state restore. Every
observation requires at least six samples at one stable digital level. The
disable/re-enable tests first require a real paired-timer capture to change
the output, so an always-high latch cannot satisfy the setup. Toggling only
the other filter must preserve that captured value.

The older-state regression reconstructs the unchanged compact representation
with a low latch under a disabled filter, as earlier versions could save it.
Removing the old-enable normalization makes this test fail:

```text
a disabled latch from an older save must be high before enable
left: 0.0
right: 1.0
```

Restoring the correction passes. This checks the retained latch and subsequent
held output; it does not claim that the separate audio-accumulator save defect
in issue #1705 is fixed.

The affected chip, machine and runtime test command completes 37 executables:
229 tests pass, none fail and 16 existing fixture-gated tests remain ignored.
That includes all 136 Atari machine/runtime library tests and the earlier
noise/polarity regressions. No optional ROM coverage is inferred from those
ignored tests. Clippy with warnings denied, formatting, diff checks and the
12-case ignore-policy self-test pass.

Primary retention evidence is umbrella commit `53fd3e57`; the original manual
is available through [Avery Lee's Altirra page](https://www.virtualdub.org/altirra.html).
No fields or serialization layouts change. This corrects the logical register
stage, while CPU-write delivery and active-filter pulse phases remain open.

## Reproduction

```sh
cargo test -p atari-pokey --test filter_latch
cargo test -p atari-pokey -p machine-atari-5200 -p machine-atari-800xl \
  -p machine-atari-7800 -p runtime-atari-5200 -p runtime-atari-800xl \
  -p runtime-atari-7800 --lib --tests
cargo clippy -p atari-pokey --all-targets -- -D warnings
cargo fmt --package atari-pokey --check
python3 scripts/check-ignore-reasons.py --self-test
```
