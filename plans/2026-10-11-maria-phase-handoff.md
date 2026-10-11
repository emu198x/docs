# Check MARIA's recovered phase handoff

Continue the approved #197 timing correction. The prior turn established a
one-step recovered `pckedge` versus the reference's CPU half-cycle level. It
was progress, not a completed physical NMI timing correction.

1. `connect_layout.py`: connect the three recovered controllers and intervening
   raster wiring through their actual placed geometry. Add diagnostic anchors
   to conductor rectangles, using each local extracted net to preserve buried
   and diffusion connections in the parent routing trace. Never join nets
   merely because their labels match. Verify critical phase and signal routes.
2. Identify the HALT and NMI output pads and determine whether their phase
   gates add timing relative to the internal controller signals. Expand only
   supported geometry and device types; retain unsupported structures as an
   explicit boundary.
3. If the recovered network supports it, add a bounded phase-transfer probe
   with explicit external inputs and initialisation. Exercise DMA release and
   fast/slow changes. Check state/edge counts and negative controls before
   comparing schedules. Keep conditional circuit results distinct from a
   validated production-revision timing claim.
4. Preserve evidence and limitations in primary notes and this plan. Change
   production only after the native-phase acceptance gate is satisfied.

No dependency or snapshot changes. Reuse the prior pinned archive, hierarchy
expander and candidate layer deck. Original geometry stays outside Git.

## Results

The placed trace covers **15,624 rectangles and 1,609 candidate transistors**.
It adds the HVSYNC cell, seven output pads and six LRC wiring cells to the
controller scope. Sixty-nine top-level instances remain unexpanded.
Conductor footprints connect by overlap/contact and by their separately
extracted local net identities. Matching labels never join components.

Two routes now have explicit acceptance checks:

- The interrupt latch's `RSYNC_LY/intf` reaches the input of NMI pad
  `PADLAY_HPAD06M__@35`.
- The top-level `pck2f` conductor reaches the sampling gate in HALT pad
  `PADLAY_HPAD06I__`.

The controller's internal HALT output and the HALT pad input remain separate
in this partial trace. A connection through an omitted cell is still possible;
we cannot bind the two merely because both carry `halt` labels.

The candidate digital pad model produces:

| Pad | Behaviour | Checked transitions |
|---|---|---:|
| HALT, 29 devices | Invert/capture input when `pck2f` is high; hold when low | 12 |
| NMI, 28 devices | Follow input without a sampling clock | 8 |

Both starting levels are covered. Forcing the HALT sampling gate open fails
`HALT sampling/holding mismatch`; the probe requires that specific failure.
This shows why an internal HALT transition and the CPU pin transition need
separate treatment. It does not yet put either on the native-clock timeline.

The pad probe drives each named supply branch independently. Its binary
switch/retention approximation rejects conflicting settled drivers, unresolved
floating charge sharing and unqualified depletion-load bias. Layer 8 is
excluded only where its rectangle fits wholly inside one metal rectangle;
its process role is still unknown. Other unknown layers are errors. These
are explicit extraction/model assumptions, not a qualified foundry deck.

## Phase mapping remains open

Five physical components carry `TOP/ph1`, four carry `TOP/ph2`, and two
carry `TOP/halt` in this scope. One component has both phase text labels.
The name-only binding check fails:

```text
ambiguous named binding TOP/ph1: 5 components
```

Those observations do not prove that the physical clocks conflict: omitted
drivers, buffered branches and text-anchor intent remain to investigate.
They do prohibit treating every matching label as one conductor. Consequently
there is no global phase simulation or newly qualified NMI assertion delay
from this slice. The next step is to trace the missing HALT/phase paths through
the remaining cells and interpret the clock generator's unsupported device
structure explicitly. Source PR 1704 remains draft.

## Verification and reproduction

Nine synthetic tests pass for geometric connectivity, local-net handoff,
ambiguous names, missing physical routes, retained pad values, a bypassed
sampling gate, conflicting drivers and unsupported load bias. Ruff lint and
format checks pass. `tests.log` records each command's actual exit status;
the two JSON summaries retain the observations and pinned source hashes.

The input is the original
[GCC layout archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip),
using the member and candidate layer deck recorded in
[the layout investigation](2026-10-11-maria-layout-evidence.md).
The probes reuse installed NumPy/SciPy and the existing bounded extractor.
They add no project dependency.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-phase-handoff -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-phase-handoff/probe_pads.py \
  /path/to/layout-artifacts.zip /path/to/pad-phase-summary.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-phase-handoff/connect_layout.py \
  /path/to/layout-artifacts.zip /path/to/connected-routing-network.json \
  --summary /path/to/phase-routing-summary.json
```

The complete generated network, source geometry and flattened masks stay in
the local research workspace, outside this public repository. Retained
summaries contain selected port relationships and results, not source masks
or a complete transistor netlist. Production revision, analogue delay, live
slow-mode changes and the native assertion phase remain unqualified.
