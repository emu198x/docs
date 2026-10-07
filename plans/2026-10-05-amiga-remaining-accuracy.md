# Amiga remaining accuracy investigations

Status: line, CPU prefetch and initial Copper WAIT corrections verified.
Area-blitter channel/holding correction verified in schema 49.
Completion-dependent WAIT remains
an explicit failing diagnostic.

## Reproduction and proposed first change

`/private/tmp/emu198x-line-dma-probe/` is an external Rust probe using the
live Agnus crate. Its first run exited 1. After the existing two startup
CCKs, standard drawing read C at CCK 1 and wrote D at CCK 2; the reference
standard schedule reads C at 2 and writes D at 4. Enabling B produced the
same two transfers, left BLTBPT at $1000 and ignored the fetched texture.
The complete output is in `red.log`. These are observed production faults,
not deductions from the diagnostic remaining-cycle counter.

The third-edition hardware manual, printed p193, states eight system ticks
per line pixel (four CCKs). Registered vAmiga's `SlowBlitter.cpp` standard
program is internal A, C read/B selection, internal result, D write.
Minimig's `BLT_L1` through `BLT_L4` independently expose those four phases.
FS-UAE's `process_blitter` labels the corresponding four line stages.

For B enabled, vAmiga uses six stages, fetches B before C and advances
BLTBPT by BLTBMOD, without the ordinary area-mode +2 increment. FS-UAE's
line B helper corroborates that pointer rule. The six-stage schedule needs
an executable reference comparison before being declared exact. The unusual
C-disabled and nonstandard-width cases must retain explicit evidence bounds.

Recommended design: extend the existing Agnus line runtime with an explicit
serialized phase and pending result. Keep startup, bus grants, completion
observer holds and the shared machine scheduler. Model internal stages as
elapsed CCKs that do not own the bus, respecting reference admission rules;
do not synthesize wait loops or use an extra timing counter. Fetch B through
the existing `ReadB` operation, and preserve its texture and modulo effects.

This requires runtime snapshot version 46, rejecting version 45. Alternative:
add only B requests to the existing two-stage engine. Rejected as a complete
fix because it would retain the independently reproduced standard timing
fault. The user approved the full line-stage design and snapshot break.

The user authorized investigating and fixing the remaining blitter, Copper,
disk, CPU and video accuracy issues on 2026-10-05. Work proceeds as separate,
bounded changes. New pipeline designs and snapshot incompatibilities still
require agreement under the project rules.

## 1. Line-mode DMA

Read `knowledge/decisions/amiga-blitter-line-texture-phase.md`,
`amiga-blitter-line-onedot.md` and `amiga-blitter-completion-pipeline.md`
in the emulator repository. Compare the live scheduler against registered
FS-UAE, vAmiga and Minimig implementations before editing production code.

Files: `crates/commodore-agnus-ocs/src/agnus.rs`, its line-mode integration
tests and changelog; `crates/runtime-commodore-amiga/src/snapshot.rs` and
snapshot tests if serialized phases are added. Update the line-mode decisions
and add source observations to the primary Amiga reference library.

Verification: an external failing probe records real reads/writes and CCKs;
then regressions cover B disabled/enabled, B pointer modulo, fetched texture,
internal-cycle CPU availability, C-disabled drawing, ONEDOT and mid-phase
restore. Run affected OCS/ECS/AGA machine tests, runtime snapshots, build,
formatting and strict Clippy. No golden requalification without investigation.

## 2. Copper completion-dependent WAIT

Files: `crates/common-commodore-amiga/src/copper.rs`, the shared driver,
`crates/commodore-agnus-ocs/src/agnus.rs`, Copper tests,
`knowledge/decisions/amiga-copper-wait-skip-comparison.md`.

Build a bus trace around WAIT eligibility and first fetch. Compare reference
ownership, cancellation and timing. Change only demonstrated disagreements;
agree a pipeline extension before implementation if required.

## 3. Disk stream

Files: `crates/peripheral-commodore-amiga-floppy/src/lib.rs`, `mfm.rs`,
`crates/common-commodore-amiga/src/` disk driver and Paula disk tests.

Bound the integer word interval against reference timing first. Separate a
small timing correction from new media support. Flux/IPF/custom-track support
needs a concrete design and dependency approval before implementation.

## 4. CPU bus timing

Files: `crates/motorola-68020/src/cpu.rs`,
`crates/motorola-68030/src/cpu.rs`, processor timing tests and the shared
Amiga driver. Reproduce the recorded 32-bit prefetch limitation before
changing it. Compare ordered bus transactions and timing, not final registers
alone. Cache/MMU expansion needs a separately agreed design.

## 5. Video combinations

Extend project-authored guests under `test-data/commodore/amiga/` to cover
HAM, sprite/playfield priority and timed register changes. Retain reference
producer identity, full common rasters, adjacent fields and source hashes.
Only fix demonstrated mismatches; passing coverage must not be described as
silicon validation.

## Verification in progress

The corrected external probe passes: C/D at CCK 2/4 in standard mode and
B/C/D at 2/3/6 with B enabled. The compiled registered vAmiga table adapter
confirms four/four/six/six stages across all B/C enable combinations. Agnus
regressions cover actual transfers, texture, modulo, reserved cycles, CPU
availability, C-disabled output and first-D/later-C destination selection.
Runtime tests compare the original live machine with its restored continuation
at each four/six line stage, including pending D.

The first broad regression run stopped at an existing ECS CLXDAT assertion:

```text
assertion `left == right` failed: CLXDAT must route to Denise (clear at reset), not open-bus $FFFF
  left: 32768
 right: 0
```

Registered FS-UAE `CLXDAT` and vAmiga `DeniseRegs.cpp` independently return
the raw latch OR $8000. The binding collision decision already requires that
fixed bit, and the A1200 test already expects it. Only the stale ECS test is
updated. The original failing log is retained as `regression.log`; the wider
rerun is recorded separately as `regression-final.log`.

## CPU investigation boundary

`motorola-68000/src/icache.rs` explicitly fills one word at a time. The
primary MC68020 manual section 4.1 and instruction-pipe description say that
external prefetch loads an aligned long word into a cache holding register
even with the cache disabled. Registered FS-UAE `fill_icache020` agrees.
Before treating this as a timing-only limitation, test modification of the
sibling instruction after a fill: prefetched contents can affect executed
instructions, not just the bus-cycle count. No CPU production change is made.

## Completed line-stage verification

The broad release run covered 150 targets: 738 tests passed and the remaining
OCS CLXDAT test failed with the same stale zero-value assertion as ECS. Its
source-backed correction was rerun with the complete three-test target green,
for 739 passing unique tests. There are 121 explicitly ignored historical
fixture/diagnostic/campaign tests; they are not counted as passes. Both
separately invoked Test Kit gates pass six exact patterns each. Boot goldens
remain unchanged. Native release build, strict Clippy, formatting and Ruff
pass. `regression-complete.log`, `m7-chipset-reads.log`, `test-kit.log`,
`build.log` and `clippy.log` preserve those outcomes.

The earlier OCS unit tests also expected the pre-output colour queue that the
binding colour-output decision removes on OCS. Two source-backed expectation
updates preserve palette diagnostics and assert the current MOVE output
colour. The line arbitration test now covers both internal A followed by a
bus-using C request and a suppressed D followed by internal A; each permits
CPU memory access without retrospective ownership. All 37 OCS unit tests pass.

## Proposed MC68020/68EC020 prefetch correction

The external `/private/tmp/emu198x-prefetch-probe/` drives the real CPU through
its bus signals, completes a prefetch at aligned $1004, then changes the
instruction at $1006 from MOVEQ #1,D7 to MOVEQ #2,D7 at an instruction boundary.
Both cache-disabled and cache-enabled runs execute the replacement, D7=2.
The probe exits 1 against the primary manual's full-long retention rule.
Its original output and bus-read list are retained as `red.log`.

Recommended design: extend the existing instruction-prefetch path to request
an aligned long word through the existing SIZ/DSACK transaction stages. Retain
its two words in a saved holding register in the existing 68020 instruction
cache/prefetch state even when caching is disabled; fill a complete cache entry
only after the full transfer completes. Serve the neighbouring word from that
register. Do not peek at memory, add bus callbacks, add instruction-level
execution, or change clocks. Preserve reset, CACR, exception and FC behaviour.

Files: `motorola-68000/src/cpu.rs` and `icache.rs`, the MC68020 variant binding,
processor bus/prefetch tests, Amiga snapshot envelope and replay tests. The
narrow initial claim is MC68020/68EC020; MC68030/68040 retain their existing
binding until separately audited. The additional serialized holding register
requires Amiga snapshot version 47 with explicit version-46 rejection.

Alternative: adjust cache timings or fill the neighbouring word by a direct
memory read. Rejected because it would preserve wrong retained instructions
or bypass visible bus arbitration. The signal-driven holding-register design
and additional snapshot break need user agreement before production changes.

The user approved the bounded signal-driven MC68020/68EC020 correction and
version-47 snapshot break on 2026-10-05. Production work now proceeds within
that design; later CPU bindings remain unchanged.

## Completed MC68020 prefetch verification

The original functional probe now retains MOVEQ #1,D7 with the cache both
on and off. Four directed tests cover all port widths, compatibility responses,
every partial byte phase and completed holding-register replay, low-word entry,
complete warm lines, freeze, program space and reset. The unchanged odd-target
regressions still pass. Across five CPU crates, 460 release tests pass with
18 explicitly ignored fixture cases. The A1200 machine and Amiga runtime run
adds 305 passes across 42 targets with 31 ignored cases: 765 unique passing
release tests, not double-counting the separately rerun snapshot target.
All 40 runtime snapshots pass, including split ROM prefetch and held data.
Both separately invoked Test Kit gates pass. Strict boot images match without
requalification; strict Clippy, formatting and native release build pass.
Logs, source hashes and scope are recorded in
`/private/tmp/emu198x-prefetch-probe/verification.json`.

The first CPU run found four RTE tests that observed PC before the old external
sibling fetch, but now after the internal holding hit: `left: 4104 right: 4102`
(or `left: 12292 right: 12290`). They now assert the return opcode and the
following word's address, preserving their actual return/frame invariant.
The indexed-MOVE timing characterization also changed: `left: 17 right: 13`.
Its extra compatibility phase is now explicitly asserted as two program reads;
the clock characterization includes that issue/three-clock phase. This is not
an assertion of silicon-perfect total instruction timing.

The first Test Kit invocation used relative ROM paths from the test crate and
failed with `EMU198X_AMIGA_KICKSTART_13_ROM does not name a readable file:
../roms/kick13.rom` and the analogous A1200 message. Absolute paths rerun both
gates successfully; the original setup failure remains in `test-kit.log`.
No expected image or CPU functional outcome was updated to hide a mismatch.

## Copper guest investigation

`/private/tmp/emu198x-copper-blitwait-probe/` builds paired project-authored
ADF guests. Each has 48 rows spanning eight blit lengths, three horizontal
start positions and BLTPRI off/on. One WAIT checks completion (BFD=0); its
paired control ignores completion (BFD=1). The capture accepts READY identities
and three adjacent fields (guest counters 9–11), hashes ADF/source data and
compares the full source-defined common raster. A positive marker-content
assertion caught the first guest's incorrect Copper DMA enable mask before
any result was accepted. The corrected guest uses $82C0. No Copper production
change has been made.

## Proposed Copper WAIT idle-stage correction

The corrected AGA PAL guest produces positive red markers in both emulators.
Native READY memory confirms its SPHX magic, case identity and field counter;
registered FS-UAE captures confirm the same identities at adjacent guest
fields 9, 10 and 11. Comparing every pixel in the fixed full common raster
fails in all six fields, without alignment search or interior masking.

The BFD=1 control has exactly 1,536 different pixels per field. All 48 colour
edges are 16 full-resolution pixels (two CCKs) early, in each of the two output
rows per source line. BFD=0 has 22,512 different pixels per field with a
size-dependent displacement, so its additional discrepancy is not yet assigned
to wake-up or DMA scheduling. Preserve it as a separate failing investigation.

Registered FS-UAE `custom.cpp` has `COP_wait_in2` (first free idle cell) then
`COP_wait1` (second free idle/comparison cell). Registered vAmiga
`CopperEvents.cpp` has `COP_WAIT1` followed by `COP_WAIT2`, scheduled two CCKs
apart. Our live `common-commodore-amiga/src/copper.rs` has only one eligible
post-decode decision cell. This explains the isolated BFD=1 control error.

Recommended bounded design: extend the existing pending WAIT state with its
idle phase, preserve it in snapshots, and evaluate the live condition at the
second eligible cell. Internal idle stages require a free Copper cell but do
not allocate the bus. Keep the existing completion observer and persistent
wake path pending their separate trace; do not silently revise SKIP sampling
based on the WAIT-only guest. This is an extension of the existing pipeline,
not a new scheduler. It requires snapshot version 48, rejecting version 47.
Alternative: add a fixed delay to colour writes. Rejected because the fault
precedes the next instruction fetch and applies to non-colour instructions.

Files: live Copper, shared Copper tests, runtime snapshot envelope/replay,
Copper comparison decision, primary Amiga observations and a durable guest
builder. Verification: the BFD=1 full-raster control must become exact; direct
phase and bus-availability tests, snapshot replay at both stages, existing
ordinary WAIT and SKIP tests, prior video corpora, boot/Test Kit/build/Clippy.
The BFD=0 guest stays an explicit failing boundary until separately explained.
This additional pipeline and snapshot design requires user agreement before
production edits. Diagnostics and comparison are in
`/private/tmp/emu198x-copper-blitwait-probe/`.

## Independently reproduced area-blitter rate fault

