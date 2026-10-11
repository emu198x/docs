# Qualify MARIA's internal HALT generator and output handoff

Continue the approved engineering-frontier timing correction. Physical phase
routes are established, but the previous NMI sweep imposed internal HALT
release independently of its generator and sampled output pad.

1. In the existing pinned layout, isolate the HALT fan-in cone at explicit
   request, reset, edge and phase boundaries. Reuse the bounded extractor and
   switch/retention solver; reject unsupported or ambiguous boundaries.
2. Exercise phase-sensitive capture and release against independently stated
   signal relationships. Trace the HALT pad's `pck2f` control back toward the
   CPU-clock generator. Do not bind separate phase labels by name.
3. Combine only qualified stages with the interrupt controller and latch.
   Sweep release and clock-mode transitions where their inputs are qualified;
   keep other inputs explicit conditions. Require nonzero pulse inventories
   and negative controls which break the relevant timing relationship.
4. Preserve primary observations before this derived record, run affected
   tests and lint, and commit the bounded evidence. Source PR 1704 stays draft
   until native-clock assertion and guest acceptance gates are met.

Exact files: new probes/tests/evidence in the adjacent
`2026-10-11-maria-halt-generator-handoff/` folder; reuse
`2026-10-11-maria-physical-phase-branches/probe_phases.py`,
`2026-10-11-maria-phase-handoff/probe_pads.py` and `connect_layout.py`.
Primary observations belong in the umbrella's
`reference/by-system/atari-7800/gcc-maria-layout-evidence.md`.
No emulator schema or architectural change in this research step.

## Results

The [GCC1702B specification](https://7800.8bitdev.org/images/5/58/Gcc1702b_maria_specs.pdf),
printed p. 7, identifies PCLK2 as a CPU phase-2 input and PCLK0 as MARIA's
phase-0 output to the processor. The scan was visually checked. The placed
layout supplies a four-device inverter between `pck2` and the HALT pad's
`pck2f` sampling control; this separate CPU return signal is an explicit
boundary of the experiment.

The newly exercised stages are:

| Stage | Extracted devices | Qualified behaviour |
|---|---:|---|
| HALT generator | 32 | Start/end-of-vblank requests and reset sample in phase 2; the final HALT latch opens in phase 1 on the held edge pulse. |
| Raster clock output | 10 | Slow input is retained while `epck0f` is high; phase 2 captures `epck0f` and PCLK0 outputs its inverse. |
| HALT pad clock inverter | 4 | `pck2f` follows inverted `pck2`; its conductor reaches the pad gate. |

The combined probe also uses the previously recovered 32-row interrupt
controller, 13-device NMI latch, 29-device HALT pad and the raster controller's
128 normal-line transfer rows. Both original request sources are exercised.

## Conditional sweep

All **32,832 cases** pass the stated handoff checks, producing **16,416 NMI
pulses**. The matrix covers two constant clock modes and both rate transitions;
twelve reset positions; 56 mode-change positions for each transition; DLI
clear/set; both request sources; two slow-input orderings; and assumed CPU
return delays of zero, one or two half-phase steps.

Each run first proves an idle interval after reset. It must then contain one
HALT assertion/release and exactly the requested NMI inventory, return to idle,
and keep internal HALT edges in phase 1, NMI edges in phase 2 and pad HALT
edges outside CPU phase 2. Every interrupt pulse spans exactly one PCLK0
falling edge.

| Clock condition | Pulse widths | Delay from internal HALT release | Delay from HALT pad release |
|---|---|---|---|
| Constant fast | 8 | 17 | 16–17 |
| Constant slow | 12 | 25 | 24–25 |
| Fast to slow | 8, 10, 12 | 17, 19, 21, 23, 25 | 16–25 |
| Slow to fast | 8, 10, 12 | 17, 19, 21, 23, 25 | 16–25 |

All numbers are **abstract half-phase steps**, not qualified emulator ticks.
The ten-step pulse combines clock intervals during a rate transition. It is
compatible with the recovered circuit under these assumptions, so the earlier
FPGA observer's intermediate width alone cannot reject that timing candidate.

Slow input changes coincident with its derived gate closing need an explicit
ordering. The first stage check failed `slow latch sampling mismatch` because
the iterative switch model could capture new data before the gate inverter
settled. The preliminary sweep was stopped. The final experiment runs both
data-first and control-first order; 672 matched pairs have different output
edges. Neither order is promoted to a measured setup/hold relationship.

The constant-mode assertion delay remains roughly two CPU periods from HALT
release under both orderings. That conflicts with a literal reading of the
specification's p. 14 description of one cycle after release. We have narrowed
the disagreement, not settled it. Production revision, analogue propagation,
native-phase alignment and the actual processor return delay remain open.
[Source PR 1704](https://github.com/emu198x/emu198x/pull/1704) remains draft and
issue 197 stays open. The next useful evidence is an independent check of the
dynamic controller-bank schedule or a matching revision's test waveform.

## Verification and reproduction

Thirty-two clock-stage observations cover both initial levels and held/open
gates. Six observations verify the pad-clock inverter. Four live gate
mutations fail with these exact errors:

- `HALT changes outside phase 1`
- `HALT pad changes during CPU phase 2`
- `slow latch sampling mismatch`
- `PCLK0 sampling mismatch`

Removing the inverter pulldown also breaks inversion after a verified high
starting level. Its negative deliberately charges the retained node first;
starting low concealed the missing pulldown. Eight synthetic tests reject
missing pulses, missing clocks, wrong phases, failed warm-up and incomplete
or duplicate matrices. Ruff lint and formatting pass.

The large sweep caches complete internal solver states and fixed inputs.
Forty representative full traces are checked against uncached execution,
including both request sources, both input orderings and both rate transitions.
The summary verifies the exact Cartesian case inventory, pulse counts and
edge-derived measurements, and retains the full matrix's canonical digest.
Original layout geometry and the full generated matrix stay outside Git.

The input is the same pinned
[GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
used by the preceding probes. Its hash and member hash are in `summary.json`.
The primary record is the umbrella's
`reference/by-system/atari-7800/gcc-maria-layout-evidence.md`.

```sh
# Reuse the placed network generated by the preceding phase-branch probe.
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-halt-generator-handoff/qualify_stages.py \
  /path/to/layout-artifacts.zip /path/to/physical-phase-branches/network.json \
  /path/to/local-output/stages.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-halt-generator-handoff/probe_handoff.py \
  /path/to/layout-artifacts.zip /path/to/local-output/matrix.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-halt-generator-handoff/summarize.py \
  /path/to/local-output/matrix.json /path/to/local-output/summary.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-halt-generator-handoff -v
```

`sample-fast.json` retains a complete representative trace for the guard tests.
`stages.json` retains the stage observations and mutation outcomes; the four
full smoke traces produced by `qualify_stages.py` remain in local output.
No production code or save-state format is changed by this research slice.
