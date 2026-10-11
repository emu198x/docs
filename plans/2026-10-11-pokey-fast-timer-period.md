# Restore the high-speed POKEY timer period

Engineering-frontier correction found while qualifying issue 192's upstream
timer phases. Unlinked channels 1/3 currently reload AUDF directly, producing
AUDF+1 clocks per event at high speed. The hardware reference p. 105 and
Altirra's `RecomputeTimerPeriod` specify AUDF+4. The existing linked counter
already represents its six propagation clocks in the same retained counter.

1. Execute unchanged `RecomputeTimerPeriod` across all AUDF bytes, channels
   and base/fast clock modes. Keep reference extraction in scratch storage.
2. Add reference-backed chip tests for both fast channels and public timer-1
   IRQ-spacing tests. Include base-clock channels, both regional clocks, and
   linked-mode controls. Demonstrate failure before changing production code.
3. Extend the existing unlinked fast counter's reload by three clocks, including
   its initialization through the current STIMER path. Preserve linked/base
   behaviour. Update tests that currently assert the wrong fast period.
   Exact CPU-write delivery and separate borrow stages remain unqualified;
   do not claim this period correction settles those phases.
4. Run chip and affected machine/runtime tests, Clippy and formatting. Preserve
   primary observations, commit one bounded correction and merge after CI.
   No new fields, API, dependency or snapshot schema.

Exact source files: `crates/atari-pokey/src/lib.rs` and focused timer tests in
`crates/atari-pokey/tests/`. Evidence lives in the adjacent plan directory;
primary observations go to `reference/by-system/atari-8bit/pokey-timer-period.md`.

## Result

The compiled reference supplies all **3,072 unlinked period cases**, covering
four channels, three clock selections and all 256 AUDF values. The original
counter fails all **512 fast-channel rows**; base-clock rows already match.
The first failing row is:

```text
512 period mismatches; first: Some(([0, 2, 0, 4], [1, 2, 3]))
```

The independent public IRQ probe fails all **512 clock/divider cases**:

```text
512 IRQ period mismatches; first: Some((1789772, 0, [1, 2, 3, 4, 5]))
```

Both now pass. `Channel::reload` includes three additional direct-clock counts;
its two callers select fast mode from the channel and AUDCTL. Linked reloads
still replace the low counter with their existing 16-bit/+6 value. Base-clock
reloads remain AUDF. The maximum fast period, 259 clocks, fits the existing
32-bit saved counter. Two unit tests which asserted the old AUDF+1 timing now
use the corrected modeled counter interval.

All **45 chip tests** and **136 affected machine/runtime library tests** pass.
Existing linked-period, serial, noise, filter-latch and polarity checks pass.
Clippy with warnings denied, Rust formatting, four capture guards and Python
lint/formatting pass. The capture checks reject missing/duplicate rows and
removing fast propagation; both new production tests were observed failing
before the correction. Full local output is in
`/private/tmp/pokey-fast-timer-period/`; the two initial failures and pinned
reference hashes are retained beside this plan.

No API or save-layout change. This establishes settled pitch and IRQ spacing,
not exact STIMER write latency, AUDF/AUDCTL delivery during an in-flight borrow,
linked low/high event ordering, or half-cycle filter pulse timing. Issue 192
remains open. The broader output-stage design still needs the borrow-phase
qualification begun in the preceding timing plan.

The original reference is Avery Lee's *Altirra Hardware Reference Manual*,
p. 105, available through [the author's site](https://www.virtualdub.org/altirra.html).
The implementation is by the same author; these are corroborating descriptions,
not independent hardware captures. The primary note named above records the
exact source hashes and observation limits.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-fast-timer-period/capture.py \
  ../../emulators/atari/altirra/src/ATAudio/source/pokey.cpp \
  /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-fast-timer-period -v
```

The emitted `periods.txt` matches the source fixture
`crates/atari-pokey/tests/data/timer-periods.txt`. The capture compiles the
unchanged function under C++17 with warnings denied; generated reference code
stays outside Git. Run `cargo test -p atari-pokey` in the source checkout for
the complete fixture and public IRQ checks.