While the WAIT design request is pending, the separate
`/private/tmp/emu198x-area-dma-probe/` drives the live Agnus with no contention,
D-only constant-output mode, no fill and eight words. After the separately
handled two startup CCKs, real writes occur at CCKs `[1,2,3,4,5,6,7,10]`.
The first six inter-word periods are all one CCK. The last write includes the
existing pending-D completion tail and is not used to measure steady rate.
The probe exits 1 and checks eight actual writes plus completion, rather than
a diagnostic remaining-count estimate.

The primary HRM printed p193 requires a minimum four system ticks per area
word (two CCKs). Registered vAmiga's live `copyBlitInstr[1][0][0]` starts
with internal HOLD_D/BUSIDLE then WRITE_D/REPEAT. FS-UAE's obsolete, compiled-out
diagram independently describes this pair but is corroboration only; active
vAmiga table and the primary manual establish the missing idle
stage. Our area word state currently offers WriteD immediately once absent
read channels are marked complete. It has no per-word idle stage, unlike the
now-corrected line state.

This explains why the full BFD=0 raster disagreement grows with blit length,
although it does not yet prove the precise wake-up offset or every DMA pattern.
No area production change is made. A future bounded stage design must preserve
the validated pending-D/IRQ/observer tail and check all channel combinations,
fill-dependent extra stages, bus availability, and serialized continuation.
Keep this distinct from the currently proposed two-cell WAIT correction.

The user approved the bounded WAIT idle-stage extension and snapshot version
48 on 2026-10-05. SKIP and persistent completion wake remain outside that
production change.

## WAIT-stage verification

The BFD=1 control now has zero mismatched pixels across all three full common
reference fields. The BFD=0 case remains at 22,512 differing pixels in each
field; the durable comparator explicitly selects either case and must exit 1
for this known boundary. Its native READY, red-marker, ADF/source, reference
identity and adjacent-field guards all run before comparison. Rebuilding the
durable guests produces byte-identical ADFs to the independently captured ones.

The broad five-crate Amiga release run passes 702 tests across 137 targets,
with 121 explicitly ignored fixtures/history/diagnostics. It includes 41
runtime snapshot tests, the two new direct Copper phase tests and unchanged
SKIP tests. Strict boot goldens match; both separately invoked Test Kit gates
pass. Native release build, strict Clippy and formatting pass. The first unit
run failed the three old one-decision-cell expectations, including
`3rd eligible CCK enters waiting (HRM's 3-cycle rule)`; these tests now check
two actual fetch cells and two free idle cells, without equating the manual's
aggregate memory-cycle count with internal eligible-cell count.

The first prior-video rerun failed 102/384 comparisons at the old fixed
180-frame capture point. A failing large guest showed the ROM boot-screen
colour rather than its authored picture. At 360 frames, its READY memory
contains the exact case identity and completed field counter 179, and the
previous picture matches again. The guarded rerun checks native READY magic,
identity and counter >=9 for all 128 guests before accepting any raster.
Original failed results remain in `prior-video.json`; later guarded results
are stored separately in `prior-video-ready.json`. No production change or
expected-image update was made to address the premature capture.

A compiled adapter for all 32 active vAmiga area programs (16 channel-enable
patterns, fill off/on) confirms the primary manual's stage counts, including
fill's additional idle stage for D without C. This is source-table execution,
not a complete reference-emulator DMA trace. It is retained separately in
`/private/tmp/emu198x-area-dma-probe/reference-schedule.json` for the next
area-blitter design. Production area stages remain unchanged.

## Proposed next area-blitter stage correction

The independent D-only live probe fails before any area production change:
six steady-state write intervals are one CCK instead of two. The registered
active vAmiga table adapter executes all 32 channel/fill programs and retains
the actual flags, not just a restatement of our remaining-count formula.
The live area engine currently requests only enabled reads and D, or one
internal operation when all channels are off. This cannot represent the
source-defined free idle, holding and result stages.

Recommended design: extend the existing Agnus area word/runtime stages with
explicit channel/fill phases and retained holding/pending-result state. Route
A/B/C/D through the existing operations; route source-defined idle stages
through the existing free-cell admission path while yielding the physical bus
to the CPU. Preserve the shared scheduler and separately modelled final-D,
IRQ and busy observer responsibilities, verifying their edges against the
new real transfer schedule. No instruction-level blit, memory peek, extra
clock loop, dependency or new scheduler is introduced.

The saved area phase/result requires snapshot version 49, rejecting version
48. A D-only timing patch is the alternative; it is incomplete because the
same representation also lacks other channel/fill stages. Do not increase a
remaining-cycle diagnostic or add elapsed delays as a substitute for actual
bus operations and timed result state.

Files: `commodore-agnus-ocs/src/agnus.rs`, area/blitter/fill/collision tests,
shared-driver tests if arbitration needs an admission adjustment, runtime
snapshot envelope/replay/queries, blitter completion/area phase decisions,
primary area observations and the durable Copper/blitter guest diagnostics.

Verification: execute and compare actual requests and transfer CCKs across
all 32 patterns; verify A/B/C fetch/holding/mask/shift/minterm and D contents,
descending modulos, fill carry and BZERO; test occupied DMA cells versus
CPU-usable idle cells, startup and final-D/INTREQ/BBUSY ordering; replay every
saved phase. Re-run the BFD=0 full-raster guest and trace any remaining wake
error rather than changing expected images. Strict boots, prior full-raster
video corpus, Test Kit, release tests/build/Clippy are required before the
next independent production correction. The user approved this design and
version 49 on 2026-10-05; implementation and validation are in progress.

The completed READY-guarded rerun passes all 384 prior reference fields. With
the three new BFD=1 controls, 387 full-raster comparisons cover 335,872,656
RGB samples with zero differences. The separate three BFD=0 failures remain
explicit. Source/log/binary/report hashes and bounds are recorded in
`/private/tmp/emu198x-copper-blitwait-probe/verification.json`.


## Area pipeline implementation and verification — version 49

The approved area correction is implemented in the existing Agnus scheduler.
All 32 compiled channel/fill main programs agree with actual requests,
transfers and physical bus ownership over four words. The first D cell is
locked; following D transfers consume the preceding held result. Free idle
cells can admit CPU work but still stall on occupied DMA cells. Source and
output row counters are separate. The live D-only probe now writes at CCKs
4, 6, 8, 10, 12, 14, 16 and 18 after startup: every interval is two CCKs.

Six directed tests cover the full source schedule matrix, overlapping masked
A shifts, descending independent channel modulos, fill carry reload with and
without D, held disabled B versus fetched B shifting, and denied idle-cell
admission. Runtime snapshot replay visits every unprimed/primed channel or
fill phase for ABCD, ABD fill and D-only fill, plus both final-D drain phases.
Version 49 rejects version 48 before payload decoding.

The broad release run initially exposed five stale machine arbitration setups:
they assumed draining startup immediately offered a physical D transfer.
The new first-word lock instead offered a free phase. The corrected setups
prime the source/result pipeline and positively assert a real WriteD request
and bus requirement before checking CPU priority. The same-feature six-library
rerun and final area target replace those exact targets in the aggregate:
879 passing tests across 153 targets, 121 ignored. The original failed logs
are retained. The all-target strict Clippy gate, native release build, all 42
snapshot tests, six strict real boot cases and both explicit Test Kit profiles
pass. No golden images were requalified.

The paired full-raster guest control remains exact in all three reference
fields. The BFD=0 mismatch falls from 22,512 to 1,344 pixels per field. Its
42 differing programmed marker starts are exactly 16 full-resolution pixels
(two CCKs) early; six match. This remaining completion/wake boundary must be
traced independently before another production correction. FS-UAE's
`blitter_done_notify` returns COP_bltwait to COP_wait1; that stage requires a
free comparison cell before COP_wait requests IR1. The live persistent WAIT
path resumes on a condition checked every CCK before the eligible-cell gate.
This is a candidate cause, not yet an independently traced absolute finish/
wake proof. Do not fit a colour delay or change the expected reference image.

The paired guest builder was rerun after updating diagnostic status text;
both ADFs and assembly sources remain byte-identical to the captured
reference inputs. The BFD=0 comparator remains deliberately failing and
unadmitted. New primary observations and the area-pipeline decision record
the reference evidence and limits. Final logs and hashes live under
`/private/tmp/emu198x-area-dma-probe/`.


Final area verification: all 128 prior guests and 384 reference fields pass
with READY guards, fixed producer origins and no interior masks. With the
three BFD=1 controls, 387 full-raster fields cover 335,872,656 RGB samples
with zero differences. The three BFD=0 fields remain separate failures at
1,344 pixels each. Source/binary/log/report hashes and positive count guards
are recorded in `/private/tmp/emu198x-area-dma-probe/verification.json`.

The initial corpus run stopped with exit 101 and an empty native log.
The identical binary/script succeeded on retry, with exact reference pixels;
no production correction was made for that interruption. Completed captures
were preserved, and only incomplete captures were regenerated before the
whole manifest was revalidated. The original failure log remains recorded.
Eight older playfield manifest entries lack builder ADF hashes. Their current
ADFs were positively checked against the frozen version-48 capture report,
whose own hash was checked against its verification record; the other 120
also match builder hashes. All 384 raw reference fields and metadata remain
identical to that frozen report. Missing provenance was not accepted silently.

### Completion-dependent Copper WAIT trace

Trace the remaining version-49 mismatch without changing production timing.
Preserve the current source and executable hashes, paired guest inputs and
three-field reference captures. Use a temporary native runtime runner and an
environment-guarded trace in the writable FS-UAE copy; do not edit vendored
sources. Record BLTSIZE, final destination transfer, completion notification,
Copper comparison/request states and COLOR00 with absolute beam coordinates.
Check all 48 programmed rows and the BFD=1 control with positive event counts.
Compare those boundaries before attributing the missing two CCKs to blitter
completion or Copper wake. Save logs and provenance under
`/private/tmp/emu198x-copper-wake-trace/`, restore temporary reference logging,
and record the established cause and any bounded design needed for a fix.

### Completion-dependent WAIT trace results

The version-49 trace is complete without a production timing change. Evidence
and provenance: `/private/tmp/emu198x-copper-wake-trace/verification.json`.
The analyser checks 96 unique programmed rows, 3,060 actual D writes and six
byte-identical traced/untraced reference fields. The exactness check correctly
fails with `FAIL: 48 completion-dependent Copper MOVE intervals differ from reference`.
All 48 BFD=1 dispatch-to-MOVE intervals are exact; all 48 BFD=0 intervals are
two CCKs early. The six apparently exact visible starts are hidden by blanking
(first red x=4 on both sides), not independent timing successes.

Forty-four BFD=0 busy-idle elapsed boundaries match, but native idle-to-MOVE
is four CCKs versus six. FS-UAE completion wakes COP_bltwait into COP_wait1,
requires a free comparison, then requests/processes IR1 and IR2. Native clears
persistent waiting before eligible-cell admission and immediately returns to
fetch cadence. This locates the missing wake/comparison boundary. Rows
6/21/30/45 also show busy idle one CCK early at the line boundary; their
idle-to-MOVE interval is five versus six. That admission/start discrepancy
requires separate tracing before closing the fix. Do not globally extend busy
or add a colour-output delay: 44 busy boundaries are already exact.

Actual final-D dispatch-relative elapsed timing is one CCK early in 44 rows
and two early in the four boundary rows. FS-UAE's one-CCK pipelined BLTSIZE
start is directly observed. Native busy retention compensates this in most
rows; a correct colour edge alone would not validate D DMA phase. The next
bounded design should preserve free comparison/wake stages and investigate
start/admission at refresh before changing the saved pipeline.

Primary observation record:
`198x/reference/by-system/commodore-amiga/2026-copper-blitter-wake-observations.md`.
Temporary reference logging and runnable executable have been restored with
baseline hash checks. Original temporary trace build failure (missing forward
declaration), launch failure outside FS-UAE's resource directory and native
runner dependency-cache failure remain in the artifact folder; corrected
retries passed without changing production code. Native traces observe field
280 and reference traces field 9 of the same steady guest, not simultaneous
fields or a physical hardware trace. Snapshot schema remains 49.

### Proposed completion/wake correction — approval pending

The additional request/refresh trace positively checks all 48 BFD=0 rows,
1,530 real D writes and three unchanged raw fields. Every actual reference
D write follows an admitted D request by one CCK. The native chip services
an admitted operation directly in `tick_blitter_cck`. The reference also
keeps admitted requests in flight while refresh prevents new admissions.
The four early busy inputs cannot be closed by adding a colour delay, moving
all busy holds, or accepting blanked markers as timing passes. Artifacts:
`/private/tmp/emu198x-copper-wake-trace/bfd-wait-admission/verification.json`.
This establishes the missing request/service distinction; exact porting of
its phase through the existing native slot model still requires executable
checks, rather than assuming that a one-clock output delay alone fixes it.

Recommended design: extend the existing Copper WAIT and Agnus area-blitter
stages. Keep the single Agnus slot authority and master clock. Preserve the
current main channel/fill programs; represent admitted work and completed bus
work as separate saved stages. Capture the issued channel/address and pending
result where required, and account for actual service ownership when granting
the CPU or another DMA client a cell. Distinguish Copper waiting on the beam
from waiting on blitter completion, then run its free wake/comparison phase
before resuming instruction fetch. Do not restart the original WAIT's first
idle phase or apply the completion wake to beam-only waits and SKIP.

This extends current chip pipelines rather than replacing the shared driver
or introducing a second arbiter. If the registered request trace cannot be
represented within those stages without changing other clients' scheduling,
stop and narrow the design rather than silently widening the architecture.
Completion source, BZERO, actual final D, DMACONR and BFD remain separate;
any change to their binding offsets needs explicit evidence and an updated
completion decision. The saved stages are not reconstructed from memory,
beam position, pointer differences or an observed busy flag.

