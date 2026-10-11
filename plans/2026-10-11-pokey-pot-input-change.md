# POKEY live input changes

Engineering-frontier qualification of input-rate changes and grounding/release.
No production changes or new saved state are included.

## Plan

1. Extract the unchanged original input setter alongside the previously
   qualified pot methods. Keep the reference's immediate-update workaround off.
2. Change one input at a time: unchanged control, faster/slower charge,
   grounding/release, and floating/reconnection. Cover each channel, both slow
   and fast clocks, initialization, several phases and active/completed scans.
3. Compare complete checkpoint inventories against charge-interval equations;
   check untouched channels too. Reject lost charge, lost rearming and the
   optional immediate-update workaround with negative controls.
4. Preserve observations in the primary reference layer, this plan and issue
   191; state the remaining combined SKCTL/input and physical-phase limits.

Files: adjacent capture.py, driver.cpp, test_capture.py, baseline.txt.gz and
summary.json; umbrella reference/by-system/atari-8bit/pokey-pot-input-change.md.
Reference source is read-only and extracted only in scratch.

## Results

All **1,920 reference cases** pass, covering SKCTL 0/3/4/7, retained /114 phases
0/57, starting positions 64/200, five actions, three change times and each
selected input 0–7. Actions are unchanged control, position 1, position 200,
ground/release and disconnect/reconnect. The latter two restore the original
position after 64 clocks. Input changes occur at clocks 64, 8,192 or 27,000,
so they include active and completed scans.

The reference advances on every clock. The checker validates the complete
inventory of **60,288 checkpoints**, including before/after input changes,
selected and untouched POT readings, ALLPOT, master count, scan activity and
selected/untouched charge. All seven untouched channels must agree. This is
checkpoint coverage, not exhaustive output observation on every clock.

The unchanged original `SetPotPosHires` supplies the actual input rates. Its
optional immediate-update workaround is disabled. Independent constant-rate
interval equations check charge accumulated before and after each change.

- Rate changes retain partial charge and do not replace an already-latched
  value. The resulting count depends on the input's history.
- Grounding discharges the selected input and rearms its ALLPOT bit if the
  master scan is active. The POT register resumes following the current master
  count without POTGO. Other inputs and the master count are unaffected.
- Floating stops further charging without discarding existing charge.
  Reconnection resumes charging from that level.
- After the master scan ends, grounding does not restart it or rearm ALLPOT.

Three negative variants fail: discarding charge on a rate change, omitting
rearming on grounding, and enabling the optional immediate-update workaround.
Eight capture guards pass, including untouched-channel corruption.

## Public-core failure

A public probe changes a paddle target between 64 and 200 after one-quarter,
one-half or three-quarters of the original conversion. It covers both regional
frequencies and each selected input. All **96 changed-input cases fail**; all
**32 unchanged controls pass**. The expected retained-charge count allows two
counts of phase/quantisation uncertainty; this is not exact analogue calibration.
For example, changing 64 to 200 halfway through should give about 132, but the
core gives 200. Changing 200 to 64 after 150 scan lines gives 228 instead of
about 166: the current counter has passed the new target, so no branch ever
updates the POTGO-initialized latch.

Cargo exits 101 with:

```text
assertion `left == right` failed: input changes must preserve partial pot charge
  left: [0, 32, 32, 32]
 right: [0, 0, 0, 0]
```

The temporary test is removed afterward; production is unchanged. The public
API does not represent a grounded/floating input separately, so those reference
cases are not claimed as public-core tests.

## Sources and remaining scope

Avery Lee, *Altirra Hardware Reference Manual*, printed pp. 129–132,
[original distribution](https://www.virtualdub.org/altirra.html), and original
POKEY source. The manual and implementation share an author; this is not new
hardware measurement. The primary note is
`reference/by-system/atari-8bit/pokey-pot-input-change.md` in the umbrella.
Original chip/wrap helper identities are pinned. The original setter and
assembled capture identities are recorded in `summary.json`. Original source
is extracted only in scratch; the complete observations are gzip text.

Fixed integer charge/discharge is the reference's approximation. Combined
SKCTL/input changes, physical CPU write phase and calibrated controller
response remain unqualified. The evidence establishes that target counters
alone cannot retain the required input history; it does not authorise a new
snapshot schema or architectural change.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-pot-input-change/capture.py \
  ../../emulators/atari/altirra /private/tmp/pokey-pot-input-change-reproduction
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-pot-input-change -v
ruff check plans/2026-10-11-pokey-pot-input-change/*.py
ruff format --check plans/2026-10-11-pokey-pot-input-change/*.py
rustfmt --edition 2024 --check plans/2026-10-11-pokey-pot-input-change/probe.rs
```

Copy `probe.rs` to `crates/atari-pokey/tests/pot_input_change_probe.rs` in an
isolated source worktree, run
`cargo test -p atari-pokey --test pot_input_change_probe -- --nocapture`, and
remove only that temporary file afterward. Expected result: Cargo exit 101.
