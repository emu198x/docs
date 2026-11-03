# Atari 5200 owners and Oric board qualification

Lane: engineering-frontier work. Steve approved continuing these pieces on
2026-11-03 after the controller and media prerequisites merged.

## Scope

Finish source #2241 and docs #176 first (both now merged). Review extraction
fix #2252 without editing its active workspace. Then implement the three
manufacturer-backed 5200 owners under #2144, subject to the wiring checks
below. Continue Oric qualification before assigning revision-specific owners.
Use the existing fixed-board/common-engine pattern; do not change chip timing,
introduce dependencies outside the approved private split, or publish crates.

## Tasks

1. Reinspect the 5200 service manual's original and universal schematics,
   especially missing ports and A12/A13 on CA021374. Consult the vendored
   Altirra implementation for controller selection and inactive returns. Add
   any new hardware findings to the umbrella reference layer first. Do not
   substitute an assumed open input or duplicated owner for verified wiring.
2. Freeze current version-20 5200 continuations before moving code. Include
   all four held input caches, between-scan restore, cartridge layouts, reset,
   firmware replacement, framebuffer/audio and complete final state. Keep
   original bytes independent of the new implementation.
3. Move family wiring and cartridge/controller modules from
   `crates/machine-atari-5200/src/` into `crates/common-atari-5200/`. Introduce
   fixed CA018087, CA020108 and CA021374 owners using the existing Atari
   XL/XE pattern. Each owner must fix its controller wiring and identity.
   Preserve legacy profile IDs only where mapping is justified; distinguish
   a legacy emulator configuration from a fully qualified physical machine.
4. Route the three owners through `crates/runtime-atari-5200/src/`, and
   update workspace manifests, system registry and direct owner tests.
   Preserve version-20 bytes and strict selected-profile restore semantics
   where possible. If board identity requires a new envelope or a legacy
   migration policy, write the exact proposal and obtain approval first.
5. Run old/new frozen continuations, all 5200 controller and restored-media
   tests, format, focused Clippy, system registry and meaningful negative
   controls. Retain real-firmware identities without distributing ROMs.
   Verify full applicable CI before merging the source PR.
6. Read the merged Oric primary audit (#294), inspect manufacturer PCB and
   circuit issue drawings plus modification leaflets, and compare current
   wiring against an identified fitted population. Record remaining source
   gaps explicitly; BN0130 and a BASIC ROM name alone do not prove an issue.
   Update `systems/atari/5200.md`, `systems/oric/atmos.md` and #2144 only for
   the qualification actually established.

## Workspaces and cleanup

Source: `/private/tmp/198x-5200-board-source`; docs:
`/private/tmp/198x-5200-board-docs`; temporary manual renderings:
`/private/tmp/198x-5200-board-pdfs`. Keep build output in a separate bounded
cache. Preserve unrelated primary checkouts and the earlier locked Atari/PET
investigations. Verify task commits/evidence on remote refs before removing
finished worktrees, caches and renderings.
