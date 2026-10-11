# Resolve MARIA's remaining physical phase branches

Continue the approved engineering-frontier MARIA correction. The event-input
experiment explains the bypassed selector's short pulse widths, but does not
establish the physical clock-phase alignment needed by production scheduling.

1. Reuse the placed-layout probe in `2026-10-11-maria-phase-handoff/` to trace
   clock conductors through remaining cells accepted by the current extractor.
   Start with control, address-inverter, luminance and burst cells. Retain
   explicit errors for unsupported structures; matching labels cannot join
   conductors.
2. Establish which remaining branches physically reach clock-generator
   outputs and the interrupt latch's phase gates. Record both connected and
   unresolved paths. Inspect missing-route geometry before extending any
   extraction rule.
3. Compare the recovered input/output-bank order with the reference's clock
   and selector update stages. Use independently checked transfer equations
   for any conditional phase experiment; do not promote an assumed phase
   mapping to a hardware fact because its pulse widths look plausible.
4. Add reproducible positive/negative routing or timing checks for any new
   conclusion. Preserve primary evidence first, then derived summaries here.
   Source PR 1704 remains draft until its timing and guest gates are met.

No new dependency, emulator API or snapshot change. Original geometry and
complete extracted networks stay outside Git. The current extractor accepts
96 control, 57 address-inverter, 60 luminance, 24 second-luminance and 22 burst
candidate devices. The colour-phase cell still rejects a nonordinary gate
region and is not silently included.

## Results

The placed geometry now connects clock-generator `n12` to `RSYNC_LY/ph1`
and the raster/interrupt output banks. It connects `n13` to `RSYNC_LY/ph2`
and their input banks. The two conductors remain distinct. Omitting the five
added cells makes both new acceptance checks fail `missing physical port
route`. This needs no new extraction rule.

The scope contains 17,952 conductor rectangles, 2,119 ordinary candidate
devices, two explicitly unmodelled clock structures and 60 unexpanded
top-level instances. Three components still carry `TOP/ph1`, including an
annotation attached to the physical phase-2 conductor and a separate
control-cell branch. Labels alone remain insufficient to bind a phase.

The NMI output's fan-in cone contains 13 devices. Boundary inputs stop the
walk at supply, phase, disable, set and reset ports; gate fan-out is excluded.
The switch/retention model captures set/reset in phase 2 and holds through
phase 1. Its asynchronous disable is inactive after initialisation.

Combining this cone with the recovered 32-row controller truth table gives
the following conditional observations:

| Assumed edge period | HALT release positions | Cases, DLI clear/set | Pulses | Width in half-phase steps | Assertion delay from internal release |
|---|---:|---:|---:|---:|---:|
| 4 MARIA cycles | 8 | 16 | 8 | 8 | 10–17 |
| 6 MARIA cycles | 12 | 24 | 12 | 12 | 14–25 |

All 40 cases have the expected pulse inventory and idle final output. All
20 assertions and releases occur in phase 2 after internal HALT release.
Forcing the two latch sampling gates always open fails `interrupt edge
outside phase 2`. Five synthetic tests reject missing pulses, short widths,
wrong phases, pre-HALT pulses, ambiguous boundaries and unmodelled sources.
The 13 inherited routing/pad tests also pass. Regenerating the sweep produces
the retained observations exactly.

## Limits and next gate

This assumes alternating nonoverlapping phases and a one-MARIA-step edge at
a constant period. The delays above are **abstract phase steps**, not an
assignment to emulator native ticks. The sweep deliberately imposes internal
HALT release at every possible position; the real HALT generator and its
separately sampled output pad restrict those positions.

The relative order is now backed by conductors: controller input capture in
phase 2, output update in phase 1, interrupt-latch capture in phase 2. The
previous FPGA observer kept the reference's update order, so its successful
pulse widths alone do not validate this physical pipeline. Next, qualify the
HALT generator/pad handoff and the edge generator together, including live
fast/slow transitions, before assigning assertion delay in production.
Unknown analogue clock behaviour and production revision remain explicit.
[Source PR 1704](https://github.com/emu198x/emu198x/pull/1704) stays draft.

## Reproduction

Primary evidence is recorded first in the umbrella's
`reference/by-system/atari-7800/gcc-maria-layout-evidence.md`. The input is the
pinned [GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip),
SHA-256 `849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48`.
The adjacent `summary.json` retains source hashes, selected port relationships,
all 40 observations and the three live negative outcomes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-physical-phase-branches/probe_phases.py \
  /path/to/layout-artifacts.zip /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-physical-phase-branches -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-phase-handoff -v
```

Keep generated `local-output/network.json` outside Git. Only the bounded
summary is retained here. No emulator code or snapshot schema changes in
this research slice.
