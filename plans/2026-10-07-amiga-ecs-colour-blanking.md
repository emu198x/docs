# ECS colour and programmable blanking accuracy

The user approved investigating ECS Copper colour timing and programmable
blanking after the Lisa counter-origin correction. This continues the Amiga
accuracy campaign, using the existing stages and reference producers.

1. Reuse the independent SPHX colour guest with A500+ / Kickstart 2.04.
   Capture native output and three complete reference fields, requiring the
   guest identity and all 600 active-line counter-origin observations. Retain
   source/binary/ROM/ADF hashes and failing RGB edges. Use OCS and AGA controls.
2. Inspect the existing programmable-blanking corpus and reference stages.
   Reproduce static and timed HBSTRT/HBSTOP behaviour with colour markers;
   separate counter origin, comparator phase and register delivery. Preserve
   reference pixels and native framebuffer coordinates.
3. If the trace confirms an extra ECS colour tick, correct the concrete chip
   dispatch hook in `common-commodore-amiga/src/denise_chip.rs`, keeping the saved board
   queue/layout for compatibility. First make a counter-backed output test
   fail, then verify CPU/post-output behaviour and saved-state replay in
   `common-commodore-amiga/src/denise.rs` and existing runtime tests. Record
   the evidence and updated binding phase decision before production edits.
   Any additional pipeline/schema design needs a separate concrete proposal.
4. Validate affected chip/machine/runtime tests, strict Clippy, existing
   blanking gates and both Test Kit lanes as applicable. Requalify a reference
   transform only from independently measured origins, retaining old records.
5. Rerun the wider 128-guest graphics corpus using trace-backed mapping, then
   extend combined HAM/dual-playfield/sprite/mid-line probes where coverage is
   missing. Diagnose each additional issue before its own bounded correction.

Primary observations go to
`reference/by-system/commodore-amiga/2026-ecs-colour-blanking-observations.md`.
Diagnostics and validation go under
`test-data/commodore/amiga/ecs-output-phase/ecs-colour-blanking/`.

## Confirmed corrections

- ECS COLOR00: remove the extra board pre-output queue through the existing
  concrete-chip hook. Four edges were one lores tick late. The corrected
  control is exact in all three fields; snapshot 53 is unchanged.
- Lisa programmed HBLANK: compare the next lores counter's four fine samples,
  as the reference does. Ten controls now agree across all 200 active lines,
  including fine positions in all three resolutions, wrap, equal edges and
  selectors. The separate top-of-field blanking discrepancy remains recorded.
- Blanking consumers retain native captures at either width, declare width in
  evidence, and reject differing samples before projecting to the old hires
  grid. The timed gate uses independently measured raw+6 hires mapping and
  the current serviced Copper counter (142/146). Its five AGA rows pass.

## Approved ECS signal stages — implemented and verified

ECS programmed HBLANK arrives seven lores ticks early. The central guest
produces native Denise counters 248..312 while the reference produces
255..319. The wrapping guest independently gives 120/408 versus 127/415.
Each of three complete fields differs at 32,032 samples in both guests.
The native machine directly consumes Agnus's routed blanking level.

Reference `drawing.cpp::do_denise_cck` consumes the blanking flag from the
cell three CCKs earlier; `expand_drga_blanken` and the ECS horizontal loop
retain another half-CCK level before output. This explains seven ticks
without fitting a pixel displacement.

Approved by the user on 2026-10-07: extend the existing `DeniseEcs` output
stages with the three CCK signal samples and the half-CCK output level. Sample routed Agnus blanking
on the existing machine clock; apply ECSENA/EXTBLKEN at the display-visible
stage. Preserve incoming/retained state in snapshot 54, rejecting 53.
The global snapshot version also covers Lisa's embedded ECS state; Lisa
continues to use its own programmed comparator. Do not add a clock or change
Agnus coordinates. Keep the reference's signal stages explicit rather than
adding a framebuffer offset.

Alternative: a board-level blanking pipeline would add ECS-specific state and
policy to the shared wrapper. Prefer the existing concrete ECS chip stages.

Exact affected files:

- `crates/commodore-denise-ecs/src/lib.rs`: retained CSYNC blanking samples,
  stage advancement and validation.
- `crates/machine-commodore-amiga-ecs/src/lib.rs`: deliver the routed signal
  through those stages at existing CCK/lores boundaries.
- `crates/runtime-commodore-amiga/src/{snapshot,live_access,queries}.rs`:
  snapshot version, diagnostic state and replay visibility.
- `crates/runtime-commodore-amiga/tests/{snapshot_roundtrip,queries,
  amiga_programmable_hblank,amiga_programmable_hblank_write_timing}.rs`:
  in-flight replay, negative controls and the registered guests.