Exact implementation surfaces, in small verified steps:

1. `crates/common-commodore-amiga/src/copper.rs`: preserve the blocked reason
   and free wake/comparison stage; add red/green cycle tests for even/odd
   completion, unavailable cells, live re-comparison and COPJMP cancellation.
   Retain independent beam-only and BFD=1 controls.
2. `crates/commodore-agnus-ocs/src/agnus.rs` and its area/startup/completion
   integration tests: separate request admission from service within existing
   area stages. Positively compare all 1,530 D writes, busy boundaries and
   Copper events for all 48 rows, including the four boundary rows. Retain
   all 32 channel/fill schedules, data and bus-ownership invariants.
3. `crates/common-commodore-amiga/src/driver.rs` and machine integration tests:
   consume the saved chip stages through the existing slot plan, and prove
   no double owner, no extra tick and correct CPU arbitration. Register writes
   remain live; do not drain the blitter synchronously.
4. `crates/runtime-commodore-amiga/src/snapshot.rs`, `src/queries.rs`, and
   `tests/snapshot_roundtrip.rs`: expose and persist each new stage. Advance
   the envelope to version 50, rejecting version 49 before payload decoding.
   Replay snapshots at blocked WAIT, wake comparison, admitted request,
   completed transfer and final drain; check emitted DMA and MOVE streams,
   not only restored fields.
5. Build the native binary, run relevant Rust tests and strict Clippy, then
   capture the paired guests with READY guards. Require all six full-raster
   fields and all 96 MOVE intervals to pass, with actual DMA and busy timing
   independently checked. Recheck registered boot/Test Kit gates and the
   prior 387 exact raster fields. Do not requalify goldens or fitted origins.
   Record primary observations and amend the affected decision records only
   to the extent established by those checks.

Alternative: correct and snapshot the Copper wake phase first, leaving the
four busy/admission discrepancies explicitly failing for the next chip
correction. This is smaller, but a green colour raster could hide the remaining
DMA timing fault. The combined existing-stage extension is recommended because
the user requested both boundaries and accuracy requires checking both.

Approval is needed for the additional saved chip state and rejection of
version-49 saves under the supplied AGENTS.md requirement to agree
"Breaking changes to APIs or data schemas". No production timing or schema
has changed during this design step.

The user approved the proposed existing-stage extension and version-50 save
schema. Implement the wake correction and prove request/service admission
within the single slot authority before claiming either boundary closed.

### Approved wake implementation and DMA scope boundary

The saved Copper blocked reason and free wake comparison now pass the live
96-row MOVE timing check. The original new six-row component regression
failed with `wake/comparison must yield the bus at 12`, then passed after the
correction. All 48 BFD=1 and all 48 BFD=0 MOVE intervals are now exact. This
is not closure of blitter timing: the independent BFD input check still finds
rows 6/21/30/45 one CCK early, and actual D timing remains separately reported.
Snapshot schema is 50; version 49 is rejected. Verification results follow below.

The approved design's stop condition applies to the DMA extension. Merely
queuing a D write for the next CCK under current admission would let a write
accepted at h=0 retire at h=1, where the current authority reserves refresh.
Allowing both would violate the single-owner rule. Holding it until another
free service cell loses the reference's admitted-request semantics. The
reference instead arbitrates requests one CCK ahead of service: a refresh
request blocks a *new* blitter request while a previously admitted blitter
transfer can still complete. The current driver computes one immediate plan
and dispatches other DMA clients in that same CCK. Correctly representing
in-flight ownership requires their request/service boundaries too. Do not
silently introduce a second arbiter or retime only the observed red edge.

Proposed broader design, pending agreement: extend the shared scheduler's
existing frozen plan with a saved one-CCK request/service latch, owned by the
single Agnus authority. The latch retains the admitted owner, channel/address
and required transfer metadata, then services it on the next master-derived
CCK before new requests compete. Refresh, Copper, bitplane, sprite, disk,
audio and blitter requests share that authority; CPU pins compete at the
request boundary and cannot overwrite an admitted transfer at service. Keep
physical beam/display geometry and the live CPU pin interface. Register
writes affect future admissions, not an already saved owner. Carry the new
state in the already approved version-50 envelope. Reconcile source-finish,
BZERO and the observer holds against the raw event trace before updating the
binding completion table.

This broadens the scheduler portion of step 3 beyond the approved area-stage
extension and affects the timing of other DMA clients. The original approved
plan explicitly says to stop and narrow when that is required. The change
therefore needs agreement under the supplied AGENTS.md rules about new
architectural patterns and significant deviations from existing conventions.
The alternative is to retain the independently verified wake correction and
keep the four DMA/busy failures open while planning the wider scheduler work.
No production blitter or other-client timing has changed at this boundary.


### Wake correction verification

The six-package release run passed 882 tests across 154 targets, with zero
failures and 121 ignored tests. The final targeted run additionally verified
the current three Copper integration tests and all 43 snapshot tests, including
the blocked reason, pending wake comparison and rejection of version 49.
Both explicitly enabled AmigaTestKit video profiles passed. Strict release
Clippy for the seven affected machine/runtime/native packages, formatting and
diff checks passed.

All 128 prior diagnostic guests were recaptured with READY identity/counter
guards. Their 384 reference fields retain identical raw bytes and metadata;
all 128 ADF hashes agree with the frozen provenance (120 builder manifest
hashes and eight frozen capture-input hashes). Adding both paired WAIT guests
gives 390 exact full-raster fields, comparing 338,476,320 RGB pixels without
fitted origins or golden replacement. All 96 paired MOVE intervals are exact.

The independent strict DMA check deliberately still exits 1:
`FAIL: 96 rows retain DMA or busy timing differences`. All actual D addresses,
data and write counts were positively checked. Four BFD=0 busy inputs remain
one CCK early; the BFD=1 controls also retain six early and six late busy
boundaries. D-transfer phase differences remain in both cases. Neither the
shared driver nor production Agnus changed during this wake correction.
These results close the bounded Copper correction, not the requested DMA
boundary. Broader scheduler agreement remains pending.

Evidence and hashes: `/private/tmp/emu198x-copper-wake-fix/`, including
`regression.log`, `final-targets.log`, `test-kit.log`, `final-clippy.log`,
`prior-video-ready.json`, `input-provenance.json`, paired verification reports,
`trace-results.json` and the deliberately failing `dma-red.log`.


### Shared request/service extension approved

The user approved extending the shared DMA scheduler. The one Agnus authority,
one-master-clock rule and CPU pin interface remain binding; the request and
service stages are distinct saved state, carried in the approved version 50.

Implementation sequence:

1. Audit the concrete transfer stages in `common-commodore-amiga/src/driver.rs`,
   `commodore-agnus-ocs/src/agnus.rs`, the ECS/AGA wrappers, Copper, Paula audio
   and the three machine adapters. Compare admission/service events with the
   registered FS-UAE trace and Minimig pipeline. Save current files as a
   rollback baseline before production changes.
2. Add a red regression for request admission across refresh, retained owner
   after register writes and service without a second arbitration. Extend
   Agnus's existing frozen plan to retain the transfer stage. Service the old
   request and admit the new one exactly once per CCK in the shared driver.
   Preserve admitted channel/address and transfer metadata; no speculative
   extra chip ticks or per-client competing slot authority.
3. Carry the stage through the three concrete machine adapters and CPU
   ownership checks. Preserve bitplane/sprite output timing through the
   request/service boundary and keep Paula rotational/audio clocks separate
   from memory service. Test live register changes and CPU contention.
4. Extend runtime diagnostics and snapshot replay for admitted and serviced
   transfers. Check exact event streams after restore and retain rejection of
   version 49. Update the binding slot/completion decisions only where
   measured evidence supports the change.
5. Require the independent DMA/busy/MOVE trace, all channel/fill schedules,
   machine regression/boot/Test Kit tests, strict Clippy and full-raster
   reference corpus. A raster pass alone cannot close DMA timing. Record
   any remaining limitation explicitly; do not promote native goldens.


### Reservation and address stages found in the wider trace

The original uniform one-CCK request/service proposal is incomplete. A new
registered FS-UAE trace positively pairs 3,514 reservations with service,
including 2,900 bitplane, 34 sprite, 435 refresh and 145 strobe requests.
Bitplane/sprite reservation occurs two CCKs before service. Their pointer is
sampled in the intervening addressing stage and retained until service.
Refresh/strobe enter directly at that addressing stage and service one CCK
later. All three raw reference fields and their metadata are unchanged by
the instrumentation. The earlier blitter trace separately proves its
one-CCK admission/service interval. Disk/audio/Copper use the same source
entry point; this new guest does not exercise those channels. Do not claim
dynamic closure for them from this trace.

A strict uniform-latency check must fail on all 2,934 display requests. Merely
moving every channel through one saved latch would shift already-validated
video timing and sample display pointers at the wrong event. The shared
scheduler needs reservation, address/admission and service boundaries, not
a uniform delayed dispatch. This is a significant deviation from the agreed
one-CCK latch and needs design agreement before the wider timing change.

The authorized service-stage foundation is implemented first: the complete
physical plan is saved in Agnus before a client can mutate registers, used
by CPU arbitration across both halves of the CCK, and saved/restored. It
reproduces a separate ownership fault: after a real bitplane transfer and a
later DMA disable, the old CPU service path incorrectly completes a write
in the already-consumed cell (`left: Ready(0), right: Wait`). The corrected
path waits until the next CCK, including after phase-one restore. A second
check covers every DMA owner and retained plan serialization; a duplicate
service admission is rejected. This foundation does not change the earlier
blitter request/service timings and is not closure of that fault.

Approved revised design (user approval, 2026-10-06):

1. Retain the saved current service plan and per-client actual-use latches.
   Extend the same Agnus authority with two future stage entries: display
   reservation and address/admission. A stage entry identifies its service
   cell; positional priority and CPU competition operate on that entry.
   Display reservation prevents a later lower-priority request from taking
   the same future cell. No independently recomputed second slot authority.
2. Display reservation stores plane/sprite identity and operation metadata.
   The next CCK samples its address and applicable modulo at the addressing
   boundary. Other DMA clients enter this addressing stage with their
   admitted address and operation. Preserve an immutable transfer descriptor
   through service; do not retain entire mutable chip copies or read memory
   early to manufacture a future result.
3. Each master-derived CCK services the outgoing descriptor once, advances
   the display reservation into addressing and admits eligible new requests
   in the evidence-backed reference order. Copper comparison/internal
   blitter progress remain distinct from allocating a memory transfer.
   CPU pins compete at admission and cannot overwrite the service owner.
   Beam/render geometry remains physical; no fitted origin or extra ticks.
4. Update the concrete Copper, bitplane, sprite, audio, disk and blitter
   adapters to consume their saved descriptor. Preserve logical main/result
   stages separately from memory retirement and observer holds. Retain the
   approved version-50 schema, serialize both future entries, and replay
   snapshots at each boundary against emitted transfers.
5. Require all 96 paired MOVE intervals, actual transfer and busy boundaries,
   both entry latencies and register-write/CPU contention tests. Recheck all
   32 channel/fill schedules, boot/Test Kit gates and 390 exact reference
   fields. Keep software-reference scope distinct from silicon validation.

Alternative: retain only the verified service-ownership correction and defer
the broader request pipeline. This leaves the known blitter timing failures
open. No speculative uniform-delay implementation was attempted.

Artifacts: `/private/tmp/emu198x-dma-request-service/`, including reference
trace, producer/baseline hashes, `request-stage-results.json`, unchanged raw
fields, service red/green logs and complete current crate rollback baselines.


Service-stage verification completed: the required-asset six-package release
run passes 886 tests across 155 targets, with zero failures and 121 ignored
tests. All 43 runtime snapshot tests pass. Strict release Clippy for the
seven machine/runtime/native packages, the native release build, formatting
and diff checks pass. The rebuilt native producer passes all six paired
WAIT full-raster fields. The refreshed actual-event trace retains all 96
exact MOVE intervals and all 3,060 positively checked D writes. Its strict
DMA check still exits 1 with `FAIL: 96 rows retain DMA or busy timing
differences`; the BFD=0 four early inputs and BFD=1 six early/six late inputs
remain unchanged. The service-ownership fix does not claim to close request
latency. The prior 384-field corpus was validated before this service-stage
change; it has not been recaptured for this change. The user approved the broader three-stage design on 2026-10-06.
Implementation proceeds within the already approved version-50 schema.

### First transfer-adapter correction within the approved extension

Before future admission is wired, correct the Copper adapter's paired late
read. Exact files: common Copper and its transfer regression, runtime
snapshot comment and replay regression, single-slot authority record,
primary observation and changelog. Registered `COP_read1/read2` establishes
two independent word reads. The authentic red test emits COLOR01 rather than
COLOR00 when RAM changes between the fetches, and fails PC advancement at
the first-word boundary. Retain IR1 in the approved version-50 payload and
read IR2 in its own cell. Verify required-asset six-package tests, snapshot
replay, build/Clippy, six paired rasters and actual transfer-event traces
before proceeding to the shared reservation/address stages. Those future
stages remain approved; this adapter correction does not close their timing.

The same boundary additionally exposed a saved-ownership failure. The old
Copper actual-use flag was skipped by serde. A live-driver IR1 fetch followed
by half-CCK restore incorrectly gives a mature CPU write `Ready(0)` instead
of `Wait`. Preserve that existing flag in version 50 and add
`copper_first_fetch_keeps_its_cell_owned_after_half_cck_restore` to OCS board
tests. The assertion verifies both original and restored CPU service waits
until the next free cell. Re-run snapshot/required-asset tests and Clippy
after this serializer-only correction. Record the capture producer separately
from the final saved-state producer; do not silently relabel earlier captures.

