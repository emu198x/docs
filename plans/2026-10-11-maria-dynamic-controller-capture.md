# Verify the MARIA interrupt controller's dynamic capture order

Continue the approved engineering-frontier correction. The combined handoff
model produces a longer assertion delay than the specification describes.
Its static controller truth table is qualified, but the imposed sample/output
schedule needs an independent check against the actual pass gates.

1. Inspect every interrupt-controller input and output gate in the pinned
   layout. Identify which inputs are sampled and which remain live; do not
   infer identical timing from a shared PLA interface.
2. Exercise the controller as a retained switch network across nonoverlapping
   phases, initially with feedback externally held. Compare all input/state
   combinations with the existing transfer table and check capture/hold with
   deliberately changed data on the closed phase.
3. Reconnect only the physically established feedback paths. Compare dynamic
   outputs with the previous staged controller and investigate any discrepancy
   before changing the combined model. Retain negative controls and exact
   failing examples. Do not choose a schedule to fit the prose description.
4. Update primary observations first, then the derived plan and reproducible
   probes in `2026-10-11-maria-dynamic-controller-capture/`. Run relevant tests
   and checks. Source PR 1704 remains draft until the complete timing and guest
   gates are satisfied; no production schema change is proposed here.

## Direct capture check

The 89-device controller contains five phase-2 input pass gates and five
phase-1 output pass gates. All five inputs are sampled, including the clock
edge. The FPGA's bypassed selector does not register its edge term through
the same input path, so matching its combinational equations does not qualify
its dynamic schedule.

The new probe drives the extracted devices and their retained node values
directly. Across all **1,024 ordered pairs** of the 32 input/feedback values,
it verifies all five outputs, including capture and hold. Both banks close
between phases. Changing external inputs while their bank is closed must not
change the sampled transfer. Outputs must hold while new inputs are captured.

Two live circuit mutations fail their intended gates:

- Keeping the clock-edge input gate open: `closed input bank failed to hold`.
- Keeping all five output gates open: `output changed during input capture`.

The feedback experiment joins out1 to in5 and out2 to in4 only after checking
the physical routing. The controller then updates itself through its actual
feedback conductors. Its outputs drive the extracted NMI latch. The replay
does not substitute the static truth table for the controller's devices.

## Full handoff replay

All **32,832 handoff cases** reproduce the staged model's NMI output, with
**6,829,056 matching phase observations** and **16,416 complete pulses**.
Every regenerated baseline case must first match the retained matrix exactly.
The cases include both request sources, DLI clear/set, both clock rates and
both transitions, both slow-input orderings and three CPU return delays.
Forty representative full traces also match uncached dynamic execution.

The canonical baseline digest is
`7e38e04c51a9418b3b19ef92af77fc03fdbd19bf2198a565af73dcb259b769b3`.
The retained `summary.json` records source hashes, capture checks, negative
outcomes and complete replay counts. It distinguishes the 208 observations
per case after verified warm-up from arbitrary initial retained-node values.

Two acceptance mutations verify that the comparison itself can fail:

- Empty trace: `incomplete dynamic replay`.
- Changed idle observation: `dynamic NMI differs from staged model at step 110`.

The longer assertion delay is therefore reproduced by the extracted
interrupt-controller pass gates and feedback under the declared model. It
does not come from replacing those stages with a truth-table loop. This is
an independent check of staging using the same candidate electrical network,
not a second hardware measurement. The specification disagreement remains.
[Source PR 1704](https://github.com/emu198x/emu198x/pull/1704) stays draft and
issue 197 stays open.

The next bounded check is the raster clock controller's dynamic feedback and
sampling schedule, followed by revision-matched timing evidence if the
disagreement survives. A result that merely chooses the more convenient
assertion delay would not close the accuracy gate.

## Revision boundary

All 563 complete GDSII BGNSTR records have the identical date payload
`[-1900, 13, 7, 0, 0, 0, -1900, 13, 7, 0, 0, 0]`. Both month fields are 13;
these cannot establish a calendar date or production revision. The field
layout follows the already-pinned Calma 1984 stream-format manual. No date
is inferred from the PAL filename.

The source remains the pinned
[GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip).
Hardware observations are recorded first in the umbrella's
`reference/by-system/atari-7800/gcc-maria-layout-evidence.md`. The original
geometry and complete networks remain outside Git.

## Reproduction

The full replay uses the matrix generated by
`2026-10-11-maria-halt-generator-handoff/probe_handoff.py`. Matrix inventory,
edge measurements and nonzero pulse counts are checked before replay.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-dynamic-controller-capture/probe_capture.py \
  /path/to/layout-artifacts.zip /path/to/local-output/capture.json \
  --matrix /path/to/halt-generator-handoff/matrix.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-dynamic-controller-capture/verify_evidence.py \
  /path/to/layout-artifacts.zip /path/to/local-output/guards.json
```

Omitting `--matrix` performs the 1,024 capture transitions and four smoke
replays only; its result has no `full_replay` field. It cannot stand in for
the complete matrix. Eight inherited handoff-guard tests pass. Ruff lint,
formatting and diff checks pass. No production code or save-state format is
changed in this research slice.
