# C64 Phi1 fetch observation — issue 1713

Lane: engineering-frontier accuracy. The Phi1 fetch-stage and snapshot proposal
remains pending approval. The separate PRA correction uses existing saved
state and is validated in [source PR 1714](https://github.com/emu198x/emu198x/pull/1714);
merged as `bc78410f` after all checks completed; its evidence and limits are recorded below. The uniform colour-RAM guest proves
the bus source is missing, but cannot identify individual fetch slots.

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
10 tests in 307.49 seconds. The remaining sprite-DMA fixture passes separately
in 9.53 seconds with 100% image parity, so all 11 fixture tests in
`vicii_testbench` pass; seven diagnostic-only tests are excluded. Its light-pen
measurements agree on all 5,120 bytes.
Clippy with `--all-targets -- -D warnings`, formatting and diff checks pass.
The native suite includes historical gfxfetch floors as well as exact fixtures;
this is not a claim of whole-image equivalence for every fixture or a full
external-media catalogue run. DDRA, sprite/invalid-Phi2 ownership and the missing
CPU Phi1 path remain open requirements of the broader issue.

### DDRA source audit

The next DDRA gate cannot use a single unconditional screenshot oracle. The
upstream `VICII/split-tests/fetchsplit/readme.txt` explicitly reports both
cross-board and warm-up variation, and distinguishes its constructed reference
images from the actual hardware captures. Its assembly separates PRA rows
(`line0a/b/c_do`) and DDRA rows (`line1a/b/c_do`). Inspect those row/cell boundaries
before attributing a whole-image mismatch to a missing delay.

There is also implementation disagreement: on DDRA 2→0 and 3→1, VICE and
VirtualC64's custom glue retain the old bank for the intervening fetch;
Hoxs64's active `stablewarm` path selects the requested bank immediately.
`ddra-source-audit.json` records source hashes and these two cases. This is a
source inspection, not a native comparison or proof that any one emulator
matches every physical board. The primary observation note records the same
uncertainty. Qualify stable cells and board conditions, retain disputed cells
as explicit open observations, and keep enabled-sprite/Phi2 qualification
moving independently. No DDRA production change is justified by this audit.

### PRA integration

Source PR 1714 merged by rebase as `bc78410f277ad7f51ab27530e723e620bbd80607`.
All 28 reported checks completed with success or their expected skipped/neutral
status at the reviewed head `bee39c1a`. CI's uploaded workspace evidence reports
7,757 passed, zero failed, 682 ignored and 96 fixture-dependent skips. The three
affected packages account for 402 executed tests, zero failures and zero skips;
the 11 native VIC-II fixtures were verified separately on the staged local corpus.
The broader issue 1713 and the separate Phi1 schema proposal remain open.

## Direct fetch-trace qualification

CPU-only observation cannot qualify sprite middle-byte fetches while the CPU
has lost the bus. Extend the investigation with a directly instrumented native
reference in an isolated temporary source copy; keep the vendored snapshot
immutable and make no production or snapshot change.

1. Build the pinned VICE 3.10 source with its existing headless UI and locally
   available dependencies in `/private/tmp`. Record configure/build inputs and
   source hashes. Add no dependencies. First establish an uninstrumented
   baseline using the existing original bank guest and Phi1 guest observations.
2. In that isolated copy, instrument the existing Phi1/Phi2 fetch boundaries,
   retaining requested/effective address, returned data, native clock/raster
   coordinates, DMA mask and prefetch ownership. Gate capture to a guest-owned
   marker and bounded interval. Preserve actual return values and side effects.
   Retain the original patch and build runner in this plan's evidence directory.
3. Require unchanged CPU samples and output images with tracing disabled and
   enabled before using the trace as evidence. Reject truncated captures,
   missing frame/line coverage, or an empty sprite-DMA interval.
4. Run original patterned-memory guests across five VIC models, all sprites,
   enabled/disabled DMA and bank/pointer changes. Derive expected fetch bytes
   from the recorded source RAM; distinguish physical accesses from invalid
   Phi2 ownership and never label CPU-inaccessible samples as CPU observations.
5. Write a verifier and mutation controls for missing/duplicate rows, wrong
   source selection, shifted phases and Phi2 overwriting the retained Phi1
   byte. Record remaining coverage gaps before implementing the pending fetch
   extension. Initial exact files: `build_fetch_trace.py`, `fetch_trace.patch`,
   `sprite_fetch.py`, `verify_sprite_fetch.py`, `test_sprite_fetch.py` beside
   the current observation tools; primary conclusions go to the existing
   VIC-II observation note first.

### Isolated baseline established

The uninstrumented headless VICE 3.10 build passes `fetch_trace_baseline.py`:
five original bank-guest images match the retained native PNGs (493,440 pixels),
and ten I/O1/colour captures reproduce 640 native CPU-read samples. All fifteen
cases have a completion witness and reject changed payloads. The runner also
rejects missing/short payloads and incomplete model/case coverage.
`fetch-trace-baseline.json` records the binary/source identities, build flags,
measured rows and counts; `fetch-trace-baseline.log` retains the run summary.
Ruff format/check and diff checks pass.

The isolated copy is `/private/tmp/198x-vice-fetch-trace/source`, with the
baseline binary preserved separately at `x64sc-baseline`. Configure uses
`--enable-headlessui --disable-html-docs`, followed by `make -j8 -C src`.
The initial attempt to omit reSID was rejected because no sound engine remained;
the successful build keeps the default engine. Build/run need the previously
established macOS sandbox exception: the archive wrapper uses `/dev/fd` and
native startup crashes inside the sandbox. No dependency was installed.
Headless capture omits the GTK-only `-nativemonitor` option and keeps logging
on because `-silent` hides the monitor's completion output.

### Observer and ordinary sprite DMA qualified

The isolated observer now passes the same baseline with logging disabled and
enabled: 493,440 pixels and 640 CPU samples remain identical in each mode.
The enabled run produces 1,614,206 records with complete Phi1 fetch/latch pairs
and no later Phi2 overwrite of the retained byte. `observer-build.json` pins
the patch, source, schedule-table and executable identities;
`observer-disabled.json` and `observer-enabled.json` retain the measured values.
The vendored reference remains unchanged.

`sprite-native.zip` retains 200 native captures from original CPU guests:
five models × four banks × ten enable masks (off, each sprite, all eight).
It contains full observer CSVs, original PRGs, source RAM dumps, completion
sentinels and the capture manifest. `verify_sprite_fetch.py` verifies all
1,038,800 records and 20,160 sprite bytes against the recorded RAM and expected
0–62 offset sequence: 6,720 middle-byte Phi1 reads and 13,440 first/last-byte
Phi2 reads. Pointer reads continue with DMA off. All captures span lines 72–112.

The verifier uses the pinned VICE cycle tables and the observer's exact native
boundaries. Sprite Phi2 runs before `next_vicii_cycle`, so its logged clock is
one later than the associated Phi1 while its cycle field stays unchanged.
The native line counter advances after Phi1 cycle 0. These coordinates must
not be substituted directly for completed-instruction monitor coordinates.

All 64 evidence tests pass, including 19 new ordinary-sprite/observer tests.
Mutations reject missing/duplicate clocks and cases, missing DMA bytes, wrong
banks, bytes and pointer addresses, shifted Phi2 phases, corrupted line numbers,
missing latches and Phi2 overwriting Phi1. Removing a DMA byte still passes the
structural trace checker but fails the expected byte-coverage verifier. Ruff
format/check and `git diff --check` pass.

Reproduce from the evidence directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_fetch.py sprite-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

Coverage remains bounded: these are reference-emulator observations of ordinary,
unexpanded sprites with static pointers and banks. Live pointer/bank changes
during DMA, invalid Phi2 ownership, active graphics and production save/replay
remain open. Disabled middle-slot addresses are checked; this guest does not
independently seed/dump their idle bytes. The previous CPU probes qualify idle
sources separately. The pending Phi1 stage/snapshot proposal remains unapproved;
production remains unchanged from the merged PRA correction.

### Late DMA ownership qualification

Use the existing isolated observer and original patterned-memory sprite guest.
Add `sprite_ownership.py` alongside the current tools, retaining its generated
programs, completion sentinels and complete traces. Sweep CPU-written sprite
enables across the two DMA-start checks; start with PAL calibration, then cover
all five models and boundary controls. Require positive invalid-ownership
records before claiming that case is exercised. Inspect returned data against
both source RAM and the captured internal Phi2 bus, preserving the distinction
between invalid accesses and physical reads. Extend to a live pointer-write
probe after the ownership boundary is understood. Add explicit coverage and
mutation guards in `verify_sprite_ownership.py` and `test_sprite_ownership.py`
when the measured cases establish the verifier's expectations. No production,
clock, pipeline or snapshot change is authorised by this diagnostic step.


The original CPU-enable sweep now qualifies one first-byte ownership boundary.
A 160-run two-clock calibration finds PAL/current-NTSC cases; the old NTSC
boundary needs the other phase, selected by a three-clock BIT instruction.
The retained qualification covers five consecutive enable clocks on every
model and bank: 100 captures, 515,160 observer records, 40 normal-DMA cases,
20 first-byte substitutions and 40 missed-DMA cases. All 3,780 sprite-byte
events agree: 3,760 physical RAM reads and 20 internal-bus substitutions.

The invalid first-byte event returns `$FF`, has no physical read and reports
prefetch count 1; the four banks contain `$00/$29/$52/$7B` at that address.
Phi1 retains the preceding pointer byte `$80`. CPU store traces establish the
reported enable clocks independently of DMA records: line 80, cycles 53–57
on PAL and 54–58 on both NTSC schedules. Only the middle clock takes the invalid
path; the immediately adjacent clocks fetch normally or miss DMA respectively.
This guest's internal Phi2 bus is `$FF`; do not generalise that value to every
invalid access. MC still advances past the substituted first byte.

`ownership-native.zip` retains full CSVs, generated original PRGs, CPU trace
logs, source RAM dumps, sentinels and the capture manifest. The summary pins its
hash. `ownership-calibration.json.gz` retains calibration measurements and the
CPU-trace invariance comparison: all 2,004 selected sprite records match across
three PAL controls with monitor tracing off/on. Whole-trace hashes differ in
unseeded refresh RAM; no whole-trace invariance claim is made for these guests.

All 79 tests pass, including 15 new ownership controls. An unconditional-RAM
mutation passes the structural checker but fails the expected invalid-access
check. Other mutations reject wrong data/ownership/phase, missing DMA bytes,
Phi1 overwrite, missing CPU stores/completion and missing/duplicate cases.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_ownership.py ownership-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

The production source audit recorded in `ownership-summary.json` finds that
`chain_paccess` and `chain_saccess` read sprite RAM without checking ownership.
This identifies a source-level discrepancy, not a new production execution.
Preserve the invalid-byte source and MC advancement in the pending fetch-stage
correction. No production or snapshot change is made here. Last-byte invalid
accesses, live pointer writes, active graphics and late matrix ownership remain
separate coverage requirements. The larger schema proposal remains pending.

### Live pointer-write qualification

Add original `sprite_pointer.py` guests to the existing evidence directory.
Reuse the seeded sprite blocks and change a pointer through a real CPU store
while DMA is active; record that store and the native pointer/data fetches.
Calibrate across a scanline before selecting boundary cases. Compare the old
and new source RAM and preserve MC progression across the pointer change.
Exercise both pointer directions and banks/models, with explicit coverage for
writes delayed by DMA. `verify_sprite_pointer.py` and `test_sprite_pointer.py`
will reject stale/eager pointer selection, mixed row sources, wrong phase and
missing cases. Keep sprite line-wrap cases distinct from the first sprite's
schedule. These are observation tools only; no production or snapshot design
changes are made by this step.


The sprite-0 boundary is now qualified through 160 calibration runs and 80
retained boundary captures: five VIC models, four banks, both `$80→$81` and
`$81→$80` pointer changes, and writes before/after the line-90 fetch. All 5,040
sprite bytes use the CPU-clock-selected pointer and preserve the 0–62 MC
sequence. The source changes at offset 30 or 33; each three-byte row keeps one
pointer. These captures contain 412,864 native observer records.

All forty before/after pairs add one NOP but move the actual store from cycle
55 to 62. Ten DMA-disabled controls (51,192 records) differ from their enabled
programs by only the enable byte and restore the requested two-clock gap on all
five profiles. Earlier DMA changes polling alignment, so the comparison uses
the within-pair gap; it does not assume identical absolute clocks with DMA on
and off. CPU tracing identifies the real stores independently of pointer reads.

`pointer-native.zip` and `pointer-controls.zip` retain the complete native
records, original PRGs, CPU logs, source RAM dumps and sentinels.
`pointer-calibration.json.gz` retains the sweep measurements, and
`pointer-summary.json` pins the native binary and archive identities. All 94
tests pass, including 15 new pointer/control tests. Coherent stale/eager Phi1
changes still fail the CPU-clock check, and mixed row sources or MC resets fail
even when the structural trace remains valid.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_pointer.py pointer-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

This is native reference evidence for sprite 0, not production execution or a
newly established production bug. The existing source already latches
`chain_fetch_base` for later bytes and advances its counter. Preserve that
behaviour in the pending fetch correction. Other sprites' line-wrap timing,
writes between individual fetch phases, dynamic bank changes and save/replay
remain separate gates. Production and snapshot formats are unchanged.

### Pointer/data continuity at line wrap

Use the existing `sprite_pointer.py` guest and isolated observer for the fetch
sequence that closes each line: sprite 2 on PAL/old NTSC and sprite 3 on current
NTSC. The sprite-3 sweep on all models also observes the following-slot/native
line-counter boundary on PAL/old NTSC. Calibrate CPU writes before selecting
both directions and all banks. Generalise the existing pointer-sequence checker
in `verify_sprite_pointer.py` while preserving its sprite-0 boundary guards;
add `verify_sprite_wrap.py` and `test_sprite_wrap.py` for explicit wrap coverage.
Require the absolute clock, model cycle modulus, continuous MC and held pointer
to agree even when the native line label changes. Test mutations that reset at
wrap, shift one phase, move a source change early/late or omit the wrapped byte.
Keep these reference observations separate from production execution and from
CPU writes between individual bus-owned fetch phases. No production or snapshot
change is made by this probe.


The model-specific closing sequence is now qualified: sprite 2 on PAL/old NTSC,
sprite 3 on current NTSC. Eighty native boundary captures cover five profiles,
four banks and both pointer directions. All 5,040 bytes and 1,680 wrapped rows
preserve the latched source and MC progression. The complete traces contain
412,672 records. A 256-run calibration also covers the following sprite-3 slot
on PAL/old NTSC, distinguishing a native line-label transition from an actual
absolute-clock wrap.

The generalised sequence checker verifies absolute Phi1/Phi2 clocks and model
cycle modulus. It retains the earlier sprite-0 boundary wrapper and guards.
Native Phi1's line label advances after cycle 0; native sprite Phi2 still reports
the preceding cycle. The checker rejects rewriting those labels from the current
absolute clock, resetting at wrap, mixing row sources or omitting the final byte.
All 108 tests pass, including 14 new wrap guards; Ruff and diff checks pass.

`wrap-native.zip` retains all original programs, raw traces, CPU logs, RAM dumps
and completion sentinels. `wrap-calibration.json.gz` retains the broader sweep,
and `wrap-summary.json` pins the native binary, archive hash, counts and scope.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_wrap.py wrap-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

The two CPU-store sides are 90/59 and 91/3 on PAL, 90/61 and 91/3 on current
NTSC, and 90/59 and 91/2 on old NTSC. All forty pairs preserve the seven-clock
actual gap for one additional NOP. The first new source byte is offset 30 or 33,
with no counter reset or split row at wrap. This is native reference evidence;
no additional production fault, frame-wrap guarantee or save/replay result is
claimed. Active graphics, dynamic banks during DMA, other invalid ownership
cases and production save/replay remain open. The schema proposal is unchanged
and still pending; no production or snapshot implementation follows here.

### Next probe: active graphics and matrix sources

Add `graphics_fetch.py` original guests beside the observer tools. Seed the
screen matrix and the full RAM graphics area, enable display before the first
DMA line, and capture idle graphics plus several complete badline/non-badline
groups. Cover all eight stable ECM/BMM/MCM combinations, five native models and
four banks; keep mode transitions and character-ROM mappings separate. Verify
physical addresses and data from captured RAM, the 40-column sequence, row
counter progression and retained matrix bytes between badlines. Add
`verify_graphics_fetch.py` and `test_graphics_fetch.py`, with mutations for wrong
mode/address bits, stale matrix rows, shifted counters, missing columns and
Phi2 overwriting the retained Phi1 byte. This extends reference observations
only, leaving production and snapshot proposals unchanged.


### Stable graphics and matrix source gate qualified

All 160 native captures pass: five VIC profiles × four banks × eight stable
ECM/BMM/MCM modes. The guests seed and dump the complete 1 KiB matrix and 8 KiB
RAM graphics source. Their 760,960 raw records verify 160,000 active graphics
reads, 64,000 idle graphics reads and 25,600 matrix reads. Of the active reads,
134,400 use matrix data retained between badlines. All forty columns, RC steps,
VC row changes, physical banks and data bytes match.

Text uses the captured character code; bitmap uses VC. ECM masks address bits
9–10 even in invalid modes, and selects `$39FF` for idle graphics. MCM does not
alter stable source addressing. Matrix reads occur on lines 51, 59, 67 and 75 at
native cycles 14–53, with matching graphics at cycles 15–54. Matrix Phi2 keeps
the current cycle label after the Phi1 latch; sprite Phi2 keeps the previous
cycle label before cycle advance. The checker validates each observation point
and ensures matrix reads preserve the retained Phi1 byte.

All 129 evidence tests pass, including 21 graphics tests and mutations for wrong
address sources/masks, stale screen rows, RC shifts, wrong banks/bytes, missing
columns, wrong phase labels, overwritten Phi1, missing completion and incomplete
case coverage. A coherently altered fetch and latch fails the independent RAM
source check. Ruff and diff checks pass.

`graphics-native.zip` retains the original programs, complete traces, CPU logs,
monitor commands, source dumps and sentinels. `graphics-summary.json` pins its
identity, native binary, counts and scope; `graphics-tests.log` retains the full
suite result.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_graphics_fetch.py graphics-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

Production source already selects these stable addresses and retains the matrix
row. No new production failure or save/replay result is claimed. Dynamic mode
and bank changes, character-ROM mapping, late matrix ownership and production
save/replay remain separate gates. The larger stage/snapshot proposal remains
pending; this qualification makes no production or schema change.

### Next probe: live banks during sprite DMA

Add `sprite_bank.py` original CPU guests beside the existing observer tools.
Seed all four banks with distinct sprite pointers and all eight data blocks;
change CIA2 PRA on line 90 while a selected sprite is active. Sweep CPU delay
and instruction alignment first, recording actual completed-store times so DMA
stalls do not become guessed bank timing. Include the custom-glue 1↔2 transient
and ordinary transitions/no-change controls across the five models. Verify every
pointer/data physical bank against those CPU events, retain each fetched pointer
through its three-byte row, and preserve MC through a bank change. Use the
existing observer and captured RAM, with no production or snapshot changes.

Add `verify_sprite_bank.py` and `test_sprite_bank.py` after the calibration
identifies reachable boundaries. Mutations must reject stale/early bank
selection, lost or widened transients, replacing the held pointer, shifted MC,
missing events/cases, wrong banks/bytes and overwritten Phi1. Retain raw native
traces, programs, CPU logs, RAM and sentinels; report any inaccessible phase or
board-specific uncertainty rather than claiming it was covered.


### Live PRA bank boundary qualified

All 320 cases pass: five native profiles × two explicitly selected glue types ×
sixteen old/new bank pairs × two CPU-store boundaries around sprite 0's active
line-90 row. The 1,653,056 records verify 20,160 sprite bytes, all pointer sources,
live physical banks and uninterrupted MC. Each guest seeds and dumps all four
banks' pointer tables and eight sprite blocks. These are controlled glue/chip
combinations; the matrix does not claim all were shipped boards.

The actual completed stores occur at 90/55 and 90/62 on PAL/current NTSC, and
90/56 and 90/63 on old NTSC. One extra NOP produces a seven-clock actual gap in
all 160 pairs. Custom glue's twenty 1↔2 cases use bank 3 for one observed fetch;
four hit inactive-sprite pointer reads and return that bank's pointer byte.
Discrete glue and all other bank pairs switch without that transient. The
132-run delay/alignment calibration verifies another 678,840 records and 8,316
bytes, including thirteen transient pointer reads across 66 transients.

All 151 evidence tests pass, including 22 new bank tests. Mutations reject wrong
bank timing, lost/widened or inappropriate transients, wrong pointers, MC resets,
wrong/missing data, missing CPU/completion events, overwritten Phi1 and missing
or duplicated cases. Coherently shifted CPU timestamps and metadata still fail
the independent physical-bank observation. Ruff and diff checks pass.

The runner accepts an explicit glue type while keeping earlier callers' default
unchanged; each new capture reads back the native resource. Full original
guests, traces, logs, commands, source dumps and sentinels are retained in
`sprite-bank-native.zip` and `sprite-bank-calibration.zip`. Identities and scope
are in `sprite-bank-summary.json`; the full suite result is in
`sprite-bank-tests.log`.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_bank.py sprite-bank-native.zip
PYTHONDONTWRITEBYTECODE=1 python3 verify_sprite_bank.py sprite-bank-calibration.zip --calibration
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
```

No active three-byte row is split by these ordinary CPU writes. Between-phase
writes and late invalid ownership remain distinct probes; DDRA and production
save/replay are also outside this evidence. Production already holds a relative
pointer base and applies its live bank, and the earlier PRA fix is merged.
This establishes no additional production failure and changes no production or
snapshot state. The larger Phi1 correction remains pending approval.
