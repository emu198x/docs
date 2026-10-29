# Next regional board splits

Engineering-frontier continuation of #2144, following the completed five-family
batch and the request to keep working through the remaining machines.

## Scope

| Family | Concrete owners | Existing profiles / state version |
|---|---|---|
| ZX80 | `machine-sinclair-zx80` (50 Hz), `machine-sinclair-zx80-usa` (D11 fitted) | stock, USA, 16K pack; v4 |
| ZX81 | `machine-sinclair-zx81` (50 Hz), `machine-timex-ts1000` (pin 22 grounded) | stock, 16K pack, TS1000; v5 |
| Atari 2600 | `machine-atari-2600` (NTSC), `machine-atari-2600-pal` | existing NTSC/PAL; v2 |
| Atari 7800 | `machine-atari-7800` (NTSC), `machine-atari-7800-pal` | existing NTSC/PAL; v6 |

Keep one runner/runtime per family, existing profile IDs and aliases. RAM packs
remain profiles. Move the original engines and their component tests into
`common-sinclair-zx80`, `common-sinclair-zx81`, `common-atari-2600` and
`common-atari-7800`. Fixed owners serialize the original state transparently;
selection remains in each runtime. No new registry package or chip/timing
redesign is part of this batch.

The current release-wait note predates this continuation. Record this batch
alongside the existing scoped exceptions; do not infer authorization for
unresearched board identities. Leave the active PET and C64/drive worktrees
alone. Aquarius PAL needs a runtime exposure decision; Amiga and other rows
marked check still require their source audits.

## Legacy ZX restore decision

ZX80 and ZX81 currently write the same family `model_id` for every profile.
Their payload carries the TV strap and fitted RAM. The old reader accepts a
foreign strap/RAM state without updating the runtime's selected Model, so a
valid USA/TS1000 save can run under a misleading UK profile label.

Decision: require the selected profile to match the saved hardware (Steve,
2026-10-29). Preserve v4/v5 bytes and the existing shared family header, but
validate the payload's strap and RAM against the selected profile before any
receiver mutation. Do not adopt a different runtime Model from a save. Loading
an old USA/TS1000 or RAM-pack state therefore requires selecting its matching
existing profile explicitly. Empty states retain the selected profile because
there is no hardware payload to identify. Mismatches and malformed states
reject atomically. Add direct-runtime and loader regression checks for this
contract; no nominal timing or format-version changes are implied.

## Work and verification

1. Read each core, runtime and source anchors. ZX80 D11 and ZX81 pin 22 are
   documented in `reference/by-system/sinclair-zx80/` and `sinclair-zx81/`.
   Check Atari primary/programming references before moving region wiring.
2. Before extraction, add per-family original-state captures under
   `test-data/{zx80,zx81,atari-2600,atari-7800}/board-split-*`, with test-only recipes in
   `runtime-*/src/board_baseline_tests.rs` where private clock alignment is
   needed, plus normal replay tests. ZX recipes live privately in each common
   engine's `src/board_baseline_tests.rs`, where they can capture after 37
   T-states without widening a production API solely for testing. Normal
   runtime tests replay the same envelopes and verify host output separately.
   Cover every existing profile, partial CPU/video phase, keyboard/controller,
   tape/cartridge state and audio. Compare full initial/continued state and
   every native-frame pixel, dimension, timestamp and audio sample bit. Prove
   replay fails on a deliberately corrupted expected frame.
3. For each family, move `crates/machine-*/src/` unchanged except raw-state
   names/imports into its common crate. Add fixed owners and
   `runtime-*/src/machine.rs`; adjust `profiles.rs`, `runtime.rs`, `input.rs`,
   `queries.rs` and `snapshot.rs` as required. Keep snapshot field order,
   attributes and versions. Validate hardware binding before receiver mutation.
   Run that family's tests before committing and moving to the next family.
4. Update root `Cargo.toml`/`Cargo.lock`, affected runner imports,
   `docs/status/systems.toml` and generated status pages. Give each board its
   own fixture-free boot/control, foreign-state and native-boundary evidence.
   Preserve actual software-driven ZX/TIA frame boundaries, including no-frame
   stops; nominal frame budgets are not hardware frame counters.
5. Run targeted runtime/runner/owner tests, original firmware/cartridge gates
   where available, strict Clippy/rustdoc, fleet/browser conformance, formatting
   and registry/document/fixture guards. Compare the moved engine source with
   the baseline after only declared renames/export/format normalization.
6. Inspect CI's per-board evidence before merging the exact checked head.
   Reconcile the site's explicit profile mappings, captures and routes with
   the new registry and pinned player; verify the built and live output.
7. Update #2144 with the completed owners and any separately tracked accuracy
   gaps. Verify retention and remove the task worktrees, clones, caches and
   background processes before reporting completion.

Atari source audit: PAL 2600 profile metadata advertised the NTSC clock while
the existing core/TIA use PAL timing. Correct the profile using TiaRegion's
canonical crystal frequency, with a red/green agreement test. Preserve the
original engine clocks. The 7800 captures include cartridge POKEY native output
without claiming the runtime currently mixes it into the TIA host packet; its
existing PAL border-placement uncertainty remains separate accuracy work.

## Verification record

All four extracted engine implementations match the original source after
explicit type/import/export changes, documentation-link fixes and formatting.
No CPU/chip/timing algorithm changes are part of extraction. Each of the eight
owners has four fixture-free tests. Frozen states and complete output cover
all ten existing profiles, including F8 banks and independent native cartridge
POKEY samples. ZX runtime tests cover every selected/saved profile pair,
explicit RAM overrides and the snapshot-only loader. Deliberately corrupted
expected rasters fail before the original files are restored.

The ZX fixtures preserve the existing video safety completion. They do not
establish that a fallback completion represents a physical VSYNC edge; that
accuracy concern remains separate from physical ownership.
