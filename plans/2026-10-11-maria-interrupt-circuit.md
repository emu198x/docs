# Trace the MARIA layout's interrupt controller

Follow the recovered layout in `2026-10-11-maria-layout-evidence.md` to test
whether its interrupt path can resolve the physical NMI timing disagreement.
This is engineering-frontier research for #197, within the approved staged
correction. Production timing stays gated on clock phase and chip identity.

1. Add `2026-10-11-maria-interrupt-circuit/layout_network.py` to extract a
   **hypothetical** network from the two flat cells, with exact rectangular
   coordinates, contact joins, separated transistor channels and label anchors.
   Use the installed NumPy/SciPy for the research probe, with no project
   dependency change. Check the contact/transistor primitive cells and all
   load connections before interpreting the layer roles.
2. In `trace_circuit.py`, trace top-level wires and contact primitives to map
   the controller ports. Decode all 32 controller input combinations from the
   extracted devices. Retain complete networks only in the local workspace;
   publish the own probe, port mapping, bounded truth table and counts.
3. Add `test_layout_network.py`: test contacts versus crossings, gate isolation,
   exact nonuniform coordinates, corner-only touches and malformed geometry.
   Qualify the source inventory and apply missing-route/missing-device negative
   controls. Compare extracted logic against independently expressed equations.
4. Record results and limits here and in the private primary-source notes.
   Native-clock delay still requires the `pckedge` generator and phase handoff;
   a controller event is not assumed to equal any chosen clock period. A
   filename is not production-revision identification.

Sources: [GCC's archived layout](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
and [Calma's format specification](https://www.bitsavers.org/pdf/calma/GDS_II_Stream_Format_5.1_Aug84.pdf).

## Result

The coordinate probe extracts 97 candidate devices from `RSYNC_LY` and 89
from `RSYNCPLA`. It uses exact coordinate intervals, including the five PLA
rectangles whose coordinates do not lie on the 750-unit grid of the first
cell. No coordinates are rounded. Channels are removed from diffusion before
conductor components are joined; a corner-only touch does not connect wires.

The proposed layer roles are supported by the archive's small primitive cells:
`CHD2HM` combines layers 1/6/7, `CHM2HP1A` combines 5/6/7, and three
`HMOSXIST` forms cross 1 and 5 with an additional layer 3, 2 or neither.
All 25 layer-2 devices in `RSYNC_LY` and all 29 in `RSYNCPLA` have the
self-gated supply connection expected of depletion loads. This supports the
interpretation; it is not an independently recovered foundry layer key.

The top-level trace follows 5,233 wire/contact rectangles, plus the two
cells' poly/metal wiring. It excludes 85 other active cell instances rather
than treating them as wires. Twelve controller port relationships are checked:

| Controller port | Traced signal |
|---|---|
| out5 | `intrst` |
| out4 | `intset` |
| out3 | `rsyncenable` / latch `enable` |
| out2 | feedback to in4 |
| out1 | feedback to in5 |
| in3 | `dlireq` |
| in2 | `halt` |
| in1 | `pckedge` |
| clkin | `ph2` |
| clk | `ph1` |
| vss / vdd | corresponding supply rails |

The interrupt set/reset inputs each pass through a `ph2` gate into a
cross-coupled latch. Set pulls `intqf` low; reset and `menblf` pull `intq`
low. The output stage drives `intf` low when `intq` is high. These connections
are checked against the extracted device graph, including the output pullup.

The controller's 32 combinational input combinations agree with separately
expressed equations. Number the feedback state with out1 as bit 0 and out2
as bit 1:

- State 0 resets the interrupt when `pckedge` is high. With both `halt` and
  `pckedge` high it also asserts enable and advances to state 2.
- State 2 stays while HALT is asserted. After HALT drops, no DLI returns it
  to state 0; a DLI waits for `pckedge` and then advances to state 3.
- State 3 waits for `pckedge`, then asserts set and returns to state 0.
- State 1 returns to state 0 without set/reset/enable.

Under that sequence, set and the following reset occur on successive
controller events. The truth-table solver opens both pass banks only to
recover the combinational equations. It does **not** simulate simultaneous
physical clock phases, dynamic charge retention, transistor delays or the
native-clock position of either event. The generator of `pckedge` and the
phase handoff still need qualification before any production NMI schedule is
selected. The attempt to apply the bounded two-terminal extractor to the
clock generator stopped on a channel with only one distinct connected net;
that structure needs explicit interpretation before extending the extractor.

## Verification

Eight independent synthetic tests pass: gate isolation, cut versus crossing,
buried contact, nonuniform coordinates, invalid contacts/anchors, corner-only
routing, malformed rectangles and five inverters over all 32 inputs. The four
previous record/geometry tests also pass. Ruff lint/format checks pass.

Two mutations of the recovered source-derived inputs demonstrate failing
acceptance checks:

- Removing the set-output route fails: `missing routing pla_out4/1 -> intset`.
- Removing its output transistor changes the truth table: state 0 with all
  external inputs low incorrectly produces set=1, and the equation check fails.

The complete inventories, port groups, truth table and negative-control errors
are in `summary.json`. A missing diffusion-only `dliqf` anchor is recorded in
the routing-only view; it is connected in the separate full cell extraction.
Other unconnected top labels belong to the excluded active cells and are
listed explicitly. No missing port is treated as an implicit connection.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-interrupt-circuit -v
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-interrupt-circuit/trace_circuit.py \
  /path/to/layout-artifacts.zip /path/to/summary.json
```

This narrows the timing investigation. It does not establish a production
chip revision, a delay in native ticks, or permission to release the draft
MARIA implementation with an assumed pulse schedule.
