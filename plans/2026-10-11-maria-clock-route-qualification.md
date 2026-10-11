# Qualify the remaining MARIA clock routes

Continue the approved engineering-frontier MARIA timing correction. The prior
pad investigation established conditional HALT retention and the NMI pad route,
but left the internal HALT handoff and global phase mapping incomplete.

1. Extend the bounded extractor in
   `2026-10-11-maria-interrupt-circuit/layout_network.py` to retain explicitly
   requested single-terminal gate-over-diffusion structures separately from
   ordinary transistors. Default extraction must still reject them. No digital
   solver may silently accept a network containing unmodelled structures.
   Test both rejection and diagnostic retention with synthetic geometry.
2. Extend `2026-10-11-maria-phase-handoff/connect_layout.py` to place those
   structures without joining their gate and diffusion conductors. Opt in only
   for the identified clock-generator cell. Add the already-supported raster
   logic cell. Verify which missing phase/HALT routes this actually resolves.
3. Inspect the new routes against the original geometry and reference clock
   behaviour. Preserve unsupported decoder layers and electrical behaviours
   as explicit boundaries. Do not infer timing from equal names or from a
   routing-only trace. A conditional phase probe is useful only once its
   drivers and inputs are qualified.
4. Record reproducible summaries, negative controls and remaining limits here
   and in the primary evidence note. Run affected extractor/solver tests,
   lint and formatting. Keep source PR 1704 draft until native timing and guest
   acceptance pass; this research extension changes no emulator snapshot.

The pinned clock-generator cell has 116 gate regions. Two layer-2 regions
have a single distinct diffusion terminal each; the other 114 pass the
existing two-terminal geometry rule. Their electrical role is not established
by that geometry. The raster logic cell extracts 137 ordinary candidate
devices. Adding it alone does not connect the previously separated HALT nets.

## HALT route resolved

The missing path crosses two wiring-only cells: `LM_LY_` and `GBFM2_LY`.
Their 64 and 32 extracted nets contain no transistors. Including their placed
conductors joins `RSYNC_LY/halt`, the interrupt controller's HALT input,
line-raster wiring and the input of `PADLAY_HPAD06I__`. Omitting those two
cells makes the explicit acceptance check fail `missing physical port route`.

This establishes the connection from the internal HALT generator to the
clock-gated output pad identified in the previous investigation. It does not
remove the pad's sampling gate or turn its internal transition into a CPU-pin
transition at the same instant.

## Clock routes and remaining boundary

The expanded scope covers **16,962 rectangles, 1,860 ordinary candidate
transistors and two unmodelled gate regions**. Sixty-five top-level instances
remain unexpanded.

The two unusual clock-generator regions are retained as
`single_terminal_gate_region`: `n10` over the `n13` diffusion conductor and
`n5` over `n12`, both marked by layer 2. Default extraction still rejects
them. Diagnostic retention neither joins gate to diffusion nor assigns a
transistor/capacitor model. All three digital solvers reject the resulting
network with an explicit `unmodelled structures` error.

The placed trace connects `n12` to the raster and interrupt controllers'
output-bank phase, and `n13` to their input-bank phase. Those routes now have
explicit acceptance checks. The scope still has four components labelled
`TOP/ph1` and three labelled `TOP/ph2`, including the previously separate
interrupt-latch branches. Equal names do not establish their electrical or
phase relationship.

The unknown decoder layer 10 remains an extraction error. A preliminary
trace of only its poly/metal/cut rectangles joined one further branch, but
did not complete the phase mapping or HALT path; it is not part of the
qualified scope. The HALT result above needs no decoder-layer exception.

Native assertion phase, analogue behaviour, production revision and live
fast/slow transitions remain unqualified. Source PR 1704 stays draft. The next
timing experiment can also test whether replacing the reference observer's
half-cycle input level with the recovered one-step edge pulse explains its
short NMI pulses; that causal comparison is still outstanding.

## Verification

The initial new tests failed with `unexpected keyword argument
'retain_single_terminal'` and missing solver rejection. After the bounded
extension, **32 synthetic tests pass**: 8 extraction/logic, 11 controller/
geometry and 13 routing/pad tests. Ruff lint and formatting pass.
The original interrupt, raster-controller and pad probes also pass again;
their complete JSON evidence is unchanged. `prior-evidence.json` retains the
canonical content hashes checked against the previous results.

The full placed probe passes all five route checks: NMI latch to pad, `pck2f`
to HALT sampling gate, both clock-generator-to-controller phases, and internal
HALT to its pad. Its negative controls confirm:

- Omitting the two wiring cells breaks the physical HALT route.
- The pad, transfer and PLA solvers all reject the actual expanded network
  because it contains unmodelled clock structures.
- Synthetic single-terminal geometry is rejected by default, retained only
  when explicitly requested, and never shorts gate to diffusion.

The probe uses the same pinned
[GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
and candidate layer deck as the preceding investigations. No dependency or
emulator schema changes are introduced. The retained summary contains selected
port relationships and hashes; original masks and the complete generated
network remain outside Git.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-phase-handoff/qualify_clock_routes.py \
  /path/to/layout-artifacts.zip /path/to/local-output
```

`local-output/network.json` is the complete local research network and must
stay out of this public repo. `local-output/summary.json` contains the bounded
observations and negative-control outcomes. The adjacent `tests.log` records
the affected synthetic suites and the prior hardware probes rerun against the
extended extractor.
