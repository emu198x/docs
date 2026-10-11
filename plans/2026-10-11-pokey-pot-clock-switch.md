# POKEY pot clock changes during a scan

Engineering-frontier qualification of SKCTL delivery in the existing scanner.
No production or snapshot changes.

## Plan

1. Reuse the original pot paths and extract the complete original SKCTL write
   case into a scratch harness. Isolate unrelated audio/serial/keyboard effects
   with explicit observers; reject unsupported register bits and callbacks.
2. Ground all inputs to isolate clock switching from analogue charge. Exercise
   all pairs of slow/fast and initialization/running modes at several clock
   phases and write times, including unchanged-mode controls.
3. Check complete traces against independently derived counter deadlines and
   read-transition rules. Mutations must fail for lost delivery delay, wrong
   resumed base phase and missing fast-to-slow phase retention.
4. Record evidence and remaining input-change scope in the primary reference,
   this plan and issue 191. Production correction remains pending design.

Files: adjacent capture.py, extra.cpp, driver.cpp, test_capture.py,
baseline.txt.gz and summary.json; umbrella primary note
reference/by-system/atari-8bit/pokey-pot-clock-switch.md.

## Results

All **144 cases** pass: old/new SKCTL 0/3/4/7, /114 phases 0/57/110 and
writes at clocks 16/64/128. The matrix includes 36 unchanged-mode controls.
Every clock through 27,002 checks POT, ALLPOT, master count and scan activity,
for **3,888,432 clocks and 31,107,456 POT reads** across all eight inputs.

The original SKCTL path processes two clocks of the old pot mode before
switching, then waits for that processed time to pass. Leaving initialization
sets the next /114 increment 81 clocks after the write. Fast-to-slow changes
retain the base phase. Counter value survives the change.

Removing the delivery skew, moving the resumed phase by one clock, and using
the write time instead of the retained slow phase each fail. Eight integrity
tests reject incomplete/duplicate cases and timing faults. A positive variant
includes the /114 alignment otherwise performed by audio SetupTimers; the full
capture stays byte-identical.

## Isolation and interpretation

The complete original SKCTL case is unchanged, including its conditions and
pot-clock statements. The harness supplies no-op callbacks for unrelated audio
counter setup, renderer initialization and keyboard scheduling. Unexpected IRQ,
serial, cassette, key and break callbacks fail. Only SKCTL bits 0–2 are allowed.
This validates the pot path in isolation; it does not run whole-chip audio,
serial or keyboard state machines.

The original timer-counter update has no pot writes. SetupTimers can align the
shared /114 timestamp by whole periods; the positive variant confirms that
this alignment does not change any pot observation. Physical CPU-write phase
is still not established. Harness writes precede reads at the same timestamp.
The reference eagerly processes a future counter coordinate: do not translate
that into a physical instantaneous counter change or time advancement inside
production register accessors.

Sources: Avery Lee, *Altirra Hardware Reference Manual*, printed pp. 129–132,
[original distribution](https://www.virtualdub.org/altirra.html), and the original
POKEY source. They share an author. The primary note is
`reference/by-system/atari-8bit/pokey-pot-clock-switch.md` in the umbrella.
The prerequisite capture pins source identities and reruns its negative controls.
New source/capture hashes are in `summary.json`. Original source stays in scratch.

No production correction or new public-core failure is claimed; the previous
probes already reproduce ignored pot clock selection. Grounding/release,
input-rate changes and combined input/SKCTL transitions remain the next
validation boundary before a saved representation is proposed.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-pot-clock-switch/capture.py \
  ../../emulators/atari/altirra /private/tmp/pokey-pot-clock-switch-reproduction
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-pot-clock-switch -v
ruff check plans/2026-10-11-pokey-pot-clock-switch/*.py
ruff format --check plans/2026-10-11-pokey-pot-clock-switch/*.py
```
