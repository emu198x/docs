# POKEY simultaneous clock and input transitions

Engineering-frontier follow-up to the separate clock/input captures.
No production architecture or save schema changes are included.

## Plan

1. Join the unchanged SKCTL case and input setter already qualified separately.
   Keep unrelated subsystem callbacks isolated and the input workaround off.
2. Exercise both same-timestamp call orders for rate change, grounding and
   floating, in all old/new clock-mode pairs, with empty and charged inputs.
3. Check the complete declared inventory against the prior independent clock
   oracle and closed-form charge intervals. Negative controls must reject lost
   delivery, discarded charge and erased input/write ordering.
4. Record the combined state requirements and physical-phase limitations in
   the primary reference, this plan and issue 191 before designing the correction.

Files: adjacent capture.py, driver.cpp, test_capture.py, baseline.txt.gz and
summary.json; umbrella reference/by-system/atari-8bit/pokey-pot-combined-input.md.
All original source is extracted only in scratch.

## Results

All **768 cases** pass, comprising all old/new SKCTL 0/3/4/7 pairings, two
retained phases, writes at 64/128 clocks, three input actions, two starting
charge states and both call orders. The selected input rotates evenly across
0–7; input index is not independently crossed with every combination. There
are 192 unchanged-mode controls.

Every clock advances the reference. The complete declared inventory of
**5,376 checkpoints** covers the instant before/after both calls, +1/+2/+3,
+114 and +27,000 clocks. It checks selected/untouched POT, ALLPOT, master count,
scan activity and charge; all seven untouched inputs agree. The checker
composes the preceding clock oracle with closed-form charge intervals.

Charge survives a rate change and floating, but grounding clears it and
rearms the input during an active scan. The counter and master lifetime retain
the independently qualified clock behaviour. Same-timestamp call order can
change charge because the reference eagerly processes a two-clock interval
when handling SKCTL; the rate in force at that call determines its contribution.

Three deliberately broken variants fail: dropping that processing interval,
discarding charge, and forcing all cases to clock-first order. Eight capture
integrity tests pass. C++ compiles with warnings denied; Ruff and diff checks
pass. No new public-core probe is required to establish this gate: earlier
probes already reproduce missing clock selection and retained input history.

## Required distinctions and limits

The scanner correction needs programmed/delivered clock control, a master
count and shared phase, per-input retained charge and threshold/latch state,
and a scan lifetime independent of ALLPOT. Those distinctions are now backed
by the separate and combined reference captures.

The reference's eager charge processing is not physical pin timing. Production
must advance only from clock ticks, with no time advancement in register or
input accessors. Counter coordinates and physical delivery must be mapped
before choosing exact stage constants. Calibrated capacitor response also
remains outside these fixed-rate captures. The optional immediate-update
workaround stays disabled.

The SKCTL case and input setter are unchanged. Unrelated audio/keyboard/serial
callbacks use the isolation scaffold documented in the clock-switch capture;
this is not whole-chip integration. Original sources are pinned and extracted
only in scratch. Original source: Avery Lee's *Altirra Hardware Reference
Manual*, printed pp. 129–132, and POKEY implementation,
[distribution](https://www.virtualdub.org/altirra.html). They share an author.
Primary observations are in the umbrella note
`reference/by-system/atari-8bit/pokey-pot-combined-input.md`.

This evidence does not approve additional saved state. The next design must
preserve these distinctions and all previous failing probes, while identifying
which physical-phase questions remain implementation gates.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plans/2026-10-11-pokey-pot-combined-input/capture.py \
  ../../emulators/atari/altirra /private/tmp/pokey-pot-combined-input-reproduction
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-pot-combined-input -v
ruff check plans/2026-10-11-pokey-pot-combined-input/*.py
ruff format --check plans/2026-10-11-pokey-pot-combined-input/*.py
```
