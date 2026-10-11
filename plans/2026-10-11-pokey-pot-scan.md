# POKEY pot scan qualification

Engineering-frontier investigation of issue 191. Production remains unchanged
until its required representation is established. The separately proposed
counter/audio stages do not authorise a new capacitor model.

## Plan

1. Extract unchanged Altirra StartPotScan, UpdatePots, base-clock methods and
   POT/ALLPOT read cases into a scratch-only C++ harness. Pin the source hash.
2. Capture grounded inputs in all four SKCTL combinations (slow/fast and
   initialization/running), at several retained /114 phases. Check complete
   per-cycle traces, live counter transitions and final values; reject missing
   cases and mutations of the clock selection, read transition and terminal count.
3. Execute public Emu198x probes for fast completion, slow live reads and
   initialization suspension. Preserve failures with normal completion controls.
4. Record evidence in the primary reference layer and this plan. Update issue
   191 with the verified scope and the remaining charge/restart questions.

Files: this plan and its adjacent capture.py, scaffold.cpp, driver.cpp,
test_capture.py, probe.rs, baseline.txt, summary.json and chip-red.log. Primary
observations: reference/by-system/atari-8bit/pokey-pot-scan.md in the umbrella.
No production change or issue closure is claimed by this investigation.

## Results

The unchanged reference passes all 16 cases: four SKCTL combinations and four
retained /114 phases. Every clock through 26,002 is checked, for 416,048 clock
observations and 3,328,384 POT reads. Fast mode finishes at clock 231 with a
terminal count of 229; slow initialization mode remains frozen. Three broken
reference mutations fail, and eight capture integrity tests pass.

The public Emu198x probe fails 48 of 64 cases. All 16 ordinary completed scans
pass. Fast completion, live slow reads and initialization-mode reads each fail
16 cases. Cargo exits 101 with:

```text
assertion `left == right` failed: pot scans must expose live counts and honour their clock source
  left: [16, 16, 16, 0]
 right: [0, 0, 0, 0]
```

The probe is removed from the source worktree after execution; its complete
source and output are retained here. No production files change.

## Mechanism and next boundary

The current scanner always uses its own /114 clock and reads a final-only
latch that POTGO initializes to 228. It never exposes the live counter and
ignores fast mode and slow-clock initialization suspension. It also stops the
master scan when all targets finish. This is more than a missing divider.

Before designing a fix, qualify retained charge, threshold crossings, repeated
POTGO and mid-scan clock changes. Those interactions require information that
the existing arrays do not retain. The pending counter/audio stage design does
not implicitly approve a capacitor model or further snapshot changes.

Source: Avery Lee, *Altirra Hardware Reference Manual*, printed pp. 129–132,
[original distribution](https://www.virtualdub.org/altirra.html), and its original
POKEY implementation. Both have the same author. This is implementation-backed
validation, not new physical hardware measurement. The selected /114 origin is
explicit; physical SKCTL write phase is not qualified. Public targets assume
fresh discharged high-resistance inputs; they do not calibrate analogue charge.
Hashes, observations and limits are recorded in `summary.json` and in the
umbrella primary note `reference/by-system/atari-8bit/pokey-pot-scan.md`.

## Reproduce

From this repository (substitute fresh scratch paths):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-pot-scan/capture.py \
  ../../emulators/atari/altirra /private/tmp/pokey-pot-scan-reproduction
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-pot-scan -v
ruff check plans/2026-10-11-pokey-pot-scan/*.py
ruff format --check plans/2026-10-11-pokey-pot-scan/*.py
rustfmt --edition 2024 --check plans/2026-10-11-pokey-pot-scan/probe.rs
```

For the expected red public probe, copy `probe.rs` to
`crates/atari-pokey/tests/pot_scan_probe.rs` in an isolated source worktree and
run `cargo test -p atari-pokey --test pot_scan_probe -- --nocapture`. Remove only
that temporary probe afterward. `baseline.txt.gz` contains observations, not
reference source; extracted implementation remains in scratch only.
