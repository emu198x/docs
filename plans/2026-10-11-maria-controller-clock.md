# Relate the MARIA interrupt controller to the CPU clock

Continue #197's approved timing investigation from the recovered interrupt
controller. The preceding turn produced verified circuit evidence; the exact
native-clock assertion phase remains open.

1. Add `2026-10-11-maria-controller-clock/flatten_layout.py` for the bounded
   GDSII hierarchy needed by `RCPLA_RCPLA`. Use exact orthogonal transforms,
   reflection before rotation, and explicit rectangular path handling. Reject
   unsupported transforms or geometry. Test nested transforms and paths against
   independent geometric expectations before interpreting the flattened cell.
2. Extract the raster-control controller and connect its ports through the
   top-level layout. Identify `pckedge` and its relationship to `pck0`, slow
   accesses and the MARIA phases. Reuse the qualified contact/network probe;
   do not silently accept devices outside its supported model.
3. Compare the resulting controller sequence with the interrupt controller
   and reference clocks. Add a phase probe with negative controls if the
   circuit supports it. Keep primary layout, inferred circuit and FPGA
   behaviour distinct; native timing requires the physical phase mapping.
4. Record new evidence in the primary notes and this plan. Only change
   production after the timing gate is satisfied. Source PR 1704 remains draft.

Calma's 1984 *GDSII Stream Format*, printed pp. 11–13, defines STRANS,
ANGLE and PATHTYPE. The source and hashes are those in
`2026-10-11-maria-layout-evidence.md`. No source geometry will be published.

## Recovered controller and clock output

`RCPLA_RCPLA` expands to 1,631 cell instances from 75 distinct named cells,
producing 7,565 rectangular/text elements. The candidate network contains 341
transistors: 71 marked by layer 2, 237 by layer 3 and 33 unmarked. All 71
layer-2 devices have the self-gated supply connection required by the proposed
depletion-load interpretation.

The hierarchy includes reflected and rotated references, concave Manhattan
boundaries and collinear zero-area spurs. The probe composes transforms exactly,
splits concave boundaries into horizontal rectangles, and verifies filled area
before/after removing collinear vertices. It rejects proper crossings, missing
cells, recursive references, unsupported magnification and nonorthogonal paths.
The source bytes remain unchanged.

Top-level routing connects the controller's out10 to `pckedge`, including the
interrupt controller's input, and out9 to `epck0f`. The two pass banks connect
to the same `ph2` and `ph1` nets as the interrupt controller. The `pck0` output
and `slow` input also connect through the intervening raster-control wiring.
The full routed groups are retained in `layout-summary.json`.

The own combinational solver holds sampled inputs independently while opening
the output bank. This breaks the physical feedback at its actual sample gates
for transfer-function inspection; it does not force both banks open and let
the controller race. It settles all **1,024** combinations of six feedback bits
and four external inputs, with the remaining input tied high. A digest of the
complete table is retained for reproduction.

With raster reset inactive, normal line-buffer controls and a constant inverted
slow-latch input, the controller produces:

| Condition | `pckedge` period | `pckedge` high | `epck0f` high |
|---|---:|---:|---:|
| Fast | 4 MARIA cycles | 1 MARIA cycle | 2 MARIA cycles |
| Slow | 6 MARIA cycles | 1 MARIA cycle | 3 MARIA cycles |

Each run covers 48 controller steps, giving 12 fast pulses or 8 slow pulses.
The signal is a pulse at the start of the inverse-clock high interval. These
periods correspond to the documented fast/slow CPU clock divisions. Switching
between the modes is **not** covered by these constant-input runs.

## Reference input differs

`capture_reference_clock.py` adds an observer to our existing qualified bench,
without changing the reference RTL. It samples the interrupt controller's
`PCLKEDGE` input on every MARIA cycle during a stable vertical-blank interval.
All four region/speed rows contain 256 observations; fast rows contain 63
complete periods and slow rows 42.

| Reference mode | Period | High interval |
|---|---:|---:|
| Fast, NTSC or PAL | 4 MARIA cycles | 2 MARIA cycles |
| Slow, NTSC or PAL | 6 MARIA cycles | 3 MARIA cycles |

The reference feeds `~pclk_toggle` into that port. Its measured level lasts
half the CPU period, whereas the recovered controller emits a one-step pulse.
This is evidence of a relevant input mismatch. It is a possible explanation
for the old selector observer's short NMI pulses; it is not yet a demonstrated
causal correction. The active reference NMI output bypasses that selector, so
changing this observer input alone would not validate the active output.

## Verification and limits

Eleven synthetic tests pass: eight hierarchy/geometry cases and three transfer
solver cases. They include reflect-before-rotate, nested transforms, concave
boundaries, zero-area spurs, rejected crossings, sampled inverter behaviour,
missing sample gates and conflicting settled drivers. Ruff lint/format checks
pass. Both probes use the pinned layout/reference sources.

Removing the recovered edge output's pullup fails `wrong 4-cycle edge period`.
Suppressing the reference observations fails `missing clock-input observations`.
The negative bench initially omitted `+width=0` for its empty display list and
failed `wrong graphics count`; its setup was corrected before using it as an
observation control. The final negative simulation itself passes and only the
missing-observation acceptance check fails.

The network solver recovers settled Boolean transfers under the existing
layer-role hypothesis. It does not model charge sharing, analogue propagation,
non-overlap time or physical CPU pin timing. The constant slow-latch input is
not a model of its live phase-sensitive sampling. Native-clock assertion delay,
HALT release and the transition back to slow CPU accesses still require a
phase model and comparison with the measured reference traces. Production chip
revision remains unqualified. Source PR 1704 stays draft.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-controller-clock -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-controller-clock/probe_controller_clock.py \
  /path/to/layout-artifacts.zip /path/to/layout-summary.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-controller-clock/capture_reference_clock.py \
  /path/to/reference/rtl/maria /path/to/qualified-rtl /path/to/output
```

The probes reuse installed NumPy/SciPy and Icarus Verilog; they add no emulator
or project dependency. Original geometry, flattened geometry and complete
extracted networks stay outside this repo.
