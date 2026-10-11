# C64 Phi1 fetch observation — issue 1713

Lane: engineering-frontier accuracy. Investigation only; no production timing
or schema change is approved here. The uniform colour-RAM guest proves the
bus source is missing, but cannot identify individual fetch slots.

1. Inspect the staged VICE `phi1timing` v2 source and hardware-provenance readme.
   It reads cartridge I/O1 `$DEAD`, so distinguish that decoder from colour RAM.
   Pin all three guest binaries and the source used to interpret their output.
2. Run the unmodified guests in native VICE on PAL/NTSC breadbin, PAL/NTSC C64C
   and old NTSC. Require a real `$D7FF` completion write and retain result,
   raw measurements and the embedded reference for every cycle.
3. Run the same binaries on the four shipping Emu198x boards using real ROMs
   and the existing CPU pin/tick interface. Retain failure evidence with a
   bounded execution limit. Do not infer timing from a successful file load.
4. Separately change only the measurement operand in a derived, identified
   guest to read colour RAM. Preserve native source files. Compare the high
   nibbles of each cycle's capture against native VICE; this separates missing
   I/O1 open-bus routing from missing Phi1 fetch data.
5. Use the measurements to specify the existing fetch-stage extension and
   its validation gates. Do not patch a nibble or shift a framebuffer to pass.
   Ask before additional pipeline/snapshot changes if the implementation
   needs them. Keep the MARIA and pending POKEY work intact.

Exact production paths under investigation:
`crates/mos-vic-ii/src/lib.rs`,
`crates/mos-vic-ii/src/sprite_fetch_chain.rs`,
`crates/machine-commodore-c64/src/machine.rs`,
`crates/machine-commodore-c64/src/memory.rs`.
Reference precedent: VICE 3.10 `viciisc/vicii-cycle.c`, `vicii-fetch.c`,
`vicii-phi1.c`, and `c64/c64mem.c`. Native captures are reference-emulator
observations; upstream hardware-identification notes are a separate provenance
claim and must not be relabelled as new hardware measurements.

## Measured result

All ten native rows match: 640 raw samples across five chip profiles and two
endpoints. The four shipping Emu198x boards complete all eight guests, but
fail 468 of 512 samples. I/O1 returns constant `$FF` (53 wrong slots per board).
Colour RAM returns constant `$2E` (all 63/65 slots wrong), retaining data from
the preceding real-ROM boot display. The low nibble remains correct.

The runner returns failure for the mismatch and restores its temporary source
fragment byte for byte. Nine parser/control checks pass, including a positive
native result and rejection of missing/duplicate rows, short data, invalid
bytes, a fabricated zero mismatch count and an unexpected process exit.
Primary provenance is recorded at
`reference/by-topic/vic-ii/2026-phi1-fetch-observations.md`. The staged corpus
commit is unresolved; individual sources and all guests are hash-pinned.
No third-party guest/source bytes are included in the public evidence: raw
measurement arrays, measurement-only binaries and original tools are retained.

## Proposed correction — approval required

Extend the existing VIC-II fetch and pending-cell stages. Keep the master
clock, CPU pin interface, BA/AEC ownership rules and framebuffer geometry.
This is a coordinated fetch-stage correction, not a replacement renderer.

1. Add an explicit retained Phi1 data byte and eight-bit refresh counter to
   `Vic`. Keep the existing matrix/sprite DMA diagnostic separate so the
   older BA/AEC evidence and public diagnostic do not silently change meaning.
   Refresh resets at the reference's frame-start event and advances on each
   refresh access. Validate its exact phase at frame wrap on every model.
2. Select the actual Phi1 source each clock before rendering: active/idle
   graphics, sprite pointer (even with DMA disabled), sprite middle byte when
   DMA owns that slot, refresh, or ordinary idle. Reuse existing model timing
   and MC/MCBASE state. Preserve distinct Phi2 matrix/sprite bytes and invalid
   ownership handling; a later Phi2 access must not overwrite the Phi1 byte.
3. Separate fetching from the visibility checks in `render_pixels`. Pass the
   fetched graphics through the existing pending cells without an extra memory
   read for rendering. Preserve the distinction between actual active fetches
   and delayed visible idle cells at the far-edge forced-badline transition.
   Any needed descriptor additions stay inside these existing stages.
4. Feed the retained Phi1 byte to colour RAM's upper nibble and unclaimed
   `$DE00–$DFFF` reads. Fitted cartridge/REU/GeoRAM/Ultimate decoders still
   answer first; preserve their existing side effects. Confirm both I/O1 and
   I/O2 fallthrough, fitted-device controls and bank changes with CPU guests.
5. Save the new retained state and advance C64 snapshots from **19 to 20**,
   rejecting version 19. The unapproved sprite-draw proposal also names 20;
   if this correction lands first, that later schema must use 21 or later.
   Never publish two incompatible layouts under version 20.