Verify both static edge pairs, every intermediate stage and both half-CCK
restore points. Then rerun all ten timed cases, retaining any selector or
field-counter disagreement. Requalify the static consensus gate's obsolete
absolute coordinates from source evidence; do not replace its assertions
with native measurements. Keep OCS/AGA colour controls and strict Test Kit
lanes unchanged. The 128-guest sweep and additional mode combinations must
retain their independent failures rather than being called globally exact.

## Verification completed before the next design approval

- Common/ECS/Lisa chip and integration tests pass, with all 54 runtime
  snapshot tests passing after the final comparator correction.
- Strict Clippy passes for six affected packages and all targets.
- Both Test Kit lanes pass all six unchanged exact-reference cases.
- All seventeen neutral blanking guests rebuild byte-identically.
- Requalified timed gate: five AGA cases pass; ECS remains red (three edge
  disagreements and two non-adjacent guest-field capture rejections).
- Static gate remains red on its obsolete full-viewport margin assertion;
  its native-width measurement is repaired but expectations are preserved.
- The broad sweep exposes three palette-XOR guests at 128 samples per field.
  Two were recaptured with full counter traces: all six fresh fields are
  byte-identical to their retained references and reproduce the discrepancy.

Before widening the programmed comparator claim, probe low edge values near
Denise strobe reset. The source passes a pending next counter at the second
half-CCK, which can differ from current+1; the ten ordinary controls do not
establish that boundary. No strobe-boundary failure has been measured yet.

The completed 128-guest sweep has 375 exact fields and nine failing fields,
all three palette-XOR variants at 128 RGB samples each. The input, native
executable and retained reference hashes are unchanged across the sweep.
Additional HAM/dual-playfield/sprite combinations remain follow-up work after
the confirmed stage/phase discrepancies; this pass does not claim that wider
combination coverage is complete.

## Snapshot 54 results (2026-10-07)

The approved stages now sample routed Agnus blanking at phase zero, retain
three CCK levels, and expose the oldest level on the following half-CCK.
Display-visible ECSENA/EXTBLKEN select that delayed output. The existing
clock and coordinates are unchanged. `denise.csync_blanking` exposes every
retained level. Snapshot 54 preserves them and explicitly rejects version 53.

All eight counter-traced ECS controls are exact across all three retained
fields: 24 fields and 20,774,208 compared RGB samples. Central and wrapping
blanking each improve from 32,032 mismatches per field to zero. The colour,
selector-disabled, BLANKEN-clear and equal-edge controls remain exact.
Input, reference and native executable hashes were checked across capture.
The archive is `ecs-colour-blanking/stage54/` in the existing evidence tree.

Validation passes 234 chip/machine tests, 44 query tests, all 55 snapshot
tests, strict Clippy for six packages/all targets, and both six-case Test Kit
video lanes. The new restore test visits exactly fourteen nonuniform signal
states: three pending CCK stages at each half-clock boundary and the final
half-CCK stage, on both rising and falling edges. It compares the complete
machine payload and framebuffer with the machine that was never restored.
The runtime's cached host pixel statistics are refreshed on restore; direct
chip ticks do not refresh those statistics, so that test compares chip state
rather than stale host counters.

The machine-level Copper-colour test still expected the superseded ECS board
queue. It failed with `left: 2748`, `right: 291`; its assertion now follows the
approved, reference-verified immediate ECS colour delivery. Two older snapshot
tests pinned version 53 and now pin 54. No production workaround was needed.

The ten-case timed gate improves from five to seven passing cases. All five
AGA cases remain exact. ECS HBSTOP-future and late-BLANKEN controls pass.
Three failures remain, with complete result records retained:

- ECSENA enable: expected black [396,526), actual [398,526) in host-hires
  samples. The outgoing blank edge now agrees; the selector edge remains one
  lores tick late.
- EXTBLKEN enable: `guest field counters are not adjacent: 9 then 11`.
- HBSTRT-past: `guest field counters are not adjacent: 10 then 12`.

The old static cross-family gate still needs independent registration work.
The counter-traced FS-UAE control validates the new stages, but one software
family cannot requalify a cross-family absolute-coordinate contract. Its
obsolete full-viewport margin assertion is retained, not replaced with native
measurements. That registration work, the selector stage, and the two capture
failures remain follow-up items. The earlier 128-guest result and its three
palette-XOR failures are unchanged historical evidence, not a rerun for 54.

The selector, guest-label and static-registration follow-up is now complete;
see [blanking residuals](2026-10-07-amiga-blanking-residuals.md). All ten timed
and fourteen static cases pass. Earlier failures above remain baseline
evidence, not current blockers. Snapshot 54's saved layout is unchanged.
