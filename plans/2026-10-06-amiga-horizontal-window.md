# Amiga horizontal-window and graphics-combination validation

The user authorized the next accuracy investigations after the version-52
Test Kit edge correction. Start with horizontal DIWHIGH and timed DIW writes;
then extend reference-backed graphics-combination probes. Preserve all existing
reference pixels, beam mappings, clock ownership and variant timing policies.

## 1. Reproduce window differences

- Read registered FS-UAE drawing/register stages, vendored vAmiga/Minimig and
  the primary display-register material. Separate ECS coarse extension from
  AGA fine positions and write-order behaviour.
- Add project-authored diagnostic guests under
  `emu198x/test-data/commodore/amiga/horizontal-window/`, reusing the existing
  bootloader and SPHX ready record. Include legacy and explicit-zero controls,
  extended start/stop, fine positions and timed start/stop rewrites.
- Capture three adjacent fields with the existing full-resolution reference
  producer and current native binary. Retain source, binary, media and guest
  hashes. Require ready records and use the unchanged whole-raster comparator.

## 2. Correct the demonstrated stage

- Trace `common-commodore-amiga/src/denise.rs`, register delivery in
  `memory.rs` and concrete machine adapters, and Denise/Lisa output gates.
- Record actual failing samples and the responsible register/comparator phase
  before changing production code. Agree any new retained pipeline state or
  snapshot schema change with a concrete design and evidence first.
- Add invariant regressions, controls and half-CCK replay for affected stages.
  Correct the existing pipeline only; no content-aligned crops or fitted delays.
- Verify focused tests and reference captures, strict Clippy and formatting,
  then the relevant broader raster/replay/Test Kit gates. Record limits.

## 3. Exercise graphics combinations

- Reuse the proven guest/capture path to combine HAM, sprite/playfield priority
  and timed register changes. Keep controls that isolate each contributing
  stage and use distinct data words where repeated patterns can hide faults.
- Diagnose each mismatch before proposing the next bounded correction. Treat
  new retained state or architecture as a separate design decision.

Each correction remains one self-contained change. This plan does not expand
the approved scope into disk formats, later CPU models or analogue audio.

## Reproduction and proposed correction

Seventeen real A1200 guests produce 51 full-raster field comparisons against
the existing pinned FS-UAE producer: 33 fail, 18 pass. Legacy and explicit
equivalent controls are exact. Coarse start/stop extensions fail by 409,600
and 390,400 pixels per field. Fine start and visible fine stop offsets fail
by 400/800/1,200 pixels. Timed start, stop and high-register rewrites fail by
1,952, 1,536 and 14,528 pixels per field. Original stop probes whose data ran
out early are retained as masking controls; they cannot establish fine-stop
accuracy. The source-defined common raster and comparator are unchanged.

The native gate ignores horizontal DIWHIGH and samples Agnus's immediate
DIW mirrors. The reference retains separate Denise registers in its normal
RGA stage, then compares horizontal limits at output-sample granularity.
The primary observations are in
`198x/reference/by-system/commodore-amiga/2026-horizontal-window-observations.md`.

Recommended bounded design:

1. Retain Denise-side DIWSTRT, DIWSTOP, DIWHIGH and explicit-high mode in the
   existing board pipeline. Route CPU/Copper window writes to both chips;
   keep Agnus's vertical stage distinct. Carry incoming and pending register
   writes through the existing output clock, following normal RGA delivery.
   Calibrate the additional ECS DIWHIGH phase before claiming that variant.
2. Extend the existing horizontal latch comparison to the four Lisa samples
   already produced per lores tick. Decode ECS coarse bits and AGA fine bits
   according to the installed Denise variant, preserving the existing
   OCS/ECS versus Lisa comparison phase. Do not move framebuffer coordinates.
   Retain Lisa's per-sample gate history through its existing output delay;
   delaying by one sample instead of one lores tick would shift legacy edges.
3. Pass sample-level visibility into the existing playfield/sprite priority,
   collision and HAM composition path. A final RGB mask would leave those
   internal states wrong. Preserve compatibility entry points for uniform
   gates used by isolated chip tests.
4. Serialize the delivered registers, explicit-high mode, pending stages and
   per-sample output-gate history with the retained window latch in snapshot
   version 53, rejecting version 52. Validate pending stages before restore;
   replay both half-CCK phases.

Files: `common-commodore-amiga/src/denise.rs`, `denise_chip.rs`, existing
OCS/ECS/AGA output adapters, `commodore-denise-ocs/src/chip.rs`, the three
machine register dispatchers, and runtime snapshot/query/replay tests.

Alternative: decode only the coarse bits from Agnus. This would leave the
measured fine-position and whole-line rewrite failures. A post-render crop or
mask would also leave sprite priority, HAM and collision state uncorrected.
The recommended change extends the existing chip stages; it needs agreement
for additional retained state and the version-53 snapshot break before code.