Copper adapter verification is complete. The final required-asset release
run passes 891 tests across 156 targets, zero failures, 121 ignored, including
44 runtime snapshot tests. Strict all-target release Clippy, the native
release build, formatting and diff checks pass. The word-fetch producer
passes all 390 reference fields (338,476,320 RGB pixels, zero differences);
all 128 ADF identities and all reference field/metadata hashes remain
unchanged. Its binary hash stayed fixed throughout that corpus. The later
serializer-only actual-ownership correction has a separately recorded final
producer; all six paired WAIT fields were recaptured and still match. The
2-profile Test Kit run passed before that save-only follow-up.

The event trace still checks all 96 MOVE intervals and 3,060 actual D writes;
its strict DMA negative control exits 1 with `FAIL: 96 rows retain DMA or
busy timing differences`. Preserve that evidence: neither corrected Copper
word reads nor saved ownership closes request/service timing. The full
reservation/address/admission extension remains approved but is not wired
yet. Current artifacts and producer distinctions are recorded in
`/private/tmp/emu198x-dma-request-service/copper-words/verification.json`.

### Separate Alice source finish from final-D bus admission

Current event traces explain two different faults: native D writes happen
in their admission cell; fixed-slot/Copper admission also observes service
ownership instead of the future cell around line boundaries. A further
independent bug is confirmed in the BFD-ignore width-two rows: native F=8,
source S=11, while registered FS-UAE gives S=10 and D=11.
`blitter_next_cycle_always` advances Alice's two-stage finish shifter every
CCK before bus admission. Native `FinalWrite` emits the source only after a
granted write. Contention incorrectly prolongs the busy observer.

Correct that bounded source event first within the approved separation of
logical progress and memory retirement. Exact files: Agnus `agnus.rs`, its
`tests/blitter.rs` regression, completion decision and changelog, primary
observations and this plan. Emit Alice's one-shot source on first entry to
FinalWrite even if the bus grant is denied; retain the pending address/data
and internal busy until actual write. The existing saved finish flag and
observer holds suffice, so keep approved version 50. Verify an authentic
red/green contention regression, restore while source has fired but D waits,
all 32 area schedules and component/machine/runtime release checks. Refresh
the live event trace and six paired rasters. Never call the remaining
request-stage or line-wrap faults fixed by this change.

This bounded correction is verified. Required-asset release checks pass
893 tests across 156 targets, zero failures and 121 ignored, including 45
runtime snapshot tests. All 32 compiled area programs pass. Strict seven-
package all-target Clippy, the native release build, formatting and diff
checks pass. The final contention regression covers one, two and seven
denied final-D cells. Save/restore covers emitted source with D pending,
observer expiry and later writeback without reasserting an acknowledged IRQ.

The paired trace source check fails against the prior producer and passes
against the corrected producer in all six width-two control rows. All 96
MOVE intervals and 3,060 D address/value/origin checks pass; all six paired
rasters remain exact. The strict DMA diagnostic still exits 1 with
`FAIL: 90 rows retain DMA or busy timing differences`, reduced from 96.
The six width-four control and four line-wrap wait rows retain early source
finish from incorrect admission; the remaining D service phase is still
wrong. All 1,530 reference D requests were positively paired with service
one CCK later. Preserve those distinctions while implementing the approved
shared stages. Artifacts and stable producer hashes are recorded under
`/private/tmp/emu198x-dma-completion-phase/`; the larger 384-field corpus and
Test Kit were not recaptured for this bounded source-only correction.

### Wire the approved shared stages

Continue the approved three-stage implementation from the verified Alice
source correction. A fresh six-crate rollback baseline is retained under
`/private/tmp/emu198x-shared-dma-stages/baseline/`.

1. Extend the Agnus-owned state in `commodore-agnus-ocs/src/agnus.rs` with
   typed reservation/address/service entries, defined in `src/dma.rs` and
   exported by `src/lib.rs`. No additional slot decoder belongs in that
   module. Test the independently measured two-CCK display and one-CCK other
   client latencies, immutable captured addresses, and rejected duplicate
   admission. Current service ownership remains authoritative across both
   master/4 phases. Use existing version-50 authorization for the new state.
2. Split transfer admission from service in the existing Copper/blitter and
   display/Paula adapters. Wire the entries into `common-commodore-amiga/src/driver.rs`
   and all three machine `src/lib.rs` implementations. Read memory only in
   service; sample display pointers in addressing. Resolve DDF boundary
   reservation from the registered source before changing live scheduling;
   do not anticipate a future comparator using mutable register values.
3. Extend diagnostics and runtime snapshot replay at each populated boundary.
   Require the independent 96-row timing check to turn green and all 390
   registered raster fields to remain exact before claiming completion.
   Run required-asset tests, strict Clippy/build and Test Kit. A passing pure
   stage test alone does not prove that live transfers use the stages.

#### Additional display-counter boundary found during adapter audit

The registered FS-UAE `drawing.cpp::handle_strobes` resets Denise's own
9-bit horizontal counter to two lores ticks. ECS/AGA reset it on all three
strobes; OCS resets on STRHOR/STRVBL and free-runs through STREQU.
`do_denise_cck` consumes the preceding RGA cell and commits the counter's
next value after its two output ticks. `denise_handle_quick_strobe` explicitly
identifies the refresh offset of three CCKs and pipeline delay of two CCKs.
Native `common-commodore-amiga/src/denise.rs` derives both chip comparison
position and retained raster position from Agnus's current beam instead.
There is no independently serialized strobe-driven Denise counter.

The unchanged `fmode0-offset0` guest positively pairs all 2,900 bitplane
addresses across beam lines 60–204. Native pointer advances occur at h=63,
71,79,...; registered reference reservation/address/service are h=65/66/67,
73/74/75,... . All service-counter differences are four CCKs, while existing
rasters match. This is a measured difference between the two counter views,
not proof that adding a fitted four-CCK offset is correct. Source corroborates
why a missing independent counter can be masked by early transfers. Artifacts,
ADF identity and trace hashes are retained in
`/private/tmp/emu198x-shared-dma-stages/display-trace/paired-display-events.json`.

Proposed necessary extension to the approved Agnus stage design:

- Extend the existing common/concrete Denise state with its own 9-bit output
  counter and strobe propagation/next-counter state. Drive it on the same
  master-derived output ticks; model OCS STREQU free-running separately.
- Carry the real strobe operation in the shared DMA descriptor and existing
  Denise register stage. Use that counter for Denise comparisons and raster
  projection; retain Agnus's actual counter for DMA, Copper and VHPOSR. Keep
  the recorded framebuffer origins and reference pixels unchanged.
- Exact files: `commodore-agnus-ocs/src/dma.rs`, shared `driver.rs`/`denise.rs`,
  all three machine adapters, concrete Denise OCS/ECS/AGA dispatch as required,
  runtime diagnostics/snapshot replay, and a binding decision for this counter
  boundary. Extend the ongoing approved version-50 payload with this execution
  state; do not ship an intermediate version-50 layout as a compatibility claim.
- First validate strobe-to-counter transitions against the registered source
  and independent trace, including OCS STREQU, line wrap and restored pending
  reset. Then wire all transfers and require the strict 96-row timing and
  unchanged 390-field raster gates together.

This replaces the current Agnus-derived display-coordinate convention and
adds saved Denise execution state beyond the two Agnus future entries in the
approved plan. The extension was approved on 2026-10-06: “Extend the Denise
counter and strobe stages (recommended)”. The shared live integration remains
required; isolated counter tests do not close the DMA timing defect.
Do not emulate the counter with a constant subtraction or image-fitted offset.

#### Saved Denise stage implementation, 2026-10-06

`common-commodore-amiga/src/denise_counter.rs` now retains current/next nine-bit
positions, incoming and normal-RGA strobes, and the two-output-tick commit phase.
The existing Denise wrapper owns and serializes it; OCS/ECS/AGA select their
STREQU reset policy through the existing chip trait. Agnus carries typed strobe
identity in the shared descriptor. The board diagnostic and query surface expose
all counter stage fields. The ongoing version-50 candidate validation rejects
invalid saved counter values.

Counter tests check the pinned source's strobe service -> normal RGA -> commit
boundary, wrap and restored incoming/pending/half-CCK state. Temporarily disabling
reset makes three tests fail (exit 101); restored code passes. Serialized wrapper
replay verifies all three concrete Denise policies. A full-suite diagnostic test
correctly went red when its old exhaustive field list omitted the counter; it is
extended to verify grouped/leaf-query agreement for every counter stage field.

This is saved stage implementation, **not live adapter closure**. The renderer
and driver still use the old DMA/display path. Do not mark the 90 timing rows
closed or claim newly verified 390-field output until the full live wiring passes.
The next change connects the real strobe and output clock along with display and
other DMA request/address/service adapters. Keep the framebuffer origins fixed.

An additional audit positively pairs 192 Copper MOVEs in each of the two prior
completion traces, by vpos/register/value. All 384 horizontal-position differences
are four, consistent with the bitplane counter-view observation. The independent
relative timing failures remain. Source selection must preserve `get_strobe_reg`'s
latched VE/VB inputs and the OCS/ECS first-line distinction; deriving STREQU from
the coarse native `vertb_level()` predicate would not reproduce the reference.
Counts and original trace hashes are in
`/private/tmp/emu198x-shared-dma-stages/display-trace/paired-copper-events.json`.

Final saved-stage verification: **906 tests passed across 157 targets, zero
failed, 121 ignored**, with required golden assets enabled. Strict seven-package
Clippy, native release build, formatting and whitespace checks pass. The earlier
exhaustive diagnostic failure is corrected and the complete suite rerun. Source
hashes, native producer hash, command statuses and the explicit live-integration
limit are retained in `/private/tmp/emu198x-shared-dma-stages/counter-verification.json`.

#### Live strobe retirement and output clock, 2026-10-06

Connect the first saved transfer target to the real driver before introducing
beam-driven request generation. An admitted strobe must retire once on the next
CCK, own its service cell through the single Agnus plan, reach the concrete
Denise wrapper, cross normal RGA, and commit on the existing output clock.
Clock the independent counter inside `Denise::tick_with_output_signals`; retain
the existing raster coordinates until all DMA adapters are connected.

Exact files: shared `driver.rs`/`denise.rs`, `commodore-agnus-ocs/src/agnus.rs`,
all three machine `lib.rs` adapters, runtime snapshot-roundtrip regressions and
the existing board diagnostic test. The tests supply admitted RGA operations
through Agnus's saved address stage, not a separate test-only Denise driver.
Verify all three chipsets, pending-address and half-CCK restores, once-only
retirement, outgoing Refresh ownership and OCS STREQU free-running. First run
the regressions against the unchanged driver and require red, then connect it
and run required-asset checks, strict Clippy and native build.

Automatic strobe selection remains the following adapter step: the registered
source uses latched VE/VB signals and samples selection after counter increment
but before the new position's sync events. A coarse `vertb_level()` range is
insufficient. This first live retirement step does not close the 90 DMA rows
or claim the complete bus/raster correction. Rollback copies are at
`/private/tmp/emu198x-live-strobe-boundary/baseline/`.

The first connected adapter also requires candidate-state validation in
`runtime-commodore-amiga/src/variants.rs`: reject well-typed transfers whose
live adapter is not connected yet, before installing the candidate. Extend
the existing `snapshot.rs` rejection test to cover both invalid identity and
valid-but-unconnected target on all three chipsets, preserving the target.
Reject an unclaimed outgoing service as well: runtime snapshots occur after
atomic chipset retirement, and such a candidate would otherwise fail on the
next CCK. This prevents accepting an execution state the partial live driver
cannot run. The rejection tests preserve the target byte for byte.

Fresh six-field comparisons retain exact pixels against the registered
reference: 5,207,328 RGB pixels, zero mismatches. Both unchanged guests reach
SPHX field counter 278 with the expected case identity. The producer and input
hashes remain unchanged across capture; artifacts are in
`/private/tmp/emu198x-live-strobe-boundary/`. This is a bounded raster check,
not a new full 390-field validation or closure of the 90 timing rows.

Final first-adapter verification: **907 passed across 157 targets, zero failed,
121 ignored**, required golden assets enabled. Strict Clippy and native release
build pass. The final test assertion correction preserves the snapshot API
error prefix; the earlier failure was:
`assertion failed: matches!(&error, MachineError::InvalidSnapshot { reason } if reason == "saved DMA target has no connected live adapter")`.

The independent temporary reference probe positively pairs all 37,241 request
and service events in order (line numbers can repeat across reset). Every
request is at h=2 and its matching service at h=3 with identical register and
vertical position. The output-counter range gate **failed**:
`AssertionError` after only one positively paired reset row, against a required
minimum of 1,001. That output sampling is not a range validation. Automatic
strobe generation remains pending a corrected output probe. The temporary
reference sources and runnable producer are restored with all four baseline
SHA-256 hashes verified. Detailed results are in
`/private/tmp/emu198x-live-strobe-boundary/verification.json` and
`reference-counter/verification.json` below that directory.

#### Automatic timing strobes, 2026-10-06

First correct the reference output trace. Normal RGA chunks begin at a display
line boundary, so their local CCK index is not the raw Agnus hpos. The previous
probe sampled only local indices 0 through 10, missing ordinary refresh strobes
later in those chunks; fast display paths can also bypass the sampled function.
Trace the actual incoming/pending strobe cells and post-reset counter positions,
disable reference display optimisations through its supported configuration,
and positively join by saved RGA line identity. Compare the unchanged guest
rasters to the original captures, and preserve reference producer/input hashes.

