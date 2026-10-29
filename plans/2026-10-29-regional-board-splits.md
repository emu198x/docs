# ColecoVision and SVI-328 regional board identities

Lane: engineering-frontier. Status: approved on 2026-10-29, including the
internal API/dependency changes and sequencing exception below. Continue the adopted
one-machine-per-crate decision using the Sord implementation merged in
emu198x/emu198x#2187.

## Scope and choices

Recommended: two independent, sequential family changes, ColecoVision first,
then SVI-328. Each gets two concrete regional machine crates over shared common
wiring. Keep the existing family binary/runtime, profile and firmware IDs,
browser route, and profile-based native state paths. The alternative is a data
correction batch alone, leaving the shared machine crates in place.

This replaces each old shared Rust construction API and adds six private
workspace crates/dependency edges. It adds no external registry package and
publishes nothing. Starting these rows now requires extending the Sord-only
exception to #2144's release-wait note; release PR #2170 is still open.

Aquarius is deferred from this batch: the machine offers PAL internally but the
runtime currently exposes only NTSC. Adding PAL there is a new runtime support
surface requiring its own hardware and firmware qualification. SVI-318 (#259)
is also separate work: fitted RAM chips and keyboard wiring need their own
board implementation, not a RAM-size switch inside SVI-328. Coleco staged
pre-BIOS snapshots (#2186) remain separate; no snapshot schema change is included.

## Tasks and exact owners

1. Work from current `origin/main` in isolated emulator task workspaces. Leave
   the primary extraction branch and other tasks untouched. Consult RULES.md,
   `knowledge/decisions/each-machine-has-its-own-machine-crate.md`, primary board
   references and vendored MAME configuration before moving code. Reuse the
   existing Sord static-board/common-core and family-enum conventions.
2. Before moving production code, inventory every serialized field and capture
   synthetic pre-split states for both regions in each family's `test-data/`
   directory. Add runtime compatibility tests and a capture example under
   `crates/runtime-{coleco-colecovision,spectravideo-svi-328}/`. Exercise actual
   video, audible audio, partial-field stepping, controller/key input, and for
   SVI its cassette transport and RAM banking. Record the source revision.
   Verify a deliberately changed expectation makes the comparison fail.
3. ColecoVision: move common code/history from
   `crates/machine-coleco-colecovision/` into `crates/common-coleco-colecovision/`;
   add `crates/machine-coleco-colecovision-{ntsc,pal}/`. Each constructor binds
   its board statically. Update `Cargo.toml`, `Cargo.lock`, family runtime
   imports/dispatch and app dependencies. Keep controller/NMI behaviour and
   the version-5 byte layout. Reject opposite-board states and falsely labelled
   payloads before mutating the receiving runtime.
4. SVI-328: analogously introduce `crates/common-spectravideo-svi-328/` and
   `crates/machine-spectravideo-svi-328-{ntsc,pal}/`. Move cassette common code
   with its existing state. Update workspace, runtime and app consumers. Keep
   version-7 bytes and all banking, keyboard/PPI, AY and cassette behaviour.
   No chip, clock, media, snapshot or memory-map redesign belongs to this split.
5. For each family, update `runtime-*/src/profiles.rs` and
   `docs/status/systems.toml` with distinct `machine_id` and `machine_crate`
   owners. Keep existing family issue labels/milestones as shared backlog
   links. Use the evidence ownership machinery added for Sord. Update/regenerate
   `docs/status/{current-system-usability,outstanding-work}.md`; verify fleet
   catalogue and routes under `crates/emu198x-fleet-web/`.
6. Audit current profile and knowledge wording against the primary library.
   Corrections to hardware facts go first to umbrella `reference/by-system/`
   in their owning repository. Distinguish primary chip/board evidence from
   MAME configuration precedent. Remove stale emulator-design advice from
   hardware references where it contradicts the adopted board boundary.

## Verification and finish

For each family: compare original field order and execution method bodies;
restore/re-encode and continue frozen states with identical complete state,
pixels, audio and native frame times; exercise wrong-board rejection with a
matching receiving profile so the older name guard cannot mask a missing board
check. Run machine/common/runtime/app tests, identified local firmware tests
where available, strict Clippy, formatting, fleet catalogue/capability tests,
status-script tests, registry and generated-page checks. Report missing matched
regional firmware as a qualification gap, not a pass.

Commit and push one verified family change at a time. Merge only after every
reported check on the exact head completes successfully or is intentionally
skipped; inspect the CI evidence artifact for distinct nonempty board owners
and shared common/runtime evidence. Update only the completed rows of #2144.
Prove commits retained remotely, inspect tracked/untracked/ignored files, then
remove task worktrees/caches/processes. Preserve unrelated work and worktrees.

## Independent reference correction completed

Umbrella PR stevehill1981/198x#288 removes the stale instruction to collapse
SVI-318/328 into a RAM-size parameter. The original service-manual scan was
rendered and visually checked at printed p. 4.45 / PDF p. 78: eight 4116 chips
for 16 KiB user RAM, eight 4164 chips for 64 KiB, and separate 16 KiB VRAM.
This documentation correction is merged. Both family splits were approved
on 2026-10-29; ColecoVision proceeds first, followed by SVI-328.
