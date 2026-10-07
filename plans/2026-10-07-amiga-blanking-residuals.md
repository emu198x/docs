# Amiga blanking residuals

Continue the approved accuracy campaign by fixing the three remaining timed
failures and requalifying the old static consumer. Preserve snapshot 54's
layout where the existing stages can represent the correction.

1. Trace ready-counter writes against actual video field boundaries in
   `crates/runtime-commodore-amiga/tests/amiga_programmable_hblank_write_timing.rs`.
   Check the neutral guest and shared session/runtime before attributing skipped
   counts to capture. Keep the existing failure records and adjacent-field rule.
2. Trace ECSENA/EXTBLKEN register delivery against the normal RGA reference stage.
   Correct only the demonstrated phase in `crates/commodore-denise-ecs/src/lib.rs`
   and its focused chip/runtime tests. Verify enabling and disabling both bits,
   static controls, all ten timed guests, and in-flight snapshot replay.
3. Re-read both static producer packages and their source-coordinate transforms.
   Fix the consumer in `tests/amiga_programmable_hblank.rs` using independently
   registered producer observations. Keep disagreements visible; do not fit
   native edge positions or promote one family to cross-family consensus.
4. Retain source observations, hashes, positive/negative controls and reports
   under the existing ECS blanking evidence tree. Run affected tests, Clippy,
   both blanking gates and Test Kit lanes before reporting the results.

Any additional retained chip state or schema change requires a concrete design
and separate approval. No new dependency, clock or framebuffer offset is planned.

## Completed

The selector fix retires the existing two-entry normal RGA history before
copying its oldest level into the output mirror. The mirror no longer adds
a third half-CCK. The source consumes BPLCON0/3 from the preceding CCK;
the focused test failed before the change and now passes. Repeated enable
and disable edges for each selector, plus restore at both stages, pass.
Snapshot 54's layout is unchanged.

The EXTBLKEN trace shows the guest label is published on either side of the
h=22 display-completion boundary. Video fields advance one at a time even
when labels read 9,11,11. The two HBLANK consumers share bounded helpers in
`tests/common/mod.rs`: retain the completed image, step through the existing
debugger interface to line one, require VERTB acknowledgement in the same
video field, and read the label. They request the next actual completed
field and require both video-field and guest-label adjacency. The first
adapter attempt used `run_ticks`, which this runtime does not implement;
that attempt failed explicitly and was replaced with the existing exact
instruction-step interface, which accounts for runtime clock and audio.

The static reference verifier under `tools/amiga-hblank-validation/` locks
both package hashes and validates records, APNGs, manifests, logs and decoded
pixels. It remeasures all 84 retained reference fields without a native image.
Nine comparator-coordinate agreements and five disagreements remain intact.
Copperline's post-render mask supplies comparator semantics, not UAE signal
latency. Absolute phase checks use the independent UAE counter origin and
native lores interval [4,381); no interior samples or mismatches are dropped.
All fourteen native static observations now have an explicit UAE phase check.

Validation:

- Ten timed cases pass (30 captured fields), retaining all source hashes.
- Fourteen static cases pass (42 captured fields); both field-adjacency
  checks are active and the five family disagreements remain labelled.
- All 205 affected chip tests, 44 query tests, five measurement tests,
  55 existing snapshot tests and the additional selector replay test pass.
- Two reference-admission tests pass, including a tampered-capture rejection.
- Strict Clippy passes for six packages and all targets; Rust/Python format
  checks, Ruff and shell syntax checks pass.
- Both six-case Test Kit video lanes remain exact, and the native emulator
  rebuild completes.

Durable evidence is under
`test-data/commodore/amiga/ecs-output-phase/ecs-colour-blanking/residuals/`.
Its validation manifest binds native/source/log hashes; `timed/` holds all
ten successful reports and the static log holds fourteen observations with
three native-frame hashes apiece. The baseline publication trace and failing
selector unit test are retained. The earlier palette-XOR, vertical boundary
and OCS far-edge residuals remain outside this completed slice.