Then extend existing saved Agnus sync stages in `commodore-agnus-ocs/src/agnus.rs`
and ECS timing inputs in `commodore-agnus-ecs/src/lib.rs`, with strobe admission
in the existing shared pipeline. Selection uses latched VE/VB before the
current position sync event; h=2 requests retire at h=3. Test real master-clock
execution and snapshot replay across OCS/ECS/AGA, including equalisation and
blanking edges. All work stays within the approved ongoing private v50 layout.
Run required golden assets, strict Clippy, native build and fixed-origin paired
rasters before accepting the bounded change. The 90 DMA/busy rows remain open.
Rollback sources are in `/private/tmp/emu198x-automatic-strobes/baseline/`.

The corrected reference gate passes for 29,523 requests/services and all 29,520
completed reset rows in its contiguous post-startup interval; three queued
shutdown rows are explicitly excluded. All three original raw guest fields
remain byte-identical. The native baseline fails with
`line 0: automatic request absent or wrong`. An initial test expectation kept
STREQU through line 8; the independent reference requests demonstrate STRVBL
on line 8 for the observed LOF=1 fields, so the expectation is corrected to
line 7. No native sync-stage change was made to fit that expectation.

Implementation files additionally include `runtime-commodore-amiga/src/variants.rs`
for candidate sync-state validation and `snapshot_roundtrip.rs` for automatic
request/service/reset and both-phase restore checks. Existing manually admitted
strobe coverage starts away from the physical automatic request slot so the two
sources cannot collide. Strobe reset commits at the end of h=4, making value 2
the output position at the start of h=5. Pixel projection still uses its previous
counter view; other DMA clients are not yet connected to future service stages.

Reference provenance and the restored original runnable/source hashes are in
`/private/tmp/emu198x-automatic-strobes/`. The revised trace disables supported
display optimisations; no vendored emulator or guest media was modified.

The complete-field extension exposes a real last-line admission error:
`line 311: automatic request absent or wrong`. Reference requests at the final
field line retain STRHOR with VB=2 and P_VE=0; only the next horizontal sync
updates P_VE. Registered `custom_trigger_start` runs at
`HARDWIRED_DMA_TRIGGER_HPOS=1` after that position's horizontal sync. Move
line-held blank-start/end capture to that existing sync stage, after horizontal
latch updates and before the h=2 request; do not derive P_VE immediately from
the new blank-start event. This uses the already approved saved stages.
The revised test checks all 312 native fixed-PAL lines on all three chipsets,
with snapshot replay retained at the first 27 and last three lines. The source
reference's field total is not inferred from this native control's line count.

The earlier broad suite also exposed an invalid HBLANK fixture:
`Denise strobe serviced between output ticks`. The A1200 test forced its
scheduler phase to 1 while leaving Denise in phase 0. Replace that forced
phase with two actual system ticks through the final cell. The unchanged
wide-bitplane-tail pixel assertions now pass in the targeted regression.

Final automatic-strobe verification: **984 tests passed across 159 targets,
zero failed, 121 ignored**, including the ECS component package and 47 runtime
snapshot tests. Required golden assets are enabled. The complete-field
regression passes on OCS/ECS/AGA after the field-end correction. Strict
Clippy and the native release build pass; formatting and whitespace checks pass.
Clippy initially reported `error: manual `!Range::contains` implementation`
in the test's snapshot-selection expression. Use its equivalent range form
and rerun the complete-field regression; no library behaviour changed.

The final native producer's fresh six fixed-origin comparisons are exact:
5,207,328 RGB pixels, zero mismatches. Both unchanged SPHX guests reach field
counter 278 with their expected case identity. Producer, ROM and ADF hashes
are unchanged across capture. All four original temporary reference source/
runnable hashes are restored and verified. Source hashes and command results
are in `/private/tmp/emu198x-automatic-strobes/verification.json`.

This closes automatic delivery of the three resetting timing-register kinds.
Other DMA request/address/service adapters, STRLONG handling and use of the
independent counter for raster projection remain in the wider integration.
The previously measured 90 DMA/busy timing rows stay open. No new full
390-field raster validation is claimed for this bounded change.


### Connect addressed bitplane service (bounded adapter step)

The live driver currently rejects every display address/service entry. Its
legacy Denise fetch reads BPLxPT and FMODE at service, advances the then-live
pointer, and applies modulo at line wrap. Registered `custom.cpp` instead
samples BPLxPT and the selected modulo in `bitplane_rga_ptmod`, then service
reads retained `pv` and writes `pv + fetchmode_bytes + bplmod`. This step
connects the existing typed bitplane descriptor without enabling automatic
reservations or replacing the DDF sequencer yet. Sprite/Paula/Copper/blitter
adapters remain rejected. No new slot authority or clock is introduced.

1. Add the terminal-fetch modulo identity to the approved version-50 display
   reservation in `commodore-agnus-ocs/src/dma.rs`. In `src/agnus.rs`, sample
   the addressed bitplane pointer and modulo (including AGA FMODE bit 14
   line selection), and derive outgoing bitplane ownership from the retained
   service descriptor. Preserve immutable address/increment through service.
2. Extend the existing shared `common-commodore-amiga/src/driver.rs` split
   borrow and all three machine `src/lib.rs` adapters to pass claimed
   bitplane service into Denise's existing output tick. In shared `denise.rs`,
   read RAM only at service using the captured address/width/lanes, update
   BPLxPT from the captured address, and retain fetched words in the existing
   normal RGA stage. Do not retire data one CCK early or apply the legacy
   line-wrap modulo to staged transfers.
3. Extend runtime capability validation in `src/variants.rs` for connected
   bitplane reservations/transfers only. Extend `snapshot_roundtrip.rs` and
   common `tests/dma_request_stages.rs` with pointer/modulo/FMODE rewrites,
   memory changes after address and after service, all widths and chipsets,
   one-time retirement, both CPU phases, and save/replay at each boundary.
4. Prove the unchanged live adapter fails the new regression. Then run the
   required-asset chip/common/machine/runtime suites, strict Clippy, format,
   native build and fresh six-field fixed-origin raster gates. Record exact
   coverage. The existing 90-row timing disagreement and full 390-field
   closure remain open until automatic reservations and all client adapters
   are connected. Rollback copies are under
   `/private/tmp/emu198x-bitplane-service/baseline/`; stop after repeated
   functional failures rather than fitting timing offsets.


#### Correct transfer-width boundary before acceptance

The initial addressed adapter's retained width/lanes assumption is wrong.
Registered service reads live `fetchmode_fmode_bpl` and `fetchmode_bytes`,
and existing `aga_display_register_stage::changing_width_keeps_the_next_selected_slot_but_uses_the_new_transfer_width`
explicitly requires a newly written FMODE width on an already selected slot.
Reservation preserves channel/cadence identity, not a frozen service width.
The two initial live tests passed the proposed retention assertion but do not
validate this boundary; those early results are superseded.

Keep PT and signed MOD immutable after addressing. Change the display transfer
payload's signed field from a combined pointer increment to captured modulo;
service samples the actual width/lanes from the immediate FMODE mirror, reads
those words once, and advances captured PT by actual bytes plus captured MOD.
Fetched payload width/words then remain immutable in Denise's normal RGA
stage. This is a correction within the already approved typed stage design
and ongoing private version-50 schema. No extra stages, clocks or dependencies.
Rework the live regression to fail the initially retained-width implementation,
then require it to pass with FMODE changes before service and after service.
Do not accept the earlier broad-check run as final-source evidence.


#### Addressed bitplane adapter verified

The bounded adapter is connected on OCS, ECS and AGA. Shared Agnus service
ownership derives from the outgoing bitplane descriptor even after DMA is
disabled. Addressing captures BPLxPT and selected signed MOD; service uses
immediate FMODE for actual width/lanes, reads RAM once, and updates PT from
captured PT plus actual bytes and captured MOD. The existing normal Denise
RGA stage preserves those words and width through later RAM/FMODE rewrites.
The next display address sample follows the current service pointer update.
There is no new slot decoder, clock or early read. Runtime restore accepts
connected bitplane stages while rejecting the still-unconnected targets.

Initial snapshot rejection and live adapter panic both went red. A separate
service-time-width regression went red with one word instead of two, then
passed after correcting the proposed retention boundary. The compiled
registered PT/MOD sweep matches all 128 rows at three reservation widths
(384 retained services). The service sweep emits 128 positive rows: native
matches 96 mode-0/1/3 rows, while 32 old-FS-UAE mode-2 rows are recorded as
explicit producer disagreements. The registered old branch uses fetch64 in
mode 2 despite a four-byte increment. The primary Lisa specification and
inspected newer WinUAE branch use the existing two-word page-mode transfer.
No old-reference defect was accepted as a golden. The newer upstream pointer
alignment differences are recorded as a separate investigation, not fixed
by this adapter step.

Final required-asset verification: **988 passed, 0 failed, 121 ignored,
159 targets**, including all 49 runtime snapshot tests. Both live bitplane
replay tests also pass with added assertions that data reaches the actual
Denise holding latch after normal-stage retirement, including post-service
RAM/FMODE rewrites. Strict eight-package all-target Clippy passes after those
assertions; the native release build, Rust/Python formatting, Ruff, and all
three repository whitespace checks pass. Re-extracting both source fixtures
produces byte-identical CSVs with positive coverage and the registered source
hash enforced.

Fresh final native captures (`bitplaneservice50`) have the correct SPHX/case
identity and counter 278 for both BFD guests. All six fixed-origin fields
match **5,207,328 RGB pixels with zero mismatches**. Producer, ROM, media and
changed source hashes are retained and checked; original input files and
vendored reference sources were not modified. Artifacts and consolidated
results: `/private/tmp/emu198x-bitplane-service/verification.json`.

Ordinary guests still use the legacy display grant: automatic display
reservations, other DMA client adapters and counter-based raster projection
remain pending. The ongoing private snapshot payload remains version 50,
rejecting version 49. The 90 previously measured DMA/busy discrepancies
remain open; no new full-390-field or full relative-DMA closure is claimed.
Next connect the evidence-backed DDF reservation sequencer with the remaining
shared admission/service adapters, then require their event and raster gates
together. Do not freeze transfer width at reservation or fit a counter offset.


### Correct overlapping display address/service ordering

The automatic-reservation audit found the preceding adapter's ordering claim
is wrong: both registered FS-UAE and vendored WinUAE `do_cck` call
`bitplane_rga_ptmod` before `handle_rga_out`. The shared driver currently
samples the next address after `denise_tick_with_dma` has completed the
outgoing pointer update. With overlapping same-plane entries and a pointer
rewrite, this captures the outgoing result instead of the middle-stage PT.
Fix this ordering before enabling automatic reservations. No new state,
architecture, dependencies or snapshot version is required.

1. Retain rollback copies under `/private/tmp/emu198x-display-address-order/`.
   Add a live OCS/ECS/AGA regression to
   `runtime-commodore-amiga/tests/snapshot_roundtrip.rs`: address A at 2000
   with MOD -4; reserve B, rewrite PT to 3000 and MOD to +6; on the overlap,
   require B to capture 3000/+6 before A updates PT to 1FFE. Require distinct
   fetched words, actual holding-latch retirement, retained service ownership
   on both phases, and exact snapshot replay at each populated boundary.
   Prove the unchanged driver fails the capture assertion.
2. In `common-commodore-amiga/src/driver.rs`, sample the returned display
   reservation immediately after shared stage advance and before claiming
   outgoing service or servicing any other client. Remove the late sample.
   Compare a compiled reference sampling/service sequence and require the
   live test to pass; preserve normal RGA data retirement and CPU pin timing.
3. Run required-asset suites, strict Clippy, native build and fresh six-field
   fixed-origin comparisons. Correct the previous primary observation and
   binding adapter decision's ordering claim, recording the source evidence.
   The automatic DDF sequencer, remaining client adapters and 90 timing rows
   remain open; do not claim full-390-field closure from this bounded fix.


#### Overlap ordering correction verified

The unchanged live driver captured B=1FFE instead of rewritten PT=3000;
that regression exited 101. The corrected driver samples the returned display
reservation immediately after `begin_dma_cck` and before claiming any outgoing
service. The same regression now passes on OCS/ECS/AGA, checking A/B's distinct
RAM words, actual normal-stage holding-latch retirement, retained ownership
across both phases, and byte-identical replay at every populated boundary.
The previous adapter result did not cover this overlap and its claim that
addressing follows outgoing service is superseded by this correction.

A compiled probe uses the unmodified registered PT/MOD function and pointer
retirement fragment in the call order extracted from `do_cck`. All 24
plane/width rows pass. Reversing the order exits 2 on the overlap assertion.
The probe is not a full machine trace or automatic reservation validation.
Both registered FS-UAE and inspected vendored WinUAE have the early sample
call order. Primary observations and the binding bitplane-stage decision
now record that ordering.

Required-asset suite: **989 passed, 0 failed, 121 ignored, 159 targets**,
including all 50 runtime snapshot tests. Strict eight-package all-target
Clippy, native release build, format and all three repository whitespace
checks pass. Six fresh fixed-origin fields (`addressbeforeout50`) compare
**5,207,328 RGB pixels with zero mismatches**; both SPHX guest identities and
counter 278 are verified. Producer/input and changed source hashes are
unchanged across validation. Consolidated evidence:
`/private/tmp/emu198x-display-address-order/verification.json`.

No new saved field or snapshot version was needed; the ongoing private layout
remains version 50. Automatic reservations, other DMA adapters and independent
counter-based raster projection remain pending. The 90 previously measured
relative DMA/busy rows remain open; no new full-390-field gate is claimed.
The source audit confirms a real DDF activation sequence: even-cycle start
sets pending BPRUN, the next odd comparator edge latches it on, and request
generation precedes comparator evaluation. Preserve these transitions when
connecting automatic display requests; a fitted two-CCK offset is not the
sequencer. Resolve the pending/address ownership interaction with the other
client adapters before enabling that live path.