This extends an existing architectural pattern but changes the snapshot data
schema, so the project's "Breaking changes to APIs or data schemas" approval
rule applies. No production implementation of this proposal has started.

### Alternatives considered

- Reuse the current retained DMA byte and derive refresh addresses from raster
  coordinates. This avoids a new counter but conflates Phi1 observation with
  existing Phi2 diagnostics and makes frame-start/refresh phase implicit. It
  is less clear to validate and restore.
- Replace the machine's clock/bus architecture. The evidence does not require
  that larger rewrite. Existing native-clock stages can represent the missing
  accesses and their distinct observation phases.

### Required gates

- All original and colour-RAM Phi1 rows exact on four shipping boards; old
  NTSC covered at chip level. The colour-derived guest's original full-byte
  classifier is expected to fail: compare raw native bytes instead.
- Preserve the independent 2,176-read uniform colour-RAM check from issue 1713,
  and require the source-byte negative control to change observed output.
- Cycle/address/data traces for all five chips, four banks, refresh rollover
  and frame wrap, active and idle graphics, every sprite's enabled/disabled
  slots, plus mid-line bank/pointer/ECM changes. Use unique source patterns to
  expose selection/phase errors; a uniform-byte guest cannot qualify these.
- CPU reads during ordinary and forced badlines, and after matrix/sprite Phi2
  accesses, must observe the correct Phi1 byte. Preserve all existing BA/AEC
  lead-time and invalid-access regressions and all five strict colour-fetch
  tests required by `c64-ba-aec-handover.md`.
- Save/replay across refresh, sprite halves, graphics and frame wrap; old
  snapshot rejection before mutation. Recheck every strict VIC-II fixture,
  ordinary chip/machine/runtime suites and Clippy. Explain any changed images.
- Run the full compatibility catalogue when its external media volume is
  available; record this as an unmet gate while that volume is absent.

## Refresh-address qualification

While schema approval is pending, qualify the planned refresh counter using
native CPU observations. Derive position-coded guests from the pinned corpus:
replace the refresh-page fill with its index, vary the bank and IRQ start line,
and trace every I/O1 measurement through counter rollover and frame wrap.
Preserve all source inputs and instruction sizes. Record the exact mutations,
source identities and monitor observation phase before treating the bytes as
address evidence. This work changes no production stage or snapshot.


The native matrix passes all 60 cases and 300 refresh observations. Five
models × four banks × ordinary/rollover/frame-wrap cases qualify the address
model at the captured monitor phase. Wrap samples cover the final two lines
and lines 0/1/2; rollover samples cover lines 50–54. The monitor reports
cycles 11–15 for the five refresh reads, and every traced LDA accumulator
agrees with the guest's stored byte.

`refresh.py` records the precise guest mutations and input identities.
`refresh-comparison.json.gz` retains each sample and the selected refresh page;
`verify_refresh.py` validates all sixty distinct cases and rejects four wrong
counter models. Their mismatch counts are 300 (predecrement), 280 (increment),
280 (reset every line) and 60 (no frame reset). The combined probe/parser test
suite passes 18 guards. It rejects incomplete capture data rather than treating
missing samples as agreement.

Bank 3's refresh page includes live CPU vectors. The expected byte comes from
the captured page, so the observed `$08` at `$FFFF` is preserved rather than
replaced with an assumed index byte. The selected vector byte does not change
between measurement and capture. This probe does not qualify dynamic writes
to arbitrary refresh locations.

The exact input/output phase and limitations are recorded in the private
primary observation note. The native traces are post-instruction monitor
reports, so do not apply their cycle labels to an emulator's internal counter
without normalizing the observation boundary.

Production PR 1712 is now merged as `63ff50c86ac20c6145d1cddc7dc025762a168d7a`.
Its clean temporary worktree was removed and the branch retained. This fetch
proposal remains unimplemented and awaiting the existing schema question.

## Dynamic bank observation plan

Add `bank_switch.py` beside the existing capture tools. An original CPU guest
will fill each bank's disabled-display Phi1 sources with a distinct byte,
then exercise all sixteen old/new bank pairs through CIA2 PRA and DDRA.
Observe I/O1, I/O2 and colour RAM after zero through seven NOPs. Retain native
traces and completion sentinels on all five profiles. `test_bank_switch.py`
will reject missing/duplicate cases, bad bytes and fabricated success counts.

These reads occur at least four CPU clocks after the selecting store. They
qualify settled bank routing, not the first intervening fetch. VICE's
`c64gluelogic.c` models a one-clock custom-glue transient for bank 1/2 swaps
and some DDRA changes (with an explicit accuracy caveat for the latter).
That transient needs a separate fetch/visible-output observation; do not
use the settled CPU test to waive the first-fetch timing gate. No production
or snapshot change is part of this investigation.

