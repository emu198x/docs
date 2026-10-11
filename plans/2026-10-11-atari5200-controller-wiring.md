# Atari 5200 controller wiring investigation

Lane: engineering-frontier accuracy. Issue #421 requires both fire buttons
and all four original-console controllers, including their pots and keypads.
This is an investigation plan; no production correction is implemented.

## Root-cause candidates to reproduce

`runtime-atari-5200/src/input.rs` discards the `port` field from Axis and
Button events. Its sole `ControllerCache` drives machine `set_joystick` and
`set_fire`, which address POT0/1 and TRIG0. Keypad events directly set POKEY
KBCODE, independent of the controller selected through GTIA CONSOL.
There is no upper-fire input path.

MAME supplies eight pot callbacks and four trigger bits, but its
`a5200_keypads` callback explicitly leaves accurate KR2/secondary-fire handling
as a TODO. Altirra's controller routes upper fire onto the selected POKEY
keyboard return path, including Shift, Control and Break scan positions.
Do not treat MAME's acknowledged incomplete callback as the sole oracle.

## Work before implementation

1. Inspect Atari's field-service schematic and controller drawing. Record
   the four pot pairs, four lower-fire lines and CONSOL-selected keypad/KR2
   wiring in the shared primary library. Read exact pin numbers visually.
2. Build an original 6502 guest plus original reset-vector BIOS. Through the
   runtime's real input event path, capture POT0-7, TRIG0-3, KBCODE, SKSTAT,
   IRQST and a guest execution marker. Test every port, both fires, invalid
   ports, primary alias and a four-by-four keypad-selection matrix.
3. Inspect Altirra's POKEY scanner and an executable reference. Determine
   which correction can use existing state and which needs saved scan/input
   state. Record exact state fields and affected snapshot versions before
   requesting approval for any schema or architecture extension.
4. Keep each correction one tested commit's worth. Cover input isolation,
   held/released controls, changing selected controller, disabled scans and
   save/restore continuation. Verify source CI and matching merged tree;
   close #421 only when both its acceptance items are demonstrated.

Likely source files: `crates/machine-atari-5200/src/lib.rs`,
`crates/runtime-atari-5200/src/{input,runtime,snapshot}.rs`,
`crates/atari-pokey/src/lib.rs` and integration tests in the affected crates.
The shared POKEY changes may affect the Atari 800XL envelope too; audit this
before selecting a save version. The user's separate POKEY/7800 edits in
the main checkout must remain untouched.

## Evidence now captured

