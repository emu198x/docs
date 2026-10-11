# Test the MARIA selector's edge input

Continue the approved engineering-frontier timing correction. The recovered
raster controller produces a one-step pulse, while the reference supplies a
CPU half-cycle level to its bypassed interrupt selector. Test whether that
input difference explains the selector observer's short pulses.

1. In `2026-10-11-maria-selector-edge-causality/probe_edge.py`, qualify the
   reference selector equations against all 32 recovered interrupt-controller
   truth rows. Establish the input polarity instead of assuming a high pulse
   on the named `PCLKEDGE` port is equivalent to the physical layout signal.
2. Extend our existing selector bench with independent observer states. One
   observer must reproduce the reference's current selector exactly. Two more
   use a one-MARIA-step event at either CPU-clock transition. They observe the
   live HALT/DLI inputs but cannot alter reference DMA, clocks, or NMI output.
   Assert baseline equivalence and nonzero sample/event inventories.
3. Run empty and populated direct/indirect lists, zone heights 1/2/3/16,
   unflagged/all/single flags, fast/slow accesses and PAL/NTSC. Compare pulse
   inventories, zone handoff, delay and width. Inject broken observer/pulse
   controls to prove the acceptance checks fail.
4. Preserve source hashes, summaries, evidence and remaining phase limits.
   Keep original RTL read-only. No production NMI change follows from an
   observer-only experiment without the agreed timing acceptance evidence.

Reuse the qualified reference and existing own bench; no new dependencies.
Reference equation extraction and generated simulator inputs stay in the local
research workspace. Public files contain our independent controller equations,
bench instrumentation, results and reproduction instructions.

## Polarity qualification

All **32** recovered interrupt-controller truth rows match the pinned reference
selector equations when the edge condition is inverted. The reference's
sampled HALT, DLI and feedback conditions are already inverted; its named
`PCLKEDGE` input feeds the remaining condition directly. Assuming that port is
the layout's positive edge signal disagrees in **18** rows.

The independent observer implements the recovered controller equations, with
the reference's existing input/output update timing. Its original-input mode
must match both the reference selector's decoded outputs and the earlier NMI
observer on every measured cycle. Two more instances use one-step events at
opposite transitions of the reference level. No observer drives a reference
input or changes its DMA/clock/NMI path.

## Full comparison

The matrix covers **816 cases**: 17 empty/populated object configurations,
four zone heights, three flag patterns, two CPU access speeds and two regions.
Each observer produces the expected **3,400 complete pulses**, with correct
single-zone handoff and none during HALT. The original reference's setup,
HALT, active NMI, selector and result traces are identical in all 816 cases.

| Observer input | Fast width | Slow width | Delay after HALT release | Clock-state mismatches |
|---|---:|---:|---:|---:|
| Original half-cycle level, observer 0 | 2 or 6 | 2 or 6 | 3–6 | 3,400, baseline control |
| Event at reference `PCLKEDGE` falling transition, observer 1 | 8 | 12 | 9, 11 or 12 | 0 |
| Event at reference `PCLKEDGE` rising transition, observer 2 | 8 | 10 or 12 | 8, 13, 15 or 17 | 644 |

Widths and delays are native oscillator ticks. PAL and NTSC give the same
results. Each region/speed group contains 204 cases and 850 pulses per observer.

The cycle check requires one observed CPU phase-1 event between assertion and
release **and** identical `clock_div`, `pclk_toggle` and `pclk` state at both
ends. Counting one edge alone is insufficient: a shorter pulse can straddle
an edge. Observer 1 passes this check for all 3,400 pulses. Observer 2 fails it
in 112 slow-access cases, retaining the explicit failure:

```text
NMI release has different CPU phase
```

The four-case smoke run did not expose the ten-tick transition pulses. The
full matrix did. The initial full sweep counted CPU events; the final full
sweep added the clock-state check. `comparison.json` lists every failed case
and its mismatch count. The collector records hypothesis failures so the
matrix can finish; strict parsing still raises on them. Tests verify both
strict failure and preservation in research output. Baseline observer 0 is
a control, not a candidate claimed to pass the cycle criterion.

## What this establishes

The half-cycle-versus-event discrepancy is a demonstrated cause of the
bypassed selector observer's short pulses. The observation no longer rests
only on comparing separate controller waveforms. The reference's active NMI
output bypasses this selector and remains unchanged throughout the experiment.

This does **not** settle the physical edge choice or native assertion delay.
The independent observers use the reference's sample/output timing and clock
handoff. Identical clock-counter state is a useful diagnostic, but changing
the divider can affect it; observer 2's failed check does not alone prove its
edge is physically wrong. We cannot choose observer 1 solely because it fits
the documented pulse width. The remaining layout phase branches and live
clock handoff still require qualification before production changes.

## Verification and reproduction

Eight synthetic tests cover missing observations, suppressed flagged pulses,
baseline trace changes, wrong CPU-cycle count, one edge without the same phase,
retained failed qualification, empty equations and ambiguous instrumentation.
Ruff lint and formatting pass. Two live negatives fail their intended gates:

- Sustaining the candidate event as a level: `candidate edge wider than one MARIA step`.
- Suppressing a flagged observer pulse: `wrong observer pulse inventory`.

The retained summary and comparison contain source/bench hashes and the full
matrix digest. `build.log` preserves Icarus's existing constant-select
sensitivity notices; compilation and simulation completed successfully. Two
sample traces retain the slow transition and populated-list observations.
The full generated bench, binary, 816 logs and matrix remain in the local
research workspace. Original reference RTL is read-only.

```sh
# Generate the baseline if the earlier qualified capture is unavailable.
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-nmi-selector/capture_selector.py \
  /path/to/reference/rtl/Maria /path/to/qualified-rtl /path/to/baseline
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-selector-edge-causality/probe_edge.py \
  /path/to/reference/rtl/Maria /path/to/qualified-rtl /path/to/edge-output
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-selector-edge-causality/check_evidence.py \
  /path/to/edge-output /path/to/baseline
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-selector-edge-causality -v
```

The existing qualified wildcard adaptation and source hashes are required;
the probe refuses unqualified source files or a changed baseline bench.
`--smoke` runs four cases and is explicitly marked as partial coverage.
Source PR 1704 remains draft and issue #197 remains open.