The completed read-only native traces each contain 440 observations. On the
start-rewrite guest's line 135, DIWSTRT changes from $2CC1 to $2C81 at h=100,
with next Denise counter 193 and the window still closed. The old HSTART=193
match is lost. On line 136 the same rewrite arrives at h=102 after that match,
and the latch remains open. The stop-rewrite trace likewise distinguishes
delivery before and after HSTOP=257. These traces support the location of the
fault; independent expected pixels come from the reference fields.

All seventeen ADFs reproduce byte for byte after formatter changes. The
unchanged comparator exits 1 with 33 failing fields. Both trace executions
exit 0 after checking SPHX readiness. The new example builds and passes
strict release Clippy; Rust formatting, Ruff and whitespace checks pass.
The user approved the described stage extension and version-53 snapshot break.
Implementation and replay/reference validation follow; the graphics-combination
pass follows the window correction.

## Implemented stage and validation

The approved implementation uses `common-commodore-amiga/src/denise_window.rs`
for saved Denise-local register deliveries and four-sample output history.
CPU and Copper entry points retain their existing after/before-output bus
positions. The machine dispatchers send window writes to both display chips.
The common compositor consumes a sample gate before playfield priority and
collision evaluation; Lisa retains those gates for XOR/HAM colour resolution.
The uniform-gate chip entry points remain available. Snapshot 53 rejects 52.

The first focused sweep found four isolated fixtures that only configured
Agnus; their original pixel assertions are retained and the setup now also
programs Denise. The new fractional sprite test explicitly puts group zero
in front of the playfield. This avoids mistaking correct priority suppression
for a missing sprite gate.

Additional ECS lores controls use the same full-resolution reference producer
and the same beam-origin crop. Native 70 ns samples are each repeated twice
for comparison at 35 ns, without shifting or filtering them. Legacy and
explicit-legacy controls both disagree by 3,200 samples per field: each of
400 active rows has start and stop four reference samples early. The timed
and coarse-extension cases have the same edge displacement, without the
AGA baseline's missing-line failures. This is an open absolute ECS phase
question, not a passing full-raster validation. Four hires controls reproduce the same absolute edge disagreement. The established OCS/ECS phase remains unchanged in this correction.


The initial corrected AGA producer completes all seventeen guests and all
51 full-raster comparisons with zero mismatches (44,262,288 RGB samples).
The same comparison failed 33 fields before the correction. All 54 snapshot
round-trip tests pass, along with the three new pending-window/replay tests.
The corpus validation report distinguishes this initial candidate from the
final executable, rebuilt after removing redundant scalar gate storage.
The final executable also matches nine fields across timed-start rewrite,
maximum fine-start and maximum fine-stop guests. Source and binary hashes
identify both producers.

The hires control's data ends before HSTOP and its final-data edge is also
early. The next ECS trace must distinguish window timing from counter/output
and bitplane phase; changing only the gate is not justified by these images.


The broad sweep found one additional isolated ECS vertical-window fixture
that bypassed Denise and implicitly relied on ignored horizontal DIWHIGH.
Its setup now uses the machine dispatcher, settles register delivery, and
sets the intended HSTOP high bit explicitly. The original white-pixel
assertion remains. All 141 common-board and 30 ECS-machine library tests pass
on the final source, including both legacy latch tests now exercising the
production window stage rather than a test-only scalar helper.

Both strict Amiga Test Kit video gates pass all six patterns, with registered
input identities checked. All eight golden-matrix tests pass, including the
A1000 and A1200 Workbench boots. All seven distinct ROM/disk inputs were read
and hashed independently; golden-update mode was off. No reference image was
changed for this correction. The older 128-guest/384-field graphics corpus was
not rerun.

The scrolling and superhires board fixtures also bypassed the newly distinct
Denise registers. Their setup now sends window writes to both chips. Original
expected samples remain intact; positive foreground checks additionally
prevent blank-output comparisons from passing. The overfetch plane-alignment
fixture receives the same positive-content guard. These are test-only changes
after the final native capture; production source and binary identities remain
verified. Full sweep results and corrected-target reruns belong in
`test-data/commodore/amiga/horizontal-window/validation.json`.

The complete eleven-package release sweep finished with 1,250 passed,
10 failed and 121 ignored tests across 190 target results. Its exit was 101:

```text
error: 3 targets failed:
    `-p machine-commodore-amiga-ecs --lib`
    `-p runtime-commodore-amiga --test scroll_dma`
    `-p runtime-commodore-amiga --test superhires_dma`
```

The corrected targets pass all 30, eight and six tests respectively. The
border-blanking rerun passes both tests, and the final common-board rerun
passes all 141. All 1,260 executed tests are therefore covered by passing
original results or corrected-target reruns; this is not a second complete
sweep, and the 121 ignored tests remain unclaimed. The broad run independently
passes all 54 snapshot/replay tests. Strict release Clippy passes for all
affected production targets and the final fixture changes; formatting, Ruff
and whitespace checks pass.

The bounded version-53 correction is complete. The next accuracy task is to
trace ECS counter/output and serial-data phase against the retained failing
lores/hires controls, before changing any absolute edge. Wider graphics-mode
combinations remain subsequent work.