Source main remains `10892b445182cc5d8106cff7cd142f9a64d4cf10`.
[Issue #421](https://github.com/emu198x/emu198x/issues/421) remains open.
No production source edits have been made in this worktree.

The [evidence folder](2026-10-11-atari5200-controller-evidence/README.md)
contains **420 original-guest captures, 222 mismatches**, and **2,048 compiled
reference scan cases with zero mismatches**. A deliberate debounce defect
makes 120 reference cases fail. The shared primary note is
`198x/reference/by-system/atari-5200/2026-controller-routing-observations.md`.
It distinguishes Atari's circuit drawings from Avery Lee's hardware research
and implementation precedent.

The root causes are now concrete:

- The runtime discards controller port numbers and reuses one analogue/fire
  cache. Ports 2-4 and unsupported ports change player one's inputs.
- Keypad input calls `press_key` directly. There is no held matrix, selected
  controller, scan phase or debounce transition between the event and KBCODE.
- Upper fire has no event mapping. Hardware routes it through selected KR2,
  where scan positions $00/$10/$30 detect Control/Shift/Break.
- The runtime's current host cache is not saved. Retaining more held inputs
  only in that cache would make restore dependent on the destination runtime.

## Proposed correction — approval pending

### Approaches

1. **Extend the existing shared POKEY scan state and 5200 input path
   (recommended).** Drive keyboard return pins from the selected controller,
   advance the hardware scanner from POKEY ticks, and save the complete state.
   This fixes both acceptance items without inventing an immediate-fire path.
2. Expand this into a simultaneous replacement of Atari 800XL's keyboard
   injection path. That also needs a computer keyboard matrix and its ghosting
   validation. It is a larger independent peripheral correction, so it should
   not be made a prerequisite for fixing the 5200.

A 5200-only imitation of KBCODE/Shift/Break writes is rejected: it would retain
precisely the missing scan timing demonstrated by this probe.

### Shared chip state

In `crates/atari-pokey/src/lib.rs`, add a serializable optional physical
keyboard scan stage. It contains the six-bit scan address, six-bit compare
latch, four-state key detector, retained Control/Shift/Break samples and two
keyboard return levels. An explicit physical-scan configuration enables it
for the 5200; the existing 800XL injected-key API remains available until its
own matrix correction. The 7800 has no keyboard attached.

Add the retained /114 divider phase needed by the stage. Advance it inside
`Pokey::tick`, in the existing CPU-clock domain; do not tie it to video lines,
POTGO, or AUDCTL's selected audio divider. Exit from initialization starts the
reference's next 15 kHz edge 81 CPU clocks after the write. That offset and
same-clock CPU-write ordering must be verified against the original reference
clock setup before implementation is accepted. The current executable sweep
proves scan transitions at supplied edges, not that initial phase.

Expose the scan address and return-line setter for machine wiring. At each
5200 POKEY tick, derive KR1 from the selected held keypad and KR2 from that
controller's upper fire. Keep the six-bit address mirroring in the board
wiring; POKEY itself must not know 5200 key names or controller selection.

Implement scan-enable reset, debounce, KBCODE modifier latching, Shift status,
keyboard overrun, enabled IRQ requests and Break edge detection. Preserve the
reference distinctions between retained status and current return lines.
Include the stage in any supported chip state export/import path; audit
`save_state`/`load_state` callers rather than leaving a second incomplete save
format. Do not widen this correction into unrelated POKEY audio/pot timing.

### Controller and runtime state

In `crates/machine-atari-5200/src/lib.rs`, retain all four controller key masks,
upper-fire levels and raw analogue positions. Existing lower-fire levels
remain in GTIA's four trigger inputs. Controller selection comes from GTIA's
saved CONSOL output latch. Add a read-only getter in
`crates/atari-gtia/src/lib.rs`; it needs no new GTIA saved field.

Preserve the existing normalized-axis conversion contract in this correction.
Route each physical port to its two pots and lower trigger. Honor CONSOL S2's
common pot-supply gate using the retained raw positions, without changing
those positions when power is cut. Tests distinguish this wiring behaviour
from the separate, unresolved analogue charge model.

In `crates/runtime-atari-5200/src/input.rs` and `runtime.rs`, extend the existing
cache to four controllers. Physical ports 1-4 map to indices 0-3; port 0 remains
the primary-controller alias and all unsupported ports drop silently. Keep
unported Key events on player one. Map `fire2` to upper fire; retain existing
lower-fire aliases. Hold/release keypad bits individually so releasing one
key does not clear another.

Save all four existing caches with the runtime envelope, including x/y,
up/down/left/right and lower-fire state. Decode them with the machine before
installing either, so a failed restore does not partially mutate input state.
Clear/reapply caches consistently on reset or cartridge replacement; tests
must state which controls remain held. This avoids reconstructing simultaneous
held directions from a single centre pot value after restore.

### Save versions and integration

The shared POKEY struct is serialized by all three Atari machines. Advance:

| Runtime | Current main | Proposed |
|---|---:|---:|
| Atari 5200 | 18 | 19 |
| Atari 800XL | 18 | 19 |
| Atari 7800 | 5 | 7 |

Version 6 of the 7800 is already allocated to the approved, open MARIA change
(PR #1704). Reserving it avoids giving two incompatible layouts one version.
Reject all prior envelopes before decoding. If MARIA lands first, carry this
change onto that version-6 source and advance it to 7. If this change lands
first, MARIA must receive a fresh version when its distinct machine layout is
integrated. Recheck this ordering before either merge; never silently reuse 7
for two layouts. The uncommitted main-checkout POKEY/7800 work is untouched.

This extension needs approval under AGENTS.md's **“Breaking changes to APIs
or data schemas”** rule. No new dependency is proposed.

## Implementation and acceptance sequence

1. Extend the executable reference evidence to scan enable/disable, retained
   latches, live selector changes, held/released keys and startup divider
   phase. Inspect the relevant Acid5200/Acid800 guests. Keep vendor files
   unchanged; retain source hashes and negative controls.
2. Add failing regressions in `crates/atari-pokey/tests/` and
   `crates/runtime-atari-5200/tests/controller_input.rs`. Cover all 15 keys,
   all four ports/selectors, both fires, port 0, invalid ports, both axes,
   simultaneous inputs and releasing one held key while another remains.
3. Implement the approved chip and board extensions plus the three envelope
   changes in `crates/runtime-atari-{5200,800xl,7800}/src/snapshot.rs`.
   Update the 5200 envelope's cache fields atomically with this correction.
4. Compare captures against the reference at each scan edge, including modifier
   bits and IRQ acknowledge/retrigger. Run original guest captures through
   public InputEvents; require advancing guest markers and the full matrix.
5. Save and restore between scan events and key states, after selection
   changes, with opposing directions held and with pots powered off. Compare
   uninterrupted and restored guest registers/IRQs and future host-event
   behaviour. Test rejection of old versions without changing live state.
6. Run focused chip/machine/runtime tests and Clippy across the three Atari
   dependants; verify boot regressions and runtime snapshots. Commit one
   complete, passing correction. Read executed CI evidence, merge the tested
   tree, update the primary/distilled records, and close #421 only after both
   fire buttons and all four complete controller paths are proven.

The baseline probe's constant pots and synthetic BIOS are sufficient to expose
routing. They do not establish resistor calibration, trackball support,
commercial compatibility or original-hardware timing.
