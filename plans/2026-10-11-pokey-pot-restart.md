# POKEY charge retention and scan restart qualification

Engineering-frontier follow-up to the digital pot scan capture. Qualify the
existing reference's retained charge before proposing production scanner state.
No production code or snapshot changes are included.

## Plan

1. Reuse the hash-pinned, unchanged reference methods in the preceding capture.
2. Supply explicit fixed charge rates, initial charge and retained clock phase.
   Run through POTGO restarts before and after threshold and completion.
3. Check register, master-counter, active-scan and charge observations against
   closed-form interval calculations, including initialization mode and discharge.
   Require the complete case inventory and reject broken retention/latch controls.
4. Add a public Emu198x restart probe, then preserve the root-cause evidence in
   the primary note and this plan. Keep issue 191 open until a verified fix lands.

Files: this plan; adjacent capture.py, driver.cpp, test_capture.py, probe.rs,
baseline.txt.gz, summary.json and chip-red.log; umbrella primary note
reference/by-system/atari-8bit/pokey-pot-restart.md. Original source stays in scratch.

## Results

All **288 reference cases** pass, checking **16,512 observations** and
**132,096 POT reads**. The matrix covers SKCTL 0/3/4/7, /114 phases 0/57/110,
four supplied rates, initially empty or above-threshold charge, and POTGO
restarts at clock 64, 512 or 27,000. All eight inputs are checked against one
another. The reference advances on every clock; the checker observes the
complete declared inventory of checkpoints before/after each restart and
around relevant digital boundaries. This is not an every-clock output capture.

The supplied rates are threshold divided by 8/128/1024/25,992 clocks, rounded
down as integers. Initial latches hold a sentinel value of 42. This controls
the inputs directly and does not call the reference's paddle-position setter
or its optional immediate-update workaround. Closed-form intervals check
charge, master counter, scan activity, POT and ALLPOT; the checker contains no
copy of the reference update loop.

- POTGO retains charge; restarting before threshold shortens the subsequent
  count. Restarting above threshold preserves the old latch.
- ALLPOT can clear while the master scan remains active. In initialization
  mode, capacitors charge and latch zero although the master count is frozen.
- Fast mode continues charging after scan completion; slow mode discharges.
- Three mutations that discard charge, discard latches or stop the master
  scan early fail. Eight capture integrity tests pass.

The public Emu198x probe fails **128 of 192 cases**: all restarts after 16 or
32 scan lines fail, while all 64 no-restart controls pass. It covers both
regional frequencies, all eight inputs and targets 64/100/128/200. The scan
returns the original target instead of a reduced count. Cargo exits 101:

```text
assertion `left == right` failed: POTGO must retain the input's accumulated charge
  left: [0, 64, 64]
 right: [0, 0, 0]
```

The public invariant allows two counts of uncertainty for the unqualified
clock phase and input quantisation; errors of 16 and 32 counts remain far
outside it. This demonstrates loss of scan history, not exact analogue timing.
The temporary test is removed afterward; production source is unchanged.

## Sources and limits

Avery Lee, *Altirra Hardware Reference Manual*, printed pp. 129–132,
[original distribution](https://www.virtualdub.org/altirra.html), and the original
POKEY implementation qualified by the preceding digital capture. Primary
observations are recorded in the umbrella's
`reference/by-system/atari-8bit/pokey-pot-restart.md`. Pinned source identities
are inherited by executing the prerequisite harness, including its negative
controls. Full observations and assembled-source hashes are in `summary.json`.

The reference approximates charging/discharging with fixed integer rates and
retains its two-clock startup bookkeeping on each POTGO. These are qualified
implementation properties, not measurements of capacitor physics or CPU pin
phase. The manual describes an approximately exponential discharge. Do not
promote the reference's exact constants or bookkeeping to physical facts.

Still unqualified: mid-scan SKCTL transitions, input-rate changes, grounding
and release, physical write phase and calibrated paddle response. A correction
needs a separate master counter, per-input retained charge/threshold/latch state
and shared clock phase; the present per-target counters cannot express these
observations. Qualify the remaining digital transitions before proposing the
saved representation. No new schema or architecture is approved by this capture.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-pot-restart/capture.py \
  ../../emulators/atari/altirra /private/tmp/pokey-pot-restart-reproduction
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-pot-restart -v
ruff check plans/2026-10-11-pokey-pot-restart/*.py
ruff format --check plans/2026-10-11-pokey-pot-restart/*.py
rustfmt --edition 2024 --check plans/2026-10-11-pokey-pot-restart/probe.rs
```

Copy `probe.rs` into an isolated source worktree as
`crates/atari-pokey/tests/pot_restart_probe.rs`, run
`cargo test -p atari-pokey --test pot_restart_probe -- --nocapture`, then remove
only that temporary probe. Expected result: Cargo exit 101 with the retained
failure above. Extracted reference source is generated only in scratch.