The settled-routing matrix now passes all 30 captures and 3,840 CPU reads.
Both PRA and DDRA select the expected bank for all sixteen transitions;
I/O1/I/O2 return the bank byte and colour RAM preserves its stored low nibble.
Every stored byte agrees with its traced accumulator and every guest reaches
the completion store. The earliest measurement follows the selecting store
by four CPU clocks; added NOPs extend this to eighteen clocks in steps of two.
This does not cover an immediately intervening VIC fetch.

`bank_switch.py` is an original guest generator and capture/verifier.
`bank-switch-comparison.json.gz` retains raw measurements and input hashes;
`bank-switch-traces.json.gz` retains native logs. A stale-bank model disagrees
with 2,880 measurements. Ten new guard tests pass, including rejection of a
wrong byte even when its trace and success count are falsified consistently.
The combined suite now passes 28 tests. The existing proposal remains pending;
no production stage or snapshot was changed.

## First-fetch visibility experiment

Add an original active-display guest in `bank_transient.py`. Fill all four
screen matrices identically and give their character data distinct bit
patterns. Repeated CPU bank writes will cross active graphics fetches. Capture
identical runs with VICE discrete and custom glue logic on the same chip
profile, with checked completion and final-frame screenshots. Compare exact
pixels; include transitions that do not invoke the reference's bank-1/2
transient as controls. A visible difference establishes a fetch consequence,
not physical validation of VICE's transient duration. Keep production unchanged.

The first paired PAL-C64C capture differs only for bank 1/2 switching; the
other three bank pairs are exact controls. Extend the native matrix with
bank-3 character bytes `$00/$55/$AA/$FF`. Require unchanged discrete-glue
images and exact per-bit prediction of custom-glue pixels from the two solid
patterns. Then run the same original guest through Emu198x's actual CPU:
compare marker `$00/$FF` framebuffers on all four shipping models. Breadbin
controls must remain identical; C64C must expose bank-3-dependent pixels.
Use a temporary appended test in `machine-commodore-c64/src/machine.rs`,
retain a failing transcript, and restore that file byte for byte. This is a
reproduction, not approval for a new glue-logic stage or snapshot field.

### Visible transient result

The 70 native captures identify a bank-3 fetch consequence during bank 1/2
switches. All fifteen other bank-pair controls match exactly. Changing only
the bank-3 glyph between `$00` and `$FF` leaves discrete-glue images identical
but changes 6,544 pixels on PAL/old NTSC and 6,664 on current NTSC. These solid
patterns predict every pixel of the `$55` and `$AA` custom-glue captures with
zero errors. All chip profiles are tested with both glue settings deliberately;
only the two C64C models use custom glue as their normal board configuration.

The CPU probe at source `63ff50c8` reproduces the missing consequence: both
C64C cases fail, both breadbin controls pass. All eight guests execute after
real firmware boot, reach the sentinel and produce nonblank framebuffers after
more than two full frames. The temporary test fails with `custom-glue bank swap
must expose transient bank-3 character data` (`left: 2`, `right: 0`). Its source
is restored exactly; no production code is changed.

`bank_transient.py` generates the original guest and native matrix;
`verify_transient.py` checks source-bit predictions against all retained PNGs.
`transient-native/` holds 70 screenshots, the compressed manifest and logs.
`run_transient_probe.py` and `transient_probe.rs` reproduce the CPU mismatch;
`transient-run.log` and `transient-summary.json` retain the result. Ten new
guards bring the combined suite to 38 passing tests, including rejection of
an incorrect marker image even with matching forged hash/difference metadata.

This is a separate machine glue-logic omission, beyond the pending VIC fetch
stage design above. The PRA observation boundary is qualified below; DDRA cases still need
qualification. Inspect whether the already-saved VIC bank output and CIA
port state can preserve this window before proposing additional saved state. Do not treat the existing Phi1 proposal as approval for that extension,
or copy VICE's explicitly approximate DDRA behaviour as established hardware.

## Write-to-fetch phase qualification

Add `bank_phase.py` to repeat the existing original bank-1/2 guest with native
CIA2 store tracing. Require unchanged screenshots against the retained capture
before trusting instrumentation. Relate the bank-3-dependent glyph cells to
completed CPU store times and the reference's graphics fetch table, accounting
for raster/frame wrap and screenshot crop. Reject shifted or widened windows.
Record the monitor boundary explicitly; this qualifies reference timing, not
an electrical delay measurement. Production and schema stay unchanged.

### Qualified PRA phase

