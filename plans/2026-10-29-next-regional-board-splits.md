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

Proposed: preserve the v4/v5 bytes, recover the concrete owner and published
RAM profile from the payload before committing restore, and update the live
Model to match the restored hardware. Empty states retain the selected profile;
malformed or unsupported combinations reject atomically. This behaviour choice
needs agreement before implementing the ZX decoders. The alternative is strict
receiver-profile matching with explicit legacy-loader selection; that changes
old direct-restore acceptance. Atari work does not depend on this answer.

## Work and verification

1. Read each core, runtime and source anchors. ZX80 D11 and ZX81 pin 22 are
   documented in `reference/by-system/sinclair-zx80/` and `sinclair-zx81/`.
   Check Atari primary/programming references before moving region wiring.
2. Before extraction, add per-family original-state captures under
   `test-data/{zx80,zx81,atari-2600,atari-7800}/board-split-*`, with recipes in
   `runtime-*/examples/board_baseline.rs` and normal integration replay tests.
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