### Establish executable DDF reservation evidence

Before enabling automatic reservations, compile the registered FS-UAE
`generate_bpl`, `decide_bpl`, `islastbplseq`, `bpl_dma_normal_stop` and
`get_cck_clock` functions unchanged. Preserve their request-before-comparator
order, source fetch tables and state across horizontal wrap. The harness
supplies DMA/vertical inputs and records requests; it does not arbitrate the
whole machine or establish silicon truth.

1. Add `test-data/commodore/amiga/display-dma-sequencer/build-reference.py`
   and provenance/coverage documentation. Require the registered source SHA,
   positive case/request/transition counts, source immutability and a reversed
   call-order negative control. Exercise OCS/ECS/AGA, legal widths/resolutions,
   ordinary and equal windows, hard edges, DMA disable/re-enable, rewritten
   future start and terminal requests across short/long line wrap.
2. Generate immutable request/transition fixtures in that directory, then
   independently regenerate into scratch and compare bytes. Check the basic
   request timeline against the already captured live display trace. Record
   contradictions or old-reference limitations explicitly. Do not derive the
   oracle from Emu198x's endpoint calculation or accept empty output.
3. Run Ruff and harness negative controls; document measured first/last
   request and terminal MOD events in the primary observations. Use these
   rows to specify the bounded sequencer integration next. This corpus-only
   change leaves live scheduling and private save version 50 unchanged.
   It does not close the 90 DMA/busy rows or claim a new raster comparison.

#### DDF reservation corpus verified

The unmodified compiled reference produced 336 cases with 74,577 events,
71,835 reservations and 3,772 terminal-modulo requests. Each case has
positive request coverage. A second independent compilation reproduces both
CSV fixtures and the verification record byte-for-byte. The reversed-order
negative control exits 1 with
`request-before-comparator gate failed: first BPL1 h=64, expected 65`;
a mutated source also exits 1 before compilation. Ruff format/check pass.
The ordinary lores BPL1 request positions match all 2,900 earlier live
reference reservations on 145 lines; this cross-check does not extend the
existing live capture to all 336 externally driven cases.

The source-driven cases retain real run/cycle/stopping/soft/hard state across
wrap, reveal terminal-modulo reservations on the following physical line,
and exercise enhanced restart and multiple regions. The primary observation
records measured examples and limits. The current compressed DDF decisions
remain binding until the approved full live stages replace them; these
software-reference rows alone do not resolve cross-reference or silicon
timing uncertainties.

Next integration must use one shared admission authority for future cells,
retain the sequencer's phase across wrap, sample display PT/MOD before
outgoing service, and retire data with the independent Denise counter.
A standalone shift of the old grants would not satisfy this corpus. No
production Rust files or snapshot layout changed in this corpus-only step.
Private version 50 and the 90 open relative timing rows are unchanged.

### Integrate live future-cell admission and close timing rows

Continue in the engineering-frontier lane within the approved shared
Agnus/Denise stage design and private version 50. Do not stop at another
reference corpus result: run the existing 96-row timing trace on the live
producer and demonstrate a reduction of the 90 open rows before reporting
this task finished.

1. Extend the existing Agnus display stages with saved run, cycle, stop,
   enhanced soft-enable/edge and hard-window state in
   `commodore-agnus-ocs/src/ddf.rs`, exported through the existing chip facade.
   Compare every emitted request and transition to all 336 compiled-reference
   cases, including both line lengths, modulo, repeated regions and replay.
   Keep generated phases tied to the ordinary master-derived CCK.
2. Connect those stages in shared Agnus and the ECS timing seam, preserving
   request-before-comparator order and early PT/MOD addressing. Replace legacy
   display slot ownership only with retained outgoing descriptors. Extend the
   existing single authority to distinguish future admission from outgoing
   memory service, with higher-priority retained requests preventing reuse.
3. Connect actual client address/service adapters in shared driver and chip
   code. Preserve internal blitter results/finish independently of retained
   RAM transfers and Copper compare/WAIT phases independently of fetches.
   Validate/replay the connected saved targets in runtime variants.
4. Project output through the approved strobe-driven Denise counter and remove
   legacy modulo fallback once automatic terminal requests own the update.
   Check fresh fixed-origin fields after each bounded live change; restore
   rollback copies rather than fitting origins or adding observer holds.
5. Build the trace runner from final code, verify SPHX identities, all 96 MOVE
   intervals and 3,060 actual D addresses/values, then count exact DMA/busy rows
   against the unchanged registered captures. Run required-asset suites,
   snapshot replay, strict Clippy/native build and the appropriate full raster
   gates before accepting a timing correction. Preserve every failed attempt
   and stop after repeated functional failures on the same bounded fix.

### Live shared-stage timing result

Connected source-driven display reservation, address sampling and outgoing
service; captured Copper words; queued blitter phases; fixed refresh/disk/audio
admission; and sprite reservations/addressed service. Agnus's retained outgoing
descriptor supplies physical ownership for both CPU phases. Lower-priority
requests inspect the future address cell, independently of outgoing ownership.
The installed original/ECS/AGA timing wrappers supply display and sprite gates.
Denise consumes its saved strobe-driven counter for horizontal output.

The first integrated trace exposed two distinct old assumptions. Parked WAIT
comparisons ran on every CCK instead of the Copper polarity, and BLTSIZE started
in the MOVE cell instead of passing through the reference's one-CCK register
write stage. The source trace positively records MOVE h=98, size-start h=99,
and actual final D service h=107 for the first D-only case. The shared pipeline
now preserves the size strobe in version 50 and clocks it on the ordinary edge.
The returning BFD WAIT comparison is WAIT1 itself; it does not append another
comparison before requesting IR1.

Fresh unchanged-guest runs under `/private/tmp/emu198x-live-dma-integration-final/`
close all 90 previously open DMA/busy rows. All 96 rows now match the registered
reference for every D transfer, source finish, Copper-visible busy release and
BLTSIZE-to-COLOR interval: 3,060 writes with exact address, value and relative
CCK. The strict checker is
`test-data/commodore/amiga/copper-blitter-wait/tools/compare-timing.py`.
It rejects the prior producer, and changing one actual D-write timestamp by one
CCK produces exactly one failing row while retaining all 3,060 writes. Producer
and input hashes are stable across both captures.

The component stage checks also pass all 32 independently compiled channel/fill
programs, eight D-only sizes and restoration at each pending stage. The all-336
display sequencer comparison passed before live integration. Full regression,
native build, strict Clippy, fresh fixed-origin raster, required media and
snapshot gates are still pending; this result closes the measured timing trace,
not the entire integration verification.

### Separate register propagation from retained reservations

The connected 128-guest sweep preserves control fields but exposes mid-line
BPLCON0/FMODE differences. The previous DMA copies folded selected RGA cells
into their delays. Registered `custom.cpp::BPLCON0` queues a two-CCK register
copy; `FMODE` changes fetch cadence immediately. Display reservations already
retain the following two cells in the connected pipeline. Extend the existing
register stages accordingly, retaining the direct endpoint API contract.

1. Add connected register/request tests in
   `common-commodore-amiga/tests/dma_request_stages.rs`: retain a selected
   reservation across a register change, assert register-copy boundaries,
   captured identity and service address, and replay each saved boundary.
   Run before correction to demonstrate the old double delay fails.
2. Correct only `commodore-agnus-ocs/src/agnus.rs` register-copy admission for
   connected stages. Keep existing saved arrays and version 50.
3. Rebuild after the frozen 128-case capture finishes; compare unchanged
   mode-transition/control guests at the same fixed origins, then repeat the
   full raster and timing gates. Do not change reference captures or goldens.

### Connected register result and wrap-conflict design

The register-stage correction passes both previously red connected tests,
with the previous selected display identity retained across address/service
and replay. All 66 formerly failing raster fields are now exact (57,280,608
RGB pixels). Fresh code also retains the 96-row / 3,060-write timing match.
The final complete raster sweep is running under
`/private/tmp/emu198x-live-dma-integration-verified/`, with producer/input
hash checks. The latest broad run still reports 10 failing targets; subsequent
focused runs fix direct endpoint rendering, the colour/size/line snapshot
fixtures, lifecycle publication, disk service and sprite service fixtures.
The integration is not accepted while these remaining gates are red.

A separate confirmed wrap conflict needs agreement before changing the design:
the current immutable descriptor has one target, while registered `write_rga`
combines simultaneous display and refresh RGA/type signals. The existing
HARDDIS machine regression fails at that collision. A compiled unchanged
`write_rga` probe checks 32 plane/fixed-register combinations and rejects a
dropped-fixed-request negative control. Primary observations retain the
source inspection boundary; full live service is still to be measured.

Recommended bounded extension, pending approval:

1. Extend the existing `commodore-agnus-ocs/src/dma.rs` descriptor with combined
   display/fixed RGA signals, retaining a single physical owner. Preserve the
   refresh pointer and concrete combined register/type through address and
   service. Keep the ongoing approved private version-50 envelope.
2. Extend `commodore-agnus-ocs/src/agnus.rs` refresh state and the installed
   ECS/AGA seams to reproduce the reference's register/pointer combination,
   early sampling order and refresh increment/mask. Do not silently drop either
   request or add ticks. Check normal refresh as a positive control.
3. Service the combined target through `common-commodore-amiga/src/driver.rs`
   and the existing display adapter, applying the combined register's actual
   memory/output/pointer effects. Validate it in `runtime-commodore-amiga/src/variants.rs`.
4. Add live reference wrap/collision traces and per-boundary postcard replay;
   compare pointer addresses, output delivery, strobe suppression and both CPU
   phases. Rerun ordinary 96-row timing, the complete unchanged raster corpus,
   required media and all regression/Clippy/build gates.

Further fixture investigation must preserve the source's separate DDF
register-write stage: registered DDFSTOP queues its new value, and DDFSTRT
suppresses its immediate comparator before committing the queued value. Do
not label a same-cell comparator discrepancy a stale fixture until this stage
has been checked in the connected path.

The descriptor/refresh-pointer extension above was approved explicitly on
2026-10-06. Implement only that bounded combination; preserve the uncombined
adapters and keep OCS/AGA Test Kit gradient/crosshatch failures visible.
The pre-combination full raster producer is recorded separately from any
subsequent producer after the saved descriptor extension.

### Live wrap trace: preserve the physical host scan

The full private reference trace preserves all six baseline raster fields
byte-for-byte. Its actual addressed RGA records confirm the original combined
bitplane model: end-of-cycle fixed DMAL arrives before the next PT/MOD sample.
All twelve combined service cells in the three-line trace window agree on
captured address, all four resulting BPLPTs, REFPTR and skipped MOD. The
addressed-bitplane interpretation was disproved and rolled back; no further
changes use it. Sprite reservation pointers remain a separate source case.

A capable-of-failing DMA read/write invariant identifies an independent read
mask bug at $200100; the existing write adapter already wraps chip addresses.
Masking DMA word reads independently of CPU decode passes all four supported
RAM capacities. This changes no saved fields.

The controlled wrap guest explicitly initialises low RAM to eliminate
Kickstart-allocation differences. Its control is exact, but continuous DMA
still has 275,300 differing pixels per field. The board renderer derives its
ordinary framebuffer x from Denise's counter, although registered drawing
advances its host buffer independently of that counter. Losing a STRHOR
strobe correctly leaves the hardware counter free-running. A provisional
experiment separates the host scan, without adding a clock or changing
version-50 fields. The user approved amending the raster-projection sentence
in `knowledge/decisions/amiga-denise-horizontal-counter.md` on 2026-10-06.
The decision now preserves Denise's hardware comparisons independently of
the physical host scan. Complete these bounded checks:

1. Add `lost_strobe_does_not_move_the_physical_host_scan` in
   `common-commodore-amiga/src/denise.rs`, varying the chip counter while
   preserving the physical beam/sample position. Run red before correction.
2. In that same file, derive connected host scan positions and the saved
   previous-line origin from the physical beam and the registered scan
   origin. Retire host prior-line context at the physical row boundary;
   preserve chip-counter comparisons and direct endpoint semantics.
3. Rebuild and rerun both controlled wrap guests at unchanged origins,
   ordinary 96-row timing and 128-guest raster, per-boundary snapshots,
   strict Clippy, component/broad regressions and required media gates.
   Keep any remaining failures visible; do not fit pixels or edit goldens.

The provisional experiment leaves 524 mismatched pixels in each continuous-DMA
field, with the hard-stop control exact. Of those, 492 are confined to the first
four common-raster columns; the other 32 occur at the right edge of the last
displayed row. All three captured fields repeat these counts. The full 96-row
timing comparison and six WAIT raster fields remain exact for this producer.
The unchanged 128-guest sweep passes: 384 fields, 333,268,992 RGB pixels, zero
differing fields, with producer/input hashes unchanged. Broad regressions finish
with eight failing targets; the source-bound DDF and other failures remain visible.
Complete raster accuracy is not claimed.

The host-scan regression now also checks a positively visible carried-tail
sample for both PAL line lengths at all three counter positions. All 137
shared-chip library tests, formatting and strict Clippy pass. The fresh
registered Test Kit runs retain the prior failures: OCS gradients 6 pixels;
AGA gradients 9 pixels and crosshatch 280 pixels. No assertions or goldens
were weakened.

Before a further reset change, trace the edge samples before and after
`drawing.cpp::draw_denise_line` host blanking in the private registered-source
copy. Verify its six complete fields against the baseline byte-for-byte.
The registered checkout remains immutable. Record whether the remaining
pixels originate in hardware comparisons, line-local reset or host policy;
do not emulate a frontend crop to obtain a green chip-accuracy result.

