# Verify MARIA's dynamic raster clock controller

Continue the approved engineering-frontier correction. The interrupt
controller's direct switch-network replay matches the staged model, including
the disputed assertion delay. The raster controller still supplies its clock
edge through a sampled transfer model.

1. Inspect the flattened raster controller's input/output gates and physical
   feedback conductors. Qualify phase bindings from the placed network where
   local labels are insufficient; never join conductors by name alone.
2. Exercise its actual retained network, first at constant rates and then
   through slow-input transitions. Compare clock-edge, inverse-clock and
   PCLK0 signals with the preceding staged model. Keep CPU return delay and
   simultaneous input ordering explicit.
3. Investigate any mismatch before altering the combined model. Verify any
   recovered behaviour with mutations which fail the corresponding checks.
   Expand replay across the existing handoff matrix where appropriate.
4. Preserve primary observations first, then reproducible scripts and bounded
   results in `2026-10-11-maria-dynamic-raster-clock/`. Run affected tests and
   lint. Source PR 1704 remains draft until native timing and guest acceptance
   gates are met. No emulator schema or architecture change in this slice.

## Root cause and correction

The full 341-device raster network has six physically connected feedback
paths, ten phase-1 output gates and twelve phase-2 gates: eleven for controller
inputs and one for PCLK0. No new feedback joins are imposed. An otherwise
ambiguous second local phase-1 annotation connects to no active device.

Direct simulation agrees with both constant-rate clocks, but the old staged
probe fails **12 of 228 cases**: seven fast-to-slow and five slow-to-fast
transitions, all using data-first ordering. The strict check fails:

```text
dynamic raster differs from staged clock
```

For a fast-to-slow change at step 104, the direct network keeps `edge` and
`epck0f` low while the staged model raises them. The disagreement reaches
PCLK0 at step 105 and shifts later clock phases. Eighty-one observations
differ in this case.

The staged probe updated the slow latch before closing phase 2 but kept the
controller's earlier sampled input. Its still-open input gate actually admits
the new latch value. The bounded fix in
`2026-10-11-maria-halt-generator-handoff/probe_handoff.py` refreshes the sampled
state/slow value while that old phase is still open. It changes no emulator
code or snapshot format.

## Verification

After the correction, **all 228 cases match** the retained device network,
comparing three clock signals over 240 half-phase observations per case.
The experiment explicitly seeds the same sampled state zero and slow-latch
value as the staged model; this is not a reset or power-up test. Both input
orders are exercised across 56 transition positions in each direction.

The regenerated handoff matrix passes all **32,832 cases** with **16,416
complete NMI pulses**. It changes 960 case summaries, including 696 NMI edge
schedules. Every change belongs to a clock input that failed the direct
comparison before the fix. All 31,104 cases outside those affected inputs
retain their previous summaries.

Direct interrupt-controller and NMI-latch replay covers all **1,728 affected
input cases**, including DLI-clear cases whose pulse summaries might conceal
a changed clock. It matches **359,424 phase observations** and **864 pulses**.
The existing case-inventory checks reject missing, repeated or altered inputs.
Three new comparison tests reject missing, shifted or changed clock traces;
eight inherited handoff-guard tests pass. Ruff lint, format and diff checks pass.

`clock-comparison.json` retains all twelve counterexamples and before/after
digests. `handoff-comparison.json` records the changed-case audit and direct
replay. `handoff-summary.json` contains the corrected distributions and matrix
digest `6df695c0b9b82e1efb0f1b2fed6f086e8f56b1ff26c8da37c712f2f47ed37c9a`.
The former matrix digest is
`7e38e04c51a9418b3b19ef92af77fc03fdbd19bf2198a565af73dcb259b769b3`.
Complete networks and matrices stay outside Git.

## Remaining timing gate

The correction affects transition coordinates. Constant-mode assertion delays
remain 17/25 half-phase steps from internal HALT release and 16–17/24–25 from
the sampled pad. The specification disagreement remains after checking both
controllers dynamically. There are now 1,272 input-order pairs with changed
handoff edges, replacing the earlier count of 672.

The stages are still driven by assumed alternating, nonoverlapping phases;
the electrical behaviour of the clock generator and actual CPU return delay
have not been qualified. The layout's production revision is also unknown.
[Source PR 1704](https://github.com/emu198x/emu198x/pull/1704) remains draft;
issue 197 stays open. The next evidence must address those physical inputs
or a revision-matched timing observation.

## Reproduction

The source is the pinned
[GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip).
Source hashes are retained in the comparison files. Primary observations are
recorded in the umbrella's
`reference/by-system/atari-7800/gcc-maria-layout-evidence.md`.

The pre-fix staged helper comes from docs commit
`f3d40bf6a46b1bc2022fbb4c8a35c582d24d9223`; its exact file hash is in
`clock-comparison.json`. Running the clock probe against that helper with
`--require-match` produces the twelve recorded failures. The current helper
passes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-dynamic-raster-clock/probe_raster.py \
  /path/to/layout-artifacts.zip /path/to/local-output/clocks.json --require-match
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-halt-generator-handoff/probe_handoff.py \
  /path/to/layout-artifacts.zip /path/to/local-output/handoff-matrix.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-halt-generator-handoff/summarize.py \
  /path/to/local-output/handoff-matrix.json /path/to/local-output/handoff-summary.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-dynamic-raster-clock/check_handoff.py \
  /path/to/layout-artifacts.zip /path/to/prior/handoff-matrix.json \
  /path/to/local-output/handoff-matrix.json \
  plans/2026-10-11-maria-dynamic-raster-clock/clock-comparison.json \
  /path/to/local-output/handoff-comparison.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-dynamic-raster-clock -v
```
