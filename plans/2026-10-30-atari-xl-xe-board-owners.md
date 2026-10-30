# Atari XL/XE board owners

Engineering-frontier continuation of #2144. Steve approved the split programme
and asked to continue on 2026-10-30. Apply the established private-workspace
owner/common/runtime pattern to the four existing XL/XE profiles. This is the
next scoped continuation of the release-wait exceptions; no registry crate is
added or published.

## Board and compatibility contract

| Fixed owner | Existing profile ID | Hardware |
|---|---|---|
| `machine-atari-800xl` | `atari-800xl-ntsc` | 800XL NTSC, 64 KiB |
| `machine-atari-800xl-pal` | `atari-800xl-pal` | 800XL PAL, 64 KiB |
| `machine-atari-130xe-ntsc` | `atari-130xe-ntsc` | 130XE NTSC, extended RAM controller |
| `machine-atari-130xe-pal` | `atari-130xe-pal` | 130XE PAL, extended RAM controller |

The extra controller and independent CPU/ANTIC PORTB banking make the 130XE
more than a RAM-fit profile. Source anchors are the umbrella's
`reference/by-system/atari-8bit/completeandessentialmapforthexlxepartii.txt`,
printed pages 288–289, and the NTSC/PAL section of
`1982-atari-400-800-hardware-manual.txt`. The former has OCR/table errors;
retain the existing tested bit mapping and consult the read-only Altirra and
Atari800 implementations for precedent. No chip, timing or banking algorithm
redesign is part of this ownership extraction.

Keep `runtime-atari-800xl`, the family runner, aliases, firmware IDs, BASIC
policy, parsed cartridge mapper, modified SIO disks and pending XEX handling.
Keep snapshot **version 21**, envelope field order and all raw-state serde
attributes. The old DTO names ending V2 remain untouched. Each fixed owner
serializes transparently as the original state. Decode raw state, validate
region, memory-controller type, RAM size and raster geometry, then bind to the
selected board before changing time, XEX or runtime caches. Foreign or forged
board payloads reject atomically; empty saves retain the selected profile.

## Work and verification

1. Before moving code, add the private recipe
   `crates/runtime-atari-800xl/src/board_baseline_tests.rs`. Capture all four
   profiles with flat and banked project-owned cartridges, modified disk
   sectors, pending XEX bytes, keyboard/controller state, active POKEY audio,
   extended RAM markers and a partial frame. Freeze complete starting and
   continued v21 envelopes, every frame pixel/dimension/timestamp and sample
   bit under `test-data/atari-800xl/board-split-v21/`, with SHA-256 provenance.
   Normal replay must require the files; corrupt an expected pixel to prove
   it fails, restore it, then run green before committing the baseline.
2. Move `crates/machine-atari-800xl/src/` and component tests into
   `crates/common-atari-800xl/`, renaming the serializable state only. Compare
   every moved engine file after declared type/export/comment changes. Add
   `common-atari-800xl/src/board.rs` and four thin fixed owner crates. Hide
   the old consuming `with_memory` operation from fixed owners.
3. Add `runtime-atari-800xl/src/machine.rs` for static family dispatch.
   Update construction, input, queries, profiles and snapshot modules; do not
   change the shared host contract. Preserve legacy saves and media behavior.
   Add direct guest boot/input/bank/native-boundary evidence per owner plus
   forged-header and cross-profile rejection tests. Re-run baseline replay.
4. Update `Cargo.toml`, `Cargo.lock`, `docs/status/systems.toml` and rendered
   status pages. Keep the existing base machine ID for the NTSC 800XL and add
   three IDs for the other boards. The family keeps its existing issue label
   and milestone; each board must have exclusive evidence ownership.
5. Run targeted owner/common/runtime/runner checks, strict Clippy/rustdoc,
   format, registry, fixture and documentation guards, and fleet/browser
   conformance. Exercise local original firmware where staged. Inspect CI's
   per-board ledger before merging the exact tested head.
6. In the site repo, map all four IDs to their exact existing player profiles,
   retain the pinned player, make the existing 800XL capture select NTSC,
   update expected routes and verify build, tests and accessibility. Merge
   only after the flagship registry, then verify all live pages and mappings.
7. Update #2144 with evidence and any separate accuracy gaps. Verify commit
   retention before removing worktrees, pinned UI clones, build/download
   caches, captures and task processes. Preserve active PET and 5200 work.