The private logging build preserves all six baseline fields byte-for-byte.
The logged host blanking pass changes none of the sampled edges. A separately
recorded run disables the reference's documented `display_optimizations`
shortcut, without changing guest, native producer or comparison origins.
Keep that diagnostic profile distinct from the unchanged registered corpus.

The `display_optimizations=none` run also preserves all six baseline fields
byte-for-byte and retains the same 524 differing pixels per HARDDIS field.
Neither sampled host blanking nor the shortcut renderer explains the residual.
The logging hook's current `this_line->linear_vpos` does not positively map
its samples to every captured output row; do not use that inferred mapping
as evidence of a chip fault. Trace the actual destination row and line-local
counter/reset events before another production correction. The approved host
scan amendment is implemented and checked; integrated accuracy remains open.

### Resolve the two wrap-edge signatures

Continue the engineering-frontier lane within the approved counter, combined
DMA descriptor and physical host-scan design. Investigate the 492 left-edge
pixels and 32 final-row tail pixels independently before changing production
behaviour.

1. Extend only the private reference `drawing.cpp` logging to identify actual
   framebuffer row/column from its buffer address and stride. Record line-start
   padding and row contents before/after drawing and host blanking. Preserve the
   registered source and verify all six baseline fields byte-for-byte.
2. Match those concrete writes against native physical output samples in
   `crates/common-commodore-amiga/src/denise.rs`, including the previous-line
   context and output gates. Use existing diagnostics or temporary logging;
   establish a source-backed reproduction before a fix.
3. Add an invariant regression at the responsible existing stage, verify that
   it fails before correction, and make the smallest correction supported by
   the trace. Preserve strict image assertions and fixed origins. A new saved
   stage or further binding decision amendment requires a concrete design first.
4. Rebuild and compare the paired controlled guests, ordinary DMA/Copper timing,
   existing raster corpus, relevant replay and component tests, Clippy and
   registered media gates. Attribute each result to its producer and retain
   every unresolved failure explicitly.

The address-based reference trace preserves all six fields and maps 283 logged
rows per guest exactly to final capture bytes. `get_line` writes the first four
columns as `DEBUG_LOL_COLOR` while applying `denise_lol_shift_prev=4`; these are
host padding, not Denise samples. The 492 left-edge differences stay visible in
the strict comparison until a separately justified capture contract resolves them.

The late-line trace identifies the 32-pixel tail loss independently. Reference
`custom_trigger_start` advances VPOS after h=1 and evaluates VDIW there; h=2 is
the first request/comparator cell seeing VSTOP. Native ECS/AGA currently close
VDIW at raw h=0. At v=$F4 this drops the last BPL3/BPL1 services at h=4/5.
Correct the existing ECS/AGA latch evaluation in
`crates/commodore-agnus-ecs/src/lib.rs` to the post-h=1 boundary. Add failing
latch-phase and full-sequencer service tests before changing it. Keep the current
snapshot fields, clock, descriptors and fixed image origins. This narrows the
previously unmeasured exact vertical-close cell; OCS timing is outside this fix.

### Wrap-edge result and verification

The existing ECS/AGA latch now changes before the h=2 request/comparator cell,
after preserving h=0/1. Both added regressions failed before the fix: the native
service sequence lacked `(4,2),(5,0)`, and VSTART was already active at h=0.
They now pass for ECS/Alice identities. The 78 ECS and 15 Alice chip tests pass;
existing Alice comparator tests now observe the documented h=2 boundary.
The new runtime replay test saves/restores at both half-CCK phases around the
boundary on actual ECS and AGA machines. It passes in debug and release.
No saved field, extra tick, dependency, image origin or mask changed.

The new native producer changes exactly 32 pixels, all on the final active
row's tail, and those now match the reference. The complete control framebuffer
is unchanged. The remaining 492 strict-image differences lie in the reference
host prefix. A second read-only probe captures composed samples before clipping:
6,840 control and 6,784 HARDDIS samples match native, including all 492 padded
mismatch positions. Retained columns 4–11 also match the raw reference as
coordinate anchors. Shifting by one pixel deliberately fails on 1,234 samples.
All six reference fields remain byte-identical after instrumentation. An empty
single-emitter trace was rejected before obtaining coverage across the actual
render paths. The combined patch applies to fresh registered sources and
reproduces all three recorded hashes.

Completed validation on the final producer:

- 128 unchanged guests, 384 fields, 333,268,992 RGB pixels: exact.
- Six WAIT fields, 5,207,328 RGB pixels: exact.
- 96 timing cases and all 3,060 DMA writes, finish, busy and Copper intervals:
  exact.
- Eight Workbench/boot regression matrix checks: pass.
- Strict Clippy for the affected chips/runtime and all targets: pass.
- Formatting and diff whitespace checks: pass.
- Broader tests: the same eight failing targets and 23 failing tests as the
  preceding baseline; no new failure. Ten chip/common/machine packages completed
  in debug. The unnecessarily slow debug runtime attempt was interrupted during
  the Workbench matrix and the complete runtime suite was rerun in release,
  matching the baseline profile. The non-runtime doc-test packages pass too.
- Registered Test Kit gates remain red: OCS gradients 6 pixels; AGA gradients
  9 pixels and crosshatch 280 pixels. The prior A1000 registered-archive gate
  remains unresolved; the passing regression matrix is not a replacement.

Durable provenance, trace patch and final validation summary are under
`test-data/commodore/amiga/rga-conflicts/`. Full logs and captures are in
`/private/tmp/emu198x-rga-edge-trace/`; `validation.json` indexes the results and
hashes the logs. The old strict capture still fails on host padding by design:
we have not silently changed its endpoint to declare the campaign complete.
A source-defined signal capture before host padding is the next validation
improvement; DDF register-write propagation and the existing failures remain
separate chip/integration work. This pass closes the actual wrap-edge DMA loss
and positively explains every residual pixel in the paired diagnostic.

### Next bounded investigation: DDF register-write propagation

Work remains in the best-in-class Amiga accuracy campaign. Before changing
production state, reproduce the distinct DDFSTRT and DDFSTOP write phases.

1. Add a source-hash-guarded probe under
   `test-data/commodore/amiga/ddf-register-writes/`. Reuse the existing DDF
   corpus extraction approach, compiling the registered `DDFSTRT`, `DDFSTOP`,
   `push_pipeline`, `empty_pipeline` and sequencer functions unchanged.
   Verify their enclosing `do_cck` order. Sweep old/new comparator coincidences,
   writes before/after the comparator, all three chip generations, masking,
   successive writes and line wrap. A deliberately immediate-write control
   must fail; static-register controls must agree.
2. Compare the same schedule with the current native Agnus stages, and
   reproduce a concrete Copper-delivered case through the shared driver.
   Record actual MOVE/service positions rather than trusting old tests that
   prime one Copper word and expect the other to retire immediately.
3. Record source observations in
   `reference/by-system/commodore-amiga/2026-copper-blitter-wake-observations.md`.
   Specify the smallest correction in `commodore-agnus-ocs/src/agnus.rs` and
   the shared driver, including snapshot preservation and validation. If it
   extends the approved saved-state design, obtain agreement on that concrete
   extension before production changes.
4. After agreement, implement the bounded stages; verify source corpus and
   connected Copper/CPU writes, replay at both CPU phases, affected regressions,
   unchanged live timing/raster guests, release Workbench and strict Clippy.
   Keep independent pre-existing failures visible.

#### DDF evidence and bounded design ready for agreement

The source-guarded corpus contains 1,128 distinct cases and 23,478 reference
reservations. Both the immediate-write reference negative control and the
current native handlers disagree in 76 cases; all 24 static controls match.
The initial sweep included redundant wrap/control rows; the final corpus
removes those duplicates. Three reference checks pin shared-queue flush order
for successive writes. This is compiled reference evidence, not a silicon
trace or a new live FS-UAE capture.

A connected native ECS Copper list proves the impact on actual DMA. A DDFSTRT
64→64 MOVE serviced at h=64 starts fetching at h=73 instead of suppressing
the start. A DDFSTOP 64→128 MOVE at h=64 cancels the old stop and reads eight
extra words, advancing BPL1PT 16 bytes too far. The same-value DDFSTOP control
matches reference requests h=65/73 and memory service h=67/75. The probes fail
with `native DDF register requests differ from reference` and
`2 connected DDF write cases failed`, respectively. Full logs are in
`/private/tmp/emu198x-ddf-register-writes/`.

Recommended bounded extension, pending approval:

1. In `crates/commodore-agnus-ocs/src/agnus.rs`, retain raw DDF register mirrors
   and add effective comparator copies plus one shared pending register/value
   entry. Follow the existing optional DMA-copy convention for direct chip
   initialization. DDFSTRT suppresses its comparator on write; DDFSTOP retains
   its old comparator. Repeated writes flush the previous shared entry in the
   reference order. Do not treat same-value writes as no-ops.
2. Retire that entry immediately after the existing request/comparator stage
   in `generate_display_dma_request`, before the shared driver executes CPU
   phases. A Copper-service write therefore affects the current comparator
   as above; a CPU write after that stage stays pending until the following
   comparison. Keep the single DMA authority and ordinary master-derived ticks.
3. Serialize the effective values and pending entry, advancing the runtime
   envelope to version 51 and rejecting version 50 before decoding. The prior
   pass produced and validated version-50 states; an explicit version boundary
   avoids accepting their shorter layout. Validate the new fields through
   `crates/runtime-commodore-amiga/src/variants.rs`, update
   `crates/runtime-commodore-amiga/src/snapshot.rs`, and extend diagnostics to
   distinguish raw mirrors and effective comparators.
4. Add red-to-green tests for the corpus and full connected Copper cases, then
   CPU register delivery and save/replay across both CPU phases, including a
   pending write at wrap. Verify all three installed Agnus generations and
   preserve static timing/raster controls. Reconcile old fixture assumptions
   only after observing their actual admitted/service cells.

An independent delay per register would disagree with the reference's shared
flush behaviour; moving all custom-register writes would unnecessarily affect
unrelated chips. The recommendation extends existing chip stages only. It
requires agreement because it adds saved state beyond the approved descriptor
and horizontal-counter extensions; no production change has been made here.

The DDF comparator/holding-stage design and version-51 boundary were explicitly
approved on 2026-10-06. Implementation and verification follow that bounded scope.

#### DDF implementation and final verification

The shared Agnus now retains effective DDF comparators and one typed pending
write. It retires that entry after the existing request/comparator stage.
Start suppression, old-stop retention and repeated-write flush order match
the compiled source. The installed CPU and Copper paths keep their existing
clock and service ordering. Version 51 preserves the new fields and rejects
version 50 before decoding; malformed pending values fail candidate validation
without altering the destination. Diagnostics expose the pending write.

All 1,128 reference cases and 23,478 requests match: the previous 76
discrepancies are gone. The unchanged immediate-write negative control still
fails in exactly 76 cases. Nine additional compiled reference schedules
establish the connected Copper cases and the repaired ECS test boundaries.
The latter previously primed one Copper word directly, skipped admission and
expected immediate memory service. They now execute a complete Copper list
and check actual reservation and memory-service positions. All five former
ECS DDF failures pass.

The new runtime tests cover both DDF registers, both CPU delivery phases and
ordinary/wrap boundaries on OCS, ECS and AGA. They verify pending-state replay,
nonzero real pointer movement where expected, no fetch after a suppressed
start, and atomic rejection of malformed state. CPU bus delivery is controlled
by the test; CPU instruction-to-register timing is not a new conformance claim.

Final validation on the version-51 producer:

- All 384 unchanged raster fields match: 333,268,992 RGB pixels.
- All 96 timing cases match, including 3,060 DMA writes and their finish,
  busy and Copper intervals. Six WAIT fields match another 5,207,328 pixels.
- Both native wrap PNGs are byte-identical to the preceding validated pass.
  The strict HARDDIS screenshot comparison still retains the 492 previously
  explained reference-padding differences per field; no crop or mask changed.
- All eight Workbench/boot matrix tests pass. The full eleven-package release
  sweep, with the complete snapshot target rerun, has 1,232 passing tests and
  18 existing failures in seven targets. Five prior failures are closed and
  there are no new failures. The first run caught two remaining version-50
  header assertions; after updating those to 51, the entire snapshot target
  reports 52 passed and its one pre-existing failure.
- Strict Clippy passes for the affected chips, ECS machine and runtime across
  all targets. Formatting, Ruff, fixture reproduction and whitespace checks pass.

The broad suite remains red, verbatim:

```text
error: 7 targets failed:
    `-p machine-commodore-amiga-a1200 --lib`
    `-p machine-commodore-amiga-ocs --lib`
    `-p machine-commodore-amiga-ocs --test blitter_completion`
    `-p machine-commodore-amiga-ocs --test ddf_hard_stop`
    `-p machine-commodore-amiga-ocs --test fat_agnus_8372a_extensions`
    `-p runtime-commodore-amiga --test collisions`
    `-p runtime-commodore-amiga --test snapshot_roundtrip`
```

The registered Test Kit gates retain these exact existing errors (diagnostic
directory suffixes omitted):

```text
gradients: expected an exact match but pixels differ; 6 pixels differ (0.002940%); first at (702, 18), expected RGB4 $000, actual RGB4 $DDD; bounding box (702, 18)..(703, 273)
gradients: expected an exact match but pixels differ; 9 pixels differ (0.004185%); first at (714, 18), expected RGB8 #000000, actual RGB8 #DDDDDD; bounding box (714, 18)..(716, 273)
crosshatch: expected an exact match but pixels differ; 280 pixels differ (0.130189%); first at (726, 11), expected RGB8 #FFFFFF, actual RGB8 #000000; bounding box (726, 11)..(745, 271)
```

