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

## Approved profile policy

Steve chose **retire the generic profile** on 2026-11-03. Remove
`atari-5200-ntsc` instead of assigning an uncertain legacy identity to
CA018087. Expose explicit assembly IDs for all three owners and require an
explicit native launch selection. Existing generic snapshots must reject
atomically with a clear model/profile error. Retain the v20 hardware payload
layout; compare frozen original continuations after changing only the test
fixture's envelope model ID, never as a production migration path.


## Verification and source qualification

Source #2253 implements the three explicit 5200 owners. The original v20
payload remains byte-identical under explicit four-port fixture envelopes;
retired generic and foreign-board saves reject atomically. The two-port
probe checks all 80 connected/missing-input cases, and changing its owner to
four ports makes the independent physical-port test fail. A separate red
restore test exposed the absent lower-fire case; validation now checks GTIA
as well as the held controller matrix before installation.

All three owners boot the verified real BIOS/Pac-Man inputs, produce six
colours and 90,240 non-background pixels, and preserve the complete next-frame
state after restore. Detailed logs and the private-asset probe source are in
[the evidence folder](2026-11-03-atari5200-board-evidence/README.md).
The initial hosted registry failure was stale generated pages; regeneration
and the existing checks fix it without weakening the gate. Full source CI
must still pass before the proposed status changes leave draft.

Oric qualification identified the original circuit issue 7 drawing and
archived both halves. Physical PCB issue and fitted-population mapping remain
open; the [matrix](2026-11-03-oric-board-qualification.md) names the concrete
source requirements. No additional Oric machine is counted.


## Source completion

Source #2253 merged as `43964e7098dca1d659113a1a5a2d48bf3181a778` after every
applicable hosted check passed. Its full suite records 8,597 passes, zero
failures, 713 ignored and 110 skipped tests. The status pages now describe
landed owners. Reference audits #296 and #297 are merged; extraction fix
#2252 and the prerequisite media/docs PRs #2241/#176 are also merged.

The original baseline worktree was removed after its exact generator and
all sixteen raw outputs were verified against the source commit retained
on the remote. Its disposable build cache was removed. The isolated primary
reference worktree was also verified clean and retained at the exact remote
PR ref before removal. The earlier locked investigations remain untouched.

Oric #345 still has the shared-firmware fallback fault. Its distinct
firmware-ID correction remains behind the existing explicit contract
approval; it is not silently folded into a board-name change. Physical PCB
issue and fitting qualification remain separate, even after firmware lookup
is corrected.