Five instrumented runs preserve the retained screenshots byte for byte and
record 40,965 CPU stores. Readback confirms custom glue. In the monitor's
completed-instruction coordinates, glyph column `n` is bank-3-dependent exactly
when the same line contains a 1/2 swap at reported cycle `15 + n`. Accounting
for native crop and the unfinished screenshot line predicts all 40,000 glyph
cells, with zero differences. This does not equate the monitor counter with
hardware half-cycle labels or Emu198x's internal tick counter.

The -2/-1/+1/+2 clock controls fail 8,218/8,241/8,248/8,273 cells; a two-clock
window fails 4,121. The suite now passes 45 guards, including rejection of
coherently shifted timestamps using independent pixels. `bank_phase.py`,
`phase-logs.json.gz` and `phase-summary.json` retain the capture and comparison.

The next implementation audit should examine the existing state first:
`Vic::vic_bank` is already saved separately from CIA2's selected port output,
and each board tick refreshes that bank after the VIC fetch. That may already
represent a one-fetch transient without adding fields. Snapshot restore
currently recomputes the bank immediately; any correction must preserve the
actual saved output and prove replay at the transient. This is an implementation
candidate to validate, not an approved new schema or a reason to skip the
pending Phi1 question. DDRA's separate reference approximation remains unqualified.

## Existing-state PRA correction audit

The bounded candidate uses the existing CIA-selected bank and saved VIC bank
output, without adding a pipeline type, state field or snapshot version. On a
C64C PRA write that changes physical bank 1 to 2 or 2 to 1, present bank 3 to
the next VIC tick. The existing post-fetch board refresh then selects the CIA
bank. Keep other transitions and breadbins direct. DDRA behaviour is outside
this PRA correction and remains a separate explicit requirement.

1. In an isolated source checkout, change only
   `machine-commodore-c64/src/machine.rs`: capture the previous CIA-selected
   bank for PRA writes and retain the reference-backed intermediate bank in
   the existing VIC output. Preserve that output on snapshot restore instead
   of recomputing it. Document why the post-fetch refresh ends the window.
2. Re-run the existing CPU guest reproduction. Require both C64C marker cases
   to change and both breadbin controls to remain identical. This is a coarse
   root-cause gate; a positive changed-pixel count does not prove timing.
3. Trace CPU stores and compare the resulting bank-3 glyph mask against each
   machine's fetch/output coordinates. Check one-clock timing and reject
   shifted windows; do not waive this because the coarse guest passes.
4. Exercise all bank transitions, PRA mirrors and both normal/IEC tick paths.
   Verify saved transient output survives byte serialization and replay,
   including one tick before/during/after the switch. The schema stays at v19
   only if the existing serialized fields preserve the full required state.
5. Run affected machine/runtime tests, strict VIC fixtures, formatting and
   Clippy. Commit one bounded correction only after gates pass; retain wider
   Phi1 and DDRA requirements in issue 1713. If the existing state cannot model
   the observed phase, discard this candidate and return to a concrete design.

### Existing-state correction verified

The PRA correction passes without extending saved state. The existing VIC
bank output retains bank 3 for the next fetch; the board's post-fetch refresh
then returns it to CIA2's selection. Restore now retains that saved output.
The serialized snapshot envelope remains version 19.

The permanent machine test executes the original guest on all four shipping
boards through both normal and IEC ticks, with both bank-3 markers (16 runs).
Every run completes 8,193 PRA stores. Its whole-framebuffer difference mask
matches the independently qualified store-to-fetch relation exactly, including
partially rendered lines. A second test covers all 16 bank pairs at all 16 PRA
mirrors, on both clock paths. Byte-snapshot tests cover four boards, both swap
directions and the before/during/after boundaries (24 cases), with eight ticks
of identical serialized replay.

Removing the correction makes both machine tests fail: the CPU pixel test
reports 6,568 mask mismatches on PAL C64C. Reintroducing only the old loader's
bank recalculation fails the restore regression at `C64cPal, phase 1`
(`left: 2`, `right: 3`). This separately establishes that the restore test can
catch its intended fault; reverting the whole fix would never arm the transient.

The real-firmware guest also completes all eight board/marker runs. Bank-3
markers change 6,552 PAL C64C pixels and 6,464 NTSC C64C pixels; breadbin buffers
remain identical. These counts are capture-phase dependent, so the permanent
regression checks the full phase-derived mask rather than pinning those totals.

Validation: 402 ordinary tests pass (74 fixture tests remain ignored in that
command); the explicitly selected strict native-reference suite passes all
10 tests in 307.49 seconds. Its light-pen measurements agree on all 5,120 bytes.
Clippy with `--all-targets -- -D warnings`, formatting and diff checks pass.
The native suite includes historical gfxfetch floors as well as exact fixtures;
this is not a claim of whole-image equivalence for every fixture or a full
external-media catalogue run. DDRA, sprite/invalid-Phi2 ownership and the missing
CPU Phi1 path remain open requirements of the broader issue.