The first line is OCS; the other two are AGA. The prior A1000 registered-media
identity issue remains separate. These open gates prevent a full Amiga accuracy
claim; they do not invalidate the measured DDF correction.

`test-data/commodore/amiga/ddf-register-writes/final-validation.json` preserves
the final counts, producer hash, remaining failure names and log hashes.
Full captures and logs are under `/private/tmp/emu198x-ddf-register-writes/`.
The new decision is `knowledge/decisions/amiga-ddf-register-write-stage.md`.

## Next bounded pass: OCS DDF boundary regressions

Continue the approved accuracy campaign by tracing the remaining DDF boundary
failures before changing assertions or production behaviour.

1. Reproduce `machine-commodore-amiga-ocs/tests/ddf_hard_stop.rs` and the
   open-hard-start snapshot regression in
   `runtime-commodore-amiga/tests/snapshot_roundtrip.rs`. Record real Copper
   writes, display reservations, memory services and pointer movement.
2. Reuse the registered source extraction under
   `test-data/commodore/amiga/ddf-register-writes/` to measure the hard-stop
   rewrite and the idle-line early-start schedules. For HARDDIS, distinguish
   pending cross-wrap service and combined refresh effects from word counts.
3. Repair only assertions/setup disproved by those traces. If production
   behaviour differs, identify the responsible existing stage before fixing it;
   any additional saved state or architectural extension needs separate agreement.
4. Run the affected release test targets and strict Clippy. Preserve negative
   controls and record remaining failures without weakening pixel gates.

### DDF boundary findings and corrections

The four remaining DDF failures are stale test boundaries, confirmed with
native stage traces and seven compiled registered-source schedules:

- The Copper setup delivered DDFSTOP at $DA instead of its asserted $D8.
  Admission before $D5 now delivers both real words at $D6/$D8. The test checks
  terminal memory service at $DB and next-line h=0, including pointer advances.
- The open-gate postcard test expected service at the $10 comparator.
  Reference requests begin at $12 and services at $14. The repaired test
  checks both sequences and snapshot equality after every half CCK.
- HARDDIS's extra $E2 reservation is still in flight at next-line h=0.
  Both normal and equal-boundary fixtures now compare the entire first-line
  reservation schedule, completed byte counts and retained cross-wrap state.
- The overrun fixture previously counted refresh-induced pointer replacement
  as display bytes. It now establishes an idle incoming line and explicitly
  verifies the following BPL4 read and BPL2/STRHOR combined service.

The new source-fragment fixture is `test-data/commodore/amiga/ddf-boundaries/`:
seven cases, 1,556 requests, and a reversed-order negative control that differs
in all seven cases. It does not claim a new full-reference-machine capture.
The machine tests consume the recorded reservation schedules directly.
Only tests, fixtures and documentation changed; the validated version-51
production code and existing strict pixel gates are unchanged.

Validation: all five boundary tests and all 53 snapshot-roundtrip tests pass in
release mode. Strict release Clippy passes for the OCS machine and runtime,
including every test target. The registered CSV and verification JSON reproduce
byte for byte; Cargo formatting, Ruff and whitespace checks pass. Before-fix
traces and final logs are under `/private/tmp/emu198x-ddf-boundaries/`; hashes
and counts are retained in the fixture's `validation.json`.

This closes four of the 18 failures in the preceding broad sweep and makes two
previously failing targets green. The other 14 failures have not been rerun in
this test-only pass. Existing Test Kit and full-reference capture limitations
remain; no new production-raster conformance claim is made. The next bounded
investigation is the remaining bus-ownership/Copper tests, followed by the
blitter-completion and mixed-chip DIWHIGH failures.

## Next bounded pass: Copper and chip-bus ownership

1. Reproduce the ten remaining OCS library failures in release mode; preserve
   the red log in `/private/tmp/emu198x-bus-ownership/`.
2. Trace the existing request/address/service descriptors alongside Copper IR1,
   IR2, blitter phases, disk FIFO completion and mature CPU bus transactions.
   Consult the registered FS-UAE scheduling and existing compiled timing
   fixtures before changing any observation boundary.
3. In `crates/machine-commodore-amiga-ocs/src/lib.rs`, repair setups that bypass
   required admission and assert actual memory effects, held ownership across
   both CPU phases and restore, and priority controls. Keep any production fix
   confined to the responsible existing stage; further saved state or a new
   architectural extension requires its own concrete proposal.
4. Run the complete OCS library tests, related DMA integration tests and strict
   Clippy. Record what genuinely closes and preserve any remaining failures.

### Copper and ownership result

All ten prior OCS library failures are resolved. The complete target reports
39 passed, zero failed, and strict all-target Clippy passes. Related disk,
blitter and shared DMA-stage integration targets also pass. The repairs run
real admissions before checking service; the priority controls explicitly
present the CPU transaction after the preceding half CCK, so it remains
pending at arbitration. No production behaviour changed.

The next bounded checks cover the four remaining failures in
`machine-commodore-amiga-ocs/tests/blitter_completion.rs`,
`machine-commodore-amiga-ocs/tests/fat_agnus_8372a_extensions.rs`,
`machine-commodore-amiga-a1200/src/lib.rs` and
`runtime-commodore-amiga/tests/collisions.rs`. Reproduce each, distinguish
register/comparator state from service and software observations, and preserve
positive controls. Run every affected target before the full release sweep.

### All fourteen remaining regressions closed

The four additional failures also came from stale observation boundaries:

- BFD first becomes idle on an even CCK; Copper resumes its returning WAIT1
  comparison on the next odd/free input cell, while final D remains withheld.
- The DIWHIGH fixture's equal DDF limits ran across line wrap, where combined
  refresh replaces the pointer. An ordinary in-line fetch window now isolates
  the vertical-gate comparison; separate fixtures retain the wrap coverage.
- The first AGA wide fetch is reserved at $14, addressed at $15, serviced at
  $16 and delivered to Lisa at $17. The test uses real board clocks through
  line reset, then checks its held tail with both blank and set-bit controls.
- CLXCON with no enabled comparisons permits collision bit 0 to relatch.
  Real guest programs on OCS, ECS and AGA now compare that case with an enabled
  BP1 comparison that deliberately mismatches, checking two destructive reads.

The pinned-source AGA fixture emits eight requests and reproduces byte for
byte. Reversing comparator/request order changes the result. This establishes
the request schedule, not a new whole-machine or physical-hardware claim.

All fourteen prior failures now pass. The complete eleven-package release
sweep exits successfully: 1,250 passed, zero failed, 121 explicitly ignored
tests across 188 target results, including documentation tests. All 53 runtime
snapshot-roundtrip tests pass. Strict release Clippy with all targets and
`-D warnings` passes for both affected machine crates and the Amiga runtime.
Cargo formatting, fixture reproduction, Ruff and whitespace checks pass.
The separate golden-matrix run also passes all eight tests with
`EMU198X_REQUIRE_GOLDEN_ASSETS=1`, so missing private media cannot turn those
checks into skips. Golden updates were disabled.

This pass changes tests, fixtures and documentation only. Production timing
and snapshot version 51 are unchanged. The fixture's
`test-data/commodore/amiga/bus-ownership/validation.json` preserves the closed
failure names, counts, scope and log hashes; full logs remain under
`/private/tmp/emu198x-bus-ownership/`.

The separately gated Test Kit image differences remain open: six pixels in
OCS gradients, nine in AGA gradients and 280 in the AGA crosshatch. Those gates
were not rerun or relaxed here. The strict wrap capture's 492 host-padding
differences and the A1000 archive media-identity limitation also remain as
previously recorded. The next accuracy investigation should trace those
remaining Test Kit pixel differences against the registered full-machine
captures before changing production output.

## Next bounded pass: Test Kit right-edge pixels

1. Reproduce both strict profile gates with the registered media and preserve
   their unchanged reference manifests, assertions and diagnostic images in
   `/private/tmp/emu198x-test-kit-edges/`.
2. Trace the failing gradient and crosshatch samples through the existing
   `common-commodore-amiga/src/denise.rs` raster carry, independent horizontal
   counter, DIW gate, and concrete Denise/Lisa output stages. Compare with the
   pinned full-reference source and guest register/data stream. Distinguish
   output signal from host capture clipping before selecting a correction.
3. Correct only the responsible existing stage, with a failing regression and
   control cases covering both chipset families and line-wrap boundaries.
   Preserve crops, images and exact assertions. Any new architectural stage or
   saved-state layout needs a concrete proposal and approval first.
4. Rerun both strict Test Kit gates, affected chip/machine and replay tests,
   the relevant independent raster corpus, required-media boot goldens and
   strict Clippy. Record exact results and any remaining evidence boundary.

### Test Kit edge diagnosis and proposed display-window correction

Both strict gates reproduce the recorded 6/9/280 pixel failures. The live AGA
trace retains Test Kit's DIWSTRT=$1B51 and DIWSTOP=$37D1 for crosshatch.
Denise reaches 455, then commits the strobe reset to 2 at raw h=4/5. Its
horizontal stop is $1D1 (465), so no stop comparison has occurred. The current
interval predicate closes the gate as soon as the counter resets. The first
missing canonical column, 726, maps exactly to that h=5 output.

Registered FS-UAE `drawing.cpp` uses `do_hstrt_aga`/`do_hstop_aga` to retain
`denise_hdiw` between equality events; its strobe handler changes the counter
without closing this latch. Independently, Minimig's `rtl/denise.v` updates
`window` only on start/stop equality. Test Kit v1.21's `testkit/video.c::grid`
programs the same overscan limits and supplies real white serial data on the
fourteen affected lines. This is software/RTL evidence, not a silicon capture.

The proposed bounded design extends the existing board-level Denise comparator
state with its horizontal-window latch. Clock start/stop equality at every
existing output tick, retaining the established OCS/ECS before-output and AGA
after-output phases. Counter resets and physical row changes must not close
the latch. Preserve it in diagnostics and snapshots; advance the runtime
envelope to version 52 and reject version 51. Test stop-before-reset and
stop-beyond-reset controls plus half-CCK save/replay. Do not change framebuffer
dimensions, crop, reference images or image tolerances to correct this signal.

Separately, the gradient trace shows COLOR00=$000 arriving at h=2 of the next
line after a WAIT at $DD. The current admission predicate excludes the final
odd Copper input cell; the registered reference generator has no such cutoff.
Test and trace that boundary before correcting the existing admission rule.

### Approved edge corrections implemented

The horizontal-window latch and snapshot version 52 were approved and are now
implemented in the existing Denise stages. The final odd Copper input cell is
also admitted by the existing arbitration predicate. Framebuffer geometry,
reference images, crops and exact comparison tolerances are unchanged.

Both explicit Test Kit gates now pass all six registered patterns, including
both alternating-checkerboard phases. The 6 OCS gradient pixels, 9 AGA gradient
pixels and 280 AGA crosshatch pixels all match their reference captures.
The new PAL/NTSC Copper regression passes its six boundary cases. The latch
regressions distinguish a real stop comparison from a skipped stop and retain
both states through half-CCK save/restore on OCS, ECS and AGA. Replacing the
production equality latch with the former interval predicate makes the
isolated regression fail at counter reset.

The timing rerun matches all 96 rows and 3,060 DMA writes, including finish,
busy and Copper intervals. Both WAIT raster cases match all six reference
fields (5,207,328 RGB pixels). The full release suite, strict Clippy and the
128-guest display corpus are still running; final results follow below once
their exit status and coverage have been checked.

The first full release sweep completed with 1,251 passes and two failures.
`border_blank_replaces_color_zero_only_when_enabled_and_outside_display`
reported `ECSENA=true, BRDRBLNK=true, BPL1DAT=true, DIW=true`, with black
`4278190080` instead of red `4294901760`: its synthetic mid-line setup had
never clocked HSTART. The fixture now clocks that comparison before its
existing border-control matrix. `denise_board_pipeline_exposes_complete_bounded_state_on_every_chipset`
compared an old field list against diagnostics containing the approved
`horizontal_diw_active` field. It now includes the field, checks its initial
state and compares the discoverable leaf with the live chip state. Both full
test targets pass (2 border tests and 43 query tests), and strict Clippy
passes again. These are test repairs; production output is unchanged. A
complete release rerun is in progress, with the initial failing log retained.

The final eleven-package release rerun exits successfully: 1,253 passed,
zero failed and 121 explicitly ignored tests across 189 target results,
including documentation tests. All 54 snapshot-roundtrip tests and all eight
golden-matrix tests pass. Required golden assets were enforced and golden
updates explicitly disabled. Strict release Clippy with all targets and
`-D warnings` also exits successfully after the test repairs. The display
corpus is the only remaining running check.

### Test Kit edge correction validated

The final display run exits successfully. All 128 identity-checked guests
match all 384 registered reference fields: 333,268,992 compared RGB pixels
and zero mismatches. Guest readiness was checked and producer/input hashes
remained unchanged throughout capture. Together with the six WAIT fields,
96 timing rows, both strict Test Kit profile gates and the clean release
suite, this closes the three measured Test Kit edge discrepancies without
resizing the framebuffer or changing the reference contracts.

`test-data/commodore/amiga/test-kit-edges/validation.json` records the exact
counts, before/after failures, source and producer identities, negative
control, saved-state version, and hashes of the retained logs. Cargo
formatting, Ruff and whitespace checks pass. Snapshot version 52 deliberately
rejects version 51, as approved.

This establishes the tested software-reference agreement. The earlier strict
HARDDIS wrap capture's 492 host-padding differences were not rerun or claimed
fixed here. The separate A1000 archive media-identity limitation and untested
horizontal DIWHIGH propagation remain outside this correction. No physical
hardware calibration or complete Amiga accuracy claim follows from these
results.
